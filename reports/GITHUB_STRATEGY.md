# GULA PLATFORM — GITHUB STRATEGY

**Status:** PROPOSED
**Date:** 2026-07-17

---

## PREREQUISITE: PRE-PUBLIC CLEANUP

Before making the repository public, these items MUST be resolved:

| Priority | Item | Status | Action |
|----------|------|--------|--------|
| **P0** | Add LICENSE file | ❌ | Add AGPL v3 |
| **P0** | Remove/rotate all secrets from git history | ❌ | BFG Repo-Cleaner + key rotation |
| **P0** | Resolve license contradictions | ❌ | Fix setup.py/pyproject.toml |
| **P0** | Add SECURITY.md | ⚠️ | Exists but update for public |
| **P1** | Fix version inconsistency | ❌ | Single source of truth |
| **P1** | Add CODEOWNERS | ❌ | Define module owners |
| **P1** | Add CONTRIBUTING.md | ⚠️ | Exists but update for public |
| **P1** | Configure branch protection | ❌ | Require PRs, status checks |
| **P2** | Add Issue/PR templates | ❌ | Bug report, feature request, security |
| **P2** | Remove dead code | ❌ | services/shared/, unused files |
| **P2** | Add Dependabot config | ✅ | Already configured |
| **P3** | Audit all CI secrets | ❌ | Ensure no hardcoded secrets in workflows |
| **P3** | Add CodeQL analysis | ❌ | Enable GitHub CodeQL |
| **P3** | Add FOSSA/Snyk license scanning | ❌ | Compliance automation |

---

## REPOSITORY STRUCTURE

```
gula-platform/
├── .github/
│   ├── workflows/          # CI/CD pipelines (existing)
│   ├── ISSUE_TEMPLATE/     # Bug report, feature request, security
│   ├── PULL_REQUEST_TEMPLATE/
│   ├── CODEOWNERS          # Module ownership
│   ├── dependabot.yml      # Already configured
│   └── SECURITY.md         # Updated for public
├── backend/
│   └── app/                # Production monolith
├── services/               # Reference microservice implementations
├── frontend-v2/            # React + Firebase frontend
├── frontend/               # Static HTML PWA
├── client/                 # Lightweight React SPA
├── docs/                   # Documentation
├── k8s/                    # Kubernetes manifests
├── terraform/              # Infrastructure as Code
├── scripts/                # Operations scripts
├── config/                 # Service configuration
├── reports/                # Architecture reports (NEW)
├── LICENSE                 # AGPL v3 (MUST ADD)
├── CODE_OF_CONDUCT.md      # MUST ADD
├── CONTRIBUTING.md         # UPDATE EXISTING
├── SECURITY.md             # UPDATE EXISTING
├── README.md               # UPDATE FOR PUBLIC
└── ROADMAP.md              # ADD PUBLIC ROADMAP
```

---

## BRANCH PROTECTION RULES

| Branch | Rules | Notes |
|--------|-------|-------|
| `main` | Require PR, 2 approvals, status checks pass, linear history, no direct push | Protected |
| `develop` | Require PR, 1 approval, status checks pass | Protected |
| `release/*` | Require PR, 2 approvals, must pass all CI | Release managers |
| `feature/*` | No protection (branch owner) | Convention |
| `fix/*` | No protection | Convention |

**Required Status Checks (main):**
- [x] syntax-gate
- [x] backend-test
- [x] security-scan
- [x] migration-check
- [x] license/cla (CLA Assistant)

---

## SCENARIO ANALYSIS: WHAT HAPPENS WHEN...

### Scenario 1: A company forks the project

**What they can do:**
- Modify and use internally (AGPL allows this)
- Offer commercial SaaS (AGPL requires releasing modifications)
- Sell support/services (permitted)

**What they cannot do:**
- Close-source their fork (AGPL prohibits this)
- Remove attribution/copyright
- Use GULA trademark without permission

**GULA response:**
- Monitor fork for compliance
- If they violate AGPL (no source release), contact GitHub, then legal action
- Offer them an Enterprise license as alternative

**Risk Level:** Low (AGPL protects against proprietary forks)

---

### Scenario 2: A government forks the project

**What they can do:**
- Modify and deploy nationally (AGPL allows)
- Add sensitive/classified features (must release source to users)
- Not release source to the public (only to users of the system)

**What they cannot do:**
- Close-source entirely (government employees using the software are "users" and entitled to source)
- Claim exclusive ownership

**GULA response:**
- Engage as partner, not adversary
- Offer government support contract
- Suggest contribution of modifications upstream

**Risk Level:** Medium (governments often want to keep modifications private)

