# GULA Digital Certificate System

## Overview

The GULA Digital Certificate System provides tamper-evident, verifiable digital
certificates for all certification types. Built on open standards (Open Badges 2.0,
W3C Verifiable Credentials), the system ensures certificates are portable,
verifiable, and resistant to forgery.

### Design Principles

1. **Tamper-Evident**: Any alteration invalidates the certificate
2. **Self-Sovereign**: Certificate holders own and control their credentials
3. **Instantly Verifiable**: Verification in seconds via QR or API
4. **Offline-Capable**: Verification works without internet (QR + hash)
5. **Privacy-Preserving**: Only required information exposed during verification
6. **Arabic-First**: Full Arabic language support in certificates and verification
7. **Standards-Compliant**: Open Badges 2.0 and W3C VC standards

---

## 1. Certificate Data Model

### Core Fields

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://purl.imsglobal.org/spec/ob/v3p0/context.json"
  ],
  "id": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "type": ["VerifiableCredential", "OpenBadgeCredential"],
  "issuer": {
    "id": "https://gula-platform.com/certification/issuer",
    "type": "Profile",
    "name": "GULA Certification Authority",
    "name_ar": "هيئة اعتماد جولا",
    "url": "https://gula-platform.com",
    "email": "certification@gula-platform.com",
    "publicKey": "did:gula:issuer:0xabc123..."
  },
  "issuanceDate": "2026-07-01T00:00:00Z",
  "expirationDate": "2028-07-01T00:00:00Z",
  "credentialSubject": {
    "id": "did:gula:user:550e8400-e29b-41d4-a716-446655440001",
    "type": "Person",
    "name": "د. أحمد محمد",
    "name_en": "Dr. Ahmed Mohammed",
    "nationalId": "encrypted:...",
    "role": "lab_scientist",
    "labId": "550e8400-e29b-41d4-a716-446655440002",
    "labName": "مختبر بغداد المركزي",
    "labName_en": "Baghdad Central Laboratory"
  },
  "credential": {
    "id": "https://gula-platform.com/certificate/IND-03-2026-00042",
    "type": ["GulaCertificate"],
    "name": "GULA Lab Specialist",
    "name_ar": "أخصائي مختبرات جولا",
    "description": "Advanced GULA lab management skills certification",
    "description_ar": "شهادة مهارات إدارة المختبرات المتقدمة في جولا",
    "certificationType": "IND-03",
    "level": "gold",
    "score": 91.5,
    "criteria": {
      "id": "https://gula-platform.com/certification/criteria/IND-03",
      "narrative": "Completed advanced lab operations training and passed comprehensive assessment"
    },
    "evidence": [
      {
        "id": "https://gula-platform.com/assessment/ASSESS-2026-00123",
        "type": "Assessment",
        "title": "GULA Lab Specialist Exam",
        "date": "2026-06-15",
        "score": 91.5
      }
    ]
  },
  "proof": {
    "type": "BlockchainHash",
    "created": "2026-07-01T00:00:00Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:gula:issuer:0xabc123#keys-1",
    "blockchain": "ethereum-sepolia",
    "blockNumber": 12345678,
    "transactionHash": "0xdef456...",
    "hash": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
  },
  "arabicMetadata": {
    "template": "cert-platinum-arabic",
    "font": "NotoNaskhArabic",
    "rtl": true,
    "rights": "حقوق النشر © 2026 هيئة اعتماد جولا. جميع الحقوق محفوظة."
  }
}
```

### Metadata Fields

| Category | Fields | Required |
|----------|--------|----------|
| **Identity** | id, type, issuer, issuanceDate, expirationDate | Yes |
| **Subject** | id, name, role, labId, nationalId (encrypted) | Yes |
| **Credential** | type, name, description, level, score, criteria | Yes |
| **Evidence** | assessment IDs, scores, dates | Yes |
| **Proof** | type, hash, blockchain info, signature | Yes |
| **Arabic** | template, font, rtl flag, rights | Yes |
| **Extension** | custom fields per certification type | Optional |

---

## 2. Blockchain Anchoring

### Architecture

```
Certificate Issued
       │
       ▼
Hash Generated (SHA-256 of canonical JSON)
       │
       ▼
Hash Written to Smart Contract
       │
       ▼
