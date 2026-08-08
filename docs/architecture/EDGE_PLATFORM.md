# GULA Edge AI Platform

> **Goal:** Transform user devices into trusted, sandboxed nodes for local
> AI inference and distributed processing — converting GULA from a traditional
> client/server system into a **Managed Distributed Edge AI Platform**.

This document is the implementation guide for the Edge Computing & Local AI
Utilization Directive. The directive itself is canonical; this file maps each
section to the code that fulfills it.

## Quick map (directive section → code)

| Directive | Code |
|-----------|------|
| §3 Edge Node Architecture | `backend/app/edge/` + `edge_agent/gula_edge_agent/` |
| §4 Edge Agent Core        | `edge_agent/gula_edge_agent/agent.py` |
| §5 Control Plane          | `backend/app/routes/edge.py`, `backend/app/edge/registry.py` |
| §6 Device Identity & Trust | `backend/app/edge/identity.py`, `backend/app/edge/trust.py` |
| §7 Task Execution System  | `backend/app/edge/scheduler.py` |
| §8 Task Routing Logic     | `_device_matches_task()` in `scheduler.py` |
| §9 AI Runtime Layer       | `edge_agent/gula_edge_agent/runtime.py` |
| §10 Resource Governance   | `EdgePolicy` model + `agent.py::_can_take_work` |
| §11 Idle-aware Execution  | `agent.py` battery / cpu cap checks |
| §12 Security Model        | HMAC task signing + agent-token + sandbox allowlist |
| §13 Data Privacy          | `privacy_level` on `EdgeTask`, no raw PHI in payloads |
| §14 Sync Engine           | offline queue (planned, see "Roadmap") |
| §15 Local Storage         | `state.py` Fernet-encrypted state |
| §16 Failure Handling      | `scheduler.fail_task` retry/backoff + `sweep_stale` reaper |
| §17 Observability         | `EdgeTelemetry` + `EdgeEvent` + `/edge/fleet/summary` |
| §18 Device Role Modes     | `role_mode` column on `EdgeDevice` |
| §19 Update Mechanism      | `EdgeModel.rollout_pct` + canary bucketing in `governance.py` |
| §20 Feature Flags         | `EdgePolicy.kill_switch` + `EDGE_KILL_SWITCH` env |
| §21 Multi-Tenancy         | every table tenant-scoped by `lab_id` |
| §22 Quotas & Rate Limits  | `rate_limit_user`/`rate_limit_public` on every endpoint |
| §23 Cost Accounting       | telemetry samples carry `task_completed_total` etc. |
| §24 Model Governance      | `EdgeModel` lifecycle: draft→canary→active→retired |
| §25 Disaster Recovery     | rides on existing GULA backup (`make backup`) |
| §26 Compliance Layer      | `EdgeEvent` audit trail, separate from `audit_logs` |
| §27 System Safety Rules   | command allowlist `ALLOWED_TASK_KINDS` |
| §35 Trust Scoring         | `trust.py` deltas + auto-quarantine |

## Architecture

```
┌────────────────────────────┐
│  Operator (lab admin)      │
│  POST /edge/devices/...    │
│  POST /edge/tasks          │
└──────────────┬─────────────┘
               │ JWT (lab user)
               ▼
┌─────────────────────────────────────────────────────────────┐
│             FastAPI control plane (gula-backend)            │
│   routes/edge.py  ──►  edge/{registry,scheduler,trust,…}    │
│        │                          │                          │
│        ▼                          ▼                          │
│   PostgreSQL tables: edge_devices, edge_tasks,              │
│   edge_telemetry, edge_models, edge_policies, edge_events    │
└──────────────┬─────────────────────┬────────────────────────┘
               │ heartbeat (agent_token)
               │                     ▲
               ▼                     │ result
┌─────────────────────────────────────────────────────────────┐
│        Edge Agent (`edge_agent/gula_edge_agent/`)           │
│  agent.py — heartbeat loop, sandbox, runtime adapter         │
│   ▼                                                          │
│  Ollama / GGUF locally (or "noop" diagnostic backend)        │
└─────────────────────────────────────────────────────────────┘
```