---

### Scenario 3: A startup copies the project

**What they can do:**
- Fork and build a competing product
- Offer as SaaS if they release modifications
- Hire community contributors

**What they cannot do:**
- Use GULA trademark
- Claim originality (they must retain copyright notices)
- Offer proprietary version without commercial license

**GULA response:**
- Technical leadership (stay ahead)
- Brand recognition
- Ecosystem lock-in (marketplace, connectors, community)
- Offer white-label enterprise edition as upgrade path

**Risk Level:** Medium (healthy competition is normal in open source)

---

### Scenario 4: Someone steals code (direct copying without license compliance)

**Legal response:**
1. **Copyright infringement** — GULA is copyrighted, copying without license terms is infringement
2. **Takedown notice** — DMCA takedown (if hosted in US) or equivalent
3. **Cease and desist** — Legal letter demanding removal
4. **Lawsuit** — Statutory damages for willful infringement

**Technical response:**
- Watermark proprietary identification in data formats
- Audit log crypto signatures to prove provenance

**Detection:**
- Periodic code search across GitHub, GitLab, etc.
- Community reporting

---

### Scenario 5: Someone copies the architecture

**What this means:** They study GULA's design and build something similar from scratch.

**Legal:** Architecture is not copyrightable (only expression is). Clean-room implementation is legal.

**GULA response:**
- This is inevitable and acceptable
- Focus on execution, brand, ecosystem
- Open source thought leadership positions GULA as reference architecture

**Risk Level:** Low (inevitable, manageable through brand and ecosystem)

---

### Scenario 6: Someone violates the license

**Common violations:**
- Using AGPL code in proprietary product without releasing source
- Removing copyright notices
- Not including license text

**Response:**
1. **First violation:** Friendly email requesting compliance (30 days)
2. **Second violation:** Cease and desist letter
3. **Persistent violation:** DMCA takedown + legal action
4. **GitHub:** Report violation to GitHub Trust & Safety

**Cost of non-compliance for violator:**
- Statutory damages up to $150,000 per work (US Copyright Act)
- Legal fees
- Injunction (service shutdown)
- Reputational damage

---

## SECURITY POLICY (Public)

```markdown
## Security Policy

### Supported Versions
| Version | Supported |
|---------|-----------|
| 2.x     | ✅ |
| 1.x     | ❌ (EOL) |
| < 1.0   | ❌ |

### Reporting a Vulnerability

**DO NOT** create a public GitHub issue.

Email: security@gula-platform.org (PGP key available at keybase.io/gula)

Response times:
- Critical: 24 hours
- High: 72 hours
- Medium: 1 week
- Low: Next release cycle

### Disclosure Policy
1. Report received → acknowledgment within 24h
2. Investigation → within 72h of acknowledgment  
3. Fix developed → timeline depends on severity
4. Patch released → coordinated disclosure date
5. Public disclosure → after patch is available

### Recognition
We maintain a Hall of Fame for security researchers who responsibly disclose vulnerabilities.
```

---

## COMMUNITY GOVERNANCE

```yaml
roles:
  - name: "Maintainer"
    responsibilities:
      - Review and merge PRs
      - Triage issues
      - Guide community discussions
      - Vote on project decisions
    requirements:
      - 10+ merged contributions
      - Active for 3+ months
      - Core Team nomination

  - name: "Contributor"  
    responsibilities:
      - Submit PRs and issues
      - Participate in discussions
    requirements:
      - 1+ merged contribution

code_of_conduct:
  - Be respectful and inclusive
  - No harassment or discrimination
  - Focus on technical merit
  - Disagreements resolved professionally
  - Violations reported to conduct@gula-platform.org
```

---

## RELEASE WORKFLOW

```yaml
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    steps:
      - Create GitHub Release with changelog
      - Build and push Docker images to GHCR
      - Attach SBOM to release
      - Deploy to community demo instance
      - Post announcement to Twitter/LinkedIn
      - Send email to community mailing list

  publish_pypi:
    # Community SDK packages (Python)
    - scg-sdk
    - gula-client
    
  publish_npm:
    # Community SDK packages (Node.js)
    - @gula/connector-sdk
    - @gula/client-sdk
```

---

## METRICS & KPIs (6 months post-public)

| Metric | Target |
|--------|--------|
| GitHub Stars | 500+ |
| Contributors (non-org) | 20+ |
| Forks | 50+ |
| PRs merged (non-org) | 50+ |
| Issues closed | 100+ |
| Discord/Slack members | 200+ |
| Docker pulls | 10,000+ |
| Countries deployed | 5+ |
| Community connectors | 10+ |
