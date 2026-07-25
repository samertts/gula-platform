from __future__ import annotations

import hashlib
import hmac as _hmac_module
import logging
import os

from security.modules.crypto.base import Hasher
from security.modules.crypto.models import HashAlgorithm, HashResult

logger = logging.getLogger("gula.security.modules.crypto.hashing")

_DEFAULT_SALT_SIZE = 16


class SHA256Hasher(Hasher):
    ALGORITHM = HashAlgorithm.SHA_256
    DIGEST_SIZE = 32

    def hash(self, data: bytes, salt: bytes | None = None) -> bytes:
        if not data:
            raise ValueError("Data must not be empty")
        if salt:
            data = salt + data
        return hashlib.sha256(data).digest()

    def verify(self, data: bytes, digest: bytes) -> bool:
        return _hmac_module.compare_digest(self.hash(data), digest)

    def hash_hex(self, data: bytes, salt: bytes | None = None) -> str:
        return self.hash(data, salt).hex()

    def hash_salted(self, data: bytes, salt: bytes | None = None) -> bytes:
        salt_bytes = salt if salt is not None else os.urandom(_DEFAULT_SALT_SIZE)
        return salt_bytes + self.hash(data, salt_bytes)

    def verify_salted(self, data: bytes, salted_digest: bytes) -> bool:
        if len(salted_digest) < _DEFAULT_SALT_SIZE:
            return False
        salt = salted_digest[:_DEFAULT_SALT_SIZE]
        expected = salted_digest[_DEFAULT_SALT_SIZE:]
        return _hmac_module.compare_digest(self.hash(data, salt), expected)

    def hash_stream(self, stream, chunk_size: int = 65536) -> bytes:
        h = hashlib.sha256()
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
        return h.digest()

    def hkdf_expand(self, prk: bytes, length: int, info: bytes = b"") -> bytes:
        return self._hkdf_expand(prk, length, info)

    def _hkdf_expand(self, prk: bytes, length: int, info: bytes) -> bytes:
        n = (length + self.DIGEST_SIZE - 1) // self.DIGEST_SIZE
        if n > 255:
            raise ValueError("Length too large for HKDF expansion")
        okm = b""
        t = b""
        for i in range(1, n + 1):
            t = _hmac_module.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
            okm += t
        return okm[:length]

    @staticmethod
    def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
        return _hmac_module.new(salt, ikm, hashlib.sha256).digest()

    def get_hash_result(self, data: bytes, salt: bytes | None = None) -> HashResult:
        salt_bytes = salt if salt is not None else os.urandom(_DEFAULT_SALT_SIZE)
        digest = self.hash(data, salt_bytes)
        return HashResult(
            digest=digest,
            algorithm=self.ALGORITHM,
            salt=salt_bytes,
            iterations=1,
        )


class SHA512Hasher(Hasher):
    ALGORITHM = HashAlgorithm.SHA_512
    DIGEST_SIZE = 64

    def hash(self, data: bytes, salt: bytes | None = None) -> bytes:
        if not data:
            raise ValueError("Data must not be empty")
        if salt:
            data = salt + data
        return hashlib.sha512(data).digest()

    def verify(self, data: bytes, digest: bytes) -> bool:
        return _hmac_module.compare_digest(self.hash(data), digest)

    def hash_hex(self, data: bytes, salt: bytes | None = None) -> str:
        return self.hash(data, salt).hex()

    def hash_salted(self, data: bytes, salt: bytes | None = None) -> bytes:
        salt_bytes = salt if salt is not None else os.urandom(_DEFAULT_SALT_SIZE)
        return salt_bytes + self.hash(data, salt_bytes)

    def verify_salted(self, data: bytes, salted_digest: bytes) -> bool:
        if len(salted_digest) < _DEFAULT_SALT_SIZE:
            return False
        salt = salted_digest[:_DEFAULT_SALT_SIZE]
        expected = salted_digest[_DEFAULT_SALT_SIZE:]
        return _hmac_module.compare_digest(self.hash(data, salt), expected)

    def hash_stream(self, stream, chunk_size: int = 65536) -> bytes:
        h = hashlib.sha512()
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
        return h.digest()

    def hkdf_expand(self, prk: bytes, length: int, info: bytes = b"") -> bytes:
        n = (length + self.DIGEST_SIZE - 1) // self.DIGEST_SIZE
        if n > 255:
            raise ValueError("Length too large for HKDF expansion")
        okm = b""
        t = b""
        for i in range(1, n + 1):
            t = _hmac_module.new(prk, t + info + bytes([i]), hashlib.sha512).digest()
            okm += t
        return okm[:length]

    @staticmethod
    def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
        return _hmac_module.new(salt, ikm, hashlib.sha512).digest()

    def get_hash_result(self, data: bytes, salt: bytes | None = None) -> HashResult:
        salt_bytes = salt if salt is not None else os.urandom(_DEFAULT_SALT_SIZE)
        digest = self.hash(data, salt_bytes)
        return HashResult(
            digest=digest,
            algorithm=self.ALGORITHM,
            salt=salt_bytes,
            iterations=1,
        )
