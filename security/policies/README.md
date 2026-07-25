# GSF Policies

## Overview

This directory contains the security policies for the GULA Security Framework (GSF).
Each policy document defines requirements, standards, and procedures for a specific
security domain.

## Policy Documents

| Policy | Domain | Description |
|--------|--------|-------------|
| `access-control.md` | Access Control | RBAC roles/permissions, ABAC rules, least privilege, separation of duties |
| `encryption-policy.md` | Cryptography | Algorithm requirements, key management, PHI encryption, TLS standards |
| `incident-response-policy.md` | Incident Response | Classification, response procedures, escalation, communication, forensics |
| `data-protection-policy.md` | Data Protection | Classification (PHI/restricted/confidential/internal/public), retention, disposal, masking |

## Policy Enforcement

Policies are enforced by the `enforce-policies.sh` script:

```bash
./scripts/enforce-policies.sh          # Check all policies
./scripts/enforce-policies.sh --auto-fix   # Auto-fix fixable violations
./scripts/enforce-policies.sh --policy encryption-policy  # Check specific policy
```

## Policy Review Cycle

- Access Control: Quarterly
- Encryption: Annually or after cryptographic vulnerability disclosure
- Incident Response: Quarterly or after major incident
- Data Protection: Annually or after data protection incident

## Framework Mapping

Policies align with the following regulatory frameworks:
- OWASP ASVS Level 3
- NIST CSF 2.0 (Tier 4)
- ISO 27001:2022
- HIPAA Security Rule
- GDPR
- Iraqi MoH Healthcare Regulations
