"""Secure language-pack delivery API.

The delivery service is auxiliary: failure of this service never blocks medical
services because installed packs are read locally by the runtime.
"""

from __future__ import annotations

import re
import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from .language_registry import LanguageRegistry, RegistryError
from .pack_manager import PackManager

TOKEN_TTL_SECONDS = 300
# Keep an expired session briefly so the API can return the explicit
# DOWNLOAD_TOKEN_EXPIRED code instead of an ambiguous not-found response.
EXPIRY_GRACE_SECONDS = 5


class DownloadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale_tag: str | None = None
    data_saver_enabled: bool = False
    allow_metered_network: bool = False
    roaming: bool = False
    allow_roaming: bool = False
    available_storage_bytes: int = Field(default=0, ge=0)


@dataclass(slots=True)
class _DownloadRecord:
    download_id: str
    language_id: str
    pack_bytes: bytes
    token: str
    expires_at: float
    status: str = "AVAILABLE"
    downloaded_bytes: int = 0
    last_error: str | None = None
    resumable: bool = True
    covered_ranges: list[tuple[int, int]] = field(default_factory=list)

    def progress(self) -> dict[str, object]:
        total = len(self.pack_bytes)
        progress = min(1.0, self.downloaded_bytes / total) if total else 0.0
        return {
            "status": self.status,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": total,
            "progress": round(progress, 6),
            "last_error": self.last_error,
            "resumable": self.resumable,
        }


def _load_pack_store(root: Path | None) -> dict[str, bytes]:
    if root is None:
        return {}
    if not root.exists():
        return {}
    store: dict[str, bytes] = {}
    for path in sorted(root.glob("*.zip")):
        store[path.stem] = path.read_bytes()
    return store


