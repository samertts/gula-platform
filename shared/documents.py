from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from backend.app._compat import UTC

logger = logging.getLogger("gula.documents")


class DocumentMetadata:
    def __init__(
        self,
        doc_id: str | None = None,
        filename: str = "",
        mime_type: str = "application/octet-stream",
        size_bytes: int = 0,
        tags: list[str] | None = None,
    ) -> None:
        self.id = doc_id or str(uuid4())
        self.filename = filename
        self.mime_type = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self.size_bytes = size_bytes
        self.tags = tags or []
        self.created_at = datetime.now(UTC)
        self.checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "filename": self.filename, "mime_type": self.mime_type,
            "size_bytes": self.size_bytes, "tags": self.tags,
            "created_at": self.created_at.isoformat(), "checksum": self.checksum,
        }


class DocumentStore:
    def __init__(self, storage_dir: str = "/tmp/gula/docs") -> None:
        self._storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._index: dict[str, DocumentMetadata] = {}

    def save(self, data: bytes, filename: str, tags: list[str] | None = None) -> DocumentMetadata:
        meta = DocumentMetadata(filename=filename, size_bytes=len(data), tags=tags)
        path = os.path.join(self._storage_dir, meta.id)
        with open(path, "wb") as f:
            f.write(data)
        meta.checksum = hashlib.sha256(data).hexdigest()
        self._index[meta.id] = meta
        logger.info("Saved document %s (%s, %d bytes)", meta.id, filename, len(data))
        return meta

    def get(self, doc_id: str) -> bytes | None:
        meta = self._index.get(doc_id)
        if not meta:
            return None
        path = os.path.join(self._storage_dir, doc_id)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def get_meta(self, doc_id: str) -> DocumentMetadata | None:
        return self._index.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        meta = self._index.pop(doc_id, None)
        if not meta:
            return False
        path = os.path.join(self._storage_dir, doc_id)
        if os.path.exists(path):
            os.remove(path)
        return True

    def list(self, tags: list[str] | None = None) -> list[DocumentMetadata]:
        if not tags:
            return list(self._index.values())
        return [m for m in self._index.values() if any(t in m.tags for t in tags)]


__all__ = ["DocumentMetadata", "DocumentStore"]
