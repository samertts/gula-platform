# Encryption Policy

## 1. Purpose

Define cryptographic standards and key management requirements for the GULA
National Healthcare Platform to protect patient health information (PHI) at
rest, in transit, and in use.

## 2. Scope

This policy applies to all data, systems, and communications within the GULA
platform, including databases, APIs, files, backups, logs, and network traffic.

## 3. Policy

### 3.1 Required Algorithms

| Use Case | Algorithm | Standard | Key Length |
|----------|-----------|----------|------------|
| Data at rest (AES) | AES-256-GCM | NIST SP 800-38D | 256-bit |
| Data in transit | TLS 1.3 | RFC 8446 | X.509 P-256/384 |
| Password hashing | Argon2id | RFC 9106 | Memory: 64MB, t:3, p:4 |
| Digital signatures | Ed25519 | RFC 8032 | 256-bit |
| Alternative signatures | ECDSA P-256 | FIPS 186-5 | 256-bit |
| Hash (general) | SHA-256 / SHA3-256 | FIPS 180-4 / FIPS 202 | 256-bit |
| Hash (audit chain) | SHA3-256 | FIPS 202 | 256-bit |
| Key derivation | HKDF-SHA256 | RFC 5869 | 256-bit |
| Random generation | CTR_DRBG | NIST SP 800-90A | 256-bit |

### 3.2 Prohibited Algorithms

The following algorithms are strictly prohibited:
- DES, 3DES, RC2, RC4, MD2, MD4, MD5, SHA-1, DSA, RSA < 2048-bit
- ECB mode in any block cipher
- Pseudo-random generators not conforming to NIST SP 800-90A

### 3.3 Key Management Requirements

- All encryption keys must be generated using a CSPRNG (CTR_DRBG)
- Keys stored in encrypted format using a master key
- Key access logged and audited
- Keys never stored in source code, configuration files, or environment variables
- Key escrow: master keys backed up in hardware security module (HSM)
- Key hierarchy: master key > data encryption keys > field encryption keys

### 3.4 Key Rotation Schedule

- Data encryption keys: every 90 days
- JWT signing keys: every 180 days
- TLS certificates: every 365 days (auto-renewal at 60 days)
- Master keys: every 2 years
- Patient-specific keys: per-session or on consent revocation

### 3.5 PHI Encryption Requirements

- All PHI must be encrypted at rest using AES-256-GCM
- Column-level encryption for PHI fields in databases
- Each PHI column uses a unique encryption key (envelope encryption)
- Encryption keys for PHI are stored separately from the data
- PHI encryption keys are backed by an HSM or cloud KMS
- Patient consent revocation triggers immediate key rotation

### 3.6 Field-Level Encryption Requirements

- Fields containing patient identifiers must be encrypted at the application layer
- Encrypted fields: national ID (NIN), name, address, phone, email, medical record number
- Search over encrypted data uses deterministic encryption with salt
- Index fields use HMAC-based blinded indexing

### 3.7 Transport Encryption

- All network communications use TLS 1.3 minimum
- mTLS required for inter-service communication within the platform
- TLS certificates must be from a trusted CA or internal PKI
- Certificate pinning for critical service endpoints
- HSTS enabled with max-age=31536000 and preload

## 4. Enforcement

- Automated compliance scanning runs daily
- Crypto module self-tests run on every deployment
- Violations trigger immediate incident response
- Annual penetration testing validates crypto implementations

## 5. Review

This policy is reviewed annually or after any cryptographic vulnerability
disclosure affecting the GULA platform.
