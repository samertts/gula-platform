# V4 Execution Addendum — 2026-11-24

## Purpose

This addendum records reversible engineering changes made in the isolated
execution workspace after the V2 checkpoint. It does **not** edit, reinterpret,
or replace any V2 planning document or protected audit record. The V2 SHA-256
manifest therefore remains valid and independently checkable.

## Scope and authority

| Item | Value |
| --- | --- |
| Workspace | `/home/samertts/workspace/projects/gula-integration-v4-execution` |
| Branch | `execution/gula-national-v4` |
| Baseline HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Git state | All V4 changes remain uncommitted; no push, PR, merge, or deployment |
| Authority used | Reversible engineering implementation and test evidence only |
| Authority not used | Public-health legal scope, P-03 / P-03-CONCURRENCY approval, production readiness, Stable v1.0.0 declaration |

## Execution-only supersessions of stale V2 observations

The following V2 observations were accurate at checkpoint time but are no
longer accurate in this execution workspace. They are superseded **for this
workspace only** by the evidence listed here.

| V2 observation | Execution-workspace status | Evidence |
| --- | --- | --- |
| Eight generated capability CRUD routers returned static/empty responses and were not mounted | Replaced with real `capability_records`-backed CRUD, namespaced per capability and lab, authenticated/authorized, audited, with create/list/get/update/delete lifecycle tests | `backend/app/capabilities/_shared/`, eight `backend/app/capabilities/*/routes.py`, `backend/app/factory.py`, `backend/migrations/versions/20261124_0001_capability_crud_records.py`, `backend/migrations/versions/20261124_0002_capability_record_ownership.py`, `backend/tests/test_capability_crud.py`, `backend/tests/test_capability_crud_postgres.py` |
| `contracts/export/openapi.json` was a 98-byte stub | Regenerated from the live FastAPI application: OpenAPI 3.1, `info.version = 2.5.0`, 1,850 registered paths; CI now enforces exact path equality with `app.main.app` | `backend/app/contracts/generator.py`, `backend/app/contracts/routes.py`, `contracts/export/openapi.json`, `backend/tests/test_contract_export_live.py` |
| `/contracts/schemas/{module}` imported non-existent Pydantic DTOs for domain models | Imports corrected to the canonical SQLAlchemy models; `patient`, `lab-order`, `lab-result`, and `sample` now resolve | `backend/app/contracts/routes.py`, `backend/tests/test_contract_export_live.py` |
| `/metrics/prom` and `app.openapi()` observed through stale FastAPI route walking | Single Prometheus renderer retained; Helm scrape config now uses `/metrics/prom` and injects `METRICS_BEARER_TOKEN`; contract generation uses FastAPI-native resolved routes so lazy `_IncludedRouter` entries are included | `backend/app/routes/metrics.py`, `backend/app/services/metrics_service.py`, `helm/gula-platform/values.yaml`, `helm/gula-platform/templates/_helpers.tpl`, `helm/gula-platform/templates/backend/servicemonitor.yaml` |
| Initial execution copy inherited the source worktree `.git` pointer | Execution copy now has its own Git worktree metadata; source worktree HEAD restored to `integration/gula-unification-v1`; both staged name-status manifests remain `56c524d6ffe9872c3a3ac6eff8c8f203` | `AUDIT_EXECUTION_RECORDS/V4_EXECUTION_PROVENANCE_2026_11_24.md` |

## Explicitly unchanged blockers

* `P-03 / AUD-F03` remains a separate blocked package. The chain-lock fix and
  pre-commit anchor correction are implemented and cross-track tested in this
  execution workspace, but owner decisions D1–D5 remain absent and no package
  acceptance is claimed. See `V4_P03_EXECUTION_REPORT_2026_11_24.md`.
* `P-03-CONCURRENCY` independent validation was executed on disposable
  PostgreSQL 16 with HEAD fork evidence and fixed-implementation stress runs.
  It remains `NOT APPROVED · NOT ACCEPTED`; no production code was changed from
  that workstream and no cross-track merge or owner approval is claimed.
* `production_ready_items` remains `0`; `HOLD` remains in force.
* G1–G12 remain `NOT PASSED` until verifiable gate artifacts exist and an
  authorized owner accepts them.
* No production deployment, production data migration, live patient routing,
  PHI use, provider/AI/financial external call, or secret exposure occurred.

## Relationship to manifests

* `CHECKPOINT_GULA_NATIONAL_V2_2026_11_24_SHA256.txt` still verifies the
  unchanged V2 documents.
* `V4_EXECUTION_SOURCE_SNAPSHOT_SHA256.txt` remains the immutable pre-change
  snapshot of protected documents and audit records; it still verifies
  `23/23 OK` because none of those files were edited.
* `V4_WAVE_A_POST_CHANGE_SHA256.txt` is the new post-change evidence manifest
  covering the executable code, tests, CI wiring, and this addendum.

## Post-Wave-A additive engineering batches

After Wave A was technically closed, two further additive batches were
implemented without changing release status:

1. **Event consolidation seam** — one authoritative durable publish/drain core
   (`backend/app/eventing/authority.py`) with compatibility adapters for the
   legacy outbox, kernel bus, Health Core `DomainEvent`, `SyncEvent`, and
   offline `SyncOperation`. Migration `20261124_0003_canonical_event_fabric.py`
   adds canonical columns and a unique `event_id`; Alembic reports a single
   head. PostgreSQL 16 evidence covers ordering, idempotency, rollback, strict
   acknowledgement, retry, inbound deduplication, and legacy behavior. Status:
   `IMPLEMENTED AS ENGINEERING SEAM · NOT ACTIVATED · NOT ACCEPTED`. See
   `V4_EVENT_CONSOLIDATION_2026_11_24.md`.
2. **Frontend bootstrap operationalization** — `session.read` plus three
   registered `/authz/me*` reads have typed clients, exact allowlisted GETs,
   fail-closed live-only state, and unit/E2E evidence. All clinical and
   business surfaces remain unactivated. See
   `V4_FRONTEND_OPERATIONALIZATION_2026_11_24.md`.

These batches do not imply owner approval of ADR-J/J1, BK-017, C09 version
bumps, any rollout flag, Stable v1.0.0, or G1–G12.

This addendum is additive evidence, not owner authorization.
