# GULA National Transformation V2 — Decision Register

**Document:** `GULA_NATIONAL_DECISION_REGISTER_V2.md`  
**Generated:** 2026-11-24 UTC  
**Phase:** Architecture and Execution Planning Gate  
**Status:** `PROPOSED · PENDING OWNER DECISION`  
**Authority:** This register prepares decisions. It does not decide, approve, reject, accept, release or change any prior governance record.

## 0. Standing posture

**HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED.**

No decision recorded below has been made by the owner. Every row is `BLOCKED` until the named owner records an explicit, scoped decision in the authoritative register or a successor owner instrument. This V2 register is additive and does not amend `GULA_OWNER_DECISION_REGISTER.md`, `GOVERNANCE/FINAL_DECISION.md`, GECS records, the status registry, prior SHA manifests, P-02/P-03 records, PR #307, or any source file.

## 1. Decision vocabulary

| Value | Meaning |
|---|---|
| `PROPOSED` | Prepared by engineering planning; no owner action recorded. |
| `BLOCKED` | Cannot proceed until the owner records a decision. |
| `OWNER DECIDED` | Reserved for an explicit owner record; not used in this document. |
| `SUPERSEDED` | Reserved for a later approved instrument; not used in this document. |
| `NOT APPLICABLE` | No decision required for planning-gate documentation. |

## 2. National V2 decisions required

| ID | Decision requested | Why it is required | Recommended position (not a decision) | Impact if absent | Status |
|---|---|---|---|---|---|
| NV2-D01 | Approve the V2 national target architecture and program boundaries PRG-00…PRG-10. | Establishes the common decomposition for parallel work. | Approve as target scope only; do not treat as implementation authority. | Teams may build incompatible structures. | `PROPOSED · BLOCKED` |
| NV2-D02 | Resolve mixed Git provenance before any save, merge or release action. | 20 staged `R100`, 162 modified tracked and 686 untracked paths (`-uall`) are preserved; protected status registry content exists only in the worktree. | Complete provenance resolution as a separately authorized, reversible operation. | No safe commit, merge, PR, release or auditable baseline. | `PROPOSED · BLOCKED` |
| NV2-D03 | Appoint data owners and contract owners for C01–C15. | Parallel teams cannot write conflicting patient, organization, provider or clinical semantics. | National Core owns identity/org/provider/consent/audit/terminology; domains own their authored clinical facts; analytics is derived only. | Conflicting sources of truth for patient, facility and results. | `PROPOSED · BLOCKED` |
| NV2-D04 | Approve controlled national release gates G1–G12 and continued HOLD. | Release authority must remain explicit and gated. | Approve gates; keep HOLD until all gates pass and owner accepts. | Premature national activation. | `PROPOSED · BLOCKED` |
| NV2-D05 | Decide modular-monolith default and thresholds for operational service extraction. | Directive 1(9) prohibits arbitrary microservices. | Modular monolith by default; extract only on proven scaling, isolation or deployment need. | Ad hoc service sprawl or an unscalable monolith. | `PROPOSED · BLOCKED` |
| NV2-D06 | Approve national zero-trust policy, including break-glass and service identity. | Authentication, authorization, consent and emergency access must remain distinct. | Approve policy and test harness before any new access path. | Authorization bypass, audit bypass, insider misuse. | `PROPOSED · BLOCKED` |
| NV2-D07 | Approve measurable availability, RTO/RPO, P95/P99, throughput and queue-lag targets and a measurement plan. | Reliability goals are targets, not achievements. | Ratify proposed target envelopes only after environment sizing and representative load design. | Unverifiable capacity claims. | `PROPOSED · BLOCKED` |
| NV2-D08 | Approve public-health reporting and legal-scope boundaries. | Surveillance, immunization and outbreak reporting cross legal and clinical boundaries. | Define legal basis, minimum dataset, retention and authorized recipients before national rollout. | Unlawful or ambiguous reporting. | `PROPOSED · BLOCKED` |
| NV2-D09 | Resolve historical `PRODUCTION READY`/certification claims against the current HOLD decision. | July 2026 certification reports conflict with November 2026 binding records. | Treat historical certificates as superseded engineering evidence, not release authority. | Ambiguous release authority. | `PROPOSED · BLOCKED` |
| NV2-D10 | Approve the first parallel workstream set and resource allocation. | Defines which teams can start without waiting on shared source changes. | Approve WS-CORE-01, WS-SEC-01, WS-AUD-01, WS-OBS-01, WS-DB-01, WS-E2E-01, WS-API-01 and WS-GOV-01 as planning work only. | Parallel teams idle or duplicate work. | `PROPOSED · BLOCKED` |
| NV2-D11 | Approve terminology, DICOM/PACS and national external-gateway strategy. | External adapters default to STUB and HL7→FHIR response is marked simulation-only. | Approve contract-first strategy and environment-gated live mode with no silent fallback. | Simulated integrations mistaken for live capability. | `PROPOSED · BLOCKED` |
| NV2-D12 | Record P-03 / AUD-F03 D1–D5 sub-decisions separately. | Package-level `AUTHORIZED` does not select boundaries, actor, failure, idempotency or read-route policy. | Decide using `AUDIT_EXECUTION_RECORDS/P-03_OWNER_DECISIONS_REQUIRED.md`; do not bundle into V2. | P-03 implementation scope remains undefined. | `PROPOSED · BLOCKED` |
| NV2-D13 | Approve P-03-CONCURRENCY as a separate package. | T9 chain-fork defect is proven but deferred by the approved REV3 packet. | Approve only after independent design review; never use P-03 GREEN as multi-worker proof. | Fork remains or is incorrectly “fixed” inside P-03. | `PROPOSED · BLOCKED` |
| NV2-D14 | Approve national test environments and synthetic-data policy. | PostgreSQL-specific evidence cannot come from the SQLite-forcing default conftest; no PHI may be used. | Ratify disposable PG16, synthetic fixtures, no production services, explicit `--noconftest` PG tests. | Invalid evidence or privacy incident. | `PROPOSED · BLOCKED` |
| NV2-D15 | Approve Stable v1.0.0 release candidacy only after G1–G12. | Release declaration is an owner act. | No declaration until every gate is evidenced and independently reviewed. | False national readiness claim. | `PROPOSED · BLOCKED` |