Block Confirmation (6 confirmations)
       │
       ▼
Transaction Hash Stored in Certificate
       │
       ▼
Certificate Published
```

### Smart Contract

```solidity
// GULA Certificate Registry (simplified)
pragma solidity ^0.8.20;

contract GulaCertificateRegistry {
    address public owner;
    mapping(bytes32 => CertificateEntry) public certificates;
    mapping(address => bool) public authorizedIssuers;
    
    struct CertificateEntry {
        bytes32 hash;
        uint256 timestamp;
        bool revoked;
        string metadata;
    }
    
    event CertificateRegistered(bytes32 indexed certificateId, bytes32 hash);
    event CertificateRevoked(bytes32 indexed certificateId);
    
    function register(bytes32 certificateId, bytes32 hash) external {
        require(authorizedIssuers[msg.sender], "Unauthorized issuer");
        certificates[certificateId] = CertificateEntry(hash, block.timestamp, false, "");
        emit CertificateRegistered(certificateId, hash);
    }
    
    function revoke(bytes32 certificateId) external {
        require(authorizedIssuers[msg.sender], "Unauthorized issuer");
        require(certificates[certificateId].timestamp != 0, "Not found");
        certificates[certificateId].revoked = true;
        emit CertificateRevoked(certificateId);
    }
    
    function verify(bytes32 certificateId, bytes32 hash) external view returns (bool valid, bool revoked, uint256 timestamp) {
        CertificateEntry memory entry = certificates[certificateId];
        valid = (entry.hash == hash && entry.timestamp != 0);
        revoked = entry.revoked;
        timestamp = entry.timestamp;
    }
}
```

### Chain Selection

| Chain | Purpose | Status |
|-------|---------|--------|
| **Ethereum Sepolia** | Testnet - development and testing | Active |
| **Ethereum Mainnet** | Production certificates | Planned |
| **Iraqi National Blockchain** | Sovereign anchoring (future) | Research |

### Hash Chain Integrity

Each certificate's hash is computed from the canonical JSON representation:

1. Sort all JSON keys alphabetically
2. Remove all whitespace
3. Encode as UTF-8
4. Compute SHA-256 hash
5. Store hash + certificate ID in smart contract

### Verification Process

```
Verification Request
       │
       ▼
Recompute Hash from Certificate JSON
       │
       ▼
Query Blockchain for Certificate Entry
       │
       ▼
Compare: Computed Hash == Stored Hash?
       │
       ├── Yes → Certificate is VALID
       │         Check revocation status
       │
       └── No  → Certificate is INVALID or TAMPERED
