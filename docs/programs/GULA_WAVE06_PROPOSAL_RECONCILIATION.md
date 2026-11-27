# Wave 06 Original Proposal Reconciliation

Status: **RECONCILED; WAVE 06 REMAINS PROPOSAL-ONLY FOR BLOCKED SCOPE; CATEGORY A SAFE WORK AUTHORIZED BY MASTER DIRECTIVE**. Baseline: `a01352578c0df205b92e58444242e1fa6ae7d77b`. Evidence timestamp: `20261126T053405Z`.

This document preserves every requirement from the original Wave 06 proposal and its source material. It is not a replacement plan. New work authorized by the master directive is limited to safe, independent engineering and evidence packets; original owner, government, schema, clinical, legal, and release constraints remain in force.

## Sources

- `P` = `$W053/audit/WAVE05_3_CLOSURE_20261125T122640Z/GULA_WAVE_06_PROPOSAL.md`, lines 1–266.
- `S` = `$W053/audit/WAVE05_3_CLOSURE_20261125T122640Z/40_wave06_source_material.txt`, lines 1–281.
- `$W053` = `/home/samertts/workspace/gula-preservation/20261124T173502Z/integration/GULA-WAVE-05.3-NATIONAL-IDENTITY-PERSISTENCE-SECURITY-20261125T070238ZZ`.

## 1. Global posture (preserved, unchanged)

| Requirement | Source | Status after reconciliation |
|---|---|---|
| Wave 06 proposal is `PROPOSAL ONLY / NOT APPROVED / NO IMPLEMENTATION AUTHORIZED` | P:3, P:11; S:4 | PRESERVED. No owner authorization is invented. |
| Wave 05.3 decision `RELEASE_BLOCKED` | P:8 | PRESERVED. |
| `HOLD=TRUE`, `production_ready_items=0`, `G1–G12=NOT PASSED`, `STABLE_V1_0_0=NOT DECLARED`, `PRODUCTION_READY=NOT DECLARED` | P:9, P:67, P:264; S:16–18, S:275–279 | PRESERVED. No gate or release token changed. |
| Real government verification, production KMS/HSM, schema migration/DDL, national route activation `NOT APPROVED` | S:17 | PRESERVED. |
| No branch, route, migration/DDL, credential, government connection, real citizen data, gate change, production deployment, or implementation authorized by the proposal | P:11; S:4 | PRESERVED as proposal boundary. The master directive separately authorizes only Category A safe work on a new non-protected branch. |
| `EXPLICIT` vs `INFERRED / PROPOSED` labeling required | P:11; S:29 | PRESERVED throughout this reconciliation. |
| Historical `89b2f455b6038a0714471330a763a27e9422232f` is the proposal's audited commit | P:7; S:9–10 | HISTORICAL. Current execution baseline is `a01352578c0df205b92e58444242e1fa6ae7d77b`. |

## 2. Section-by-section preservation

