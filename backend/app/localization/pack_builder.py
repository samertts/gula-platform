"""Build signed language-pack archives for release tooling and tests.

Private signing keys are supplied by the caller and are never written into a
pack or repository. Production keys must come from a protected signing environment.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .clinical import validate_pack_governance
from .language_registry import LanguageRegistry
from .pack_manager import (
    ALLOWED_SUFFIXES,
    FORBIDDEN_SUFFIXES,
    MAX_PACK_FILE_BYTES,
    MAX_PACK_TOTAL_BYTES,
    PackManager,
    UnsafeArchiveError,
)
from .pack_schema import LanguagePackManifest


def _validate_pack_files(files: Mapping[str, bytes]) -> None:
    """Reject unsafe pack inputs before any signing or archive creation."""
    total = 0
    for raw_path, content in files.items():
        if raw_path == "manifest.json":
            raise UnsafeArchiveError("source files must not contain manifest.json")
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise UnsafeArchiveError(f"unsafe pack path: {raw_path}")
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            raise UnsafeArchiveError(f"executable content is forbidden: {raw_path}")
        if suffix not in ALLOWED_SUFFIXES:
            raise UnsafeArchiveError(f"disallowed pack file type: {raw_path}")
        if len(content) > MAX_PACK_FILE_BYTES:
            raise UnsafeArchiveError(f"file too large: {raw_path}")
        total += len(content)
    if total > MAX_PACK_TOTAL_BYTES:
        raise UnsafeArchiveError("pack exceeds total size limit")


def build_signed_pack(
    *,
    registry: LanguageRegistry,
    private_key: Ed25519PrivateKey,
    language_id: str,
    pack_version: str,
    signer_key_id: str,
    publisher: str,
    files: Mapping[str, bytes],
    approval_status: str = "synthetic_test_only",
    native_name: str | None = None,
    created_at: datetime | None = None,
) -> bytes:
    """Create a deterministic signed zip archive from data-only files."""
    definition = registry.require(language_id)
    if definition.locale_tag is None or definition.direction is None or definition.script is None:
        raise ValueError("language standard is not approved; cannot build a pack")
    _validate_pack_files(files)
    validate_pack_governance(
        definition,
        catalogs=definition.catalogs or ("common",),
        files=files,
        approval_status=approval_status,
        allow_synthetic=True,
    )

    archive_files = dict(files)
    file_entries = [
        {
            "path": path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content),
        }
        for path, content in sorted(archive_files.items())
    ]
    content_hash = PackManager.compute_content_hash(archive_files)

    manifest = LanguagePackManifest(
        schema_version="1.0",
        language_id=definition.language_id,
        locale_tag=definition.locale_tag,
        native_name=native_name or definition.native_name or definition.english_name,
        fallback_locale="en",
        pack_version=pack_version,
        minimum_engine_version=definition.minimum_engine_version,
        direction=definition.direction,
        script=definition.script,
        catalogs=list(definition.catalogs) or ["common"],
        terminology_version=definition.terminology_version or "1.0.0",
        content_hash=content_hash,
        content_size=sum(len(content) for content in archive_files.values()),
        publisher=publisher,
        signer_key_id=signer_key_id,
        approval_status=approval_status,  # type: ignore[arg-type]
        created_at=created_at or datetime.now(UTC),
        files=file_entries,
        signature="AA==",
    )
    signature = base64.b64encode(private_key.sign(manifest.signing_payload())).decode("ascii")
    manifest.signature = signature

    manifest_bytes = json.dumps(
        manifest.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        for path, content in sorted(archive_files.items()):
            archive.writestr(path, content)
    return buffer.getvalue()


def public_key_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes_raw()


def write_pack(pack_bytes: bytes, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(pack_bytes)
    return destination
