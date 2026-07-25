# GULA Security Framework (GSF)

**Version 1.0.0 | Status: Active Development | Classification: Internal**

The GULA Security Framework (GSF) is the **permanent enterprise security subsystem**
for the GULA National Healthcare Platform. GSF provides comprehensive security
controls across identity, cryptography, authentication, authorization, audit,
compliance, infrastructure, and healthcare-specific security domains.

GSF is designed to meet the security requirements of a national healthcare
platform deployed across all Iraqi governorates, serving millions of patients
through thousands of healthcare facilities.

---

## Architecture Overview

GSF follows **Clean Architecture** principles with four layers:

```
┌─────────────────────────────────────────────────────────┐
│                   Frameworks & Drivers                    │
│  FastAPI  │  FHIR  │  Kubernetes  │  Terraform  │  Vault  │
├─────────────────────────────────────────────────────────┤
│                   Interface Adapters                      │
│  Middleware  │  API Controllers  │  CLI  │  Event Handlers │
├─────────────────────────────────────────────────────────┤
│                     Use Cases                             │
│  Authentication  │  Authorization  │  Audit  │  Compliance │
├─────────────────────────────────────────────────────────┤
│                     Entities                              │
│  Identity  │  Policy  │  Certificate  │  Consent  │  Secret │
└─────────────────────────────────────────────────────────┘
```

### Zero Trust Architecture

GSF implements a **Zero Trust** security model:

- **Never trust, always verify** — every request is authenticated and authorized
- **Least privilege access** — fine-grained RBAC/ABAC with resource scoping
- **Microsegmentation** — mTLS mesh with network policy enforcement
- **Continuous monitoring** — real-time threat detection and audit logging
- **Assume breach** — defense-in-depth with multiple security layers

---

## Module Index

| GSF ID | Module | Description |
|--------|--------|-------------|
| GSF-001 | identity | Multi-tenant identity provider with NIN integration |
| GSF-002 | secrets | Encrypted secret storage (Vault, AWS, local) |
| GSF-003 | crypto | AEAD encryption, signatures, key derivation |
| GSF-004 | authentication | Password, TOTP, WebAuthn, OAuth2, SAML, MFA |
| GSF-005 | authorization | RBAC/ABAC with Rego policy engine |
| GSF-006 | audit | Immutable audit log with hash chaining |
| GSF-007 | compliance | Multi-framework compliance mapping |
| GSF-008 | headers | Zero-Trust HTTP security headers |
| GSF-009 | network | mTLS mesh, network policies, traffic monitoring |
| GSF-010 | database | Column encryption, data masking, audit triggers |
| GSF-011 | container | Image signing, vulnerability scanning, seccomp |
| GSF-012 | kubernetes | PSS, OPA Gatekeeper, Kyverno, network policies |
| GSF-013 | terraform | Policy-as-Code, drift detection, IAM analysis |
| GSF-014 | github | Repo posture, secret scanning, Dependabot |
| GSF-015 | ci | CI/CD security, SBOM, SLSA attestation |
| GSF-016 | supply-chain | Dependency verification, provenance tracking |
| GSF-017 | fhir | FHIR R4 security labels, consent, SMART-on-FHIR |
| GSF-018 | privacy | Data classification, anonymization, consent |
| GSF-019 | threat-detection | Anomaly detection, SIEM integration |
| GSF-020 | integrity | File integrity monitoring, runtime verification |

---

## Quick Start

### Installation

```bash
pip install gula-security-framework
```

With optional backends:

```bash
pip install gula-security-framework[aws]      # AWS Secrets Manager support
pip install gula-security-framework[vault]     # HashiCorp Vault support
pip install gula-security-framework[all]       # All optional dependencies
```

### Basic Usage

```python
from security import GSF_VERSION
from security.modules.crypto import CryptoEngine
from security.modules.authentication import Authenticator
from security.modules.authorization import AuthorizationEngine

# Initialize cryptographic engine
crypto = CryptoEngine(key_derivation="Argon2id")

# Initialize authenticator with MFA
auth = Authenticator(
    crypto_engine=crypto,
    mfa_required=True,
    totp_enabled=True,
    webauthn_enabled=True,
)

# Initialize authorization engine
authz = AuthorizationEngine(
    rbac_enabled=True,
    abac_enabled=True,
    policy_backend="rego",
)
```

---

## Integration Guide

### With GULA Platform (FastAPI)

```python
from fastapi import FastAPI, Depends
from security.modules.headers import SecurityHeadersMiddleware
from security.modules.authentication import Authenticator
from security.modules.audit import AuditLogger

app = FastAPI()

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Initialize security services
authenticator = Authentitor(...)
audit_logger = AuditLogger(...)

@app.post("/fhir/Patient")
async def create_patient(
    patient: Patient,
    user: AuthenticatedUser = Depends(authenticator.require_auth),
):
    audit_logger.log("Patient.Create", user_id=user.id, resource=patient)
    ...
```

### With Kubernetes

```python
from security.modules.kubernetes import K8sSecurityEngine

engine = K8sSecurityEngine(
    enforce_pss=True,
    enable_gatekeeper=True,
    enable_kyverno=True,
)
await engine.apply_pod_security_standards(namespace="gula-production")
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Clean Architecture, Zero Trust, data flows |
| [THREAT_MODEL.md](THREAT_MODEL.md) | STRIDE threat model with mitigations |
| [RISK_REGISTER.md](RISK_REGISTER.md) | Risk register with 30+ identified risks |
| [ATTACK_SURFACE.md](ATTACK_SURFACE.md) | Network, application, supply chain analysis |
| [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) | IR plan aligned with NIST SP 800-61 |
| [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) | DR plan with RPO/RTO targets |
| [BUSINESS_CONTINUITY.md](BUSINESS_CONTINUITY.md) | BCP for Iraqi governorates |
| [COMPLIANCE.md](COMPLIANCE.md) | 15+ framework compliance mapping |
| [SECURITY_POLICY.md](SECURITY_POLICY.md) | Detailed security policy |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting and disclosure |
| [SECURITY_SCORECARD.md](SECURITY_SCORECARD.md) | Measurable security metrics |
| [ROADMAP.md](ROADMAP.md) | Development roadmap through Q4 2027 |

---

## License

Apache-2.0 — See [LICENSE](../LICENSE) for details.

## Contact

- **Security Issues**: security@gula.iq
- **Engineering Team**: engineering@gula.iq
- **National Coordination**: iraq-cert@gula.iq
