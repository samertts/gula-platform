# GSF-003: Cryptography Module

## Architecture

The Cryptography module provides all cryptographic primitives for the GULA platform,
organized by capability with a consistent abstract interface pattern.

```
Cipher (ABC)
    ├── AES256GCMCipher          (AES-256-GCM, AEAD)
    └── AES256CBCWithHMACCipher  (AES-256-CBC + HMAC-SHA256, encrypt-then-MAC)

Hasher (ABC)
    ├── Argon2idHasher           (Argon2id password hashing, bcrypt fallback)
    ├── SHA256Hasher             (SHA-256 with HKDF, streaming)
    └── SHA512Hasher             (SHA-512 with HKDF, streaming)

Signer (ABC)
    ├── Ed25519Signer            (Ed25519 digital signatures)
    ├── ECDSA256Signer           (ECDSA P-256 with SHA-256)
    └── HMACSigner               (HMAC-SHA256/512)

SecureRandom
    ├── Random bytes / hex / base64 generation
    ├── Password generation (configurable character sets)
    ├── PIN generation (sequential/repeating digit avoidance)
    ├── UUID v4, API keys, OTP secrets
    └── Entropy estimation

FieldEncryptor
    ├── Probabilistic encryption (AES-256-GCM, random IV)
    ├── Deterministic encryption (AES-256-GCM, HMAC-based IV)
    ├── Type-preserving (int, float, bool, JSON, string)
    ├── Null-preserving (empty/null values pass through)
    └── Blind indexing for searchable encryption

PHIEncryptor
    ├── 3-level key hierarchy (master → table → column)
    ├── Patient-consent based encryption
    ├── Break-glass decryption capability
    ├── Audit logging for all PHI access
    └── Re-encryption support

KeyRotationManager
    ├── Automatic key rotation scheduling
    ├── Key version tracking
    ├── Grace period for old keys
    ├── Emergency key rotation
    ├── Key backup and recovery
    └── Notification hooks
```

## Design Decisions

1. **cryptography library only** - All primitives use the `cryptography` library
   (OpenSSL/BoringSSL bindings). No custom crypto implementations.

2. **Encrypt-then-MAC for CBC** - AES-256-CBC mode is combined with HMAC-SHA256
   in an encrypt-then-MAC construction to provide integrity and authenticity.

3. **Argon2id with bcrypt fallback** - Primary password hashing uses Argon2id
   (configurable time/memory/parallelism). Falls back to bcrypt if Argon2id fails.

4. **PHI 3-level key hierarchy** - Master key → Table key → Column key. Each
   column gets a unique derived key per table, limiting blast radius.

5. **Deterministic encryption for indexed fields** - Uses HMAC-derived IV so same
   plaintext always produces same ciphertext for indexing, without leaking the key.

6. **Blind indexing** - Searchable encryption via HMAC-based blind indexes that
   allow equality searches without decrypting the field.

7. **Constant-time comparisons** - All security-critical comparisons use
   `hmac.compare_digest` to prevent timing attacks.

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Key compromise | Key rotation, 3-level hierarchy, master key rotation |
| Ciphertext tampering | AEAD (GCM), Encrypt-then-MAC (CBC) |
| Brute force password cracking | Argon2id (configurable cost), bcrypt fallback |
| Timing attacks | Constant-time comparison everywhere |
| PHI data breach | Per-column keys, patient consent, break-glass audit |
| Replay attacks | Random IV per encryption |
| Key loss | Key backup/recovery with passphrase encryption |
| Algorithm downgrade | Strict algorithm enforcement in encryption |

## Configuration

```python
from security.modules.crypto.models import EncryptionConfig, EncryptionAlgorithm

config = EncryptionConfig(
    default_algorithm=EncryptionAlgorithm.AES_256_GCM,
    key_rotation_days=365,
    key_derivation_iterations=600000,
    master_key_provider="environment",
)
```

## Usage Examples

### AES-256-GCM Encryption
```python
from security.modules.crypto import AES256GCMCipher

cipher = AES256GCMCipher()
key = AES256GCMCipher.generate_key()
encrypted = cipher.encrypt(b"sensitive data", key)
plaintext = cipher.decrypt(encrypted, key)
```

### Password Hashing with Argon2id
```python
from security.modules.crypto import Argon2idHasher

hasher = Argon2idHasher()
digest = hasher.hash(b"user_password")
assert hasher.verify(b"user_password", digest)
assert not hasher.verify(b"wrong_password", digest)
```

### Digital Signatures (Ed25519)
```python
from security.modules.crypto import Ed25519Signer

signer = Ed25519Signer()
private, public = Ed25519Signer.generate_key_pair()
signature = signer.sign(b"message", private)
assert signer.verify(b"message", signature, public)
```

### Field-Level Encryption
```python
from security.modules.crypto import FieldEncryptor

encryptor = FieldEncryptor(master_key=b"..." * 8)
encrypted_ssn = encryptor.encrypt_field("123-45-6789", "ssn", "patients")
# deterministic for equality checks
encrypted_email = encryptor.encrypt_field("user@example.com", "email", "users", deterministic=True)
decrypted = encryptor.decrypt_field(encrypted_ssn, "ssn", "patients")
```

### PHI Encryption
```python
from security.modules.crypto import PHIEncryptor

phi = PHIEncryptor(master_key=b"..." * 8)
token = phi.generate_consent_token("patient-123")
encrypted = phi.encrypt_phi_field("diagnosis-data", "patient-123", "records", "diagnosis", token)
decrypted = phi.decrypt_phi_field(encrypted, "patient-123", "records", "diagnosis")
```

### Secure Random
```python
from security.modules.crypto import SecureRandom

password = SecureRandom.generate_password(length=32)
pin = SecureRandom.generate_pin(length=6)
token = SecureRandom.token_urlsafe(32)
api_key = SecureRandom.generate_api_key()
uuid = SecureRandom.uuid4()
```

### Key Rotation
```python
from security.modules.crypto import KeyRotationManager

km = KeyRotationManager()
km.add_key("key-1", b"..." * 8, KeyPurpose.DATA_ENCRYPTION)
km.add_key("key-2", b"..." * 8, KeyPurpose.DATA_ENCRYPTION)
km.set_active_key("key-2")
km.start_auto_rotation(interval_hours=24)
```

## Testing Guide

Tests are in `tests/modules/crypto/`. Run with:

```bash
pytest tests/modules/crypto/ -v
pytest tests/modules/crypto/ -v -k "test_aes or test_argon"
pytest tests/modules/crypto/ -v -m crypto
```

## Security Considerations

1. Master keys must be 32 bytes (256 bits) for AES-256 operations.
2. CBC mode requires 64-byte keys (32 encryption + 32 HMAC).
3. Argon2id memory_cost should be at least 65536 (64MB) for production.
4. Deterministic encryption leaks equality patterns - only use for indexed fields.
5. PHI break-glass should be monitored and audited in real-time.
6. Key backup passphrases must be stored separately from the backup data.
7. Always use AEAD modes (GCM) unless compatibility requires CBC.
8. HKDF salt is fixed per module version - use different application-level salts.

## Future Extensions

- Hardware Security Module (HSM) integration (PKCS#11)
- Post-quantum cryptography (Kyber, Dilithium)
- Key ceremony support (split-knowledge key escrow)
- Format-preserving encryption (FF1)
- Homomorphic encryption for computation on encrypted data
- Integration with GSF-002 for key material storage
- KMIP server integration
- Key attestation and remote verification
