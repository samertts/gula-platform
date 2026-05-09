# Phase 17-02 — Operational Runbooks

This file collects the **on-call runbooks** for sovereign operation. They
extend (do not replace) the existing `make health` / `make health-deep`
toolchain.

Each runbook follows the same shape:
**Detect → Triage → Stabilize → Recover → Post-incident.**

---

## RB-01 — Backend RED grade (`make health-deep` returns RED)

**Detect:** `_health_alert_loop` fires RED via `ALERT_WEBHOOK_URL`. Grafana
panel "GULA grade" shows RED for ≥ 2 evaluations.

**Triage:**
1. `make ps` — confirm container set is intact.
2. `make health-deep` — read latencies and memory.
3. `make logs-backend` — last 100 lines; look for `circuit_open`,
   `degraded_mode`, `pool_exhausted`.

**Stabilize:**
1. If pool exhausted: `make scale REPLICAS=$((current+2))` to add capacity.
2. If circuit open: do not force; wait the half-open window. If breaker is
   stuck > 10 minutes, see RB-02.
3. If memory pressure: rolling restart (`make restart`) — preserves audit
   chain, all reads/writes resume cleanly.

**Recover:** wait for grade to return to YELLOW then GREEN; verify with
`make health-deep`.

**Post-incident:** open a `RED-incident-<date>.md` with the timeline.

---

## RB-02 — Database circuit open > 10 minutes

**Detect:** `circuit_open` in logs persisting; `DegradedModeMiddleware`
rejecting writes.

**Triage:**
1. `make db-shell` — confirm `SELECT 1` works.
2. `pg_stat_activity` — look for blocking queries, long transactions.
3. Disk: `df -h` on the DB volume; `pg_stat_bgwriter` for IO health.

**Stabilize:**
- Kill long-running rogue queries with `pg_terminate_backend(pid)` only if
  they are clearly non-clinical.
- If DB is healthy but breaker stuck, restart backend (`make restart`).

**Recover:** breaker should close on next health check.

**Post-incident:** verify audit chain integrity for the degraded window
(`scripts/verify_audit_chain.py` — to be added in a future approved phase).

---

## RB-03 — Adapter circuit open

**Detect:** Per-adapter audit shows repeated `interop.adapter_unavailable`.

**Triage:**
1. Check peer system status with peer's status page or contact channel.
2. Inspect dead-letter queue size for the adapter.

**Stabilize:**
- DO NOT bypass the breaker. Clinical writes are unaffected by adapter state
  (CS-1).
- If peer requires us to retry from a specific point: increment the
  dead-letter replay cursor; replay from outbox.

**Recover:** breaker auto-closes after `half_open_after_s` and a successful
probe.

**Post-incident:** if peer was down > SLA, notify governance liaison.

---

## RB-04 — Tenant boundary breach suspected

**Detect:** Audit row showing a query on `lab_id=A` from a session bound to
`lab_id=B`. (Should never happen — TI-1 guard.)

**Triage (treat as security incident):**
1. Freeze the affected session: revoke JWT.
2. Snapshot logs for the user, the request_id, and the database
   contextvars.
3. Capture the offending row hash from the audit chain.

**Stabilize:**
- Disable the user account.
- Rotate any shared secret in scope.
- Engage security officer.

**Recover:** depends on root cause (code bug → fix; credential leak →
revocation).

**Post-incident:** mandatory IRB-Interop + security review. File the
incident in the regulator-readiness register.

---

## RB-05 — Audit chain hash mismatch

**Detect:** Hash-chain verifier flags a discrepancy.

**Triage (treat as severe):**
1. Halt writes (`make kill-switch-on`) — preserves the rest of the chain.
2. Snapshot the chain.
3. Identify the index where the hash first diverges.

**Stabilize:**
- Do not "repair" the chain. The chain is meant to break visibly.
- Capture the snapshot, run a forensic compare against Tier-2.

**Recover:**
- Promote Tier-2 (which has the verifiable chain) per RB-09.
- Quarantine Tier-1 chain for review.

**Post-incident:** mandatory regulator notification per governance policy.

---

## RB-06 — Migration failure on a national fleet member

**Detect:** Per-tenant migration dashboard shows a member stuck behind head
revision.

**Triage:**
1. Check member's `alembic current`.
2. `make logs-backend` on member — look for migration error.

**Stabilize:**
- Halt writes on the laggard.
- Apply migration manually with operator review.
- If migration is broken, do **not** modify the migration file (CLAUDE.md
  rule). File a new migration that fixes forward.

**Recover:** validate `make health-deep` on the laggard.

**Post-incident:** root-cause why the laggard fell behind; update the staged-rollout policy.

---

## RB-07 — Edge agent offline > 72h

**Detect:** Provincial edge stops syncing.

**Triage:**
1. Determine cause (connectivity, power, hardware).
2. Inspect local outbox size.
3. Inspect last successful sync hash.

**Stabilize:**
- Local clinical operations continue per Phase 23.
- Audit emissions buffer locally (signed, hash-chained).

**Recover (on reconnect):**
- Conflict-detectable sync runs; conflicts go to human review.
- Reconciliation events trigger Phase 19 governance.

**Post-incident:** if reconciliation flagged conflicts, run the merge
governance.

---

## RB-08 — Critical-result delivery delay

**Detect:** Alert: critical result not delivered within SLA.

**Triage:**
1. Verify clinical-write path is operational (`/health/deep`).
2. Check notification subsystem (`backend/app/notifications/`).
3. Check telco adapter, if SMS used.

**Stabilize:**
- Manual delivery via paper / phone fallback (Phase 23).
- Audit row records both the delay and the manual fallback.

**Recover:** restore notification path; re-deliver any unsent.

**Post-incident:** clinical-safety committee notification mandatory.

---

## RB-09 — Tier-1 → Tier-2 cutover

**Detect:** Tier-1 unrecoverable for the RTO window.

**Triage:**
1. Confirm Tier-1 is not partially writing (split-brain risk).
2. Confirm Tier-2 audit chain is current.

**Stabilize:**
- Fence Tier-1 (block its egress).
- Promote Tier-2 PostgreSQL.
- Run audit-chain merge protocol (DR-readiness §"Audit Chain Continuity").

**Recover:**
- DNS swap to Tier-2.
- Scale Tier-2 application replicas to production target.
- Validate `/health/deep` returns GREEN.

**Post-incident:** drill review; gap analysis; report to operations chief.

---

## RB-10 — Sovereign KMS unreachable

**Detect:** `ENCRYPTION_KEY` rotation cycle fails; `national_id` decrypt
errors.

**Triage:**
1. Verify KMS endpoint reachability.
2. Verify operator credentials.

**Stabilize:**
- Pause `national_id` writes (fail closed).
- Reads use cached keys for the cache TTL.
- Engage KMS provider on-call.

**Recover:** when KMS returns, decrypt resumes.

**Post-incident:** consider local key cache TTL adjustment; never extend
beyond regulatory tolerance.
