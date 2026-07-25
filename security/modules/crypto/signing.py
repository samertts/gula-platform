from __future__ import annotations

import hashlib
import hmac as _hmac_module
import logging
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, ec, padding
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

from security.modules.crypto.base import Signer
from security.modules.crypto.models import SignatureAlgorithm

logger = logging.getLogger("gula.security.modules.crypto.signing")


class Ed25519Signer(Signer):
    ALGORITHM = SignatureAlgorithm.ED25519

    def __init__(self, private_key: bytes | None = None) -> None:
        self._private_key: ed25519.Ed25519PrivateKey | None = None
        self._public_key: ed25519.Ed25519PublicKey | None = None
        if private_key:
            self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
            self._public_key = self._private_key.public_key()

    def sign(self, data: bytes, key: bytes | None = None) -> bytes:
        signing_key = self._private_key
        if key is not None:
            signing_key = ed25519.Ed25519PrivateKey.from_private_bytes(key)
        if signing_key is None:
            raise ValueError("No private key available for signing")

        return signing_key.sign(data)

    def verify(self, data: bytes, signature: bytes, key: bytes | None = None) -> bool:
        verify_key = self._public_key
        if key is not None:
            verify_key = ed25519.Ed25519PublicKey.from_public_bytes(key)
        if verify_key is None:
            raise ValueError("No public key available for verification")

        try:
            verify_key.verify(signature, data)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_key_pair() -> tuple[bytes, bytes]:
        private = ed25519.Ed25519PrivateKey.generate()
        private_bytes = private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return private_bytes, public_bytes

    @staticmethod
    def generate_key() -> bytes:
        private, _ = Ed25519Signer.generate_key_pair()
        return private

    @staticmethod
    def serialize_private_key_pem(private_key_bytes: bytes) -> bytes:
        private = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @staticmethod
    def serialize_public_key_pem(public_key_bytes: bytes) -> bytes:
        public = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        return public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @staticmethod
    def deserialize_private_key_pem(pem_data: bytes) -> bytes:
        private = serialization.load_pem_private_key(pem_data, password=None)
        if not isinstance(private, ed25519.Ed25519PrivateKey):
            raise ValueError("Not an Ed25519 private key")
        return private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @staticmethod
    def deserialize_public_key_pem(pem_data: bytes) -> bytes:
        public = serialization.load_pem_public_key(pem_data)
        if not isinstance(public, ed25519.Ed25519PublicKey):
            raise ValueError("Not an Ed25519 public key")
        return public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )


class ECDSA256Signer(Signer):
    ALGORITHM = SignatureAlgorithm.ECDSA_P256

    def __init__(self, private_key: bytes | None = None) -> None:
        self._private_key: ec.EllipticCurvePrivateKey | None = None
        self._public_key: ec.EllipticCurvePublicKey | None = None
        if private_key:
            self._private_key = ec.derive_private_key(
                int.from_bytes(private_key, "big"), ec.SECP256R1()
            )
            self._public_key = self._private_key.public_key()

    def sign(self, data: bytes, key: bytes | None = None) -> bytes:
        signing_key = self._private_key
        if key is not None:
            signing_key = ec.derive_private_key(
                int.from_bytes(key, "big"), ec.SECP256R1()
            )
        if signing_key is None:
            raise ValueError("No private key available for signing")

        signature = signing_key.sign(data, ec.ECDSA(hashes.SHA256()))
        return signature

    def verify(self, data: bytes, signature: bytes, key: bytes | None = None) -> bool:
        verify_key = self._public_key
        if key is not None:
            verify_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), key
            )
        if verify_key is None:
            raise ValueError("No public key available for verification")

        try:
            verify_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    @staticmethod
    def generate_key_pair() -> tuple[bytes, bytes]:
        private = ec.generate_private_key(ec.SECP256R1())
        private_bytes = private.private_numbers().private_value.to_bytes(32, "big")
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        return private_bytes, public_bytes

    @staticmethod
    def generate_key() -> bytes:
        private, _ = ECDSA256Signer.generate_key_pair()
        return private

    @staticmethod
    def serialize_private_key_pem(private_key_bytes: bytes) -> bytes:
        private = ec.derive_private_key(
            int.from_bytes(private_key_bytes, "big"), ec.SECP256R1()
        )
        return private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @staticmethod
    def serialize_public_key_pem(public_key_bytes: bytes) -> bytes:
        public = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), public_key_bytes
        )
        return public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


class HMACSigner(Signer):
    def __init__(self, algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256) -> None:
        if algorithm not in (SignatureAlgorithm.HMAC_SHA256, SignatureAlgorithm.HMAC_SHA512):
            raise ValueError(f"Unsupported HMAC algorithm: {algorithm}")
        self._algorithm = algorithm
        self._hash_fn = hashlib.sha256 if algorithm == SignatureAlgorithm.HMAC_SHA256 else hashlib.sha512

    def sign(self, data: bytes, key: bytes) -> bytes:
        if not key:
            raise ValueError("HMAC key must not be empty")
        return _hmac_module.new(key, data, self._hash_fn).digest()

    def verify(self, data: bytes, signature: bytes, key: bytes) -> bool:
        if not key:
            raise ValueError("HMAC key must not be empty")
        expected = self.sign(data, key)
        return _hmac_module.compare_digest(expected, signature)

    def sign_hex(self, data: bytes, key: bytes) -> str:
        return self.sign(data, key).hex()

    def verify_hex(self, data: bytes, signature_hex: str, key: bytes) -> bool:
        signature = bytes.fromhex(signature_hex)
        return self.verify(data, signature, key)

    @staticmethod
    def generate_key(byte_length: int = 32) -> bytes:
        return os.urandom(byte_length)
