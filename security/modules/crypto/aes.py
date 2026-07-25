from __future__ import annotations

import hashlib
import hmac as _hmac
import logging
import os

from cryptography.hazmat.primitives.ciphers import Cipher as CipherCtx
from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from security.modules.crypto.base import Cipher
from security.modules.crypto.models import EncryptionAlgorithm

logger = logging.getLogger("gula.security.modules.crypto.aes")


class AES256GCMCipher(Cipher):
    ALGORITHM = EncryptionAlgorithm.AES_256_GCM
    KEY_SIZE = 32
    IV_SIZE = 12
    TAG_SIZE = 16

    def encrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        if not data:
            raise ValueError("Data must not be empty")

        aesgcm = AESGCM(key)
        iv = os.urandom(self.IV_SIZE)
        aad_bytes = aad if aad is not None else b""
        ciphertext = aesgcm.encrypt(iv, data, aad_bytes)
        return iv + ciphertext

    def decrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        if len(data) < self.IV_SIZE + self.TAG_SIZE:
            raise ValueError("Data too short to contain IV and tag")

        aesgcm = AESGCM(key)
        iv = data[:self.IV_SIZE]
        ciphertext = data[self.IV_SIZE:]
        aad_bytes = aad if aad is not None else b""
        return aesgcm.decrypt(iv, ciphertext, aad_bytes)

    def encrypt_with_associated_data(self, data: bytes, key: bytes, aad: bytes) -> bytes:
        return self.encrypt(data, key, aad)

    def decrypt_with_associated_data(self, data: bytes, key: bytes, aad: bytes) -> bytes:
        return self.decrypt(data, key, aad)

    @staticmethod
    def generate_key() -> bytes:
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def derive_key(password: bytes, salt: bytes, iterations: int = 600000) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, dklen=32)

    def encrypt_stream(self, data: bytes, key: bytes, chunk_size: int = 65536) -> bytes:
        return self.encrypt(data, key)

    def decrypt_stream(self, data: bytes, key: bytes, chunk_size: int = 65536) -> bytes:
        return self.decrypt(data, key)


class AES256CBCWithHMACCipher(Cipher):
    ALGORITHM = EncryptionAlgorithm.AES_256_CBC
    KEY_SIZE = 32
    IV_SIZE = 16
    HMAC_KEY_SIZE = 32
    TOTAL_KEY_SIZE = KEY_SIZE + HMAC_KEY_SIZE

    def encrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        if len(key) != self.TOTAL_KEY_SIZE:
            raise ValueError(f"Key must be {self.TOTAL_KEY_SIZE} bytes (encryption + HMAC)")
        if not data:
            raise ValueError("Data must not be empty")

        enc_key = key[:self.KEY_SIZE]
        hmac_key = key[self.KEY_SIZE:]

        iv = os.urandom(self.IV_SIZE)
        cipher = CipherCtx(algorithms.AES(enc_key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        padded_data = self._pad(data)
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        aad_bytes = aad if aad is not None else b""
        mac_data = aad_bytes + iv + ciphertext
        tag = _hmac.new(hmac_key, mac_data, hashlib.sha256).digest()

        return iv + tag + ciphertext

    def decrypt(self, data: bytes, key: bytes, aad: bytes | None = None) -> bytes:
        if len(key) != self.TOTAL_KEY_SIZE:
            raise ValueError(f"Key must be {self.TOTAL_KEY_SIZE} bytes (encryption + HMAC)")
        if len(data) < self.IV_SIZE + 32:
            raise ValueError("Data too short to contain IV and HMAC tag")

        enc_key = key[:self.KEY_SIZE]
        hmac_key = key[self.KEY_SIZE:]

        iv = data[:self.IV_SIZE]
        tag = data[self.IV_SIZE:self.IV_SIZE + 32]
        ciphertext = data[self.IV_SIZE + 32:]

        aad_bytes = aad if aad is not None else b""
        mac_data = aad_bytes + iv + ciphertext
        expected_tag = _hmac.new(hmac_key, mac_data, hashlib.sha256).digest()

        if not _hmac.compare_digest(tag, expected_tag):
            raise ValueError("HMAC verification failed - data may be tampered")

        cipher = CipherCtx(algorithms.AES(enc_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        return self._unpad(padded)

    def _pad(self, data: bytes) -> bytes:
        block_size = 16
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    def _unpad(self, data: bytes) -> bytes:
        if not data:
            raise ValueError("No data to unpad")
        pad_len = data[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("Invalid padding")
        for i in range(1, pad_len + 1):
            if data[-i] != pad_len:
                raise ValueError("Invalid padding bytes")
        return data[:-pad_len]

    @staticmethod
    def generate_key() -> bytes:
        return os.urandom(64)

    @staticmethod
    def derive_key(password: bytes, salt: bytes, iterations: int = 600000) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, dklen=64)
