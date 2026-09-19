# ADR-028 — The `services/` tree has no caller identity; a decision is required before it can have one

**Status:** Proposed — decision required
**Date:** 2026-09-19
**Supersedes:** nothing
**Related:** NR-142, NR-127 (`nhop-platform/app/core/trusted_context.py`), NR-128/F2,
ADR-002 (monolith-first), ADR-003 (multi-tenant isolation),
`tests/integration/test_deployment_exposure.py`

## Context

The NR-139 identity sweep covered `backend/app` and stopped there. NR-142
extended it to the trees it had not reached: `services/`, `nhop-platform/` and
`edge_agent/`. Two of the three came back clean:

- **`edge_agent/`** serves no HTTP surface at all — no router, no app. Nothing
  to classify.
- **`nhop-platform/`** is fail-closed at the perimeter. `api/v1/__init__.py`
  attaches `require_trusted_context` to the whole `/v1` router, and that
  dependency raises 503 unconditionally until a real identity provider is
  federated (NR-127). Measured, not assumed: every route on the mounted
  surface — including the paths that raise 404 or 409 before any handler code
  reads an actor — returns 503 to a caller with no context. There is no
  pre-context existence oracle.

The third did not.

## The finding (NR-142)

`services/lab`, `services/patient`, `services/order`, `services/result`,
`services/sample`, `services/notification`, `services/ai` and
`services/autonomous_manager` perform **no authentication and no authorization
of any kind**. The string `Authorization` appears in each of them exactly once,
in `CORSMiddleware(allow_headers=[...])`, where it grants a browser permission
to send a header that nothing then reads.

They are not inert. `docker-compose.full.yml` — a deployment target CLAUDE.md
documents — builds all eight, points them at `labdb` through pgbouncer (the
database the monolith serves), and published them on **every interface of the
host**: `"8001:8000"` … `"8006:8000"`, `"8010:8000"`, `"9000:9000"`. They are
not behind the gateway; `config/nginx/conf.d/api.conf` proxies to
`gula_backend` and `gula_frontend` and to nothing else. The published port was
the whole perimeter.

The sharpest instance:

```python
@app.get("/patients", response_model=list[PatientResponse])
async def list_patients(lab_id: int | None = None, skip: int = 0, limit: int = 100):
    ...
    if lab_id:
        rows = await conn.fetch("... WHERE lab_id = $1 ...", lab_id, limit, skip)
    else:
        rows = await conn.fetch("... FROM patients ORDER BY created_at DESC ...")
```

The tenant is a query parameter, and omitting it removes the filter rather than
denying the request. That is both halves of the forbidden pattern in one
signature: a client-authored tenant treated as a security fact, and an
object-level authorization gap behind it. It violates security invariant 1
(*all patient-data queries MUST filter by `lab_id = current_user.lab_id`*) and
invariant 2 (*all mutations MUST write to the audit log*) — `POST /patients`
publishes a RabbitMQ event and writes no audit row.

`POST /restart/{service_name}` on the autonomous manager is a smaller case and
is stated precisely rather than dramatically: `service_name` is checked against
an allow-list, so there is no command injection, and the compose file removes
the Docker socket, so `docker restart` inside the container has nothing to talk
to and the call returns `{"restarted": false}`. What an unauthenticated caller
gets is the service inventory and health map from `GET /status`.

## What was done now

The binding, and only the binding. Every service this repository builds now
publishes on `127.0.0.1`, matching `api-gateway` in the same file and
`gula-demo-api` in `docker-compose.demo.yml`, and enforced going forward by
`tests/integration/test_deployment_exposure.py`, which keys on `build:` so a
service added later is covered without anyone remembering this ADR.

This changes nothing for a legitimate caller. Inter-service traffic resolves
over the `gula-net` Docker network by service name (`http://patient-service:8000`),
never through a published host port, and `tests/load/gula-load-test.js` runs on
the host, where loopback still answers.

It is containment. It narrows *who can reach* an unauthenticated clinical
surface. It does not give that surface a caller, and it must not be recorded as
having fixed the authorization defect.

## The decision required

**Is the `services/` tree a live deployment surface, or is it dead code kept
for a decomposition that has not happened?**

Nothing in the repository answers this, and the two answers demand opposite
work:

| | If **live** | If **dead** |
|---|---|---|
| Control | Federate GULA identity into the tree and derive `lab_id` from it — never from the query string | Remove the eight services from `docker-compose.full.yml`; nothing else references them |
| Precedent | `nhop-platform/app/core/trusted_context.py` is the shape to copy: one dependency, applied once to the router, failing closed until federation lands | ADR-002 already says the monolith is the source of truth |
| Cost | Real: eight services, eight Dockerfiles, and a token-verification path that does not yet exist outside `backend/app/security/` | Small, but irreversible-feeling, and it deletes a documented deployment target |

The evidence leans toward **dead**: CLAUDE.md states the monolith is the source
of truth for business logic and that `services/` "is not the primary deployment
target"; the tree has **zero tests** outside `device_bridge`; **no workflow builds
its images** — CLAUDE.md describes a `build-and-push` job publishing "backend +
7 microservices" to GHCR, and `ci.yml` has no such job, only the vestigial
`REGISTRY: ghcr.io` env var it used to read, so the images these compose
entries would run are not produced by CI at all; `backend/gateway/api_gateway.py` — the only other thing
that knows these ports — is imported by nothing and maps `patients` to 8001 and
`labs` to 8002 while the compose file assigns them the other way round, a
contradiction that could only survive in code no one runs.

That is an argument, not an authority to act on. Retiring a documented
deployment target is exactly the kind of change that needs a person, and
"abruptly deleting legacy" is out of scope by instruction. So the finding is
contained, the decision is recorded here, and the work resumes elsewhere.

## Consequences

- An unauthenticated clinical surface is no longer reachable from off-host in
  the `full` deployment. It remains reachable from on-host, and from any
  container on `gula-net` — the control is still absent.
- NR-142 stays **open at P0** until this decision is taken. The loopback
  binding is not a fix and the guard test's docstring says so.
- If the answer is *live*, `nhop-platform`'s trusted-context module is the
  template, and NR-127's unresolved half (federating GULA identity) becomes the
  blocking dependency for both services at once.

## What this ADR does not decide

Third-party services in the same compose file also publish on every interface —
`vault` on 8200, `keycloak` on 8081, `clickhouse` on 8123, `kafka` on 9092,
`minio`, `prometheus`, `grafana`, `loki`, `jaeger`. That is a real exposure and
a separate class: none of it is code this repository writes, several have
documented access workflows (CLAUDE.md describes reaching monitoring over an
SSH tunnel, which loopback binding would in fact serve correctly), and changing
them is not this sweep's finding. Recorded as NR-143, unfixed.
