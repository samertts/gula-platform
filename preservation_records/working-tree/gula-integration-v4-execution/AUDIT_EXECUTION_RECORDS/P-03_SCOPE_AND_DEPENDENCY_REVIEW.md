# P-03 — scope and dependency review (2026-11-24)

Generated 2026-11-24 UTC. **Additive governance document.** It does not modify the
approved REV3 packet, the owner register, prior closure records, prior SHA
manifests, source, tests, configuration, release status or PR #307.

**Review verdict:** P-03 and `P-03-CONCURRENCY` are **two separate packages** with
different defects, decisions, code surfaces, acceptance evidence and rollback
boundaries. They must not be merged. P-03 implementation remains **BLOCKED** until
the owner records D1–D5 explicitly.

## 1. Purpose and method

This review closes the governance/design documentation gap identified after the
P-02 closure and the 2026-11-24 P-03 readiness assessment. It records:

1. what belongs to P-03 / AUD-F03;
2. what belongs to `P-03-CONCURRENCY`;
3. what dependencies exist between packages, decisions, evidence and shared
   infrastructure;
4. what may not be inferred from package-level authorization or single-process
   evidence.

Method: read-only review of `P-03_DECISION_PACKET_REV3.md`,
`P-03_READINESS_2026_11_24.md`, `GULA_OWNER_DECISION_REGISTER.md`, P-02 closure
evidence, the prior serialization decision, HEAD source references quoted in the
REV3 packet, and repository integrity checks. No P-03 code, migration, schema,
staging operation, commit, push, PR, merge, release or deployment was performed.
No database, provider, PHI, secret value or production service was used in this
document phase.

## 2. Package separation

| Dimension | P-03 / AUD-F03 REV3 | P-03-CONCURRENCY |
|---|---|---|
| Defect class | Missing canonical audit evidence at selected control-plane boundaries | Hash-chain fork under concurrent writers at the canonical audit writer |
| Source surface (HEAD) | `backend/app/control_plane/routes.py:211-226,291-306,309-327`; `release/manager.py`; `control_plane/config/secrets.py`; `control_plane/audit.py`; new route wiring only | `backend/app/services/audit_service.py:106-112,184-268`; isolation/lock behavior; append-only schema context |
| Owner decisions | D1 boundaries, D2 actor, D3 failure, D4 idempotency, D5 audit read; D6 separately for staging/commit | Separate authorization required; lock/key/isolation/retry/recovery decisions not in D1–D5 |
| Tests proposed | T1, T2, T5, T6, T7, T8, T10 as applicable; T3/T4 only if B3/B4 selected | Fork matrix, isolation rejection, locking/order, rollback, deadlock/timeout, recovery, performance |
| RED evidence | No B1–B4 RED/GREEN suite exists yet; cannot be scoped before D1–D5 | Clean PG16 diagnostic RED exists: `1 failed / 1 passed`, broken hash `571f43b6…` vs `5bb1ab4d…` — defect evidence only |
| GREEN evidence status | none | none |
| Schema change | none authorized | none authorized; unique correlation key would be a separate decision |
| Rollback | revert selected control-plane hunks only | revert canonical audit serialization hunks only; no historical-row rewrite |
| Current status | `PREPARED ONLY · NOT IMPLEMENTED`; owner package authorization exists but D1–D5 absent | `PREPARED ONLY · NOT APPROVED · NOT IMPLEMENTED` |

**Prohibition:** T9 must not be added to P-03 acceptance “for completeness”. The
REV3 packet §2, §6 and §7 explicitly defers it. A single-process RED/GREEN result
for control-plane audit writing is not a multi-worker chain-integrity proof, and
the current T9 diagnostic is not a fix proof.

## 3. P-03 in scope

Subject to owner D1–D5 decisions, P-03 may include only:

- `Depends(get_db)` wiring on owner-selected control-plane routes, using an
  existing dependency from the authenticated principal graph;
- canonical `log_action` calls with action values from the existing taxonomy and
  actor fields from the authenticated principal only;
- audit row commit/flush before in-memory release state mutation, with fail-closed
  behavior if D3=(a) is selected;
- B3 secret-reference auditing only if D1=(b) or (c) is selected, using key
  references only and never secret values;
- B4 canonical read helper and route re-pointing only if D1=(c) and D5=(a) are
  selected;
- PostgreSQL RED/GREEN tests for the selected boundaries, using disposable PG16,
  synthetic data, `--noconftest` where the repo SQLite fixture would interfere,
  and no PHI or production access.

## 4. P-03 explicitly out of scope

The following are excluded by REV3 §4/§7 or by absence of owner decision:

- T9 concurrent chain serialization, advisory locks, isolation guard changes,
  lock ordering, deadlock/retry architecture and chain recovery;
- any change to `backend/app/services/audit_service.py` for concurrency;
- two-person rule, role/permission changes, service-actor identity plumbing;
- durable outbox, correlation-key schema, unique constraints, dedupe migration;
- new audit-read schema or new response contract beyond B4/D5=(a);
- deploy/rollback route additions, changes to deployment behavior, or fleet
  deploy unless D1=(e) is explicitly selected;
- commit, staging changes, push, Draft PR, merge, release, deployment, change to
  HOLD, or change to `production_ready_items = 0`;
- use of the working-tree `audit_service.py` advisory-lock lines as HEAD evidence.

## 5. P-03-CONCURRENCY in scope for its own future packet

