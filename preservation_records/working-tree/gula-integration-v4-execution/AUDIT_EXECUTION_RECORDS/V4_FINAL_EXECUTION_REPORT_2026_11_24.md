# V4 integrated national platform execution report — 2026-11-24

> Factual engineering handoff. This report records executed work, exact test
> evidence, preserved failures, and unresolved authority boundaries. It is not
> owner acceptance, production readiness, a release decision, or Stable
> v1.0.0.

## Part 1 — Executive status

* Execution mode: `EXECUTE`, not planning only.
* Workspace: `/home/samertts/workspace/projects/gula-integration-v4-execution`.
* Branch: `execution/gula-national-v4`; all V4 work remains uncommitted.
* No commit, push, PR, merge, deployment, production data migration, PHI use,
  live patient routing, or provider/AI/financial external call occurred.
* Wave A: technically closed with a clean full backend regression and durable
  evidence.
* Event consolidation: implemented as an engineering seam with one durable
  authority and compatibility adapters; **not activated** as the sole runtime
  bus and **not accepted**.
* Frontend-v3: bounded operationalization of four session/authorization
  bootstrap contracts; all clinical and business data surfaces remain
  non-operational or blocked.
* P-02 remains `IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED` and
  `DECISION-READY`, not accepted.
* P-03 and P-03-CONCURRENCY have green technical evidence but remain owner-gated
  and not accepted.
* `production_ready_items = 0`; `HOLD` remains in force; G1–G12 remain
  `NOT PASSED`.

## Part 2 — Mandate interpretation and authority

The V4 mandate superseded the prior read-only posture **for this isolated
execution workspace only**. Autonomous engineering authority was used to add
reversible code, tests, migrations for disposable databases, and evidence.
Owner authority was not used or simulated. V2 planning documents were left
unchanged; drift and supersession were recorded additively in
`V4_EXECUTION_ADDENDUM_2026_11_24.md`.

Free/open-source/self-hosted constraints were respected: PostgreSQL, SQLAlchemy,
FastAPI, Alembic, in-process event dispatch, and existing React/Vite tooling
were reused. No paid dependency, SaaS broker, or vendor-specific runtime was
introduced. New dependencies were not added.

## Part 3 — Preservation and provenance

Baseline invariant evidence:

* Original HEAD: `2206654dc713ea2de8c564a3207dfe05fde23549`.
* Original branch: `integration/gula-unification-v1`.
* Staged name-status MD5: `56c524d6ffe9872c3a3ac6eff8c8f203` (20 `R100`
  entries, untouched).
* Protected MD5s: `effdfeaf10234678d83b2668c4489552`,
  `1a02c01563c93b07a7cdb92c0462bf36`,
  `ea3969d09aaf7b0b28a065838b44a594`.
* Protected `gula-platform` working tree: clean.
* V2 additive manifest: `18/18 OK`.
* V4 immutable pre-change source snapshot: `23/23 OK`.

Full preservation reverification output is recorded in
`V4_FINAL_PRESERVATION_VERIFICATION_2026_11_24.txt`. It confirms `18/18`,
`23/23`, and all post-change manifest entries with `0` failures,
the three protected MD5s, original branch/HEAD/status, clean protected
repository, execution branch/status, and `production_ready_items = 0`.

Final execution worktree status with all untracked files expanded: `204`
modified tracked, `793` untracked, `20` staged renames; staged name-status MD5
unchanged.

## Part 4 — Wave A delivery

Wave A replaced eight static/empty capability CRUD surfaces with real
`capability_records` persistence. Each capability is namespaced by capability
and lab, authenticated, authorized, ownership-checked, audited, and exercised
through create/list/get/update/delete lifecycle tests. Migrations
`20261124_0001` and `20261124_0002` add records and ownership columns; a
PostgreSQL round trip removed and restored ownership columns successfully.

Wave A also added correlation IDs to logging/middleware/contracts, removed a
duplicate Prometheus renderer in favor of `/metrics/prom` delegation, and
applied the Python 3.10 `UTC = UTC` compatibility alias.

Master evidence: `V4_WAVE_A_EXECUTION_REPORT_2026_11_24.md`.
Post-hardening evidence: `V4_WAVE_A_FINAL_POST_HARDENING_RESULT_2026_11_24.md`.

## Part 5 — Contract, version, schema, and CI verification

