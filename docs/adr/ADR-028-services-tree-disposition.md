# ADR-028 — The `services/` tree is DORMANT, and has no caller identity

**Status:** Accepted — classified DORMANT 2026-09-19
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

## The decision, taken

**`services/` is DORMANT.** Not live, not dead, and the distinction carries
work either way.

It is not DEAD, because `docker-compose.full.yml` — a deployment target
CLAUDE.md documents — builds all eight services from source and points them at
the production database. Code that a documented target will start is not dead
code, whatever its state of repair.

It is not LIVE either, and the evidence for that is a conjunction, not one
observation:

| Question | Answer |
|---|---|
| Does CI build its images? | No. CLAUDE.md describes a `build-and-push` job publishing "backend + 7 microservices" to GHCR; `ci.yml` has no such job, only the vestigial `REGISTRY: ghcr.io` it used to read. |
| Do any tests cover it? | None, outside `device_bridge`. |
| Does anything import it? | No. (`backend/services/identity_engine/` is a different tree; `app/engineering/crud/generator.py:217` is a codegen template string.) |
| Does any deploy script or k8s manifest name these services? | No. |
| Is it the source of truth for its own logic? | No — CLAUDE.md states the monolith is, and that `services/` "is not the primary deployment target". |
| Is it reachable if started? | Yes, but only on loopback now, and it authenticates nothing (NR-142). |

So: startable, and maintained by nothing.

**`services/device_bridge/` is explicitly excluded from this classification and
is LIVE.** It has its own `docker-compose.yml` profile, thirteen test modules,
and does real ASTM/HL7 instrument work. It is the one part of this tree that is
neither dormant nor unauthenticated — its routes carry an `_auth` dependency.

### What DORMANT obliges, and what it does not

Per the programme's own rule for this state: document it and move on. So:

- **Nothing is deleted.** Retirement stays available and is not taken here.
- **The containment stands.** Loopback binding (NR-142) and the guard in
  `tests/integration/test_deployment_exposure.py` keep a dormant,
  unauthenticated surface off every interface.
- **NR-142 stays OPEN at P0** on the authorization defect itself. Dormant is a
  statement about maintenance, not about safety: `GET /patients` still returns
  every patient row across every tenant to anyone who reaches it.
- **The precondition for retirement is recorded, not met.** Removing the eight
  services from `docker-compose.full.yml` is safe and reversible in git, but it
  deletes a documented deployment target, and that is a person's call rather
  than a consequence of this classification.

### If it is ever woken

`nhop-platform/app/core/trusted_context.py` is the template: one dependency,
applied once to the router, failing closed until a real identity provider is
federated. Waking this tree without that is waking the P0 with it.

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