| Section | Original content | Classification | Disposition in current execution |
|---|---|---|---|
| 1 — Proposal status and decision authority | No gate passed; owner record alone moves to `ACCEPTED`; synthetic validation cannot lift HOLD; no owner decision resolved by code/tests; owner must authorize Wave 06 and each work package | EXPLICIT / PROPOSED | PRESERVED. Master decision register MDEC-006 records no gate/release change. |
| 2 — Objective | Wave 06 should be an evidence-and-unblocking wave, not production release; no definitive Wave 06 engineering spec exists; only long-range strategy exists; 31 owner decisions unresolved | INFERRED / PROPOSED | ADOPTED as framing. This execution produces reconciliation and safe remediation evidence, not release. |
| 3 — Source material and scope derivation | Canonical repo, Wave 05.3 evidence root, V2 gate definitions, `40_wave06_source_material.txt`; unrelated CI/reproducibility \"Wave 6\" record excluded | EXPLICIT | PRESERVED. Sources read fully; unrelated record not treated as scope. |
| 4 — In-scope candidates W06-P01..P13 | Durable identity/NIDP persistence, PG16 concurrency evidence, key custody, no-raw-NID exposure, audit/consent/role/break-glass, government verification packet, official card/NFC/OCR packet, patient linkage policy, API/contract readiness, offline/event durability, performance/DR/observability evidence plan, multi-ministry planning | INFERRED / PROPOSED | PRESERVED as candidate backlog. Mapped to master gaps MGR-001..MGR-042. No blocked item implemented. |
| 5 — Out of scope | No production deployment/HOLD lift/declarations; no DDL, migrations, triggers, schema change, route mount, dependency, credential, production config; no real citizen data/card/NFC/invented chip keys; no synthetic verification as real; no store collapse; no vendor lock-in/paid dependency without analysis; no independent OCR path to `VERIFIED`; no Wave 06 source implementation under the proposal | EXPLICIT | PRESERVED verbatim as hard boundary. |
| 6 — Architecture impact and canonical reuse | FastAPI monolith production architecture; `services/` not production target; one canonical implementation per concern; reuse listed identity/crypto/ADE/audit/MPI/outbox components; no duplicates | EXPLICIT / PROPOSED | ADOPTED. Master architecture register records canonical vs duplicate/unwired. |
| 7 — API and data-contract strategy | No national/NIDP route mount; same-major backward compatibility; event/schema backward compatibility and integration tests; prepare contract inventories, OpenAPI reconciliation, C01–C15 ownership, negotiation, headers, schema-endpoint repairs, generated-client proof | EXPLICIT / PROPOSED | PRESERVED. No route mounted in this execution. |
| 8 — Database/persistence/migration strategy | Wave 05.3 added no DDL; 101 migrations, one root/head; replay state in-process; conflicting source-of-truth map; in-process tests insufficient for PG16; schema-owner packets; parent future migration on current head; forward-only/backward compatible; downgrade preserves history; no migration/DDL authored/staged/executed under proposal | EXPLICIT / PROPOSED | PRESERVED. No DDL/migration performed. |
| 9 — Security/privacy/compliance | Reuse canonical Decision Engine/audit builder; hard-deny raw NID/NFC/card image/encrypted NID; 14 NIDP operations; keyed HMAC/`compare_digest`; default-closed government adapter; unresolved raw NID exposure, in-memory break-glass, placeholder consent, audit wiring, KMS/HSM, key custody, TLS/mTLS, retention/disclosure, independent review; security packets and free/self-hosted alternatives | EXCEPT: EXPLICIT + PROPOSED | PRESERVED. Only null-scope fail-closed is attempted now (MGR-015); all other items owner-gated. |
| 10 — Government verification/card readiness | Real authority, API, credentials, endpoint, registry, status semantics, keys, revocation, transport `NOT APPROVED`; adapter default-closed; `CHIP_AUTHENTICITY_VERIFIED`, `DOCUMENT_AUTHENTICITY_CONFIRMED`, canonical `VERIFIED` unreachable; copy/forgery/mismatch/uncertainty/expiry/OCR/NFC failure route to human review; only questionnaires/spec requests/workflow designs | EXPLICIT / PROPOSED | PRESERVED. No live connection or invented card/chip material. |
| 11 — Patient identity safety/clinical workflow | Helpers exist; workflow blocked; prior-record display, rollback authority, facility mapping, linkage, consent, durable uniqueness missing; no clinical sign-off/G3 E2E; decision packets only; no patient data | EXPLICIT / PROPOSED | PRESERVED. No clinical workflow activated. |
| 12 — Offline synchronization/event durability | G9 durable queues/quarantine/convergence/idempotent replay/no lab overwrite; existing outbox/event insufficient; four engines, process-local stores, uncommitted quarantine fix, no proof; single offline contract, deterministic conflict policy, replay/fault-injection plan | EXPLICIT / PROPOSED | PRESERVED. No offline engine declared authoritative. |
| 13 — Performance/capacity/DR/observability | Targets: error `<1%`, read p95 `<500 ms`, write p95 `<1000 ms`, health p99 `<200 ms`, throughput `>=100 rps`; no reproducible national-scale artifact; G6 backup→restore→PITR, measured RTO/RPO, failover, CI DR job; G10 `/metrics/prom`, SLO metrics, OTel traces, alert webhook, incident drill; plans only, no self-awarded gates | EXPLICIT / PROPOSED | PRESERVED. Targets remain proposed until ratified and measured. |
| 14 — Test and validation strategy | Compile, lint, pre-existing tests, style, no secrets, no dead code, type hints; unit/integration/error/deterministic tests, 80% coverage for new/modified modules; CI gates; exact commands/logs/exit codes/hashes; do not rerun expensive suites without reason; focused then regression then justified full suites; no new skip/xfail; no sensitive data in evidence | EXPLICIT / PROPOSED | ADOPTED for safe changes. Exact commands and exit codes recorded in phase evidence. |
| 15 — Rollback and operational readiness | Runbook `PROPOSED`; key rotation, incident, audit review, correction, duplicate, outage, OCR/NFC failure, DB recovery, backup/restore, DR, escalation design-only; no restore/government connection/production access; rollback preserves history | EXPLICIT / PROPOSED | PRESERVED. No runbook marked executed. |
| 16 — Milestones M0–M6 | Authorization decision, evidence gap pack, architecture/contract packet, persistence/security packet, government/card/clinical packet, validation planning, owner acceptance gate; no implementation under proposal | PROPOSED | M0–M5 partially supported by this execution's reconciliation and evidence; M6 remains owner-only. |
| 17 — Dependencies, risks, approvals | G1–G12 evidence; OD-01..OD-31; NV2-D01..D15; legal/privacy; government authority; schema owner; security; clinical/institutional; release authority; seven named risks and mitigations | EXPLICIT / PROPOSED | PRESERVED. Deprecated risks are listed in master decision/gap registers. |
| 18 — Decision requested, measurable outcomes, DoD | Owner must authorize Wave 06 and each package; migration graph revalidated; PG16 plan; zero new raw NID; canonical reuse invariant; compile/lint/tests/security checks for authorized implementation; gates remain `NOT PASSED`; alternatives documented; posture unchanged; proposal DoD | PROPOSED / EXPLICIT | PRESERVED. This execution measures only what it actually runs; no gate self-award. |