```

---

## 3. QR/Verification Codes

### QR Code Structure

```
QR Data Payload:
{
  "v": 1,
  "cid": "550e8400-e29b-41d4-a716-446655440000",
  "h": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "t": "sha256",
  "u": "https://verify.gula-platform.com/cert/550e8400"
}
```

### QR Placement

Certificates display QR codes in a consistent location:

- **Digital PDF**: Top-right corner of certificate
- **Physical Print**: Lower-right corner
- **Digital Wallet**: Card-style certificate, right side
- **Email**: Embedded in email footer
- **Social Media**: Included in share image

### Verification URL

```
Format: https://verify.gula-platform.com/cert/{certificateId}
Example: https://verify.gula-platform.com/cert/IND-03-2026-00042
```

### Verification Response

```json
{
  "valid": true,
  "certificate": {
    "number": "IND-03-2026-00042",
    "type": "GULA Lab Specialist",
    "type_ar": "أخصائي مختبرات جولا",
    "level": "gold",
    "holder": "د. أحمد محمد",
    "holder_en": "Dr. Ahmed Mohammed",
    "issuance_date": "2026-07-01",
    "expiration_date": "2028-07-01",
    "status": "active"
  },
  "blockchain": {
    "verified": true,
    "network": "ethereum-sepolia",
    "transaction": "0xdef456...",
    "block": 12345678,
    "timestamp": "2026-07-01T00:00:00Z"
  },
  "arabic": {
    "rtl": true,
    "lang": "ar"
  }
}
```

---

## 4. Certificate Templates

### Template Design Specifications

| Element | Specification |
|---------|---------------|
| **Dimensions** | A4 (210 × 297 mm) for print, 800 × 600 px for digital |
| **Resolution** | 300 DPI print, 72 DPI digital |
| **Color Scheme** | GULA brand colors (#1a73e8 primary, #34a853 secondary) |
| **Typography** | Noto Naskh Arabic (Arabic), Inter (English) |
| **RTL Support** | Right-aligned text, Arabic header placement |
| **Security Features** | Microtext, guilloche patterns, holographic overlay, QR code |
| **Digital Elements** | Embedded JSON-LD, verifiable credential data |

### Template Types

#### Individual Certificate Template

```
┌─────────────────────────────────────────────────────────────┐
│  [GULA Logo - Arabic]          [Gold Level Badge]            │
│  هيئة اعتماد جولا                                            │
│  GULA Certification Authority                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │           ي certify that                               │   │
│  │                                                      │   │
│  │           د. أحمد محمد                                │   │
│  │                                                      │   │
│  │       has successfully achieved the                   │   │
│  │                                                      │   │
│  │           GULA Lab Specialist                         │   │
│  │          أخصائي مختبرات جولا                          │   │
│  │                                                      │   │
│  │           Level: Gold | Score: 91.5%                  │   │
│  │                                                      │   │
│  │  [Detailed text describing the certification scope]   │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Certificate No: IND-03-2026-00042          [QR Code]        │
│  Issued: 2026-07-01  |  Expires: 2028-07-01                 │
│  Issued by: هيئة اعتماد جولا                                │
│                                                              │
│  ────────────────────────────────────────────────────────   │
│  Verify at: verify.gula-platform.com/cert/IND-03-2026-00042  │
│  Blockchain: Ethereum Sepolia | Tx: 0xdef456...             │
│                                                              │
│  [Authorized Signature]          [Digital Seal]             │
└─────────────────────────────────────────────────────────────┘
```

#### Organizational Certificate Template

```
┌─────────────────────────────────────────────────────────────┐
│  [GULA Logo - Arabic]          [Platinum Level Badge]       │
│  هيئة اعتماد جولا                                            │
│  GULA Certification Authority                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │            ي certify that                              │   │
│  │                                                      │   │
│  │        مختبر بغداد المركزي                            │   │
│  │      Baghdad Central Laboratory                       │   │
│  │                                                      │   │
│  │        has achieved the                               │   │
│  │                                                      │   │
│  │           GULA-Compliant Lab                          │   │
│  │          مختبر متوافق مع جولا                         │   │
│  │                                                      │   │
│  │           Level: Platinum | Score: 97.2%              │   │
│  │                                                      │   │
│  │  [Detailed scope: all laboratory departments]          │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Certificate No: ORG-02-2026-0015           [QR Code]        │
│  Issued: 2026-06-01  |  Expires: 2027-06-01                 │
│  Issued by: هيئة اعتماد جولا                                │
│                                                              │
│  ────────────────────────────────────────────────────────   │
│  Verify at: verify.gula-platform.com/cert/ORG-02-2026-0015   │
│                                                              │
│  [Authorized Signature]          [Digital Seal]             │
└─────────────────────────────────────────────────────────────┘
```

### Template Variables

Each template supports variable substitution:

```
{{certificate_number}}
{{holder_name_ar}}
{{holder_name_en}}
{{holder_title_ar}}
{{holder_title_en}}
{{organization_name_ar}}
{{organization_name_en}}
{{certification_name_ar}}
{{certification_name_en}}
{{level_name_ar}}
{{level_name_en}}
{{score}}
{{issue_date}}
{{expiry_date}}
{{issuer_name_ar}}
{{issuer_name_en}}
{{verification_url}}
{{qr_code_data_url}}
{{blockchain_info}}
{{signature_image_url}}
{{seal_image_url}}
```

---

## 5. Issuance Workflow

### Automated Issuance

```
Trigger: Assessment Passed OR Certification Approved
       │
       ▼
1. Generate Certificate ID
       │
       ▼
2. Populate Template Variables
       │
       ▼
3. Generate Certificate JSON-LD
       │
       ▼
4. Compute SHA-256 Hash
       │
       ▼
5. Submit Hash to Blockchain
       │
       ▼
6. Generate QR Code
       │
       ▼
7. Generate PDF Document
       │
       ▼
8. Store in Certificate Repository
       │
       ▼
