# GULA Platform — Risk Register
**Date:** 2026-07-17

---

## Risk Scoring
- **Likelihood**: 1 (Rare) → 5 (Almost Certain)
- **Impact**: 1 (Negligible) → 5 (Catastrophic)
- **Risk Score**: Likelihood × Impact (1-25)

---

## 1. CRITICAL Risks (Score 15-25)

| ID | Risk | Description | L | I | Score | Mitigation |
|----|------|-------------|---|---|-------|------------|
| R01 | **Firebase bypasses backend security** | frontend-v2 writes directly to Firestore, bypassing RBAC, ABAC, audit, rate limiting, encryption | 5 | 5 | **25** | Migrate frontend-v2 to backend API; enforce Firestore security rules |
| R02 | **No automated backup restore testing** | Backups exist but no evidence of restore tests | 4 | 5 | **20** | Implement automated restore verification in CI |
| R03 | **Patient data exposure via Firebase** | Unauthorized Firestore access could expose patient records | 4 | 5 | **20** | Restrict Firestore access; audit all Firestore reads |
| R04 | **Executive Order violations (AI providers)** | EO 3 & 4 mandate Ollama-only; Gemini + Groq integrations exist | 5 | 4 | **20** | Remove external providers or update EOs |
| R05 | **No staging environment** | Changes deployed directly to production | 4 | 4 | **16** | Create staging environment with production parity |
| R06 | **Single PostgreSQL instance in production (MVP)** | No HA, no failover | 3 | 5 | **15** | Deploy full.yml with Patroni HA or managed PostgreSQL |
| R07 | **Version tracking inconsistency** | config.py: 2.1.0, CHANGELOG: 2.3.2 | 4 | 3 | **15** | Align version tracking; single source of truth |

---

## 2. HIGH Risks (Score 10-14)

| ID | Risk | Description | L | I | Score | Mitigation |
|----|------|-------------|---|---|-------|------------|
| R08 | **Low route test coverage (35%)** | Most routes untested | 4 | 3 | 12 | Add route integration tests |
| R09 | **Low service test coverage (30%)** | Business logic untested | 4 | 3 | 12 | Add service unit tests |
| R10 | **Zero edge/interop test coverage** | Edge platform completely untested | 3 | 4 | 12 | Add edge integration tests |
| R11 | **6 microservice stubs with 0 tests** | Cannot deploy as microservices | 3 | 4 | 12 | Implement or remove stubs |
| R12 | **JWT uses HS256 (symmetric key)** | Key distribution risk across services | 3 | 4 | 12 | Migrate to RS256/ES256 |
| R13 | **No automated secrets rotation** | Credentials never rotated | 4 | 3 | 12 | Implement rotation pipeline |
| R14 | **Massive schema churn (17 migrations in 1 day)** | 2026-07-16 introduced 17 migrations | 4 | 3 | 12 | Stabilize schema; test thoroughly |
| R15 | **No frontend security testing** | XSS, CSRF risks unmitigated | 3 | 4 | 12 | Add frontend security scan |
| R16 | **No E2E tests** | Integration failures undetected | 3 | 4 | 12 | Add Cypress/Playwright |
| R17 | **Terraform targets AWS, runs on DO** | Infrastructure-as-Code is mismatched | 4 | 3 | 12 | Re-target Terraform for DO |
| R18 | **Clinical CDS is schema-only** | CDS rules exist in DB but no code executes them | 3 | 3 | 9 | Remove or implement |
| R19 | **National platform domains schema-only** | 200+ tables with no code | 3 | 3 | 9 | Ship or remove |

---

## 3. MEDIUM Risks (Score 5-9)

| ID | Risk | Description | L | I | Score | Mitigation |
|----|------|-------------|---|---|-------|------------|
| R20 | **Monster route files** | ehr.py (73KB), compliance.py (47KB) | 4 | 2 | 8 | Split into smaller modules |
| R21 | **Duplicate AI engines** | routes/ai.py vs services/ai/main.py | 3 | 2 | 6 | Consolidate into one |
| R22 | **No DICOM server** | Radiology can't store images | 2 | 3 | 6 | Implement DICOM or integrate |
| R23 | **No LOINC/SNOMED/ICD data populated** | Models exist, tables empty | 3 | 2 | 6 | Populate terminology data |
| R24 | **Documentation significantly behind code** | 36 documented routes vs 53+ actual | 4 | 1 | 5 | Update documentation |
| R25 | **No load test baseline** | k6 scripts exist but no baseline | 3 | 2 | 6 | Run k6 and capture baseline |
| R26 | **No synthetic monitoring** | Production behavior unknown between health checks | 2 | 3 | 6 | Add synthetic checks |

---

## 4. LOW Risks (Score 1-4)

| ID | Risk | Description | L | I | Score | Mitigation |
|----|------|-------------|---|---|-------|------------|
| R27 | **AWS Terraform for DO deployment** | Low impact while MVP works | 2 | 2 | 4 | Update Terraform |
| R28 | **Old MySQL reference in docs** | Documentation typo | 2 | 1 | 2 | Fix documentation |
| R29 | **No internationalization** | Arabic-only limits market | 1 | 2 | 2 | i18n framework |
| R30 | **No customer evidence** | Business plan unvalidated | 2 | 2 | 4 | Find first customer |

---

## 5. Risk Heat Map

```
Impact →
  5 │ R01 R02 R03 R04     R06
  4 │     R10 R12 R13 R15 R16
  3 │ R11 R14 R17 R18 R19
  2 │ R20 R21 R22 R23 R25 R26
  1 │ R27 R28 R29 R30
    └──────────────────────────
      1   2   3   4   5   Likelihood
```

---

## 6. Top 5 Risks Requiring Immediate Action

| Rank | ID | Risk | Action |
|------|----|------|--------|
| 1 | R01 | Firebase security bypass | Migrate frontend-v2 to backend API |
| 2 | R02 | No backup restore testing | Automate restore verification |
| 3 | R04 | EO AI provider violations | Remove Gemini/Groq or update EOs |
| 4 | R06 | Single PG instance | Deploy HA PostgreSQL |
| 5 | R03 | Patient data exposure | Firestore security audit |
