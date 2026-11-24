# Consolidated Execution Backlog — National Unified Health Infrastructure

**Document:** 15 · **Program:** GULA National Integration & Adversarial Assurance
**Date:** 2026-11-18 · **Baseline:** integration HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (Phase B)
**Data class:** `SYNTHETIC_ONLY` · **Status vocabulary:** the canonical seven only

> **Authority boundary.** This backlog is an engineering work queue. It does not
> grant owner approval, clinical validation, legal certification, production
> readiness or deployment authority. `HOLD`, MPI `REJECT`, `MP-001`,
> `ODR-001…004`, `D-020/D-021`, `ADR-A…J` and `AUD-02/07/16` remain in force.
> `production_ready_items == 0`. The `gula-platform` repo stays read-only at
> `f478676b6fc375338648dde46fbf076c015a3f91`.

---

## 1. Current state (verified this session)

| Fact | Evidence |
|---|---|
| Phase A committed | `0cb067aef8c4276f60e2ec0e53e2a78f335c269b` (19 files) |
| Phase B committed | `2206654dc713ea2de8c564a3207dfe05fde23549` (34 files, +7991/−14) |
| Phase B review | independent read-only subagent, **PASS**, zero findings (scope-limited) |
| Phase B gate after commit | 6/6 PASS; focused 235; health_core 773; ruff clean; mypy 0 new |
| Protected md5s | unchanged (`effdfeaf…`, `1a02c015…`, `ea3969d0…`) |
| Registry verdict | PASS (one expected advisory WARN: HEAD advanced after Phase A baseline) |
| Pre-existing staged renames | 20 `R100` renames preserved, excluded from both commits, still staged |
| Untracked surface | ~500 files (GLOSI, most GOVERNANCE, all `backend/app/health_core/`) — preserved, not committed |
| Pre-existing disclosure | NR-011 FK test fails only under `tests/identity` co-collection — disclosed, not suppressed |

**Terminology conflict resolved.** Two T-numberings exist and must not be mixed:
- *Registry/doc-02 tranche* `T1…T5`: T1=WS-04/05, T2=WS-02/03, T3=WS-06, T4=WS-01, T5=WS-07.
- *Program Director task IDs* `PD-T1…PD-T6`: PD-T1 terminology, **PD-T2 client**, PD-T3 reliability,
  **PD-T4 MPI**, PD-T5 security/audit, PD-T6 FHIR HTTP.
Phase B delivered PD-T1, PD-T3, PD-T5, PD-T6 and the DB classification.
**Remaining continuity items: PD-T2 (client) and PD-T4 (MPI).**

---

## 2. Active program queue (highest priority)

### AQ-1 — Extreme Adversarial Audit & Remediation Program — `ACTIVE`

Six disjoint Team A auditor workstreams were launched against the on-disk checkout
(no source, git, DB or config mutation). Each owns distinct artifacts under
`GOVERNANCE/ADVERSARIAL_ASSURANCE/`:

| Auditor | Scope | Owned required artifacts |
|---|---|---|
| A1 | Architecture + asset inventory | `COMPLETE_ASSET_INVENTORY.md`, `ARCHITECTURE_ADVERSARIAL_REVIEW.md` |
| A2 | Security + patient-data privacy | `SECURITY_ASSESSMENT.md`, `PATIENT_DATA_PRIVACY_ASSESSMENT.md` |
| A3 | MPI + clinical safety | `MPI_AND_IDENTITY_AUDIT.md`, `CLINICAL_SAFETY_HAZARD_REGISTER.md` |
| A4 | Database + API/interoperability | `DATABASE_INTEGRITY_REPORT.md`, `API_AND_INTEROPERABILITY_AUDIT.md` |
| A5 | Performance + offline + frontend | `PERFORMANCE_AND_SCALABILITY_REPORT.md`, `OFFLINE_RESILIENCE_REPORT.md`, `FRONTEND_UX_AUDIT.md` |
| A6 | Dependencies + infrastructure/DR | `DEPENDENCY_AND_SUPPLY_CHAIN_REPORT.md`, `INFRASTRUCTURE_AND_DR_REPORT.md` |

Remaining artifacts (consolidation / remediation / verification roles, not auditor-owned):
`FINDINGS_REGISTER.json`, `REMEDIATION_REGISTER.json`, `INDEPENDENT_VERIFICATION_REPORT.md`,
`TEST_EVIDENCE_INDEX.md`, `BLOCKED_ITEMS_AND_EXTERNAL_DEPENDENCIES.md`,
`FINAL_ASSURANCE_DECISION.md`, `EXECUTIVE_AUDIT_REPORT.md`.

