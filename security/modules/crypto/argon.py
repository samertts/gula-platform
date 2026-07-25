from __future__ import annotations

import hashlib
import logging
import os

from passlib.hash import argon2
from passlib.hash import bcrypt

from security.modules.crypto.base import Hasher
from security.modules.crypto.models import HashAlgorithm, HashResult

logger = logging.getLogger("gula.security.modules.crypto.argon")

_DEFAULT_TIME_COST = 3
_DEFAULT_MEMORY_COST = 65536
_DEFAULT_PARALLELISM = 4
_DEFAULT_SALT_SIZE = 16


class Argon2idHasher(Hasher):
    ALGORITHM = HashAlgorithm.ARGON2ID

    def __init__(
        self,
        time_cost: int = _DEFAULT_TIME_COST,
        memory_cost: int = _DEFAULT_MEMORY_COST,
        parallelism: int = _DEFAULT_PARALLELISM,
        salt_size: int = _DEFAULT_SALT_SIZE,
        use_bcrypt_fallback: bool = True,
    ) -> None:
        self._time_cost = time_cost
        self._memory_cost = memory_cost
        self._parallelism = parallelism
        self._salt_size = salt_size
        self._use_bcrypt_fallback = use_bcrypt_fallback

    def hash(self, data: bytes, salt: bytes | None = None) -> bytes:
        if not data:
            raise ValueError("Data must not be empty")

        salt_bytes = salt if salt is not None else os.urandom(self._salt_size)

        try:
            hashed = argon2.using(
                time_cost=self._time_cost,
                memory_cost=self._memory_cost,
                parallelism=self._parallelism,
                salt=salt_bytes,
            ).hash(data.decode("utf-8", errors="replace"))
            return hashed.encode("utf-8")
        except Exception as exc:
            logger.warning("Argon2id hash failed, falling back to bcrypt: %s", exc)
            if self._use_bcrypt_fallback:
                return self._bcrypt_hash(data, salt_bytes)
            raise

    def verify(self, data: bytes, digest: bytes) -> bool:
        if not data or not digest:
            return False

        digest_str = digest.decode("utf-8", errors="replace")

        if digest_str.startswith("$argon2id$"):
            try:
                return argon2.verify(data.decode("utf-8", errors="replace"), digest_str)
            except Exception:
                return False
        elif digest_str.startswith("$2b$") or digest_str.startswith("$2a$"):
            try:
                return bcrypt.verify(data.decode("utf-8", errors="replace"), digest_str)
            except Exception:
                return False
        else:
            logger.warning("Unknown hash format in digest")
            return False

    def needs_rehash(self, digest: bytes) -> bool:
        digest_str = digest.decode("utf-8", errors="replace")
        if not digest_str.startswith("$argon2id$"):
            return True

        try:
            parsed = argon2.parsehash(digest_str)
            if parsed.time_cost != self._time_cost:
                return True
            if parsed.memory_cost != self._memory_cost:
                return True
            if parsed.parallelism != self._parallelism:
                return True
            return False
        except Exception:
            return True

    def get_hash_result(self, data: bytes, salt: bytes | None = None) -> HashResult:
        salt_bytes = salt if salt is not None else os.urandom(self._salt_size)
        digest = self.hash(data, salt_bytes)
        return HashResult(
            digest=digest,
            algorithm=self.ALGORITHM,
            salt=salt_bytes,
            iterations=self._time_cost,
        )

    def _bcrypt_hash(self, data: bytes, salt: bytes | None = None) -> bytes:
        if salt:
            encoded_salt = salt.hex()[:22]
        else:
            encoded_salt = None

        hashed = bcrypt.using(
            rounds=12,
            salt=encoded_salt.encode() if encoded_salt else None,
        ).hash(data.decode("utf-8", errors="replace"))
        return hashed.encode("utf-8")
