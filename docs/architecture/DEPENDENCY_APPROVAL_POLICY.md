# Dependency Approval Policy

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution Amendment — PROGRAM-CONSTITUTION-001, Article 5 & 12
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Policy Statement

Every new dependency in the GULA National Digital Health Platform MUST go
through a formal approval process. This ensures all dependencies are:
- License-compliant
- Maintained and secure
- Cost-justified (if paid)
- Replaceable
- Necessary (not duplicating existing functionality)

---

## Dependency Categories

| Category | Definition | Approval Level |
|----------|-----------|---------------|
| **Standard Library** | Python/Node.js standard library | No approval needed |
| **Existing Dependency** | Already approved in platform | No approval needed (locked version) |
| **New Open Source** | New dependency, OSI-approved license | Tech Lead approval |
| **New Paid** | New dependency requiring payment | Engineering Lead + Architecture Board |
| **New Vendor SDK** | New dependency coupling to vendor | Architecture Review Board |
| **Dev Dependency** | Testing/linting/build only | No approval (but must be OSI-approved) |

---

## Approval Process

### Step 1: Justification

Document WHY this dependency is needed:
```
Dependency: [name]
Version: [version]
Purpose: [what problem does it solve?]
Existing alternatives in platform: [list and explain why unsuitable]
Open source alternatives: [list at least 3]
Paid alternatives: [list if applicable]
```

### Step 2: License Check

- Verify OSI-approved license
- Check license compatibility with Apache 2.0
- Flag copyleft licenses (GPL, AGPL) for legal review
- Document license in dependency registry

### Step 3: Security Scan

- Run `safety check` / `pip-audit` / `npm audit`
- Check CVE history (last 3 years)
- Verify security policy (SECURITY.md in repo)
- Document security findings

### Step 4: Maintenance Check

```
Criteria:                              Status:
- Last release:                        [date]
- Last commit:                         [date]
- Active maintainers:                  [count]
- Response to issues:                  [days]
- Documentation quality:               [adequate/needs improvement]
- Test coverage:                       [visible/not visible]
- Breaking change frequency:           [low/medium/high]
```

### Step 5: Cost Analysis (Paid Dependencies Only)

| Item | Amount |
|------|--------|
| License cost (annual) | $ |
| Support cost (annual) | $ |
| Infrastructure cost (annual) | $ |
| Migration cost (if switching away) | $ |
| Total 3-year TCO | $ |
| Free alternative TCO | $ |
| Cost difference | $ |

### Step 6: Approval

| Dependency Type | Approver | Documentation |
|----------------|----------|---------------|
| New open source | Tech Lead | PR comment + label |
| New paid < $100/mo | Tech Lead | ADR required |
| New paid $100-$1000/mo | Engineering Lead | ADR required |
| New paid > $1000/mo | Architecture Review Board | ADR + Board vote |
| New vendor SDK | Architecture Review Board | ADR + Board vote |

---

## Dependency Registry

Every approved dependency MUST be registered in the dependency registry:

```
backend/dependency_registry.json
```

Format:
```json
{
  "name": "dependency-name",
  "version": "x.y.z",
  "license": "MIT",
  "purpose": "What it does",
  "approved_by": "username",
  "approval_date": "2026-07-23",
  "adr": "docs/adr/ADR-XXX.md",
  "cost_annual": 0,
  "renewal_date": "2027-07-23",
  "migration_strategy": "Replace with X when available"
}
```

---

## Dependency Health Monitoring

### Automated Checks (CI)
- **Weekly**: Dependency vulnerability scan
- **Weekly**: Outdated dependency detection
- **Per PR**: Duplicate dependency detection
- **Per PR**: License compliance check
- **Per PR**: Size impact analysis

### Manual Reviews
- **Monthly**: Dependency health review (maintenance status)
- **Quarterly**: Full dependency audit
- **Annually**: Dependency TCO review (paid dependencies)

---

## Dependency Lifecycle

```
Proposal → Review → Approval → Adoption → Monitoring → Deprecation → Removal
   │          │          │          │            │             │          │
   │          │          │          │            │             │          │
   └──────────┴──────────┴──────────┴────────────┴─────────────┴──────────┘
  Justify    License    Approve    Integrate    Track health   Find       Remove
             Security                        Plan replace     replace     from
             Maintenance                     Deprecate        ment       codebase
```

---

## Removal Strategy

Every dependency MUST have a documented removal strategy, including:
- What to replace it with
- Migration steps
- Data migration (if any)
- Testing strategy
- Rollback plan

---

## CI Enforcement

CI will enforce:
1. **License gate**: Reject dependencies with non-OSI-approved licenses
2. **Duplicate gate**: Reject if same functionality exists in platform
3. **Security gate**: Reject if critical unpatched CVEs
4. **Approval gate**: Reject paid dependencies without approved ADR
5. **Vendor lock-in gate**: Reject vendor SDKs without abstraction layer
6. **Maintenance gate**: Warn if dependency has not been updated in >12 months

---

## Violations

| Violation | Consequence |
|-----------|-------------|
| Unapproved dependency merged | Revert PR, Architecture Review notification |
| Paid dependency without ADR | Revert PR, Engineering Lead notification |
| Vendor lock-in without abstraction | Revert PR, Architecture Review Board notification |
| Duplicate dependency | Revert PR, remove duplicate |
| License violation | Revert PR, Legal review |
| Security vulnerability | Immediate patch or replacement |

---

## Quarterly Dependency Audit Process

1. Export all dependencies from `requirements.txt`, `package.json`, and registry
2. Cross-reference with dependency registry
3. Identify unapproved dependencies
4. Run security scan on all dependencies
5. Check maintenance status of all dependencies
6. Review paid dependency costs
7. Plan replacements for at-risk dependencies
8. Generate dependency health report
9. Present to Engineering Lead
10. Update dependency registry
