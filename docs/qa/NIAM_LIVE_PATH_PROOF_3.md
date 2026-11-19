# NIAM Live Path Proof 3 — Persistence Closure, Full Round Trip

Phase 10.6.6/10.6.7. Real app (`app.main.app`), real disposable
PostgreSQL 16, real disposable Redis, real HTTP requests via
`fastapi.testclient.TestClient` (real lifespan/`startup_guard`), real
JWTs. No service function called directly.

## What changed (closing the three blockers from NIAM_LIVE_PATH_PROOF_2.md)

**1A — Audit UUID.** `CanonicalAuditService.record()`
(`app/identity/services/canonical_audit.py`) now sets
`uuid=str(uuid.uuid4())` on every new `IdentityAuditEntry`, matching the
exact convention every sibling `*Service` call site in this codebase
already uses (`PlatformAuthorityService.grant`, `FederationService.*`,
`TrustFrameworkService.*` all set `uuid=str(uuid.uuid4())` explicitly —
`canonical_audit.py` was the one outlier, confirmed via `grep -rn "uuid="`
across every construction site). Regression test added:
`tests/identity/test_security_audit_phase9.py::test_canonical_audit_record_assigns_a_real_uuid`
— verified failing on the pre-fix code (`assert None is not None`) and
passing after.

**1B — Transaction ownership.** Traced the existing GULA convention:
`app/routes/admin.py` (and dozens of sibling legacy routes) mutate the
ORM object, stage an audit entry via a helper that only `add()`s/flushes,
then the **route handler itself** calls `db.commit()` once, after both
the mutation and its audit entry are staged — never the dependency
(`get_db()`/`get_niam_db()` never commit, by design, only rollback on
exception), never the service layer. This is the canonical, pre-existing
pattern — not invented here. Applied identically to the two NIAM routes:
`federation/routes.py::update_provider` and
`trust/routes.py::update_framework` now call `await db.commit()` once,
only on the success path (after the entity is found and updated; the
`not_found` early-return path never commits, since nothing was mutated).
Failure rollback needs no new code: `get_niam_db()`'s existing
`except Exception: await session.rollback(); raise` (from Phase 10.6.5)
already covers any exception raised before that commit line — proven
below with a real, induced failure. `app/database.py`/`get_db()` was
**not** touched.

