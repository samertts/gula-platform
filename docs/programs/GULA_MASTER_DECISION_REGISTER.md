# GULA Master Decision Register

Status: **LIVING REGISTER — NO NEW PRODUCTION APPROVAL GRANTED**. Baseline: `a01352578c0df205b92e58444242e1fa6ae7d77b`, branch `integration/gula-national`. New execution branch: `execution/gula-master-consolidation-20261126`.

Classification: **FACT** = directly observed in preserved evidence; **NOT APPROVED** = no owner acceptance artifact found; **BLOCKED** = external authority required.

## 1. Permanent release posture (unchanged)

| Token / state | Value | Evidence |
|---|---|---|
| `HOLD` | `TRUE` | `$W053/WAVE05_3_FINAL_VALIDATION.txt:109-124` |
| `production_ready_items` | `0` | same |
| `G1` … `G12` | `NOT PASSED` | same; `$W053/audit/WAVE05_3_CLOSURE_20261125T122640Z/32_g1_g12_gate_audit.txt` records all as `BLOCKED` |
| `STABLE_V1_0_0` | `NOT DECLARED` | same |
| `PRODUCTION_READY` | `NOT DECLARED` | same |
| Wave 05.3 | `RELEASE_BLOCKED` | `$W053/audit/WAVE05_3_CLOSURE_20261125T122640Z/GULA_WAVE_05_3_CLOSURE_AUDIT.md` |
| Wave 06 | `PROPOSAL ONLY / NOT APPROVED` | `$W053/audit/WAVE05_3_CLOSURE_20261125T122640Z/GULA_WAVE_06_PROPOSAL.md` |

No decision in this register changes these values.

## 2. Inherited technical decisions

| ID | Decision | Status | Owner / approval | Evidence | Effect on execution |
|---|---|---|---|---|---|
| D-001 | National integration architecture baseline | ADOPTED | Architecture board | `$NCI/ARCHITECTURE_DECISION_REGISTER.md` | Reuse existing canonical components; no second identity/MPI/LIMS/consent/audit engine |
| D-002 | Canonical route/composition boundary | ADOPTED | Architecture board | same | Single HTTP composition root in `app/factory.py`; do not mount dormant routers without approval |
| D-003 | Canonical data ownership | ADOPTED | Data owners | same | Each data class needs a named owner before persistence changes |
| D-004 | Synthetic evidence boundary | ADOPTED | Review board | same | Synthetic E2E cannot be represented as operational proof |
| D-005 | Wave 05.3 posture preservation | ADOPTED | Program Director | same | HOLD/gates unchanged |
| D-006 | Free-first/open-source shortlist | PROPOSED | Architecture + procurement policy owner | `$W053/audit/NATIONAL_TRANSFORMATION_20261125T133950Z/TRANSFORMATION_DECISION_REGISTER.md` | HAPI FHIR JPA, OpenELIS Global 2, OpenTelemetry Collector, Prometheus, OpenBao, SOPS are proposed only; no dependency added |
| D-006a | Free-first license/source review | PROPOSED | Architecture + legal | transformation decision register | Standalone review artifact missing; no adoption claim |
| D-007 | NIDP/NIAM persistence governance | IMPLEMENTED, TESTED (synthetic boundary) | Identity + schema owner | transformation decision register | Durable DB constraints remain blocked by schema owner |
| D-008 | Route-free composition-only clinical integration layer | IMPLEMENTED / TESTED / INDEPENDENTLY REVIEWED | Clinical integration owner | `$NCI/09_D008_FINAL.md`, `$NCI/FINAL_REPORT.md` | Synthetic chain only; not production release, not wired into runtime |
| S-03, S-04 | Prior security fixes | FIXED | Security owner | `$NCI/05_discovery_governance_security.md` | Preserve fixes; regression tests required |
| S-07 | Prior security item | MITIGATED ONLY | Security owner | same | Do not claim closed |
| S-01, S-02, S-05, S-06, S-08 | Open security/governance items | OPEN | Consent/privacy/security/audit owners | same | Require policy decision before canonical remediation |
| G1 … G12 | National acceptance gates | NOT PASSED / BLOCKED | Gate owners + independent review board | gate audit | No gate may be opened by engineering work |

## 3. Owner decision state