9. Notify Certificate Holder
       │
       ▼
10. Publish to Digital Wallet
```

### Manual Issuance (for organizational certificates)

```
Application Approved
       │
       ▼
1. Certification Officer Reviews Final Documents
       │
       ▼
2. Certificate Created in Admin Portal
       │
       ▼
3. Digital Signatures Applied
       │
       ▼
4. Blockchain Anchoring (same automated steps 4-6)
       │
       ▼
5. Certificate Issued via Portal
```

### Bulk Issuance

For batch certification (e.g., all staff at a newly certified lab):

```
1. Upload candidate list (CSV/JSON)
2. Verify prerequisites completed
3. Generate certificates in batch
4. Individual blockchain anchoring for each
5. Bulk notification (email + SMS)
```

---

## 6. Revocation Process

### Revocation Grounds

| Ground | Description | Effective | Notification |
|--------|-------------|-----------|--------------|
| **Expiry** | Certificate validity period ended | Automatic | 90/30/7 days before |
| **Violation** | Terms of certification violated | Immediate | Within 24 hours |
| **Misrepresentation** | False information in application | Immediate | Within 24 hours |
| **Non-compliance** | Failed surveillance audit | After appeal period | 30 days notice |
| **Voluntary surrender** | Holder requests revocation | On request | Immediate |
| **System error** | Certificate issued in error | Immediate | Within 24 hours |

### Revocation Workflow

```
Revocation Triggered
       │
       ▼
1. Revocation Reason Documented
       │
       ▼
2. Holder Notified (right to appeal)
       │
       ▼
3. Certificate Status Updated in DB → "revoked"
       │
       ▼
4. Blockchain Updated (revocation flag)
       │
       ▼
5. Digital Wallet Updated (automatic sync)
       │
       ▼
6. Verification API Returns "revoked" Status
       │
       ▼
7. Internal Systems Notified (EventBus)
       │
       ▼
8. Certificate Removed from Public Directory
```

### Revocation Record

```json
{
  "certificateId": "IND-03-2026-00042",
  "revokedAt": "2027-03-15T10:30:00Z",
  "revokedBy": "cert-officer@gula-platform.com",
  "reason": "Non-compliance with continuing education requirements",
  "reason_ar": "عدم الامتثال لمتطلبات التعليم المستمر",
  "evidence": "https://gula-platform.com/certification/revocations/2027-001",
  "appealDeadline": "2027-04-14T10:30:00Z",
  "blockchainTx": "0x789abc...",
  "notifiedAt": "2027-03-15T11:00:00Z",
  "notificationMethod": "email_sms"
}
```

---

## 7. Verification API

### Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/certificates/verify/{certificateId}` | GET | Verify certificate by ID | None (public) |
| `/api/v1/certificates/verify` | POST | Verify certificate by payload | None (public) |
| `/api/v1/certificates/{certificateId}` | GET | Get certificate details | API Key |
| `/api/v1/certificates/{certificateId}/image` | GET | Download certificate image | API Key |
| `/api/v1/certificates/{certificateId}/pdf` | GET | Download certificate PDF | API Key |
| `/api/v1/certificates/search` | GET | Search certificates | API Key |

### Public Verification API

```python
# Example: Verify certificate
GET /api/v1/certificates/verify/IND-03-2026-00042

Response 200:
{
    "valid": true,
    "status": "active",
    "level": "gold",
    "holder_name_ar": "د. أحمد محمد",
    "holder_name_en": "Dr. Ahmed Mohammed",
    "certification_name_ar": "أخصائي مختبرات جولا",
    "certification_name_en": "GULA Lab Specialist",
    "issue_date": "2026-07-01",
    "expiry_date": "2028-07-01",
    "blockchain_verified": true,
    "blockchain": {
        "network": "ethereum-sepolia",
        "transaction": "0xdef456...",
        "block": 12345678,
        "timestamp": "2026-07-01T00:00:00Z"
    }
}

Response 200 (revoked):
{
    "valid": false,
    "status": "revoked",
    "revocation_reason": "Non-compliance with continuing education requirements",
    "revoked_at": "2027-03-15T10:30:00Z"
}

Response 200 (not found):
{
    "valid": false,
    "status": "not_found"
}
```

### Rate Limiting