* `APP_VERSION = 2.5.0`; runtime `app.main.app`, checked-in OpenAPI, and
  `ContractGenerator().generate_openapi(app.main.app)` agree.
* OpenAPI 3.1 export: `1,850` paths and `643` schemas; exact runtime `paths`
  equality is enforced.
* `create_app(override_mode='test')` intentionally exposes `1,843` paths; the
  authoritative guard compares the deployment entrypoint, not the test app.
* Schema endpoints resolve for `patient`, `lab-order`, `lab-result`, and
  `sample`.
* Correlation-ID propagation and sanitization are enforced by
  `test_integration_contract_enforcement.py`.
* Automated no-silent-STUB guard checks all `1,850` exported operations;
  targeted result `17 passed, 1 warning in 97.60s`, exit `0`.
* CI guard now includes contract, CRUD, PostgreSQL P-03, CRUD-PG, correlation,
  envelope, metrics, no-STUB, and event-authority suites.

Evidence: `V4_CONTRACT_VERIFICATION_2026_11_24.md`,
`V4_NO_STUB_DRIFT_GUARD_2026_11_24.txt`.

## Part 6 — Capability CRUD and PRG-00–PRG-10 status

All eight generated CRUD route families are database-backed with DI, schemas,
validation, authentication, authorization, ownership, audit, and migration
support. PostgreSQL, rollback, migration, negative authorization, and
transaction tests were executed. Honest per-capability status is in
`V4_CAPABILITY_STATUS_2026_11_24.md`.

PRG statuses remain deliberately mixed: PRG-00, PRG-08, PRG-09, and PRG-10 are
`PARTIAL` with the exact scope recorded; PRG-01–PRG-07 are `NOT ACCEPTED` or
`BLOCKED`. See `V4_PRG_STATUS_2026_11_24.md`.

## Part 7 — P-03 and P-03-CONCURRENCY

* P-02: unchanged decision-ready status; no owner acceptance claimed.
* P-03: SEC-015 lock fix and deferred anchor emission tied to
  `after_commit`/`after_rollback` implemented in the execution branch.
* P-03 chain integrity: `14 passed` on PostgreSQL 16.
* P-03 cross-track compatibility: `14 passed`.
* HEAD fork reproduced; isolated chain fix green; no merge from mixed-provenance
  worktree prototypes.
* P-03 D1–D5 remain absent; package remains `NOT OWNER-APPROVED · NOT ACCEPTED`.

P-03-CONCURRENCY was run as a separate workstream with disposable PostgreSQL 16.
HEAD fork and fixed-chain harness results are technical validation evidence
only; the design package remains unapproved.

Evidence: `V4_P03_EXECUTION_REPORT_2026_11_24.md`.

## Part 8 — Architecture consolidation

Event duplication inventory was recorded despite source-document disagreement
over exact enumeration. The authoritative implementation is
`backend/app/eventing/authority.py`: transactional publish, ordered locked
drain, explicit acknowledgement, and durable inbox staging. Compatibility
adapters cover legacy `emit_to_outbox`, kernel `Event`, Health Core
`DomainEvent`, `SyncEvent`, and offline `SyncOperation`; no adapter implements
delivery semantics.

Migration `20261124_0003` adds canonical columns and a unique `event_id`.
Alembic reports a single head. PostgreSQL 16 evidence covers ordering,
idempotency, rollback, strict acknowledgement, retry/final failure, inbound
deduplication, adapter translation, and preservation of legacy zero-handler
acknowledgement. Migration round trip passed (`0` canonical columns at
`20261124_0002`, `9` at `20261124_0003`).

Status: `IMPLEMENTED AS ENGINEERING SEAM · NOT ACTIVATED AS SOLE RUNTIME BUS ·
NOT ACCEPTED`. Kernel and Health Core stacks retain historical behavior; dual
worker registration, ADR-J/J1, BK-017, C09 version bumps, and
`asyncapi.json` stub remain owner-gated or unchanged.

Evidence: `V4_EVENT_CONSOLIDATION_2026_11_24.md`.

## Part 9 — Frontend-v3 operationalization

No clinical or business page was activated. The bounded batch covers
`session.read`, `authorization.context.read`,
`authorization.permissions.read`, and `authorization.menu.read`. Exact typed
GET clients were added to the initialization read allowlist; all corresponding
writes remain blocked. Live sessions load reflected UX context; demo sessions
issue no `/authz/*` request; failures and malformed responses fail closed.
RoleGuard, RBAC, clinical gateway rollout, and server authorization remain
unchanged.

