# P-03 / AUD-F03 — owner decisions required (D1–D5)

Generated 2026-11-24 UTC. **Additive document.** Does not modify the approved
`P-03_DECISION_PACKET_REV3.md`, the owner register, any prior SHA manifest, any
source file, or any release status.

**Status of this document:** `PREPARED FOR OWNER` — it *recommends*; it does not
decide. No D1–D5 selection is recorded here. P-03 remains
`PREPARED ONLY · NOT IMPLEMENTED`. Owner directive §9 records package-level
`P-03 / AUD-F03: AUTHORIZED` but no D1–D5 sub-decisions, so implementation scope
is undefined until the owner records them explicitly.

## 0. Decision gate summary

| ID | Issue | Options in REV3 §8 | Recommendation in this document | Blocks implementation? |
|---|---|---|---|---|
| D1 | Which control-plane boundaries are audited | (a) B1+B2; (b) B1+B2+B3; (c) B1+B2+B3+B4; (d) defer; (e) B1+B2+fleet deploy | **(a)**, with B3/B4/fleet deploy deferred to separate packets | YES |
| D2 | Who is the audited actor | (a) principal only; (b) principal + defined service identity; (c) defer | **(a)** | YES |
| D3 | Behavior on audit-write failure | (a) fail closed; (b) durable outbox design | **(a)** with explicit availability acceptance | YES |
| D4 | Idempotency / duplicate events | (a) at-most-once under test + disclosure; (b) dedupe/schema design | **(a)** for this packet; (b) separately | YES |
| D5 | Audit-read route | (a) re-point to canonical rows when B4 selected; (b) leave unchanged | **(b)** if D1=(a); **(a)** only if owner selects B4 | YES if B4 selected |
| D6 | Staging/commit scope | decided separately | no recommendation; no commit authority | YES for commit only |

---

## D1 — Boundaries

### Issue addressed
Decides which of the four HEAD-confirmed unaudited boundaries receive canonical
`log_action` writes: B1 approval (`control_plane/routes.py:295-298`), B2 release
deploy (`:291-306` only), B3 secret access (`config/secrets.py:29-57`), B4 audit
read (`:309-327`), plus the separate fleet deploy surface (`:211-226`) available
only under option (e).

### Available options
(a) B1+B2 · (b) B1+B2+B3 · (c) B1+B2+B3+B4 · (d) defer ·
(e) B1+B2 + `POST /control-plane/fleet/deploy`.

### Safest / most scalable choice — **(a) B1+B2 only**
It closes the two state-changing release decisions that currently use a
body-supplied actor and contain a swallowed exception, in the smallest verifiable
change-set. It establishes the reusable pattern — `Depends(get_db)` → canonical
writer committed before in-memory mutation → principal actor → fail closed — that
later packets can extend. Deferring B3 avoids coupling secret retrieval to audit-DB
availability; deferring B4 avoids adding a new canonical query helper in the same
change-set; deferring (e) avoids a second execution engine (`ProvisioningEngine`)
with different failure semantics.

### Audit-chain integrity impact
Each selected boundary produces exactly one canonical chained row via
`log_action`; the stale shared writer is not used. Unselected boundaries remain
unaudited and must be explicitly disclosed — especially fleet deploy under (a).
B4 is a read path and adds no rows.

### Performance / availability impact
One additional INSERT and chain-hash computation per approval/deploy; no new
infrastructure. Under (b) or (c), secret access and audit reads also gain a DB
dependency; with D3=(a) a DB outage would block secret retrieval — a material
platform-wide availability risk that warrants its own design.

### Risks / side effects
Choosing (a) leaves secret access, audit read and fleet deploy unaudited. Choosing
(b)/(c) widens the blast radius and the acceptance matrix. Choosing (e) requires
auditing a second engine whose exception-swallow behavior differs from
`ReleaseManager`. No option changes deployment behavior itself.

### Acceptance tests required
T1 (approval), T2 (deploy), T5 (missing principal), T6 (body spoofing), T7 (audit
failure), T8 (retry), T10 (rollback) on PostgreSQL 16 with synthetic data. T3/T4
apply only if B3/B4 are selected; a fleet-deploy-specific PG test is required only
under (e). All on `GULA_P03_PG_DSN`-style disposable PG, never SQLite.

---

## D2 — Actor policy

### Issue addressed
HEAD takes `user` from the request body (`routes.py:294`) and never compares it
to the authenticated principal from `get_current_user` — auditable actor identity
is forgeable.

### Available options
(a) authenticated human principal only (packet-recommended);
(b) principal plus an explicitly defined authenticated service identity (requires
its own design); (c) defer. Request-body actors are rejected in every option.

### Safest / most scalable choice — **(a)**
The authoritative principal (`.id`, `.role`, `.lab_id`) already exists in the
dependency graph. Option (b) requires defining a service identity and its
`user_role` mapping — a separate design package, not an invention to be made
inside P-03.

### Audit-chain integrity impact
Actor fields participate in the canonical chain-hash record. Principal-only
attribution makes the hash deterministic and authentic; accepting a body actor
would write a forged identity into an otherwise valid hash chain.

### Performance / availability impact
Negligible — no extra query; the principal is resolved by the existing dependency.
Automated/service callers, if any ever exist, would be rejected (401/403) until a
service identity is designed; HEAD evidence shows no service principal concept on
these routes.

### Risks / side effects
Break-glass or automation flows that currently pass a body actor would stop
working. The attempted spoofed value should be omitted from `details` by default;
recording `details.attempted_actor` requires a separate explicit owner selection.