**Independence disclosure.** Team C is a fresh-context read-only subagent with no
ownership of the remediated files. This is independent *engineering* review, not
an external human auditor, clinical validator or regulator. That limitation is
recorded in the final assurance decision; no `INDEPENDENTLY VERIFIED` claim
exceeds engineering evidence.

**Loop:** DISCOVER → REPRODUCE → CLASSIFY → PRIORITIZE → DESIGN → IMPLEMENT →
TEST → INDEPENDENTLY VERIFY → DOCUMENT → REASSESS. Repeat until no new material
finding appears or every remaining finding has an owner and mitigation.

### AQ-2 — Continuity: PD-T2 client implementation — `ACTIVE, BOUNDED`
Surface: `backend/app/health_core/client_integration/**` (6 modules), 30 guard tests.
Current: manifest guards fail-closed; `end_to_end_verified = False`.
Achievable now: synthetic contract-simulation coverage, malformed/idempotency
cases, drift detection, honest reporting. **Blocked:** iOS Xcode project absent,
Expo platform authorization, real-device E2E, 101 frontend drift acceptance.
The A5 frontend audit will feed the concrete task list; no duplicate work.

### AQ-3 — Continuity: PD-T4 MPI evidence/decision package — `ACTIVE, BOUNDED`
Surface: `backend/app/services/mpi/**`, `identity_matching.py`, 10 MPI test files,
`GOVERNANCE/IDENTITY_REMEDIATION/**`.
Achievable now: synthetic adversarial cases (twins, newborn, missing/incorrect
identifiers, concurrent registration/merge, reversal, duplicate events,
interrupted transactions) and evidence traceability.
**Decision boundary:** engineering evidence cannot lift MPI `REJECT` or `HOLD`;
only a named authority can. A3 audits this surface; its findings drive the work.

---

## 3. Workstream map WS-01…WS-22

Statuses describe *engineering evidence in this checkout*, never owner approval.
`NOT YET ASSESSED` means the current adversarial sweep has not yet produced a
workstream-specific verdict; it is not a claim of absence or presence of defects.

**Numbering caveat — do not merge these two schemes.** The mandate defines
**WS-01…WS-22** (canonical for this table). The legacy `status_registry.json`
uses a different **WS-01…WS-07** for the original National Integration Program:
legacy WS-01 Identity&MPI → mandate WS-02; legacy WS-02 Security&Audit → WS-17;
legacy WS-03 FHIR → WS-16; legacy WS-04 Terminology → WS-16;
legacy WS-05 Reliability/Offline → WS-18; legacy WS-06 Client → WS-20;
legacy WS-07 National domains → WS-01/WS-22. This collision is itself a
documentation-integrity finding for the adversarial register; it is reported,
not silently reconciled. This table does not mutate the registry.

