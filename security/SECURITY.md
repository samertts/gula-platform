# Security Policy — GULA Security Framework (GSF)

## Supported Versions

| Version | Supported | End of Life |
|---------|-----------|-------------|
| 1.0.x   | Yes       | TBD         |
| < 1.0   | No        | —           |

Only the latest minor release of the current major version receives security
updates. Users must upgrade to the latest version to receive fixes.

## Vulnerability Reporting

### Private Disclosure Process

We take the security of the GULA platform seriously. If you believe you have
found a security vulnerability in the GULA Security Framework or any GULA
platform component, please report it to us immediately.

**DO NOT** report security vulnerabilities through public GitHub issues,
discord channels, or other public forums.

### Reporting Channels

| Channel | Contact | Response Time |
|---------|---------|---------------|
| Primary Email | security@gula.iq | 24 hours |
| PGP Encrypted | security-pgp@gula.iq | 24 hours |
| National CERT | iraq-cert@gula.iq | 4 hours (critical) |

### PGP Key

```
Fingerprint: 4A3B 5E8F 1C2D 9E7F 0B6A  3C8D 2E1F 4A5B 6C7D 8E9F
Key ID: 0xABCDEF1234567890
```

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected GSF version(s)
- Affected module(s) (GSF-001 through GSF-020)
- Any proof-of-concept code (if safe to share)
- Your contact information for follow-up

### What to Expect

1. **Acknowledgment** within 24 hours of submission
2. **Initial assessment** within 72 hours
3. **Remediation timeline** within 5 business days
4. **Regular updates** every 48 hours until resolution

## Disclosure Policy

### Coordinated Disclosure

GSF follows a coordinated disclosure process:

1. **Triage** — Our security team verifies and assesses the vulnerability
2. **Fix Development** — A patch is developed and tested internally
3. **Embargo Period** — 90 days maximum from initial report to public disclosure
4. **Release** — A security advisory is published alongside the fix
5. **Public Disclosure** — After users have had time to update

### Vulnerability Publication

We publish all confirmed vulnerabilities with the following information:

- CVE identifier (if assigned)
- GSF advisory ID (GSF-ADV-YYYY-NNN)
- Affected versions
- Fix version
- CVSS 4.0 score
- Credits to the reporter

## Bug Bounty Program

GSF participates in a coordinated bug bounty program managed through the
Iraqi National Cybersecurity Authority (NCSA). This program is aligned with
Iraq's national healthcare security initiative.

### Scope

All GSF modules (GSF-001 through GSF-020) and GULA platform components:

- Core framework and libraries
- API endpoints and authentication
- Cryptographic implementations
- Authorization policies
- Audit logging integrity
- Infrastructure security controls
- FHIR security implementations

### Out of Scope

- Previously reported vulnerabilities
- Issues in third-party dependencies (report upstream)
- Theoretical attacks without practical exploit path
- Self-XSS or similar user-targeted attacks requiring social engineering
- Rate limiting bypass without demonstrable impact

### Rewards

| Severity | CVSS 4.0 Score | Reward (IQD) | Reward (USD) |
|----------|---------------|--------------|--------------|
| Critical | 9.0–10.0 | 5,000,000 | ~$3,400 |
| High     | 7.0–8.9   | 2,500,000 | ~$1,700 |
| Medium   | 4.0–6.9   | 1,000,000 | ~$680   |
| Low      | 0.1–3.9   | 500,000   | ~$340   |

## Security Contacts

| Role | Name | Contact |
|------|------|---------|
| GSF Security Lead | GULA Security Team | security@gula.iq |
| Deputy Security Lead | GULA Engineering | engineering@gula.iq |
| National CERT Liaison | Iraqi CERT | iraq-cert@gula.iq |
| Compliance Officer | GULA Compliance | compliance@gula.iq |
| Incident Response Lead | GULA SOC | soc@gula.iq |

## Changelog

- **2026-07-25**: Initial security policy (v1.0.0)
