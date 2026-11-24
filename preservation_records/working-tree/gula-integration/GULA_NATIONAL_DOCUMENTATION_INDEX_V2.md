# GULA National Transformation V2 — Documentation Index

**Document:** `GULA_NATIONAL_DOCUMENTATION_INDEX_V2.md`  
**Generated:** 2026-11-24 UTC  
**Phase:** Architecture and Execution Planning Gate  
**Status:** `PROPOSED · PENDING OWNER APPROVAL`  
**Posture:** **HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED.**

## 1. Purpose

This index is the navigation map for the V2 national planning set. It lists only the new additive V2 documents created in this gate. It does not replace, re-date, re-classify or supersede any prior architecture document, certification, closure record, owner register, status registry or SHA manifest.

All V2 documents are plans. None is an approval, release authorization, implementation record or evidence of production readiness.

## 2. V2 document set

| # | File | Primary purpose | Key dependencies |
|---|---|---|---|
| 1 | `GULA_NATIONAL_MASTER_EXECUTION_PLAN_V2.md` | Master execution strategy, waves, critical path, parallel governance model. | 2, 3, 4, 5, 13, 16, 17 |
| 2 | `GULA_NATIONAL_ARCHITECTURE_BLUEPRINT_V2.md` | Target national architecture across layers A–G; modular-platform decision. | 1, 3, 4, 6, 7, 11 |
| 3 | `GULA_NATIONAL_MODULE_REGISTRY_V2.md` | Authoritative V2 module inventory, ownership, lifecycle and target placement. | 2, 4, 5, 8, 13 |
| 4 | `GULA_NATIONAL_CAPABILITY_INVENTORY_V2.md` | Evidence-backed inventory of existing capability status; no invented completion scores. | 2, 3, 14, 15 |
| 5 | `GULA_NATIONAL_PROGRAM_CHARTERS_V2.md` | Charters for PRG-00…PRG-10 with mission, scope, deliverables, dependencies, acceptance. | 1, 2, 3, 6, 10, 13, 16 |
| 6 | `GULA_NATIONAL_INTEGRATION_CONTRACT_V2.md` | Binding-target contracts C01–C15, standards, versioning, idempotency, ownership. | 2, 3, 8, 9, 10, 13 |
| 7 | `GULA_NATIONAL_ZERO_TRUST_SECURITY_PLAN_V2.md` | Zero-trust controls, identity separation, break-glass, anti-abuse test requirements. | 2, 6, 8, 9, 10, 14 |
| 8 | `GULA_NATIONAL_DATA_GOVERNANCE_PLAN_V2.md` | Data ownership, source of truth, retention, quality, lineage, conflict policy. | 3, 6, 7, 9, 12 |
| 9 | `GULA_NATIONAL_CLINICAL_SAFETY_PLAN_V2.md` | Patient safety invariants, result integrity, corrections, late data, CDS controls. | 6, 7, 8, 10, 12 |
| 10 | `GULA_NATIONAL_TESTING_AND_QUALITY_STRATEGY_V2.md` | Test strategy incl. PG16, E2E journey, anti-abuse, contract, offline, load and DR. | 4, 6, 7, 9, 11, 12, 15 |
| 11 | `GULA_NATIONAL_INFRASTRUCTURE_AND_RELIABILITY_PLAN_V2.md` | HA, backup/PITR/DR, observability, capacity and migration safety design. | 6, 10, 12, 14 |
| 12 | `GULA_NATIONAL_CONTROLLED_RELEASE_PLAN_V2.md` | Gates G1–G12, staged rollout, rollback, stop conditions, release authority. | 7, 9, 10, 11, 15, 17 |
| 13 | `GULA_NATIONAL_DEPENDENCY_GRAPH_V2.md` | Program, module, contract and evidence dependency graphs; critical path. | 1, 2, 3, 5, 16 |
| 14 | `GULA_NATIONAL_RISK_REGISTER_V2.md` | National planning risks R-01… with mitigation, triggers, owners and gate links. | 4, 7, 10, 11, 12, 17 |
| 15 | `GULA_NATIONAL_ACCEPTANCE_MATRIX_V2.md` | Acceptance criteria mapped to gates, evidence types, owners and current status. | 6, 9, 10, 11, 12, 14 |
| 16 | `GULA_NATIONAL_EXECUTION_BACKLOG_V2.md` | Executable, ordered, verifiable work packages and first parallel workstream set. | 1, 5, 13, 15, 17 |
| 17 | `GULA_NATIONAL_DECISION_REGISTER_V2.md` | Owner decisions NV2-D01… required before execution/release authority. | all |
| 18 | `GULA_NATIONAL_DOCUMENTATION_INDEX_V2.md` | This index. | all |
| — | `CHECKPOINT_GULA_NATIONAL_V2_2026_11_24_SHA256.txt` | Additive SHA256 manifest for documents 1–18. | all |

