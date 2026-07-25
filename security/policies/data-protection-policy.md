# Data Protection Policy

## 1. Purpose

Define data classification, handling, retention, and disposal requirements for
the GULA National Healthcare Platform to protect patient health information
(PHI) and ensure compliance with Iraqi healthcare regulations, HIPAA, and GDPR.

## 2. Scope

This policy applies to all data processed, stored, or transmitted by the GULA
platform, including electronic health records, laboratory results, imaging data,
administrative data, and system metadata.

## 3. Data Classification

### 3.1 Classification Levels

| Level | Definition | Examples | Access Control |
|-------|------------|----------|----------------|
| **PHI** | Protected Health Information | Patient names, NIN, diagnoses, lab results, treatment records | Encrypted at rest, role+ABAC, MFA required |
| **Restricted** | Highly sensitive non-PHI data | Encryption keys, credentials, audit logs, security config | Encrypted, limited access, audit trail |
| **Confidential** | Internal sensitive data | Business plans, architecture docs, employee data | Access-controlled, no public disclosure |
| **Internal** | Internal operational data | Operational metrics, internal procedures | All employees, no external sharing |
| **Public** | Intended for public consumption | Marketing materials, public APIs, documentation | No restrictions |

### 3.2 Handling Requirements

| Level | Storage | Transfer | Retention | Disposal |
|-------|---------|----------|-----------|----------|
| **PHI** | AES-256-GCM encrypted | TLS 1.3 + field encryption | Per regulation (min 10 years) | Cryptographic erase + secure wipe |
| **Restricted** | AES-256-GCM encrypted | TLS 1.3 | Per policy (min 7 years) | Cryptographic erase |
| **Confidential** | Standard encryption | TLS 1.3 | Business need + 3 years | Secure delete |
| **Internal** | No encryption required | TLS 1.3 | Business need | Standard delete |
| **Public** | No protection required | No restrictions | Indefinite | N/A |

## 4. Data Retention Schedules

| Data Type | Retention Period | Legal Basis | Disposal After |
|-----------|-----------------|-------------|----------------|
| Patient health records | 25 years after last encounter | Iraqi MoH regulation | Cryptographic erase |
| Laboratory results | 10 years | CAP/CLSI standards | Secure wipe |
| Prescription records | 10 years | Pharmacy regulation | Secure delete |
| Audit logs | 7 years | HIPAA, Iraqi regulation | Archive then delete |
| Authentication logs | 2 years | Security best practice | Archive then delete |
| Security incidents | 10 years | Legal/regulatory | Archive indefinitely |
| Financial data | 10 years | Tax/accounting law | Secure wipe |
| Employee records | 5 years after departure | Labor law | Secure delete |
| Session data | 24 hours | Operational | Automatic deletion |
| Temporary files | End of session | Operational | Automatic deletion |

## 5. Data Disposal Procedures

### 5.1 Digital Data
- **PHI**: AES-256-GCM key destruction (cryptographic erase) followed by NIST SP 800-88 purge
- **Restricted**: Cryptographic erase or overwrite (3-pass random)
- **Confidential/Internal**: Standard secure delete (1-pass zero)
- **Media destruction**: Physical shredding or degaussing for decommissioned drives

### 5.2 Physical Records
- Shred using cross-cut shredder (particle size < 1mm x 5mm)
- Incineration for highest security
- Certificate of destruction required for third-party disposal

## 6. Data Transfer Requirements

- All PHI transfers: TLS 1.3 + field-level encryption + audit trail
- Cross-governorate transfers: encrypted with recipient's public key
- International transfers: only to countries with adequate protection (GDPR Art 45)
- Third-party transfers: require BAA and data processing agreement
- Email: never send PHI via email (use secure portal)
- Removable media: prohibited for PHI

## 7. Data Masking Requirements

| Data Element | Masking Rule | Production | Test/Dev |
|-------------|--------------|------------|----------|
| National ID (NIN) | Show last 4 digits | Full | Masked |
| Patient name | Show first name + last initial | Full | Pseudonymized |
| Phone number | Show last 4 digits | Full | Masked |
| Email address | Show domain only | Full | Random |
| Address | Show city only | Full | Randomized |
| Medical record number | Sequential pseudonym | Full | Random |
| Date of birth | Show year only [YYYY] | Full | Randomized year |

## 8. Enforcement

- Automated data classification scanning runs daily
- Data loss prevention (DLP) monitoring for sensitive data egress
- Quarterly data protection audits
- Annual data protection impact assessment (DPIA)
- Violations reported to CISO and DPO

## 9. Review

This policy is reviewed annually or after any data protection incident.