Regression tests added (`tests/identity/test_platform_authority_phase10.py`):
`db.commit_count == 1` on both success paths;
`test_update_{provider,framework}_not_found_never_commits` (`commit_count == 0`
when nothing was mutated) — required a one-line addition
(`async def commit(self): ...`) to the existing `_FakeDb` test fake,
which lacked one entirely (that's what actually broke first, catching a
real gap in the fake's own completeness).

**1C — TrustFramework FK.** Traced `authority_id`'s real intended target:
a genuine `IdentityAuthority` model exists
(`app/identity/governance/models.py`, table `niam_gov_authorities`) — and
the **already-deployed, already-correct migration**
(`migrations/versions/20260723_0002_niam_completion_tables.py:312`)
creates `niam_trust_frameworks.authority_id` with
`sa.ForeignKey("niam_gov_authorities.id", ...)`. Only the **ORM model
string** (`app/identity/trust/models.py`, both occurrences) was stale,
referencing a nonexistent `niam_identity_authorities` — a model/migration
drift bug, not a missing table. **No migration added** — the schema was
already correct; only `trust/models.py`'s two FK strings were corrected to
match it exactly. Verified directly: importing the app and forcing mapper
configuration (`TrustFramework.__mapper__._sorted_tables`) now resolves
cleanly with zero exception, where it previously raised
`NoReferencedTableError`.

## STEP 1 GATE

| Check | Result |
|---|---|
| Audit UUID defect fixed | PASS — regression test fails pre-fix, passes post-fix |
| Transaction ownership explicit and proven | PASS — `commit_count` assertions, both success and not-found paths |
| TrustFramework FK resolved correctly | PASS — mapper resolves, no migration needed (schema was already right) |
| No security regression | PASS — `tests/identity/` 198 passed / 4 skipped (was 195/4 before this step; +3 new tests) |
| No unrelated source changes | PASS — only `canonical_audit.py`, `trust/models.py`, `federation/routes.py`, `trust/routes.py`, 2 test files touched |
| NIAM async boundary intact | PASS — `niam_async_db.py` untouched |

## STEP 2 — full live-path proof (real PostgreSQL + Redis + HTTP)

Same seeding method as `NIAM_LIVE_PATH_PROOF_2.md` (two real
accounts/identities/sessions, one with `federation_manage` +
`trust_manage` granted, one without; real JWTs).

### Request matrix

| Case | Federation | Trust |
|---|---|---|
| No token | **401** | **401** |
| Wrong/missing capability | **403** | **403** |
| Correct capability | **200** | **200** |

### Fresh-session persistence (separate DB session, after the request)

```json
"provider": {
  "name_en": "Updated Provider Name Again",      // both updates applied, in order
  "issuer_url": "https://issuer.example",         // protected field: unchanged
  "client_secret_encrypted": null,                // protected field: unchanged (attacker-supplied value never persisted)
  "provider_id_unchanged": true                   // immutable field: unchanged
},
"framework": {
  "name_en": "Updated Framework Name",
  "status": "draft",                              // protected field: unchanged (attempted "active" rejected)
  "framework_id_unchanged": true                  // immutable field: unchanged
}
```

Field-boundary enforcement (Phase 10's own allow-list design) is now
proven not just at the unit-test level but at the **real, persisted,
live-HTTP** level: every attacker-supplied protected/immutable field in
the request body was silently ignored, and only allow-listed fields
reached the database.

### Audit evidence (fresh session)

- Federation: **2** `FEDERATED_PROVIDER_UPDATED` entries — exactly
  matching the 2 successful federation calls made (no duplicates, none
  missing). Each entry: correct `actor_id` (the granted account's real
  id), correct `target_id` (the provider's real id), a real UUID
  (confirming 1A's fix persists correctly against a real NOT-NULL
  constraint).
- Trust: **1** `TRUST_FRAMEWORK_UPDATED` entry, same correctness
  properties, matching the single successful trust call.

### Rollback proof (real, induced failure)

A real exception was induced *after* the service had already staged both
the business mutation and the audit entry via `flush()`, but *before* the
route's `db.commit()` — `unittest.mock.patch.object(CanonicalAuditService,
"_hash", side_effect=RuntimeError(...))` (this process only; no source
file touched; same technique Phase 10's own negative-gate test already
established as this codebase's convention for proving a real code path is
load-bearing without editing source).

| Check | Result |
|---|---|
| Request status | **500** |
| Provider `name_en` before vs. after the failed call | unchanged (`"Updated Provider Name Again"` both times — the attempted `"SHOULD NEVER PERSIST"` never persisted) |
| Federation audit count before vs. after | unchanged (2 both times — no orphan/partial audit row survived) |

**No partial state remains.** The pre-existing `get_niam_db()` rollback
path (Phase 10.6.5) correctly discards the entire in-flight transaction —
both the business mutation and its audit entry — the moment any exception
occurs before commit.

## Required boundary — fully traversed

```
HTTP → Authentication → Async DB → NiamActor → Platform Authority →
Authorization → Service → Audit → Commit → Fresh-session persistence
```

Every stage above is now empirically, individually confirmed reached and
correct, for both routes.

## RESULT

**VERIFIED**

## Files changed (this step)

| File | Change |
|---|---|
| `backend/app/identity/services/canonical_audit.py` | `record()` now sets `uuid=str(uuid.uuid4())` |
| `backend/app/identity/trust/models.py` | 2 FK strings corrected: `niam_identity_authorities` → `niam_gov_authorities` |
| `backend/app/identity/federation/routes.py` | `update_provider`: `await db.commit()` added on the success path |
| `backend/app/identity/trust/routes.py` | `update_framework`: `await db.commit()` added on the success path |
| `backend/tests/identity/test_security_audit_phase9.py` | +1 regression test, +1 import |
| `backend/tests/identity/test_platform_authority_phase10.py` | `_FakeDb.commit()` added; +2 `commit_count` assertions; +2 not-found tests |

No migration. No schema change (the deployed schema was already
correct — only the ORM model string drifted from it). No other
NIAM route touched. `app/database.py` untouched.

## Tests executed

| Check | Result |
|---|---|
| `python -m py_compile` (4 changed source files) | PASS |
| `ruff check` (4 source + 2 test files) | PASS (0 findings) |
| `pytest tests/identity/` (202 tests) | PASS — 198 passed, 4 skipped |
| Live HTTP proof (both routes, 3 auth scenarios + persistence + audit + rollback) | VERIFIED, see above |

## Resource usage

One disposable PostgreSQL 16 + one disposable Redis instance, one real
app boot, ~9 real HTTP requests, both torn down after. No production
data. No external network calls.