Verification: TypeScript `0`, `62/62` unit tests, `56/56` E2E tests, and both
governance verifiers `0`. The remaining 90 of 94 inventoried surfaces remain
non-operational or blocked.

Evidence: `V4_FRONTEND_OPERATIONALIZATION_2026_11_24.md`.

## Part 10 — Test evidence, failures, and classification

Final full backend regression:

```bash
cd /home/samertts/workspace/projects/gula-integration-v4-execution/backend
/home/samertts/.cache/gula-int-py312/bin/python -m pytest -q \
  > /tmp/opencode/v4_full_backend_tests_final.log 2>&1
echo "EXIT=$?" >> /tmp/opencode/v4_full_backend_tests_final.log
```

| Field | Value |
| --- | --- |
| Interpreter | `/home/samertts/.cache/gula-int-py312/bin/python` |
| Python | `3.12.13` |
| pytest | `9.2.0` |
| Collected | `5,307` |
| Result | `5,223 passed, 84 skipped, 213 warnings in 770.27s (0:12:50)` |
| Exit | `0` |
| Failures/errors | `0` / `0` |
| Preserved log | `AUDIT_EXECUTION_RECORDS/V4_WAVE_A_FULL_TEST_LOG_FINAL_EXECUTION_2026_11_24.txt` |
| SHA-256 | `411c0f1e40509d15a9ab274a63ea686f80f510e8faf38ac823a4ac0de4bd359b` |

Compared with the post-hardening Wave A run (`5,216 passed, 80 skipped, 213
warnings`), the final run includes the seven new event-consolidation tests and
the two new event-authority PostgreSQL tests (the latter skipped without their
DSN), plus the no-STUB guard additions already present in the suite. The 213
warnings are unchanged dependency/deprecation warnings; none was promoted to an
error. PostgreSQL-specific suites were separately executed with disposable
DSNs and were green, so the skips are not hidden failures.

Important preserved failures and classifications:

* Pre-fix full regression failure: stale patch target; fixed and rerun clean.
* Session leak in combined PostgreSQL guard: harness/session-scope defect;
  fixed and rerun with `75 passed, 1 warning`.
* Event adapter patch-seam failure: legacy monkeypatch attribute removed; seam
  restored and `26 passed`.
* PG event missing-commit and duplicate-assertion failures: harness errors;
  corrected and `4 passed`.
* Frontend `pnpm` install timeout: package-manager/environment failure; local
  `tsc` passed.
* Frontend E2E session bootstrap/desktop timeouts: harness timing; mocked
  deterministic bootstrap and `3 passed`.
* Frontend full E2E hardcoded browser path failure: pre-existing harness
  defect; rerun with installed Chromium path.
* One reports-spec 390px flake: isolated `9 passed`, full suite rerun `56 passed`.

No failure was hidden, relabeled as a pass, or deleted.

## Part 11 — Blockers and owner gates

Unresolved owner decisions and gates:

* P-03 D1–D5; P-03 design/acceptance authority.
* P-03-CONCURRENCY design approval.
* Public-health legal scope NV2-D08; policy-dependent PRG-05 behavior isolated.
* ADR-J/J1, BK-017, C09/C10/C11 version bumps.
* Event/offline runtime activation and ownership of authoritative stack.
* Server-side frontend rollout and contract registry expansion for clinical
  pages.
* G1–G12 gate evidence and owner acceptance.
* DR/PITR drill and reproducible load targets/report.
* Any change to `HOLD`, `production_ready_items = 0`, or Stable v1.0.0.

Helm template rendering was not validated because `helm` is unavailable.
`contracts/export/asyncapi.json` remains a 102-byte stub and was not promoted.

## Part 12 — Handoff and declaration boundary

Durable evidence is in `AUDIT_EXECUTION_RECORDS/`; executable changes are
uncommitted on `execution/gula-national-v4`. The post-change SHA-256 manifest
`V4_WAVE_A_POST_CHANGE_SHA256.txt` was regenerated and verified with `0`
failures; the exact entry count and digest are recorded in the final
preservation verification log. The immutable pre-change snapshots and original
repository remain preserved.

Final declaration: engineering execution completed to the bounded, evidence
level described above. No production deployment, owner acceptance, release
status, `PRODUCTION READY`, Stable v1.0.0, or G1–G12 pass is declared.