## 3. Non-droppable constraint union

The following constraints appear in one or both source files and remain binding:

1. Proposal-only authority; no owner authorization is inferred from code, tests, synthetic evidence, strategy documents, historical certificates, or this reconciliation.
2. Release posture and all G1–G12 tokens unchanged.
3. Synthetic validation cannot lift HOLD, declare release, activate identity, reach canonical `VERIFIED`, or replace human review.
4. No DDL, migration, trigger, schema change, staged migration, or execution without schema-owner approval. Future migration must be parented on current head, revalidated, forward-only, backward-compatible, and preserve historical correction/audit/review/authenticity records on downgrade.
5. Conflicting identity representations are not collapsed; provenance preserved.
6. FastAPI monolith remains production architecture; one canonical implementation per concern; no second identity generator, MPI, audit store, authorization engine, citizen database, state machine, OCR engine, or patient-identity system.
7. No national/NIDP route mounted; contract work is readiness-only; same-major and event/schema changes must be backward compatible and integration-tested.
8. In-process/SQLite tests do not prove PG16 constraints, advisory locks, transactional generation, replay durability, or production durability.
9. Hard-deny raw NID/NFC payload/card image/encrypted NID; keyed HMAC and `compare_digest`; default-closed government adapter; no new raw NID exposure.
10. Real government/card/NFC/OCR authority inputs are `NOT APPROVED`; no live connection, credentials, invented chip keys/APDUs/certificates, or real citizen data.
11. Clinical workflow remains blocked; no patient data; linkage, rollback, facility mapping, prior-record display, consent, and human-review ownership require clinical/institutional decisions.
12. Existing outbox/event components are not G9 convergence proof; no offline engine is authoritative; conflict policy, quarantine, idempotency, replay, and fault injection remain required.
13. Performance/DR/observability claims require reproducible artifacts, executed drills, measured targets, and independent review; no self-awarded gates.
14. Exact commands, exit codes, hashes, and logs preserved; no new skip/xfail or weakened `pytest.ini`; focused tests before regression before justified full suites.
15. Free/open-source/self-hosted and replaceable alternatives documented before any paid or vendor-specific dependency.
16. No real citizen data, card images, raw NFC payloads, credentials, or sensitive external transfers.

## 4. Mapping to master programs

| Wave 06 candidate | Master gaps | Program | Current disposition |
|---|---|---|---|
| W06-P01..P03 | MGR-002,MGR-003,MGR-005,MGR-023 | P0 National Core | BLOCKED — schema/government/clinical approval |
| W06-P04..P05 | MGR-018,MGR-035,MGR-036 | P10 Security/Infrastructure | BLOCKED/packet-only except dependency triage planning |
| W06-P06 | MGR-006,MGR-007,MGR-009,MGR-010,MGR-012,MGR-013,MGR-016 | P0/P10 | BLOCKED except MGR-015 Category A fix |
| W06-P07..P08 | MGR-001,MGR-003,MGR-008 | P0 Identity | BLOCKED — government authority |
| W06-P09 | MGR-004,MGR-005,MGR-022 | P1 Clinical | BLOCKED — clinical/institutional approval |
| W06-P10 | MGR-043, G1/G4 gaps | P0/P10 | Readiness-only; no route activation |
| W06-P11 | MGR-019,MGR-028,MGR-029,MGR-042 | P1/P10 | BLOCKED — durability/field proof |
| W06-P12 | MGR-030..MGR-037 | P10 | BLOCKED — executed evidence required |
| W06-P13 | Program planning | P9 | DESIGN_ONLY / planning only |

## 5. Reconciliation conclusion

All 18 sections and their correct requirements are preserved. Wave 06 remains `PROPOSAL ONLY / NOT APPROVED` for owner-gated implementation. The current master directive authorizes only independent Category A engineering now; this reconciliation provides the traceability needed to ensure that safe work does not silently expand into blocked scope.
