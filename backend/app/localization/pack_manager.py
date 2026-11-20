"""Signed, resumable, atomic language-pack manager.

Packs are data only. No script, binary, archive member, or manifest field is
ever executed. Existing valid packs are preserved on any failed update.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import stat
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .clinical import PackGovernanceError, validate_pack_governance
from .language_registry import LanguageRegistry
from .pack_schema import LanguagePackManifest, parse_version, version_ge
from .runtime import ENGINE_VERSION

MAX_PACK_FILE_BYTES = 10 * 1024 * 1024
MAX_PACK_TOTAL_BYTES = 50 * 1024 * 1024
ALLOWED_SUFFIXES = {".json", ".md", ".txt", ".woff", ".woff2", ".ttf", ".otf"}
FORBIDDEN_SUFFIXES = {
    ".exe", ".dll", ".so", ".dylib", ".js", ".mjs", ".cjs", ".py", ".pyc",
    ".sh", ".bash", ".bat", ".cmd", ".ps1", ".apk", ".ipa", ".dmg", ".jar",
}

State = str

_ALLOWED_TRANSITIONS: dict[State, set[State]] = {
    "NOT_INSTALLED": {"AVAILABLE", "QUEUED", "DISABLED"},
    "AVAILABLE": {"QUEUED", "DISABLED"},
    "QUEUED": {"DOWNLOADING", "FAILED", "NOT_INSTALLED"},
    "DOWNLOADING": {"VERIFYING", "FAILED", "QUEUED"},
    "VERIFYING": {"INSTALLING", "FAILED"},
    "INSTALLING": {"READY", "ROLLBACK_REQUIRED", "FAILED"},
    "READY": {"UPDATE_AVAILABLE", "DISABLED", "QUEUED"},
    "UPDATE_AVAILABLE": {"QUEUED", "DISABLED"},
    "FAILED": {"QUEUED", "NOT_INSTALLED", "DISABLED"},
    "ROLLBACK_REQUIRED": {"READY", "DISABLED"},
    "DISABLED": {"AVAILABLE", "NOT_INSTALLED"},
}


class PackError(ValueError):
    """Base error for pack-manager failures."""


class InvalidStateTransition(PackError):
    pass


class SignatureVerificationError(PackError):
    pass


class IntegrityError(PackError):
    pass


class CompatibilityError(PackError):
    pass


class UnsafeArchiveError(PackError):
    pass


class DownloadIncompleteError(PackError):
    pass


class StorageQuotaError(PackError):
    pass


class ApprovalError(PackError):
    pass


@dataclass(slots=True)
class DownloadSession:
    download_id: str
    language_id: str
    status: State
    downloaded_bytes: int = 0
    total_bytes: int = 0
    resumable: bool = True
    last_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        progress = 0.0 if not self.total_bytes else min(1.0, self.downloaded_bytes / self.total_bytes)
        return {
            "status": self.status,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "progress": round(progress, 6),
            "last_error": self.last_error,
            "resumable": self.resumable,
        }


@dataclass(slots=True)
class VerificationResult:
    manifest: LanguagePackManifest
    files: dict[str, bytes]
    content_hash: str


class PackManager:
    """Manages pack lifecycle in a local root directory.

    A transport callable may be injected for HTTP range downloads. It must accept
    ``(language_id, offset)`` and return the remaining byte payload.
    """

    def __init__(
        self,
        root: Path,
        registry: LanguageRegistry,
        *,
        public_key: bytes | None = None,
        allow_synthetic_packs: bool = False,
        max_total_bytes: int = MAX_PACK_TOTAL_BYTES,
    ) -> None:
        self.root = Path(root)
        self.registry = registry
        self.allow_synthetic_packs = allow_synthetic_packs
        self.max_total_bytes = max_total_bytes
        self._public_key, self._public_key_error = self._load_public_key(public_key)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self._state: dict[str, dict[str, object]] = self._load_state()

    def _load_state(self) -> dict[str, dict[str, object]]:
        if not self.state_path.exists():
            return {"languages": {}}
        with self.state_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload.setdefault("languages", {})
        return payload

    def _save_state(self) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, sort_keys=True, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.state_path)

    def _language_state(self, language_id: str) -> dict[str, object]:
        return self._state["languages"].setdefault(
            language_id,
            {"state": "NOT_INSTALLED", "active_version": None, "previous_version": None},
        )

    def state(self, language_id: str) -> State:
        return str(self._language_state(language_id)["state"])

    def active_version(self, language_id: str) -> str | None:
        value = self._language_state(language_id)["active_version"]
        return str(value) if value else None

    def transition(self, language_id: str, target: State) -> None:
        current = self.state(language_id)
        if target not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidStateTransition(f"{current} -> {target} is not permitted for {language_id}")
        self._language_state(language_id)["state"] = target
        self._save_state()

    def _prepare_for_install(self, language_id: str, pack_version: str) -> None:
        current = self.state(language_id)
        active = self.active_version(language_id)
        if current == "READY" and active == pack_version:
            return
        if current == "DOWNLOADING":
            self.transition(language_id, "VERIFYING")
            return
        if current == "READY" and active != pack_version:
            self.transition(language_id, "UPDATE_AVAILABLE")
        if current in {"READY", "UPDATE_AVAILABLE", "NOT_INSTALLED", "AVAILABLE", "FAILED", "ROLLBACK_REQUIRED", "DISABLED"}:
            if current not in {"READY", "UPDATE_AVAILABLE"}:
                if current != "NOT_INSTALLED":
                    self.transition(language_id, "NOT_INSTALLED")
                self.transition(language_id, "QUEUED")
            self.transition(language_id, "DOWNLOADING")
            self.transition(language_id, "VERIFYING")

    @staticmethod
    def _load_public_key(explicit: bytes | None) -> tuple[bytes | None, str | None]:
        if explicit:
            return explicit, None
        encoded = os.getenv("GULS_PACK_PUBLIC_KEY_B64")
        if encoded:
            try:
                return base64.b64decode(encoded, validate=True), None
            except (ValueError, TypeError):
                # Never fail application import because of malformed deployment
                # configuration. Verification fails with a stable error instead.
                return None, "configured language-pack public key is invalid"
        path = os.getenv("GULS_PACK_PUBLIC_KEY_PATH")
        if path:
            key_path = Path(path)
            if key_path.exists():
                return key_path.read_bytes(), None
            return None, "configured language-pack public key file is missing"
        return None, None

    def verify(self, pack_bytes: bytes, language_id: str, *, expected_hash: str | None = None) -> VerificationResult:
        definition = self.registry.require(language_id)
        files = self._safe_extract(pack_bytes)
        manifest_bytes = files.get("manifest.json")
        if manifest_bytes is None:
            raise IntegrityError("manifest.json is missing")
        try:
            manifest = LanguagePackManifest.model_validate_json(manifest_bytes)
        except Exception as exc:  # pydantic validation errors are intentionally normalized
            raise IntegrityError(f"invalid manifest: {exc}") from exc

        if manifest.language_id != language_id:
            raise IntegrityError("manifest language_id does not match requested language")
        if manifest.locale_tag != definition.locale_tag:
            raise IntegrityError("manifest locale_tag is not approved for this language")
        if manifest.direction != definition.direction:
            raise CompatibilityError("manifest direction is not approved for this language")
        if manifest.script != definition.script:
            raise CompatibilityError("manifest script is not approved for this language")
        if not version_ge(ENGINE_VERSION, manifest.minimum_engine_version):
            raise CompatibilityError("pack requires a newer language engine")
        try:
            validate_pack_governance(
                definition,
                catalogs=manifest.catalogs,
                files=files,
                approval_status=manifest.approval_status,
                allow_synthetic=self.allow_synthetic_packs,
            )
        except PackGovernanceError as exc:
            raise ApprovalError(str(exc)) from exc

        expected_files = {entry.path: entry for entry in manifest.files}
        actual_paths = set(files) - {"manifest.json"}
        if set(expected_files) != actual_paths:
            raise IntegrityError("manifest file list does not match archive contents")
        for path, entry in expected_files.items():
            digest = hashlib.sha256(files[path]).hexdigest()
            if digest != entry.sha256 or len(files[path]) != entry.size:
                raise IntegrityError(f"content mismatch for {path}")
        computed_hash = self._content_hash(files)
        if computed_hash != manifest.content_hash:
            raise IntegrityError("content hash mismatch")
        if expected_hash and expected_hash != manifest.content_hash:
            raise IntegrityError("expected hash mismatch")

        self._verify_signature(manifest)
        return VerificationResult(manifest=manifest, files=files, content_hash=computed_hash)

    @staticmethod
    def _content_hash(files: Mapping[str, bytes]) -> str:
        digest = hashlib.sha256()
        for path in sorted(files):
            if path == "manifest.json":
                continue
            file_digest = hashlib.sha256(files[path]).hexdigest()
            digest.update(f"{path}:{file_digest}:{len(files[path])}\n".encode())
        return digest.hexdigest()

    def _verify_signature(self, manifest: LanguagePackManifest) -> None:
        if self._public_key_error:
            raise SignatureVerificationError(self._public_key_error)
        if not self._public_key:
            raise SignatureVerificationError("no trusted language-pack public key configured")
        try:
            ed25519_key = Ed25519PublicKey.from_public_bytes(self._public_key)
            ed25519_key.verify(base64.b64decode(manifest.signature, validate=True), manifest.signing_payload())
        except (InvalidSignature, ValueError, TypeError) as exc:
            raise SignatureVerificationError("invalid language-pack signature") from exc

    def _safe_extract(self, pack_bytes: bytes) -> dict[str, bytes]:
        extracted: dict[str, bytes] = {}
        total = 0
        try:
            with zipfile.ZipFile(io.BytesIO(pack_bytes)) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    path = PurePosixPath(info.filename)
                    if path.is_absolute() or ".." in path.parts:
                        raise UnsafeArchiveError(f"unsafe archive path: {info.filename}")
                    mode = (info.external_attr >> 16) & 0o170000
                    if mode == stat.S_IFLNK:
                        raise UnsafeArchiveError(f"symlink entries are forbidden: {info.filename}")
                    suffix = path.suffix.lower()
                    name = path.name
                    if suffix in FORBIDDEN_SUFFIXES:
                        raise UnsafeArchiveError(f"executable content is forbidden: {info.filename}")
                    if name != "manifest.json" and suffix not in ALLOWED_SUFFIXES:
                        raise UnsafeArchiveError(f"disallowed pack file type: {info.filename}")
                    if info.file_size > MAX_PACK_FILE_BYTES:
                        raise UnsafeArchiveError(f"file too large: {info.filename}")
                    total += info.file_size
                    if total > self.max_total_bytes:
                        raise UnsafeArchiveError("archive exceeds total size limit")
                    extracted[info.filename] = archive.read(info)
        except zipfile.BadZipFile as exc:
            raise UnsafeArchiveError("invalid zip archive") from exc
        return extracted

    def download(
        self,
        language_id: str,
        *,
        expected_size: int | None = None,
        transport: Callable[[str, int], bytes] | None = None,
        resume_from: int = 0,
        download_id: str,
    ) -> tuple[DownloadSession, bytes]:
        """Create/continue a download session and return the accumulated bytes."""
        definition = self.registry.require(language_id)
        if not definition.is_active:
            raise ApprovalError(f"language is not active: {language_id}")
        if not definition.is_publishable and not self.allow_synthetic_packs:
            raise ApprovalError(f"language pack is not publishable: {language_id}")
        current = self.state(language_id)
        if resume_from <= 0 and current in {"DOWNLOADING", "VERIFYING", "INSTALLING", "QUEUED"}:
            raise PackError(f"a download or installation is already in progress for {language_id}")
        if current in {"NOT_INSTALLED", "AVAILABLE"} or current in {"FAILED", "UPDATE_AVAILABLE"}:
            self.transition(language_id, "QUEUED")
        if self.state(language_id) == "QUEUED":
            self.transition(language_id, "DOWNLOADING")

        total = int(expected_size or 0)
        chunk = transport(language_id, resume_from) if transport else b""
        downloaded = resume_from + len(chunk)
        session = DownloadSession(
            download_id=download_id,
            language_id=language_id,
            status="DOWNLOADING",
            downloaded_bytes=downloaded,
            total_bytes=total,
            resumable=True,
        )
        if total and downloaded > total:
            session.status = "FAILED"
            session.last_error = "downloaded_bytes_exceeds_expected_size"
            self.transition(language_id, "FAILED")
            raise DownloadIncompleteError(session.last_error)
        if total and downloaded < total:
            session.last_error = "partial_download_resumable"
            return session, chunk
        return session, chunk

    def install(self, language_id: str, pack_bytes: bytes, *, expected_hash: str | None = None) -> LanguagePackManifest:
        """Verify then atomically install a pack, preserving the previous version.

        The active version is changed only after all files are written and
        fsynced. A failed verification or write therefore leaves the currently
        active pack untouched.
        """
        verification = self.verify(pack_bytes, language_id, expected_hash=expected_hash)
        manifest = verification.manifest
        current_active = self.active_version(language_id)

        if current_active == manifest.pack_version and self.state(language_id) == "READY":
            return manifest
        if current_active and parse_version(manifest.pack_version) < parse_version(current_active):
            raise CompatibilityError("language-pack downgrade is not permitted")

        state = self.state(language_id)
        try:
            if state == "DOWNLOADING":
                self.transition(language_id, "VERIFYING")
            elif state == "VERIFYING":
                pass
            elif state == "READY":
                self.transition(language_id, "UPDATE_AVAILABLE")
                self.transition(language_id, "QUEUED")
                self.transition(language_id, "DOWNLOADING")
                self.transition(language_id, "VERIFYING")
            elif state == "UPDATE_AVAILABLE":
                self.transition(language_id, "QUEUED")
                self.transition(language_id, "DOWNLOADING")
                self.transition(language_id, "VERIFYING")
            elif state in {"NOT_INSTALLED", "AVAILABLE", "FAILED", "ROLLBACK_REQUIRED", "DISABLED"}:
                if state != "NOT_INSTALLED":
                    self.transition(language_id, "NOT_INSTALLED")
                self.transition(language_id, "QUEUED")
                self.transition(language_id, "DOWNLOADING")
                self.transition(language_id, "VERIFYING")
            else:
                raise InvalidStateTransition(f"cannot install from state {state} for {language_id}")

            self.transition(language_id, "INSTALLING")
            self._write_pack(language_id, manifest, verification.files)
        except Exception:
            entry = self._language_state(language_id)
            if current_active:
                # The active version and its files were never replaced.
                entry["active_version"] = current_active
                entry["state"] = "READY"
            else:
                entry["active_version"] = None
                entry["state"] = "FAILED"
            self._save_state()
            raise

        entry = self._language_state(language_id)
        entry["previous_version"] = current_active
        entry["active_version"] = manifest.pack_version
        entry["state"] = "READY"
        self._save_state()
        return manifest

    def rollback(self, language_id: str) -> str:
        entry = self._language_state(language_id)
        previous = entry.get("previous_version")
        if not previous:
            raise PackError(f"no previous pack version available for {language_id}")
        entry["active_version"] = previous
        entry["previous_version"] = None
        entry["state"] = "READY"
        self._save_state()
        return str(previous)

    def active_catalog(self, language_id: str, catalog_name: str) -> dict[str, str]:
        version = self.active_version(language_id)
        if not version or self.state(language_id) != "READY":
            raise PackError(f"language pack is not ready: {language_id}")
        path = self.root / "packs" / language_id / version / "catalogs" / f"{catalog_name}.json"
        if not path.exists():
            raise PackError(f"catalog not found: {language_id}/{catalog_name}")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise PackError(f"invalid catalog: {language_id}/{catalog_name}")
        return {str(key): str(value) for key, value in payload.items()}

    def remove(self, language_id: str, *, force: bool = False) -> None:
        entry = self._language_state(language_id)
        if entry.get("state") == "READY" and not force:
            raise PackError("refusing to remove an active ready pack without force")
        version = entry.get("active_version")
        if version:
            target = self.root / "packs" / language_id / str(version)
            if target.exists():
                for item in target.iterdir():
                    if item.is_file():
                        item.unlink()
                target.rmdir()
        entry.update({"state": "NOT_INSTALLED", "active_version": None, "previous_version": None})
        self._save_state()

    def check_storage_quota(self, additional_bytes: int = 0) -> None:
        used = sum(item.stat().st_size for item in self.root.rglob("*") if item.is_file())
        if used + additional_bytes > self.max_total_bytes:
            raise StorageQuotaError("language pack storage quota exceeded")

    @staticmethod
    def compute_content_hash(files: Mapping[str, bytes]) -> str:
        return PackManager._content_hash(files)

    def _write_pack(self, language_id: str, manifest: LanguagePackManifest, files: Mapping[str, bytes]) -> None:
        """Write to a staging directory, then swap it into place atomically.

        Stale staging directories from an interrupted write are removed. If a
        target version already exists, it is moved aside before the swap and
        restored if the swap fails.
        """
        language_root = self.root / "packs" / language_id
        language_root.mkdir(parents=True, exist_ok=True)
        for stale in language_root.glob(".staging-*"):
            shutil.rmtree(stale, ignore_errors=True)

        token = os.urandom(8).hex()
        staging = language_root / f".staging-{manifest.pack_version}-{token}"
        target = language_root / manifest.pack_version
        backup = language_root / f".backup-{manifest.pack_version}-{token}"
        staging.mkdir(parents=False, exist_ok=False)
        try:
            payload = dict(files)
            payload["manifest.json"] = manifest.model_dump_json(indent=2).encode("utf-8")
            for path, content in payload.items():
                destination = staging / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
            if target.exists():
                target.rename(backup)
            try:
                staging.rename(target)
            except Exception:
                if backup.exists():
                    backup.rename(target)
                raise
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        else:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
