# Identity & Platform Remediation — Implementation Master Plan

> **STATUS: PHASE 0 BASELINE ESTABLISHED — CONTROLLED IMPLEMENTATION IN PROGRESS**
> This document implements the owner's *EXECUTION AUTHORIZATION — CONTROLLED IMPLEMENTATION v1.0*.
> It is **not** a release decision. `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**.
> D-020 and D-021 remain `PENDING_APPROVAL`. Nothing in this program changes either.

## 1. Objective

Convert the completed 22-document architecture study
(`GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/`) into a bounded, evidence-backed
remediation program in `gula-integration`, starting with source-verified
Priority-0 defects in identity privacy, authentication, session revocation and
Master Patient Index (MPI) merge integrity.

Success is measured by **correctness, test evidence and honesty**, not by the
number of files changed. No production-readiness claim is made at any point.

## 2. Absolute boundaries

| Boundary | Rule |
|---|---|
| Repository | `gula-integration` only; branch `integration/gula-unification-v1` |
| Protected repo | `gula-platform` is read-only and must stay clean |
| Release posture | HOLD unchanged; D-020 / D-021 unchanged |
| Git | No commit, push, merge, rebase, PR, `git add -A`, reset or clean |
| Data | No operational/production DB, no DDL, no migration execution, no real patient data |
| Services | No dormant router/engine activation (notably `national_router`, `document_intelligence`) |
| Secrets | No generated permanent production keys; no private key material in source |
| Tests | No disabled/weakened assertions; synthetic fixtures only |

Stop conditions are enforced per work item (§7); an isolated blocked item does
not stop unrelated authorized work.

## 3. Governance classification vocabulary

Every backlog item carries exactly one classification:

- `OWNER_APPROVED` — covered by the current controlled-implementation authorization.
- `RECOMMENDED` — safe to propose, needs owner acknowledgement before implementation.
- `NEEDS_OWNER_DECISION` — architectural/data-ownership choice required.
- `LEGAL_REVIEW_REQUIRED` — Iraqi statutory interpretation or consent/retention basis required.
- `SECURITY_REVIEW_REQUIRED` — security design/sign-off required (D-020 cannot be substituted).
- `BLOCKED_BY_EXTERNAL_DEPENDENCY` — government interface, key material, library or
  authorized calibration data unavailable.

D-IDENTITY-01…11 are **product-design decisions only**; they do not authorize
implementation, schema change or release-status change by themselves.

## 4. Program structure

```
PHASE 0  Baseline and implementation governance        ← current phase
PHASE 1  Critical identity privacy & authentication defects (P0 tranche)
PHASE 2  MPI merge integrity & duplicate-resolution safety (P0/P1 boundary)
PHASE 3  NHID and identity lifecycle consolidation
PHASE 4  Provisional identity and care continuity
PHASE 5  Citizen registration and account recovery
PHASE 6  Child and guardian lifecycle
PHASE 7  Birth and death evidence lifecycle
PHASE 8  OCR and document-intelligence hardening
PHASE 9  API and healthcare integration
PHASE 10 Security, performance and reliability validation
PHASE 11 Controlled pilot readiness
```

Each phase records scope, dependencies, files changed, risks, tests, acceptance
criteria, rollback, remaining blockers and required approvals. Phases may not
be merged into a single unbounded pass.

## 5. P0 tranche definition (this authorization)

| Unit | Scope | Classification |
|---|---|---|
| P0-A | Canonical NID normalization/HMAC, registration & matching consistency, no new raw NID at rest, no NID in corrected URL path | `OWNER_APPROVED` (security-sensitive; security review still required for certification) |
| P0-B | OAuth2/OIDC JWKS fail-closed; no misleading empty key set | `OWNER_APPROVED` implementation; `SECURITY_REVIEW_REQUIRED` for OIDC readiness |
| P0-C | WebAuthn configuration, challenge serialization/lifecycle, origin/RP validation, replay protection | `OWNER_APPROVED` implementation; `SECURITY_REVIEW_REQUIRED` for passkey activation |
| P0-D | Permission-version/session revocation correctness and fail-safe policy | `OWNER_APPROVED` implementation; device→session termination `NEEDS_OWNER_DECISION` |
| P0-E | MPI merge claim repointing, cycle/idempotency/consistency guarantees | `OWNER_APPROVED` for explicitly owned references; full cross-domain merge + unmerge `BLOCKED` |

Explicitly **out of scope** for this tranche: HOLD→GO, D-020/D-021 approval,
`backend/migrations/env.py` (preserve the pre-existing `+49/-0` delta), schema
migrations/DDL, government/civil-registry/NFC integration, key-rotation policy,
national router mounting, DocIntel activation, OCR benchmark claims, and any
biometric collection or new retention policy.

## 6. Engineering standards

- Python 3.12 target; source uses PEP 695 syntax, so tests require a 3.12 interpreter.
- Synthetic fixtures only; no operational database connections.
- Every code change has a test; every bug fix has a regression test.
- Smallest relevant suite first, then related integration tests, Ruff, MyPy where practical.
- Record exact command, exit code, counts, skips and environment limitations.
- Preserve Clean Architecture, existing API/event/audit contracts except where a
  documented security correction requires a contract change (see P0-B evidence).
- Arabic-first RTL and offline-first behavior are preserved; no new paid/vendor dependency.

## 7. Stop conditions (per item)

Stop the affected item, document the blocker and continue unrelated work if:

1. A target file contains conflicting pre-existing user changes.
2. A schema migration is required but not approved.
3. A legal decision is required.
4. A security design decision cannot be safely inferred.
5. Patient-record corruption or reference loss is possible.
6. A merge cannot preserve all explicitly owned references.
7. A cryptographic key/secret is missing.
8. A test would require production data.
9. A dependency cannot be satisfied safely.
10. An existing *working* API contract would be broken.
11. A protected repository/file would need modification.

## 8. Honesty baseline (must be carried into every report)

- 0 PRODUCTION_VERIFIED · 0 RUNTIME_VERIFIED · 0 E2E_VERIFIED.
- RPO / RTO **UNMEASURED / NOT VERIFIED**.
- `TEST_VERIFIED` in the study means test *source exists*, never that it was executed.
- All study findings were static source observations; this tranche adds unit/integration
  evidence on synthetic fixtures only and does not change the above verdicts.
- OCR and NFC remain assurance level `L0`; ID Scan remains advisory with `needs_confirmation`.
- F-085, R-01…R-11, ADR-C…ADR-J, D-020, D-021 remain open/pending as recorded.

## 9. Deliverables

Seven Phase-0 documents plus five phase/remediation reports:
`SECURITY_REMEDIATION_REPORT.md`, `IDENTITY_AND_MPI_REMEDIATION_REPORT.md`,
`OCR_READINESS_REPORT.md`, `DATABASE_MIGRATION_READINESS.md`,
`NEXT_PHASE_AUTHORIZATION_REQUEST.md` — all under this directory.

## 10. Current status

Phase 0 baseline recorded in `SOURCE_BASELINE.md`; backlog in
`IMPLEMENTATION_BACKLOG.md`; dependency map in `DEPENDENCY_GRAPH.md`; risks in
`CHANGE_RISK_REGISTER.md`; execution log in `IMPLEMENTATION_PROGRESS.md`;
test evidence in `ACCEPTANCE_EVIDENCE.md`. Implementation begins only after
these documents are in place and target files are confirmed free of user conflicts.