| Register | Finding | Status |
|---|---|---|
| `$W053/OWNER_DECISION_REGISTER.md` and `$W053/GULA_OWNER_DECISION_REGISTER.md` | All production decisions `NOT APPROVED`; no HOLD-lift authority | FACT |
| `GULA_OWNER_DECISION_PACKAGE.md` in the working project | \"Nothing here is approved. All four decisions are `BLOCKED`\" | FACT |
| Raw NCI independent-review transcripts | Not preserved in evidence package; only summary in `$NCI/FINAL_REPORT.md` section H | EVIDENCE_MISSING |
| Complete G1–G12 acceptance packs and owner acceptance | Not found in audited evidence package | EVIDENCE_MISSING |

## 4. New execution decisions (Phase 0/1)

| ID | Decision | Status | Authority | Rationale |
|---|---|---|---|---|
| MDEC-001 | Use `execution/gula-national` baseline and create non-protected branch `execution/gula-master-consolidation-20261126` | EXECUTED | This directive's engineering authority | Preserves current work; avoids `main` and protected branches |
| MDEC-002 | Preserve all prior evidence in read-only preservation roots | EXECUTED | Phase 0 baseline | Manifests verified OK; no historical file modified |
| MDEC-003 | Treat previous National Operational Readiness decision `NOT READY FOR OPERATIONAL PILOT` as baseline for this execution | ADOPTED | Evidence-based assessment | Final decision file and 46 open gaps remain authoritative until new evidence and owner approval |
| MDEC-004 | Perform only Category A safe remediation now: fail-closed null scope, stub labeling, documentation, and targeted tests | AUTHORIZED BY DIRECTIVE | Section 21 Category A | No DDL, external approval, real data, new route, or dependency required |
| MDEC-005 | Defer identity authenticity, real authority/government exchange, DDL, clinical quarantine policy, governorate policy, audit retention/keying, DR drills, and external FHIR exchange | BLOCKED / DEFERRED | External owners listed in master gap register | Requires government, schema, clinical, legal, security, or operations approval |
| MDEC-006 | Do not change HOLD, gates, `production_ready_items`, Stable, or Production Ready declarations | EXECUTED | Section 19 and prior posture | Owners only; no independent evidence supports a change |
| MDEC-007 | Reuse canonical MPI, NIAM, consent, ADE, audit, LIMS, FHIR, and offline primitives instead of creating parallel systems | ADOPTED | REUSE FIRST principle | Master architecture register records canonical vs duplicate/unwired components |
| MDEC-008 | Keep all synthetic and unwired components explicitly labeled | EXECUTED | Evidence discipline | Prevents overclaiming capabilities and gate contamination |
| MDEC-009 | Treat Phase 4 fixes for MGR-015 and MGR-027 as narrow engineering mitigations only, not gap closure | EXECUTED | Independent review boundary | Focused tests passed, but security-owner and integration review-board acceptance remain absent |

## 5. Missing approvals required for later phases

| Area | Required approval owner | Required artifact | Current status |
|---|---|---|---|
| G1–G12 closure | Gate owners + independent review board + Program Director | Evidence packs, independent verdicts, owner acceptance, HOLD-lift decision | NOT APPROVED |
| Database schema/migrations | Schema/database owner | Approved migration design, PG round-trip, rollback | NOT APPROVED |
| National identity authenticity | Government verification authority | Authenticity procedure, authority interface, credential custody | NOT APPROVED |
| Consent/ADE policy | Consent/privacy authority + security owner | Consent binding, guardian purposes, break-glass, governorate scope policy | NOT APPROVED |
| Clinical/LIMS release | Clinical authority + LIMS owner | Critical quarantine, human release, patient correlation policy | NOT APPROVED |
| External FHIR/government exchange | Interoperability authority + counterparties | Conformance, auth/consent, external test environment | NOT APPROVED |
| Production operations | Infrastructure/DR + legal/sovereignty authorities | DR/HA/monitoring/load drills, residency decision, BCP exercise | NOT APPROVED |

## 6. Decision discipline

Engineering completion, security verification, clinical approval, legal approval, institutional acceptance, operational readiness, and production authorization remain distinct states. No single test result, commit, or report advances any of them without the named owner's recorded acceptance.
