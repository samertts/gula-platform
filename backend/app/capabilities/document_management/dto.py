from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document_managementCreateRequest:
    document_id: str
    filename: str
    mime_type: str
    size: str


@dataclass
class Document_managementUpdateRequest:
    document_id: str = None
    filename: str = None
    mime_type: str = None
    size: str = None


@dataclass
class Document_managementResponse:
    document_id: str
    filename: str
    mime_type: str
    size: str