Subject to separate owner approval, `P-03-CONCURRENCY` may include only the
canonical audit write serialization design and its evidence:

- transaction-scoped PostgreSQL advisory lock with one versioned global key;
- isolation guard accepting only `READ COMMITTED`;
- lock acquisition before sequence reservation, tail read and row locks;
- rollback semantics, sequence-gap disclosure and anchor timing correction;
- bounded SQLSTATE retries and a separate idempotency schema decision;
- multi-worker/multi-node PG16 tests and chain verification detection tests.

The 2026-11-24 design document `P-03_CONCURRENCY_DESIGN.md` is a proposal only;
it does not approve or implement any of these items.

## 6. Decision dependency graph

| Dependency | Requirement | Consequence if unmet |
|---|---|---|
| REV3 packet accepted as scope source | already satisfied for decision purposes; packet remains unchanged | no implementation may use older packets REV1/REV2 |
| Owner D1 | must select boundary set | no lawful list of routes/tests/files |
| Owner D2 | must select actor policy | audited actor cannot be determined; body spoofing cannot be safely resolved |
| Owner D3 | must select failure policy | fail-closed vs outbox availability trade-off remains undecided |
| Owner D4 | must select idempotency policy | duplicate-event acceptance basis remains undefined |
| Owner D5 | required only if B4 selected; otherwise must accept inert route | audit-read behavior ambiguous |
| D1=(c) ↔ D5=(a) | if B4 audited, read route must expose canonical rows | selecting B4 without D5=(a) leaves oversight surface inert |
| D1=(e) | explicit separate selection for fleet deploy | B2 must not be represented as covering all deployment surfaces |
| D2=(b) | separate service-identity design required | must not infer service actor from request body |
| D3=(b) | separate durable-outbox design required | cannot be substituted inside P-03 |
| D4=(b) | separate schema/migration decision required | cannot add dedupe index or unique constraint inside P-03 |
| D6 | separate staging/commit authorization | no commit, staging change, push, PR or merge may occur |
| P-03-CONCURRENCY owner approval | separate package approval | T9 fix cannot be bundled into P-03 |

## 7. Evidence dependency graph

| Evidence | What it proves | What it does **not** prove |
|---|---|---|
| P-02 RED `6 failed / 2 passed`, GREEN `8 passed`, related suites `224 passed / 9 skipped` | P-02 critical-alert audit fail-closed behavior on PG16 | P-03 control-plane audit; P-03 acceptance; production readiness |
| P-02 independent review verdict `DECISION-READY`, 0 CRITICAL/HIGH/MEDIUM, 2 accepted LOW residuals | P-02 engineering review completed | owner acceptance of P-02 or P-03; `PRODUCTION READY` |
| P-02 closure manifest `6/6 OK` | P-02 evidence set stable after review | any later package scope |
| Disposable PG gate validation | suitable non-production PG16 environment exists | production capacity or availability |
| T9 PG diagnostic `1 failed / 1 passed` | concurrent chain fork defect at HEAD | P-03 RED/GREEN; T9 fix; multi-worker GREEN |
| `CHECKPOINT_P03_READINESS_2026_11_24_SHA256.txt` `2/2 OK` | readiness evidence stable | D1–D5 decided; implementation authorized |
| This design manifest | new additive design files stable | implementation approved |

## 8. Shared-resource and conflict review

| Shared resource | Status / rule |
|---|---|
| Baseline HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` remains the evidence baseline; no commit or history rewrite |
| Branch | `integration/gula-unification-v1` unchanged |
| Staged renames | 20 `R100`, staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`; untouched by this work |
| Working tree | 162 unstaged tracked files and pre-existing untracked files preserved; design files added only under `AUDIT_EXECUTION_RECORDS/` |
| `backend/app/services/audit_service.py` | working tree contains uncommitted mixed-provenance advisory-lock lines; not reviewable evidence for HEAD, P-03 or P-03-CONCURRENCY |
| PG gate container/network | validated, disposable, labeled non-prod and isolated; no published ports; credentials outside repo; no value disclosed |
| Protected MD5s | unchanged |
| PR #307 | untouched |
| Sibling `gula-platform` | HEAD only checked; no file read/write/change; HEAD unchanged at `f478676b6fc375338648dde46fbf076c015a3f91` |
| Status registry | `production_ready_items = 0` unchanged |

## 9. Execution ordering proposal — not an authorization

1. Owner records D1–D5 in `GULA_OWNER_DECISION_REGISTER.md` using the exact REV3
   decision text, and separately decides D6 if a commit is ever contemplated.
2. If P-03 proceeds: create the selected B1/B2/B3/B4 PG16 RED tests first, then
   implement only selected hunks, run focused and related suites, independent
   review, and produce `P-03_AFTER_REV3.md`.
3. If P-03-CONCURRENCY proceeds: obtain a separate owner decision and implement
   against the design package, with no reuse of P-03 control-plane GREEN as
   multi-worker evidence.
4. If either package reaches engineering completion, it still does not become
   `ACCEPTED`, `PRODUCTION READY` or a release authorization without explicit
   owner decision.

## 10. Current blocking statement

The only new artifacts from this phase are additive design/governance documents.
No owner decision was invented. No P-03 implementation, no T9 fix, no schema, no
migration, no commit and no release action occurred.

**HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED ·
PRODUCTION READY NOT AUTHORIZED.**