| WS | Name (mandate) | Principal code surface(s) | Status | Known blockers / notes |
|---|---|---|---|---|
| WS-01 | Core architecture & domain boundaries | `domain_platform/**`, `scripts/architecture/**`, `architecture/`, `interoperability/**` | `INTEGRATED` | 11/11 domain certification; 25 acknowledged architecture findings frozen; ADR-A..J owner-gated (A1) |
| WS-02 | National identity & MPI | `identity/**`, `services/mpi/**`, `health_core/identity/**` | `TESTED` | 127 synthetic MPI tests; owner `REJECT`/`MP-001`/`ODR-002,003` unchanged (A3) |
| WS-03 | Clinical records & encounters | `clinical/**`, `ehr/**`, `nursing/**`, `critical_care/**` | `NOT YET ASSESSED` | clinical hazard register in progress (A3) |
| WS-04 | Hospital & primary healthcare | `hospital/**`, `care_continuum/**`, `chronic_care/**`, `pilot_platform/**` | `NOT YET ASSESSED` | A1/A5 boundary review |
| WS-05 | Laboratory & diagnostic services | `lims/**`, `health_core/lab/**`, `sample_tracking/` | `NOT YET ASSESSED` | analyzer E2E needs real devices (blocked) |
| WS-06 | Pharmacy & medication | `pharmacy/**` | `NOT YET ASSESSED` | CDS/medication automation must stay inactive |
| WS-07 | Radiology & imaging | `radiology/**` | `NOT YET ASSESSED` | DICOM conformance unverified (A4) |
| WS-08 | Emergency & ambulance | `ems/**` | `NOT YET ASSESSED` | offline emergency operation unmeasured (A5) |
| WS-09 | Public health & epidemiology | `public_health/**` | `NOT YET ASSESSED` | A1/A3 data-ownership review |
| WS-10 | Blood banks & transfusion | `blood_bank/**` | `NOT YET ASSESSED` | traceability/guard review pending (A3) |
| WS-11 | Workforce & facility registry | `certification/**`, `identity/professional_registry/**`, `hospital/**` | `NOT YET ASSESSED` | software records ≠ official licensing |
| WS-12 | Supply chain & medical equipment | `biomedical/**`, `devices/**` | `NOT YET ASSESSED` | A6 supply-chain review |
| WS-13 | Finance & administration | `billing/**`, `financial/**`, `insurance/**`, `payments/**` | `NOT YET ASSESSED` | real payment integration blocked |
| WS-14 | Governance, licensing & quality | `governance/**`, `legal/**` | `NOT YET ASSESSED` | owner decisions immutable |
| WS-15 | Telehealth & remote care | `communication/**`, `clinical_gateway/**` | `NOT YET ASSESSED` | A5 UX/reliability review |
| WS-16 | Interoperability & terminology | `health_core/fhir/**`, `health_core/terminology/**`, `interoperability/fhir_http/**`, `capabilities/fhir_interoperability/**` | `TESTED` | PD-T6 router NON-activated; licensed datasets `BLOCKED` (A4); WS-E guard intact |
| WS-17 | Security, privacy & audit | `security/**`, `audit/**`, `health_core/authorization/**`, `health_core/audit_anchor/**` | `TESTED` | `D-020`, `ADR-D`, R-01…R-11; durable external anchor `NOT IMPLEMENTED` (A2) |
| WS-18 | Offline & synchronization | `health_core/reliability/**`, `health_core/integration/offline.py`, `edge/**`, `edge_agent/` | `TESTED` | PD-T3 queue synthetic/in-process, not runtime-wired; RPO/RTO unmeasured (A5) |
| WS-19 | Analytics & national intelligence | `nhdw/**`, `national_data/**`, `command_center/**`, `command_intelligence/**`, `ai/**`, `knowledge_graph/**` | `NOT YET ASSESSED` | AI must not autonomously decide high-risk care |
| WS-20 | Frontend & application ecosystem | `frontend-v3/`, `mobile/`, `mobile-expo/`, `hospital_desktop/`, `apps/`, `client/` | `TESTED` | PD-T2 contract guards; RTL/i18n guards; iOS absent; 101 drifts owner-gated (A5) |
| WS-21 | Infrastructure, DevOps & observability | `docker/`, `k8s/`, `helm/`, `terraform/`, `cloudflare/`, `digitalocean/`, `.github/workflows/`, `scripts/kernel/` | `NOT YET ASSESSED` | DR drill evidence to be verified (A6) |
| WS-22 | Testing, clinical safety & independent assurance | `backend/tests/**`, `tests/{chaos,integration,load,recovery,soak,spike,stress}/`, `GOVERNANCE/**` | `INTEGRATED` | this program; full suite 4865 collected; 1 disclosed order-dependent baseline failure |

`NOT YET ASSESSED` means the current adversarial sweep has not yet produced a
workstream-specific verdict; it is not a claim that defects are absent or present.

---

## 4. Selection rules for the next task

1. Patient safety > identity integrity > critical security > confidentiality >
   clinical data integrity > authorization/tenant isolation > durability/recovery >
   interoperability > reliability > performance > completeness > UX > debt.
2. Prefer a task that is unblocked, reproducible and has a deterministic gate.
3. A genuine external dependency must be recorded as `BLOCKED` with exact required
   decision/evidence and an owner, then work continues elsewhere.
4. No fix is complete without a regression test and independent verification;
   high-risk fixes require a fresh-context verifier.
5. Never widen a commit to adjacent pre-existing work; always use explicit paths.

---

## 5. Definition of done (per domain)

Approved/provisional requirements · data model · business logic · API contract ·
UI · authn/authz · audit/provenance · error handling · security tests · unit and
integration tests · documentation · monitoring · backup/recovery · independent
review · end-to-end synthetic workflow evidence — reported under separate status
headings, never collapsed into one percentage.
