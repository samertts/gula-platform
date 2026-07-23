# Open Source Policy

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution Amendment — PROGRAM-CONSTITUTION-001, Article 2
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Policy Statement

Open Source software SHALL always be preferred over proprietary software
in the GULA National Digital Health Platform. Commercial products are the
final option, used only when no suitable open source alternative exists.

---

## License Priority

| Priority | License Type | Examples | When to Use |
|----------|-------------|----------|-------------|
| 1 | Apache 2.0 | Kubernetes, Hadoop, Kafka, TensorFlow | Preferred — permissive, patent protection |
| 2 | MIT | React, Node.js, Express, jQuery | Preferred — maximally permissive |
| 3 | BSD (2/3-Clause) | PostgreSQL, Redis, Nginx, OpenBSD | Preferred — permissive, minimal restrictions |
| 4 | MPL 2.0 | Mozilla Firefox, Thunderbird | Acceptable — file-level copyleft |
| 5 | LGPL | GNU libraries | Acceptable — library-level copyleft |
| 6 | GPLv2/v3 | Linux, Git, WordPress | Acceptable — strong copyleft (verify compatibility) |
| 7 | AGPL | MongoDB (pre-2018), Grafana (AGPLv3) | Use with caution — network copyleft |
| 8 | Proprietary/Commercial | — | Final option — requires exception approval |

---

## Open Source Evaluation Criteria

Every open source component considered for use MUST be evaluated against:

### 1. License Compatibility
- License MUST be OSI-approved
- License MUST be compatible with Apache 2.0 (primary platform license)
- Copyleft licenses (GPL, AGPL) require legal review for distribution scenarios

### 2. Maintenance Status
- Last release: within 12 months
- Last commit: within 6 months
- Active maintainer response to issues
- Clear roadmap or release cadence

### 3. Community Health
- GitHub stars: >100 for critical components
- Contributors: >5 active contributors
- Forks: evidence of community adoption
- Documentation quality

### 4. Security Posture
- No unpatched critical CVEs
- Security policy documented (SECURITY.md)
- Recent security releases
- Dependency chain scanned

### 5. Production Readiness
- Stable API (not alpha/beta for critical components)
- Test coverage visible
- Deployment documentation
- Backup/restore procedures documented

---

## Prohibited Dependencies

Without explicit Architecture Review Board approval:

- **Proprietary SDKs** — Must use abstraction layer
- **Vendor-locked services** — Must have replacement strategy
- **Dual-licensed projects** — Must use the open source terms
- **Source-available (not OSI-approved)** — Not considered open source
- **Freeware/Shared Source** — Not acceptable

---

## Open Source First Workflow

```
Need a capability
        │
        ▼
Search existing platform — Already have it? Reuse.
        │
        ▼ (not found)
Search open source ecosystem
        │
        ├── Found suitable OSS? → Evaluate → Adopt
        │
        └── No suitable OSS?
                │
                ▼
        Consider building in-house (open source our solution)
                │
                ▼
        Commercial product (last resort, with exception)
```

---

## Contributing Back

As a platform built on open source, we SHOULD contribute back:
- Bug fixes to dependencies we use
- Performance improvements
- Localization (Arabic translations)
- Documentation improvements
- Non-core modules we build (as new open source projects)

---

## Dependency Declaration

Every open source dependency MUST be declared with:
1. Package name and version
2. License type
3. Purpose in the platform
4. Alternative considered (if any)
5. Security scan result

For Python: in `backend/requirements.txt` with comment annotation
For Node: in `package.json` with license field

---

## Compliance

### CI Enforcement
- CI validates license of every dependency
- CI blocks PR if dependency has non-OSI-approved license
- CI reports if newer stable version available

### Quarterly Review
- Full dependency audit every quarter
- Identify end-of-life or abandoned dependencies
- Plan replacements for at-risk dependencies
- Review license changes in upstream projects

---

## Exceptions

Exceptions to Open Source First policy require:
1. Architecture Decision Record
2. Technical justification
3. Cost analysis (commercial vs open source TCO)
4. Migration strategy to open source
5. Engineering Lead + Architecture Review Board approval
6. Annual re-evaluation