def create_router(
    *,
    registry: LanguageRegistry,
    pack_manager: PackManager,
    pack_store: Mapping[str, bytes] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/localization", tags=["localization"])
    store: dict[str, bytes] = dict(pack_store or {})
    downloads: dict[str, _DownloadRecord] = {}

    def _purge_expired() -> None:
        now = time.monotonic()
        for download_id in [
            key
            for key, record in downloads.items()
            if record.expires_at + EXPIRY_GRACE_SECONDS <= now
        ]:
            downloads.pop(download_id, None)

    def _error(
        code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> HTTPException:
        return HTTPException(status_code=status_code, detail={"code": code, "message": message})

    @router.get("/languages")
    def list_languages() -> dict[str, object]:
        languages = []
        for definition in registry.all():
            languages.append(
                {
                    **definition.public_dict(),
                    "installed": pack_manager.state(definition.language_id) == "READY",
                    "lifecycle_state": pack_manager.state(definition.language_id),
                }
            )
        return {"registry_version": "1.0.0", "fallback_language": "en", "languages": languages}

    @router.get("/languages/{language_id}/manifest")
    def get_manifest(language_id: str) -> dict[str, object]:
        if registry.resolve(language_id) is None:
            raise _error("LANGUAGE_NOT_FOUND", "The requested language is not registered.", 404)
        pack_bytes = store.get(language_id)
        if pack_bytes is None:
            raise _error(
                "PACK_NOT_AVAILABLE", "No published pack is available for this language.", 404
            )
        try:
            result = pack_manager.verify(pack_bytes, language_id)
        except RegistryError as exc:
            raise _error(
                "LANGUAGE_NOT_FOUND", "The requested language is not registered.", 404
            ) from exc
        except Exception as exc:
            raise _error("PACK_VERIFICATION_FAILED", str(exc), 409) from exc
        return result.manifest.model_dump(mode="json")

    @router.post("/language-packs/{language_id}/download")
    def request_download(
        language_id: str, payload: DownloadRequest, request: Request
    ) -> dict[str, object]:
        _purge_expired()
        definition = registry.resolve(language_id)
        if definition is None:
            raise _error("LANGUAGE_NOT_FOUND", "The requested language is not registered.", 404)
        if payload.locale_tag and definition.locale_tag != payload.locale_tag:
            raise _error(
                "LOCALE_MISMATCH", "The locale tag does not match the registered language.", 409
            )
        if not definition.is_active:
            raise _error("LANGUAGE_NOT_ACTIVE", "The language standard has not been approved.", 409)
        if pack_manager.state(language_id) == "READY":
            raise _error("ALREADY_INSTALLED", "A ready pack is already installed.", 409)
        if payload.data_saver_enabled and not payload.allow_metered_network:
            raise _error(
                "DOWNLOAD_BLOCKED_BY_DATA_SAVER",
                "Data saver restrictions prevent this download.",
                409,
            )
        if payload.roaming and not payload.allow_roaming:
            raise _error(
                "DOWNLOAD_BLOCKED_BY_ROAMING", "Roaming restrictions prevent this download.", 409
            )
        pack_bytes = store.get(definition.language_id)
        if pack_bytes is None:
            raise _error(
                "PACK_NOT_AVAILABLE", "No published pack is available for this language.", 404
            )
        if (
            payload.available_storage_bytes
            and payload.available_storage_bytes < len(pack_bytes) * 2
        ):
            raise _error("INSUFFICIENT_STORAGE", "Insufficient storage for safe installation.", 409)

        download_id = secrets.token_urlsafe(18)
        token = secrets.token_urlsafe(32)
        downloads[download_id] = _DownloadRecord(
            download_id=download_id,
            language_id=definition.language_id,
            pack_bytes=pack_bytes,
            token=token,
            expires_at=time.monotonic() + TOKEN_TTL_SECONDS,
        )
        hash_value = ""
        signature_metadata: dict[str, object] = {}
        try:
            verification = pack_manager.verify(pack_bytes, definition.language_id)
            hash_value = verification.content_hash
            signature_metadata = {
                "signer_key_id": verification.manifest.signer_key_id,
                "publisher": verification.manifest.publisher,
                "signature_present": True,
            }
        except Exception as exc:
            raise _error("PACK_VERIFICATION_FAILED", str(exc), 409) from exc

        base_url = str(request.base_url).rstrip("/")
        return {
            "download_id": download_id,
            "language_id": definition.language_id,
            "pack_version": verification.manifest.pack_version,
            "download_url": f"{base_url}/api/v1/localization/downloads/{download_id}/content?token={token}",
            "expected_size": len(pack_bytes),
            "expected_hash": hash_value,
            "signature_metadata": signature_metadata,
            "expires_in": TOKEN_TTL_SECONDS,
        }

    @router.get("/downloads/{download_id}")
    def get_download(download_id: str, token: str = Query(default="")) -> dict[str, object]:
        _purge_expired()
        record = downloads.get(download_id)
        if record is None:
            raise _error("DOWNLOAD_NOT_FOUND", "The download session does not exist.", 404)
        if not secrets.compare_digest(token, record.token):
            raise _error("INVALID_DOWNLOAD_TOKEN", "The download authorization is invalid.", 403)
        return record.progress()

    @router.delete("/downloads/{download_id}")
    def cancel_download(download_id: str, token: str = Query(default="")) -> dict[str, object]:
        _purge_expired()
        record = downloads.get(download_id)
        if record is None:
            raise _error("DOWNLOAD_NOT_FOUND", "The download session does not exist.", 404)
        if not secrets.compare_digest(token, record.token):
            raise _error("INVALID_DOWNLOAD_TOKEN", "The download authorization is invalid.", 403)
        downloads.pop(download_id, None)
        return {"code": "DOWNLOAD_CANCELLED", "download_id": download_id}

    @router.get("/downloads/{download_id}/content")
    def download_content(
        download_id: str, request: Request, token: str = Query(default="")
    ) -> Response:
        _purge_expired()
        record = downloads.get(download_id)
        if record is None:
            raise _error("DOWNLOAD_NOT_FOUND", "The download session does not exist.", 404)
        authorization = request.headers.get("authorization", "")
        bearer = authorization[7:] if authorization.startswith("Bearer ") else ""
        presented = token or bearer
        if not secrets.compare_digest(presented, record.token):
            raise _error("INVALID_DOWNLOAD_TOKEN", "The download authorization is invalid.", 403)
        if time.monotonic() > record.expires_at:
            raise _error("DOWNLOAD_TOKEN_EXPIRED", "The download authorization has expired.", 403)

        total = len(record.pack_bytes)
        start = 0
        end: int | None = None
        range_header = request.headers.get("range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d+)(?:-(\d*))?", range_header.strip())
            if match is None:
                raise _error("INVALID_RANGE", "Only byte ranges are supported.", 416)
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else None
            if start >= total or (end is not None and end < start):
                raise _error("INVALID_RANGE", "The requested byte range is outside the pack.", 416)
            if end is not None:
                end = min(end, total - 1)

        chunk = record.pack_bytes[start : end + 1 if end is not None else None]
        chunk_end = start + len(chunk) - 1
        record.covered_ranges.append((start, chunk_end))
        merged: list[tuple[int, int]] = []
        for range_start, range_end in sorted(record.covered_ranges):
            if merged and range_start <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], range_end))
            else:
                merged.append((range_start, range_end))
        record.covered_ranges = merged
        # Only a contiguous prefix counts as delivered. A tail-only range must
        # never make the session look complete.
        covered = merged[0][1] + 1 if merged and merged[0][0] == 0 else 0
        record.downloaded_bytes = covered
        complete = covered >= total
        # This is a transport status. "READY" is reserved for a verified and
        # installed pack in the PackManager lifecycle.
        record.status = "COMPLETE" if complete else "DOWNLOADING"
        record.last_error = None if complete else "partial_download_resumable"
        record.resumable = not complete
        headers = {
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{record.language_id}-pack.zip"',
            "Accept-Ranges": "bytes",
        }
        if range_header:
            range_end = end if end is not None else total - 1
            headers["Content-Range"] = f"bytes {start}-{range_end}/{total}"
        return Response(
            content=chunk,
            status_code=206 if range_header else 200,
            media_type="application/zip",
            headers=headers,
        )

    return router