### Acceptance tests required
T6 with a body actor differing from the principal (assert principal fields in the
row, no spoofed value), T5 missing principal (401/403, zero rows, no state
mutation), and invalid-actor paths from `dependencies.py:65-104` (unknown/inactive/
unverified, permission-version mismatch, deactivated lab).

---

## D3 — Failure policy

### Issue addressed
What must happen when the canonical audit write fails.

### Available options
(a) fail closed; (b) durable outbox design package (not authorized in this packet).

### Safest / most scalable choice — **(a)** for this packet; **(b)** separately
Fail closed guarantees no unaudited state transition. A durable outbox preserves
availability but requires new persistence, replay, dedupe and monitoring design —
a separate package.

### Audit-chain integrity impact
(a) preserves a strict invariant: no in-memory release mutation without a
committed canonical row. (b) introduces eventual-consistency windows and duplicate
risk that the current schema cannot dedupe.

### Performance / availability impact
Material: with (a), approval/deploy fails when the audit DB is unavailable. The
owner must explicitly accept this availability loss. No new latency beyond the
audit INSERT; no queue infrastructure.

### Risks / side effects
Client retries during an outage can produce duplicate attempts (see D4). The
pre-commit anchor side effect in `log_action` means a later rollback may leave an
anchor line with no persisted row — a pre-existing residual to disclose, not
introduce. Cross-resource atomicity between the DB row and the in-memory dict is
impossible and must remain disclosed.

### Acceptance tests required
T7 (forced writer failure → rollback, no state mutation, non-2xx), T10 (in-memory
status unchanged), plus a test that no audit row and no anchor side effect is
emitted on the rejected path where practical; chain verification after successful
writes only.

---

## D4 — Idempotency

### Issue addressed
`log_action` has no correlation/dedupe parameter and HEAD has no idempotency key;
exactly-once semantics cannot be guaranteed.

### Available options
(a) accept at-most-once under test with duplicate-risk disclosure (packet-
recommended); (b) separate dedupe/schema design package.

### Safest / most scalable choice — **(a)** for P-03; **(b)** for production-grade
exactly-once
(a) introduces no schema change and keeps the packet narrow. (b) requires a unique
constraint/correlation key and a replay policy — legitimate but a separate design
and migration decision. Note that P-03-CONCURRENCY may also need correlation IDs
for retries; that is designed separately, not smuggled into P-03.

### Audit-chain integrity impact
Duplicate rows, if they occur, are individually valid chained rows; the chain hash
remains verifiable. The defect is semantically duplicated audit events, not a
broken chain.

### Performance / availability impact
(a) adds no lookup or index cost. (b) adds a uniqueness lookup and a migration.

### Risks / side effects
Under retry, more than one audit row may exist for one logical operation;
downstream consumers must tolerate this. No silent dedupe may be claimed.

### Acceptance tests required
T8: repeat the same operation and assert at most one canonical row *under test*,
with the duplicate risk explicitly disclosed; verify the chain is still valid if a
duplicate is deliberately injected.

---

## D5 — Audit-read route

### Issue addressed
`GET /control-plane/audit-log` currently returns an empty response because
`sdk.audit is None`, or uses a stale shared helper whose columns
(`entity_type`, `entity_id`, `previous_hash`, `timestamp`) do not exist on the
canonical `AuditLog` model.

### Available options
(a) re-point the route to a new canonical read helper when B4 is selected;
(b) leave unchanged and accept the inert-route risk.

### Safest / most scalable choice
- If D1=(a)/(b)/(e) — B4 not selected: **(b)**, with the inert route disclosed.
  Selecting (a) without B4 expands scope without a corresponding audit need.
- If D1=(c) — B4 selected: **(a)** is required; leaving the route inert would mean
  the oversight surface still cannot display the canonical rows it is meant to
  expose.

### Audit-chain integrity impact
Read-only; adds no rows. (a) makes oversight operate on canonical chain data,
including `chain_hash`; (b) leaves a misleading "successful empty" response.

### Performance / availability impact
(a) requires a new canonical query helper in `audit_service.py` with bounded
filters and pagination to avoid unbounded scans; no secret value may appear in
responses. (b) has zero cost but zero utility.

### Risks / side effects
A new query helper must map canonical columns correctly and must not reuse the
stale shared writer path. No schema change is authorized.

### Acceptance tests required
T4 only if B4/D5=(a) is selected: canonical rows returned with filters, no secret
values, chain data exposed, no call to the stale shared helper. With D5=(b), record
the inert-route risk in the residual register.

---

## Combined decision text (owner to complete)

> "I authorize package P-03 / AUD-F03 REVISION 3, baselined at HEAD
> `2206654dc713ea2de8c564a3207dfe05fde23549`, exactly as scoped in
> `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV3.md`, with D1=__, D2=__,
> D3=__, D4=__, D5=__. Request-body actors and secret values are never written to
> audit details. I accept the fail-closed availability loss if I select D3=(a),
> and I understand `POST /control-plane/fleet/deploy` remains unaudited unless I
> select D1=(e). I understand T9/concurrent chain integrity is deferred to
> `P-03-CONCURRENCY`. This decision does not authorize a commit, staging change,
> push, Draft PR, merge, release, deployment, `PRODUCTION READY`, or any change to
> HOLD or `production_ready_items = 0`. D6 is decided separately."

Alternative: "P-03 is deferred; keep AUD-F03 open and this packet prepared."

## Status statement

No owner decision is invented or recorded here. No P-03 code was written or run.
**HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED ·
PRODUCTION READY NOT AUTHORIZED.**
