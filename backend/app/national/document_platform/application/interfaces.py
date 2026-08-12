from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageAdapter(ABC):

    @abstractmethod
    async def store(self, path: str, data: bytes, mime_type: str) -> str: ...

    @abstractmethod
    async def retrieve(self, path: str) -> bytes: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> str: ...


class SignatureVerifier(ABC):

    @abstractmethod
    async def verify(self, document_hash: str, signature_value: str, certificate_id: str) -> dict[str, Any]: ...


class QRCodeGenerator(ABC):

    @abstractmethod
    async def generate(self, data: str) -> str: ...

    @abstractmethod
    async def verify(self, qr_data: str) -> dict[str, Any]: ...


class PDFGenerator(ABC):

    @abstractmethod
    async def generate(self, content: dict[str, Any], template: str = "") -> bytes: ...
