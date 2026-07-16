"""Standardized document/file management module."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.documents")


@dataclass
class Document:
    id: str = ""
    filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    storage_path: str = ""
    created_at: str = ""


class DocumentService:
    def __init__(self, storage_dir: str = "/app/data/documents") -> None:
        self._storage_dir = storage_dir

    def upload(self, filename: str, content: bytes, mime_type: str = "application/octet-stream") -> Document:
        import os
        doc_id = str(uuid.uuid4())
        safe_name = f"{doc_id}_{filename}"
        os.makedirs(self._storage_dir, exist_ok=True)
        filepath = os.path.join(self._storage_dir, safe_name)
        with open(filepath, "wb") as f:
            f.write(content)
        return Document(
            id=doc_id, filename=filename, mime_type=mime_type,
            size_bytes=len(content), storage_path=filepath,
        )

    def download(self, document_id: str) -> bytes | None:
        for fname in os.listdir(self._storage_dir):
            if fname.startswith(document_id):
                filepath = os.path.join(self._storage_dir, fname)
                with open(filepath, "rb") as f:
                    return f.read()
        return None

    def delete(self, document_id: str) -> bool:
        for fname in os.listdir(self._storage_dir):
            if fname.startswith(document_id):
                os.remove(os.path.join(self._storage_dir, fname))
                return True
        return False

    def list_documents(self) -> list[dict]:
        docs = []
        for fname in os.listdir(self._storage_dir):
            filepath = os.path.join(self._storage_dir, fname)
            if os.path.isfile(filepath):
                docs.append({
                    "id": fname.split("_")[0] if "_" in fname else fname,
                    "filename": fname,
                    "size_bytes": os.path.getsize(filepath),
                })
        return docs


PlatformRegistry.register("documents", DocumentService(), capabilities=[
    {"name": "upload", "description": "Upload a document to platform storage"},
    {"name": "download", "description": "Download a document by ID"},
    {"name": "delete", "description": "Delete a document by ID"},
    {"name": "list_documents", "description": "List all stored documents"},
])
