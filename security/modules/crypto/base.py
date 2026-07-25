from __future__ import annotations

from abc import ABC, abstractmethod


class Cipher(ABC):
    @abstractmethod
    def encrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        ...

    @abstractmethod
    def decrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        ...


class Hasher(ABC):
    @abstractmethod
    def hash(self, data: bytes, salt: bytes | None = None) -> bytes:
        ...

    @abstractmethod
    def verify(self, data: bytes, digest: bytes) -> bool:
        ...


class Signer(ABC):
    @abstractmethod
    def sign(self, data: bytes, key: bytes) -> bytes:
        ...

    @abstractmethod
    def verify(self, data: bytes, signature: bytes, key: bytes) -> bool:
        ...


class KeyGenerator(ABC):
    @abstractmethod
    def generate(self, length: int | None = None) -> bytes:
        ...

    @abstractmethod
    def derive(self, password: bytes, salt: bytes, length: int, iterations: int = 100000) -> bytes:
        ...


class KeyRotator(ABC):
    @abstractmethod
    def rotate(self, key_id: str) -> str:
        ...

    @abstractmethod
    def get_current_key_id(self) -> str:
        ...

    @abstractmethod
    def get_key_by_id(self, key_id: str) -> bytes:
        ...