| Tier | Rate Limit | Applied To |
|------|------------|------------|
| Public (no API key) | 10 requests/min per IP | Verify endpoints |
| Standard API key | 100 requests/min | All endpoints |
| Premium API key | 1000 requests/min | All endpoints |
| Internal | Unlimited | Internal services |

---

## 8. Digital Wallet

### User Wallet Features

| Feature | Description |
|---------|-------------|
| **Certificate Collection** | All earned certificates in one place |
| **QR Display** | Display QR for scanning |
| **Share** | Share certificate via email, link, social |
| **Verify** | Real-time verification status |
| **Download** | PDF/PNG download options |
| **Auto-Sync** | New certificates automatically appear |
| **Revocation Alerts** | Notification if certificate revoked |
| **Expiry Tracking** | Countdown to certificate expiry |
| **Portable Profile** | JSON-LD export for third-party systems |

### Wallet UI (Mobile & Web)

```
┌─────────────────────────────────┐
│  [Back]  محفظة الشهادات          │
│         Certificate Wallet      │
├─────────────────────────────────┤
│                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │      │ │      │ │      │   │
│  │ Gold │ │ Silver│ │Plat. │   │
│  │ Lab  │ │ Clin.│ │Admin │   │
│  │ Spec.│ │ User │ │      │   │
│  │      │ │      │ │      │   │
│  │IND-03│ │IND-01│ │IND-04│   │
│  └──────┘ └──────┘ └──────┘   │
│                                 │
│  ┌──────────────────────┐      │
│  │  إظهار رمز الاستجابة    │      │
│  │  Show QR Code        │      │
│  └──────────────────────┘      │
│                                 │
│  ┌──────────────────────┐      │
│  │  مشاركة الشهادة        │      │
│  │  Share Certificate   │      │
│  └──────────────────────┘      │
│                                 │
│  ┌──────────────────────┐      │
│  │  تنزيل PDF           │      │
│  │  Download PDF        │      │
│  └──────────────────────┘      │
│                                 │
│  Expires in: 365 days          │
│  Blockchain: ✓ Verified        │
│                                 │
└─────────────────────────────────┘
```

### Wallet API

| Endpoint | Description |
|----------|-------------|
| `/api/v1/wallet/certificates` | List user's certificates |
| `/api/v1/wallet/certificates/{id}` | Get certificate details |
| `/api/v1/wallet/share/{id}` | Generate share link |
| `/api/v1/wallet/export` | Export all certificates as JSON-LD |
| `/api/v1/wallet/import` | Import certificate from external issuer |

---

## 9. Integration with GULA Core

### User Profile Integration

```python
# Certificate data available in user profile
GET /api/v1/users/{id}/profile

Response includes:
{
    "certifications": [
        {
            "id": "IND-03-2026-00042",
            "type": "IND-03",
            "name_ar": "أخصائي مختبرات جولا",
            "name_en": "GULA Lab Specialist",
            "level": "gold",
            "status": "active",
            "expires_at": "2028-07-01",
            "badge_url": "/static/badges/lab-specialist-gold.svg"
        }
    ],
    "cme_hours": {
        "current": 35,
        "required": 25,
        "target_date": "2027-06-30",
        "status": "on_track"
    }
}
```

### SSO Integration

- Certificate wallet accessible via GULA single sign-on
- No separate login required for certificate portal
- Certificate data synced to GULA user profile
- Badge display in GULA dashboard navigation

### Event Bus Integration

| Event | Trigger | Consumer |
|-------|---------|----------|
| `certificate.issued` | New certificate issued | Notification service, user profile |
| `certificate.revoked` | Certificate revoked | Notification service, user profile |
| `certificate.expiring` | 90/30/7 days before expiry | Notification service |
| `certificate.updated` | Level change, renewal | User profile, analytics |
| `certificate.verified` | Certificate externally verified | Analytics (verification metrics) |

### Audit Integration

All certificate operations logged to GULA Audit Service:

- Certificate issuance (who, when, for whom)
- Certificate verification (who verified, result)
- Certificate revocation (who, why, when)
- Certificate download/sharing (user action, timestamp)

---

## 10. Standards Compliance

### Open Badges 2.0

The GULA certificate system implements the IMS Global Open Badges 2.0 standard:

| Requirement | GULA Implementation |
|-------------|---------------------|
| BadgeClass | Certificate type definition |
| Issuer | GULA Certification Authority |
| Assertion | Individual certificate instance |
| Evidence | Assessment results, training records |
| Endorsement | Third-party verification (future) |
| Bake endpoint | Certificate image embedded with metadata |
| Verification | Blockchain + API verification |

### W3C Verifiable Credentials

| Requirement | GULA Implementation |
|-------------|---------------------|
| Context | W3C VC context + OB context |
| Type | VerifiableCredential, OpenBadgeCredential |
| Credential ID | UUID-based unique identifier |
| Issuer DID | Decentralized identifier |
| Subject DID | Holder's decentralized identifier |
| Proof | Blockchain hash + digital signature |
| Status | Revocation registry on blockchain |

### Mapping to W3C VC Data Model

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", ...],
  "id": "urn:uuid:...",
  "type": ["VerifiableCredential"],
  "issuer": { "id": "did:gula:issuer:..." },
  "issuanceDate": "2026-07-01T00:00:00Z",
  "expirationDate": "2028-07-01T00:00:00Z",
  "credentialSubject": { ... },
  "credentialStatus": {
    "id": "https://gula-platform.com/certificate/status/IND-03-2026-00042",
    "type": "BlockchainStatusList2021",
    "blockchain": "ethereum-sepolia",
    "contractAddress": "0x..."
  },
  "proof": { ... }
}
```

### ISO 17024 Compliance

The certification system aligns with ISO/IEC 17024 (Conformity assessment —
General requirements for bodies operating certification of persons):

| ISO 17024 Clause | GULA Implementation |
|------------------|---------------------|
| Certification body structure | GULA Certification Board |
| Impartiality | Conflict of interest policy, auditor rotation |
| Personnel competence | Auditor qualification program |
| Certification scheme | Published certification criteria per type |
| Examination | Standardized, proctored, recorded |
| Certification decision | Independent of examination |
| Appeals | Formal appeals process |
| Records | Immutable audit trail |

---

## Appendix: Certificate File Formats

| Format | Use Case | File Extension | MIME Type |
|--------|----------|---------------|-----------|
| PDF | Official document, print | .pdf | application/pdf |
| PNG | Digital display, sharing | .png | image/png |
| SVG | Web display, responsive | .svg | image/svg+xml |
| JSON-LD | Data exchange, wallets | .json | application/ld+json |
| JWT | Compact verification tokens | .jwt | application/jwt |

## Appendix: Certificate Repository Structure

```
certificates/
├── issued/                    # Active certificate storage
│   ├── IND-03-2026-00042/
│   │   ├── certificate.json   # JSON-LD credential
│   │   ├── certificate.pdf    # PDF document
│   │   ├── certificate.png    # PNG image
│   │   ├── qr.png             # QR code image
│   │   └── metadata.json      # Issue metadata
│   └── ...
├── templates/                 # Certificate templates
│   ├── individual-gold/
│   ├── individual-platinum/
│   ├── organizational-silver/
│   └── ...
├── revoked/                   # Revoked certificate archive
└── blockchain/                # Blockchain transaction cache
```

## Appendix: Verification Widget (Embedded)

Third-party websites can embed certificate verification:

```html
<!-- Embedded verification widget -->
<iframe 
  src="https://verify.gula-platform.com/embed/IND-03-2026-00042"
  width="400"
  height="600"
  frameborder="0">
</iframe>

<!-- Or via JavaScript widget -->
<script src="https://verify.gula-platform.com/widget.js"></script>
<script>
  GulaVerify.init({
    certificateId: 'IND-03-2026-00042',
    container: '#verify-container',
    language: 'ar'
  });
</script>
```

## Appendix: Certificate Statistics and Analytics

| Metric | Description |
|--------|-------------|
| Certificates issued (total) | Lifetime certificate count |
| Certificates active | Currently valid certificates |
| Verification requests | Daily/weekly/monthly verification volume |
| Average verification time | Time to complete verification |
| Revocation rate | Percentage of certificates revoked |
| Top certification types | Most popular certifications |
| Average score | Average assessment score per type |
| Renewal rate | Percentage of certificates renewed |
| Appeal rate | Percentage of decisions appealed |
| Fraud attempts | Detected forgery attempts |
