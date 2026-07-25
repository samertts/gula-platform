"""GSF-003: Crypto Module — Cryptographic operations.

Provides all cryptographic primitives for the GULA platform including
AEAD encryption, digital signatures, key derivation, key wrapping,
and key rotation. Backed by the cryptography library (OpenSSL/BoringSSL).

Exports:
    Cipher: Abstract encryption interface
    Hasher: Abstract hashing interface
    Signer: Abstract signing interface
    KeyGenerator: Abstract key generation interface
    KeyRotator: Abstract key rotation interface
    AES256GCMCipher: AES-256-GCM encryption
    AES256CBCWithHMACCipher: AES-256-CBC with HMAC-SHA256
    Argon2idHasher: Argon2id password hashing
    SHA256Hasher: SHA-256 hashing
    SHA512Hasher: SHA-512 hashing
    Ed25519Signer: Ed25519 digital signatures
    ECDSA256Signer: ECDSA P-256 signatures
    HMACSigner: HMAC-SHA256/512 signing
    SecureRandom: Secure random generation
    FieldEncryptor: Field-level encryption
    PHIEncryptor: PHI (health data) encryption
    KeyRotationManager: Key lifecycle management
"""

from security.modules.crypto.aes import AES256CBCWithHMACCipher, AES256GCMCipher
from security.modules.crypto.argon import Argon2idHasher
from security.modules.crypto.base import Cipher, Hasher, KeyGenerator, KeyRotator, Signer
from security.modules.crypto.field_encryption import FieldEncryptor
from security.modules.crypto.hashing import SHA256Hasher, SHA512Hasher
from security.modules.crypto.key_rotation import KeyRotationManager
from security.modules.crypto.models import (
    EncryptedData,
    EncryptionAlgorithm,
    EncryptionConfig,
    HashAlgorithm,
    HashResult,
    KeyMetadata,
    KeyPurpose,
    SignatureAlgorithm,
)
from security.modules.crypto.phi_encryption import PHIEncryptor
from security.modules.crypto.random import SecureRandom
from security.modules.crypto.signing import ECDSA256Signer, Ed25519Signer, HMACSigner

__all__ = [
    "AES256CBCWithHMACCipher",
    "AES256GCMCipher",
    "Argon2idHasher",
    "Cipher",
    "ECDSA256Signer",
    "Ed25519Signer",
    "EncryptedData",
    "EncryptionAlgorithm",
    "EncryptionConfig",
    "FieldEncryptor",
    "HMACSigner",
    "HashAlgorithm",
    "HashResult",
    "Hasher",
    "KeyGenerator",
    "KeyMetadata",
    "KeyPurpose",
    "KeyRotationManager",
    "KeyRotator",
    "PHIEncryptor",
    "SHA256Hasher",
    "SHA512Hasher",
    "SecureRandom",
    "SignatureAlgorithm",
    "Signer",
]
