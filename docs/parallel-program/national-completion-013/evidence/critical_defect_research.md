# Critical defect research — read-only, main vs PR #261

Source: independent read-only research agent, 2026-11-20. All file contents were fetched with `gh api repos/samertts/gula-platform/contents/<path>?ref=<ref> --jq .content | base64 -d`; no local file was modified.

## PR #261 coverage matrix

| Defect | Fixed in PR #261? |
|---|---|
| `result.critical` ID contract (`lab_results.id` vs `lims_results.Result.id`) | No |
| Unauthenticated `/niam/persons/` POST + GET | Yes (mount-level guard) |
| gRPC gateway false success (`ImportError` → connected, echo payload) | No — byte-identical to main |
| Self-registration/MPI unverified NID → victim canonical ULID | No — byte-identical to main |
| Migration FK `String(26)` → `Integer` | Yes |
| `datetime.UTC` on Python 3.10 | Partially — device bridge only; backend shim and 3 migrations not |

## 1. Critical-result ID contract

- Producer `backend/app/routes/test_results.py:391-405` emits `"result_id": result.id` where `result` is `LabResult` (`lab_results` table).
- Second producer `backend/app/services/order_service.py:308-320` emits `RESULT_CRITICAL` with **no** `result_id`.
- Consumer `backend/app/lims/workflows.py:221-240` queries `app.lims.models.Result` (`lims_results`) using the incoming ID.
- HTTP entry `backend/app/lims/routes.py:2173-2182` passes the path ID directly.
- The two tables have independent integer primary keys and no cross-reference; a wrong-row alert or silent miss is possible.
- `contracts/events/catalog.json` and `docs/events/EVENT_CATALOG.md` document the ambiguous contract.

PR #261 changes only flag calculation/comments in `test_results.py`; the emitting payload is untouched and `lims/workflows.py` is absent.

Proposed repair: namespace the producer field (`lab_result_id`, `result_store="lab_results"`), remove bare `result_id`, require an explicit store in the consumer, and refuse ambiguous payloads.

## 2. Unauthenticated NIAM persons endpoints

Main `backend/app/identity/api/router.py:30-44` mounts `persons.router`, `sessions.router`, and `devices.router` **before** `_AUTH_REQUIRED` is defined and applied. Handlers in `persons.py` take only `db: AsyncSession = Depends(get_db)`. `GET /persons/{uuid}` returns `{"error":"not_found"}` with HTTP 200 on miss.

PR #261 patch applies `_AUTH_REQUIRED` to those three routers and changes the miss to HTTP 404. Proposed additional hardening: handler-level dependency as defense in depth, authenticated happy-path tests, and a mount ratchet test.

## 3. gRPC gateway false success

`backend/app/integration/gateway/grpc_gateway.py`:

```python
except ImportError:
    logger.warning("gRPC not installed — grpc gateway will use HTTP fallback")
    self._connected = True
    return True
...
response = await self._invoke_unary(...)
return GatewayResult(success=True, data=json.loads(response.decode()) if response else None, ...)
...
async def _invoke_unary(...):
    return payload
```

There is no HTTP fallback. `base.py:70-75` reports `healthy` when `_connected`. PR #261 does not change this file (SHA-256 identical).

Proposed repair: fail closed on `ImportError`, return failure from `send()` when no real channel exists, perform a real `grpc.aio.Channel.unary_unary` call, and never echo the request payload.

## 4. Self-registration / MPI identity bypass

- `backend/app/routes/register.py:59-67`: if a supplied NID hash matches an existing Citizen, the function returns that citizen's canonical ULID.
- New citizens are stored with `nid_verified=False`, but their `nid_hash` is still populated.
- `backend/app/services/mpi/resolver.py:226-236`: `nid_exact` fast path queries `Citizen.nid_hash` without checking `nid_verified`, sets score 1.0 and method `nid_exact`.
- `PUBLIC_SELF_REGISTRATION_ENABLED` defaults to false (`config.py:303-308`), but `/mpi/resolve` is reachable by authenticated lab users, so disabling public registration alone is not a fix.
- PR #261 does not change `register.py` or `resolver.py` (SHA-256 identical).

Proposed repair: never disclose an existing identity from an untrusted NID; do not store unverified NID in the authoritative `nid_hash`; gate `nid_exact` on `nid_verified is True`; require an explicit authenticated verification event before any verification claim becomes authoritative.

## 5. Migration defects

- `backend/migrations/versions/20260815_0023_drug_substitution.py:27-28` declares two `String(26)` FKs to `pharmacy_drug_catalog.id`, which is `Integer` from `20260716_0003`. PostgreSQL aborts with `DatatypeMismatch`; all later revisions are unreachable.
- `backend/app/_compat.py:8` is `UTC = UTC` (NameError on Python <3.11).
- `backend/migrations/versions/20260814_0005_role_permission_engine.py`, `...0006_security_audit_governance.py`, `...0007_clinical_gateway_scope.py` all contain `from datetime import UTC, datetime` at line 9.
- PR #261 fixes the FK and the device-bridge shim, but not the backend shim or the three backend migrations.

## Exact commands used (representative)

```bash
gh api repos/samertts/gula-platform --jq '{default_branch,full_name,updated_at}'
gh api repos/samertts/gula-platform/pulls/261 --jq '{number,title,state,head:.head.ref,base:.base.ref,merged_at,additions,deletions,changed_files}'
gh api --paginate repos/samertts/gula-platform/pulls/261/files --jq '.[] | {filename,status,additions,deletions,patch}'
gh api repos/samertts/gula-platform/contents/backend/app/integration/gateway/grpc_gateway.py?ref=main --jq .content | base64 -d | nl -ba
gh api repos/samertts/gula-platform/contents/backend/app/identity/api/router.py?ref=main --jq .content | base64 -d | nl -ba
gh api repos/samertts/gula-platform/contents/backend/app/identity/api/persons.py?ref=main --jq .content | base64 -d | nl -ba
gh api repos/samertts/gula-platform/contents/backend/app/_compat.py?ref=main --jq .content | base64 -d | nl -ba
gh api repos/samertts/gula-platform/contents/backend/migrations/versions/20260815_0023_drug_substitution.py?ref=main --jq .content | base64 -d | nl -ba
gh api repos/samertts/gula-platform/contents/backend/app/routes/test_results.py?ref=main --jq .content | base64 -d | nl -ba | sed -n '386,406p'
gh api repos/samertts/gula-platform/contents/backend/app/lims/workflows.py?ref=main --jq .content | base64 -d | nl -ba | sed -n '218,258p'
gh api repos/samertts/gula-platform/contents/backend/app/routes/register.py?ref=main --jq .content | base64 -d | nl -ba | sed -n '30,110p'
gh api repos/samertts/gula-platform/contents/backend/app/services/mpi/resolver.py?ref=main --jq .content | base64 -d | nl -ba | sed -n '205,245p'
for f in backend/app/routes/register.py backend/app/services/mpi/resolver.py backend/app/integration/gateway/grpc_gateway.py backend/app/_compat.py; do
  a=$(gh api "repos/samertts/gula-platform/contents/$f?ref=main" --jq .content | base64 -d | sha256sum | cut -d' ' -f1)
  b=$(gh api "repos/samertts/gula-platform/contents/$f?ref=claude/independent-audit-1" --jq .content | base64 -d | sha256sum | cut -d' ' -f1)
  printf '%s main=%s pr=%s\n' "$f" "$a" "$b"
done
```