## 3. Recommended reading order

1. **Start:** `GULA_NATIONAL_MASTER_EXECUTION_PLAN_V2.md` — strategy and execution gates.
2. **Then:** `GULA_NATIONAL_CAPABILITY_INVENTORY_V2.md` — what actually exists.
3. **Then:** `GULA_NATIONAL_ARCHITECTURE_BLUEPRINT_V2.md` and `GULA_NATIONAL_MODULE_REGISTRY_V2.md` — target structure and module placement.
4. **Then:** `GULA_NATIONAL_PROGRAM_CHARTERS_V2.md` and `GULA_NATIONAL_DEPENDENCY_GRAPH_V2.md` — team boundaries and critical path.
5. **Then:** `GULA_NATIONAL_INTEGRATION_CONTRACT_V2.md`, `GULA_NATIONAL_ZERO_TRUST_SECURITY_PLAN_V2.md`, `GULA_NATIONAL_DATA_GOVERNANCE_PLAN_V2.md`, `GULA_NATIONAL_CLINICAL_SAFETY_PLAN_V2.md` — shared non-negotiable contracts.
6. **Then:** test, infrastructure and release plans — evidence production.
7. **Then:** risk register, acceptance matrix, backlog and decision register — control and execution.
8. **Finally:** SHA manifest for integrity verification.

## 4. Canonical identifier map

| Identifier family | Values | Defined in |
|---|---|---|
| Programs | `PRG-00` … `PRG-10` (`P0` … `P10`) | Master plan, program charters |
| Contracts | `C01` … `C15` | Integration contract |
| Release gates | `G1` … `G12` | Controlled release plan |
| Risks | `R-01` … | Risk register |
| Owner decisions | `NV2-D01` … `NV2-D15` | Decision register |
| Waves | `W0` … `W4` | Master plan, backlog |
| Workstreams | `WS-CORE-01`, `WS-SEC-01`, `WS-AUD-01`, `WS-OBS-01`, `WS-DB-01`, `WS-E2E-01`, `WS-API-01`, `WS-GOV-01` | Execution backlog |

**Naming warning:** `PRG-03` means Diagnostics and Laboratory Systems. The legacy audit package is always written `P-03 / AUD-F03`; it is not this program.

## 5. Relationship to prior governance

The V2 set treats the following as binding inputs that must not be modified:

- `GULA_OWNER_DECISION_REGISTER.md` — owner decision authority and OD items.
- `GOVERNANCE/FINAL_DECISION.md` — HOLD release decision.
- `GOVERNANCE/GECS/MASTER_CONTROL.md` — HOLD enforcement.
- `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` — `production_ready_items = 0`.
- `GULA_AUDIT_REMEDIATION_ROADMAP.md`, `GULA_COMPLETION_PLAN.md`, `GULA_ARCHITECTURE_DECISIONS.md` — prior remediation and ADR inputs.
- `AUDIT_EXECUTION_RECORDS/P-02_FINAL_CLOSURE_2026_11_24.md` and P-03 governance/design records — preserved audit evidence.
- All prior SHA manifests, including `CRITICAL_FILE_SHA256.txt` with its documented historical superseded entries.

Any difference between V2 proposals and prior governance is recorded as a required owner decision in `GULA_NATIONAL_DECISION_REGISTER_V2.md`, never applied by changing old records.

## 6. Integrity

The V2 SHA manifest is additive. It covers documents 1–18 only; it does not include itself and does not replace any prior manifest. Verify from the repository root:

```bash
sha256sum -c CHECKPOINT_GULA_NATIONAL_V2_2026_11_24_SHA256.txt
```

Expected: one `OK` line per V2 document and zero `FAILED` lines.

## 7. Evidence basis

- `GULA_OWNER_DECISION_REGISTER.md`
- `GOVERNANCE/FINAL_DECISION.md`
- `GOVERNANCE/GECS/MASTER_CONTROL.md`
- `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`
- `AUDIT_EXECUTION_RECORDS/CHECKPOINT_P03_DESIGN_2026_11_24_SHA256.txt`
- Repository root and active source tree structure inspected during the V2 planning gate.

**End state:** All V2 documents remain proposed and pending owner approval. No source, protected record, prior evidence or release status was changed.