## 3. Decisions already recorded in prior governance — not reopened here

| Prior item | Actual recorded state | V2 treatment |
|---|---|---|
| OD-001 / SEC-015 F-01 engineering scope | `ACCEPTED` only for scoped engineering remedy; does not authorize commit, merge, release or other OD items. | Preserve; do not broaden. |
| P-02 / AUD-F02 | `IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED`; verdict `DECISION-READY`; 2 accepted LOW residuals; `ACCEPTED = NO`; `PRODUCTION READY = NO`. | Preserve; `DECISION-READY` is not acceptance. |
| P-03 / AUD-F03 | Package-level `AUTHORIZED`; D1–D5 absent; `PREPARED ONLY · NOT IMPLEMENTED`. | Preserve; separate decision NV2-D12. |
| P-03-CONCURRENCY | Design prepared, not approved, not implemented; T9 RED is defect evidence only. | Preserve; separate decision NV2-D13. |
| Release posture | HOLD from `GOVERNANCE/FINAL_DECISION.md`; `production_ready_items = 0`. | Preserve; no V2 document changes it. |
| Protected SHA manifests | Prior additive manifests verify; `CRITICAL_FILE_SHA256.txt` has historical superseded failures. | Preserve; V2 receives a new additive manifest only. |

## 4. Conflict register requiring owner resolution

| Conflict | Evidence | Required decision |
|---|---|---|
| Route counts differ across baseline reports (1,442 / 1,804 / 1,815 / 1,817 paths). | `docs/constitution/runtime/02_route_registration_certification.md`, `GULA_MASTER_BASELINE.md`, `TEAM_C_INDEPENDENT_VERIFICATION_REPORT.md`, `GOVERNANCE/WAVE_0_BASELINE.md`. | NV2-D02, NV2-D14: establish one reproducible route/OpenAPI measurement in a clean baseline. |
| Historical production certifications conflict with HOLD. | `RC_READINESS_REPORT.md`, `MASTER_RELEASE_CERTIFICATION.md`, `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md` vs `GOVERNANCE/FINAL_DECISION.md`. | NV2-D09. |
| Protected status registry exists in worktree but not identically at HEAD. | `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` worktree vs HEAD blob hash. | NV2-D02. |
| 8 of 10 capability scaffolds are empty CRUD stubs yet registered as metadata capabilities. | `backend/app/capabilities/*`, `backend/app/kernel/capabilities_registry_populator.py`. | NV2-D01, NV2-D03: decide whether to complete, rename or reclassify; no deletion in this phase. |
| External gateways default to STUB and HL7→FHIR returns `simulationOnly: True`. | `backend/app/gateways/mode.py`, `backend/app/capabilities/fhir_interoperability/routes.py`. | NV2-D11. |
| Four offline engines and three event buses coexist with different semantics. | `backend/app/services/offline_sync_service.py`, `integration/offline.py`, `citizen_platform/offline.py`, `core/sync_engine.py`, `shared/events/bus.py`, `backend/app/kernel/event_bus/`, `integration/esb/message_bus.py`. | NV2-D01, NV2-D03, NV2-D05. |
| National route tree is complete in source but not imported by the active factory. | `backend/app/national/api/routes/__init__.py`; no factory import. | NV2-D01, NV2-D04. |
| Migration revision count and chain description conflict across reports. | 111 files on disk vs historical “48 migrations/110 files” claims; single head `20261119_0003`. | NV2-D02, NV2-D14. |

## 5. Decision authority boundaries

- Only an owner-recorded decision may change `BLOCKED` to `OWNER DECIDED`.
- No architecture document, code change, test result, independent review verdict, CI gate or program charter may change release authority.
- Any change to C01–C15 national contracts requires contract review, explicit version bump and G1 revalidation.
- Any change to HOLD, `production_ready_items`, Stable v1.0.0 status or PRODUCTION READY authority requires a distinct owner decision outside this V2 planning gate.
- Any change to prior protected records, SHA manifests or PR #307 is out of scope.

## 6. Evidence basis

- `GULA_OWNER_DECISION_REGISTER.md` §§1, 2, 3, 5, 8, 9.
- `GOVERNANCE/FINAL_DECISION.md` §§1, 4, 7, 8, 9, 10.
- `GOVERNANCE/GECS/MASTER_CONTROL.md` §§3, 7, 8.
- `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`.
- `AUDIT_EXECUTION_RECORDS/P-02_FINAL_CLOSURE_2026_11_24.md`.
- `AUDIT_EXECUTION_RECORDS/P-02_INDEPENDENT_REVIEW_2026_11_24.md`.
- `AUDIT_EXECUTION_RECORDS/P-03_OWNER_DECISIONS_REQUIRED.md`.
- `AUDIT_EXECUTION_RECORDS/P-03_CONCURRENCY_DESIGN.md`.
- `AUDIT_EXECUTION_RECORDS/CHECKPOINT_P03_DESIGN_2026_11_24_SHA256.txt`.
- `backend/app/factory.py`, `backend/app/capabilities/`, `backend/app/gateways/mode.py`, `backend/app/national/api/routes/__init__.py`.

**End state:** All V2 decisions remain proposed and blocked. No decision has been invented or recorded.