## Lifecycle of a task

1. **Submit.** Operator `POST /edge/tasks` with `{kind, payload, priority,
   privacy_level}`. Server validates kind against `ALLOWED_TASK_KINDS`,
   checks the policy `allow_kinds`/`deny_kinds`, signs payload with HMAC,
   row enters `pending`.
2. **Claim.** Agent's heartbeat hits `POST /edge/agent/heartbeat`. The
   scheduler runs `claim_next_task(device)` which locks one row with
   `SELECT ... FOR UPDATE SKIP LOCKED`, applies routing filters
   (lab match, capabilities, trust gate, privacy gate, concurrency cap),
   flips status to `dispatched`, and returns it.
3. **Execute.** Agent runs the task in its `Runtime` with a wallclock cap
   of `timeout_s`. Sandbox checks: kind is in local allowlist, payload
   under `MAX_PAYLOAD_BYTES`, no shell.
4. **Report.** `POST /edge/agent/tasks/{uid}/result` carries `success` and
   either `result` or `error`. Trust score adjusts, status flips to
   `completed` or (after `max_attempts` hits) `failed`.
5. **Reap.** A background loop (`edge_maintenance_loop`) requeues or fails
   anything stuck in `dispatched` past `timeout_s + EDGE_DISPATCH_GRACE_S`
   and marks devices that haven't heartbeated as `offline`.

## Configuration

All knobs live in `.env` — see `.env.example` for the full list. Hot ones:

| Var | Default | Meaning |
|-----|---------|---------|
| `EDGE_ENABLED` | `true` | Master enable for the entire edge plane |
| `EDGE_KILL_SWITCH` | `false` | Global kill switch; trumps per-tenant policy |
| `EDGE_HEARTBEAT_TIMEOUT_S` | `180` | Mark device offline after this much silence |
| `EDGE_TELEMETRY_RETENTION_DAYS` | `14` | Telemetry row TTL |
| `EDGE_TRUST_QUARANTINE_BELOW` | `20.0` | Auto-quarantine when trust drops below |
| `EDGE_TASK_SIGNING_KEY` | unset (falls back to `SECRET_KEY`) | HMAC key |
| `EDGE_TASK_SIGNING_KEY_PREV` | unset | Old HMAC key (for rotation) |

## Operator playbook

```bash
# Inspect fleet health for the current lab
curl -H "Authorization: Bearer $JWT" \
     https://gula-platform.org/edge/fleet/summary

# Submit a translation task
curl -H "Authorization: Bearer $JWT" -X POST \
     -d '{"kind":"ai.translate","payload":{"text":"Hello","target":"ar"}}' \
     https://gula-platform.org/edge/tasks

# Quarantine a misbehaving device
curl -H "Authorization: Bearer $JWT" -X POST \
     "https://gula-platform.org/edge/devices/EDG.../quarantine?reason=anomaly"

# Activate the kill switch for one lab (requires admin)
curl -H "Authorization: Bearer $JWT" -X PUT \
     -d '{"kill_switch": true}' \
     https://gula-platform.org/edge/policy
```

## Roadmap (post-MVP)

* **Sync engine** for offline-first operation (Section 14) — outbox-on-device
  with conflict-resolution policy.
* **Hardware attestation** (TPM/SecureEnclave) — currently the agent ships an
  attestation_blob; verification is informational only.
* **JWT-signed tasks** instead of HMAC — agent-side public-key verification.
* **Auto-update** binary delivery (Section 19) — currently `agent.self_update`
  is a hook, not an implementation.
* **GPU scheduling** — the scheduler honors `gpu_pct` telemetry but doesn't
  yet route GPU-only kinds.
