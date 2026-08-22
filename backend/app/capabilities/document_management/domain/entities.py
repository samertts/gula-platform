from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class Document_management:
    id: str = field(default_factory=lambda: str(uuid4()))
    document_id: str
    filename: str
    mime_type: str
    size: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
