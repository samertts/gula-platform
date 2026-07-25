GSF-003: Crypto Module — Cryptographic operations.

Provides all cryptographic primitives for the GULA platform including
AEAD encryption, digital signatures, key derivation, key wrapping,
and key rotation. Backed by the cryptography library (OpenSSL/BoringSSL).

Exports:
    CryptoEngine: Core cryptographic engine
    AeadEncryptor: Authenticated encryption (AES-256-GCM, ChaCha20-Poly1305)
    KeyDerivation: PBKDF2, Argon2id, HKDF key derivation
    DigitalSigner: Ed25519, ECDSA, RSA-PSS signature operations
    KeyManager: Key lifecycle management and rotation
    CertificateAuthority: X.509 certificate operations
"""

from security.modules.crypto.engine import CryptoEngine
from security.modules.crypto.aead import AeadEncryptor
from security.modules.crypto.kdf import KeyDerivation
from security.modules.crypto.signer import DigitalSigner
from security.modules.crypto.key_mgmt import KeyManager
from security.modules.crypto.ca import CertificateAuthority

__all__ = [
    "CryptoEngine",
    "AeadEncryptor",
    "KeyDerivation",
    "DigitalSigner",
    "KeyManager",
    "CertificateAuthority",
]
