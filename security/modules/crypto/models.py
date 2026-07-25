from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EncryptionAlgorithm(str, Enum):
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"


class HashAlgorithm(str, Enum):
    SHA_256 = "sha-256"
    SHA_512 = "sha-512"
    ARGON2ID = "argon2id"
    BCRYPT = "bcrypt"


class SignatureAlgorithm(str, Enum):
    ED25519 = "ed25519"
    ECDSA_P256 = "ecdsa-p256"
    ECDSA_P384 = "ecdsa-p384"
    HMAC_SHA256 = "hmac-sha256"
    HMAC_SHA512 = "hmac-sha512"


class KeyPurpose(str, Enum):
    DATA_ENCRYPTION = "data_encryption"
    FIELD_ENCRYPTION = "field_encryption"
    PHI_ENCRYPTION = "phi_encryption"
    TOKEN_SIGNING = "token_signing"
    TLS = "tls"
    DOCUMENT_SIGNING = "document_signing"


class EncryptedData(BaseModel):
    ciphertext: bytes
    iv: bytes
    tag: bytes
    algorithm: EncryptionAlgorithm
    key_id: str
    created_at: datetime | None = None


class KeyMetadata(BaseModel):
    key_id: str
    purpose: KeyPurpose
    algorithm: EncryptionAlgorithm | HashAlgorithm | SignatureAlgorithm
    created_at: datetime | None = None
    expires_at: datetime | None = None
    rotation_count: int = 0
    status: str = "active"


class EncryptionConfig(BaseModel):
    default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_rotation_days: int = 365
    key_derivation_iterations: int = 600000
    master_key_provider: str = "environment"


class HashResult(BaseModel):
    digest: bytes
    algorithm: HashAlgorithm
    salt: bytes | None = None
    iterations: int = 0
