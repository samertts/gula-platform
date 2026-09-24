# Production Readiness Matrix

Built per the "GULA Full Forensic Production Closure" directive (Batch 8),
`claude/mustafa-parallel-engineering` branch. Every VERIFIED entry below
cites the executable evidence it rests on. Allowed statuses: **VERIFIED**,
**PARTIALLY VERIFIED**, **BLOCKED**, **UNKNOWN**, **NOT STARTED**. No other
words are used to describe status in this document.

## Branch/baseline note (read first)

This matrix is built against `claude/mustafa-parallel-engineering`
(HEAD at time of writing: see `MUSTAFA_ACTIVE_REPAIR_QUEUE.md`'s latest
entry). The forensic-closure directive that requested this document stated
a baseline (`HEAD 96f40e02`, "3338 passed, 329 skipped, 0 failed") that does
**not** exist on this branch's history — it belongs to a sibling branch,
`claude/p0-2-pharmacy-reconciliation`, which forked from the same `main`
commit (`46158e90`) but has since diverged onto an entirely separate,
NR-numbered engineering effort (pharmacy reconciliation, MPI, ORM
writability, LIMS result-release, national-ID identity work, etc.). This
branch's own real baseline, re-measured this pass: **3128 passed, 27
skipped, 2 pre-existing/unrelated failures, 0 new failures** (full command
in `MUSTAFA_ACTIVE_REPAIR_QUEUE.md`'s Batch 8 entry). **HUMAN ACTION
REQUIRED**: confirm which branch this production-closure effort is meant to
track — the two branches' engineering programs are not reconcilable by an
automated pass without risking silently overwriting or duplicating each
other's work.

---

## Architecture

**PARTIALLY VERIFIED.** Monolith-first structure confirmed
(`backend/app/` is the source of truth; `services/` is a parallel,
not-yet-primary decomposition — CLAUDE.md, `docs/adr/ADR-002-monolith-first.md`).
117 router modules confirmed mounted via runtime registration count
(re-derived this pass, not textually assumed — see Live Runtime Surface Map);
2103 individual route operations confirmed via a live `app.openapi()`
schema dump. Duplicate-ownership and shadow-tree audits have been done
domain-by-domain across 8 batches, not exhaustively for the full tree —
see Authorization Coverage Matrix for the per-domain breakdown (61 of 117
router modules still UNKNOWN).

## Security (general)

**PARTIALLY VERIFIED.** 7 confirmed P1 authorization findings closed across
Batches 6-7 (missing-permission-check pattern in `identity.py`, `patients.py`,
`test_results.py`, `compliance.py`, `ehr_fhir.py`, `device_results.py`,
`critical_alerts.py`, `batch.py`), each with real 401/403/404/200 negative
proof and git-stash-verified restoration (`AUTHORIZATION_GAP_REGISTER.md`).
A carried-forward P1 (`adaptive-auth-account-id-idor`) remains BLOCKED —
NEEDS_DECISION, not fabricated closed. No generic super-admin bypass found
in any audited domain.

## Authorization

**PARTIALLY VERIFIED.** See `AUTHORIZATION_COVERAGE_MATRIX.md` for the full,
router-by-router accounting: of 117 mounted router modules, 61 remain
UNKNOWN (not yet traced), the rest VERIFIED/PARTIALLY VERIFIED/BLOCKED with
real evidence per row. `ADR-009` (this session's own architecture decision,
`docs/national/ADR.md`) documents 109 EHR/FHIR routes explicitly BLOCKED
pending a human taxonomy decision between the legacy flat RBAC and the
National domain's own dormant, more sophisticated ABAC/RBAC/consent/
break-glass layer — not silently resolved either way.

## Tenant Isolation

**PARTIALLY VERIFIED.** Every authorization finding closed in Batches 6-8
confirmed tenant scoping (`lab_id`) was already correct at the point the
permission gate was missing — the pattern found repeatedly was "tenant
isolation correct, role/permission layer absent," never a tenant-isolation
bypass itself. One hardcoded-tenant-ID instance found this pass
(`app/services/telegram_bot_commands.py` — `lab_id=1` for a Telegram bot's
`/alerts`/`/stats` commands) — confirmed **NOT reachable**: the router that
would expose this (`app/routes/telegram_webhook.py`) is never mounted in
`app/factory.py` (grep-confirmed, zero `include_router` reference). Recorded
as a P3 observation (dead code; if ever mounted, should not hardcode a
single lab), not a live finding.

## Ownership

**PARTIALLY VERIFIED.** Server-derived ownership (`current_user.lab_id`,
`current_user.id`, `current_user.role`) confirmed as the sole source of
scope/actor identity in every route this program has traced — no request
schema in any audited domain declares a client-controllable `role`,
`lab_id`, or `user_id` field for state-changing operations (confirmed this
pass for LIMS's 4 request schemas and Hospital's nested-entity `Create`
schemas by direct inspection of their Pydantic field lists). Not
exhaustively confirmed for the 61 still-UNKNOWN router modules.

## Database / ORM / Migrations

**PARTIALLY VERIFIED — 1 known BLOCKED.** Hospital domain: 13 of 14 tables
lack Alembic migrations (documented, carried forward across every batch
since discovery); fully code-reachable and testable via the SQLite test
harness (used again this pass for the audit-role-threading fix), but will
`UndefinedTable` on real PostgreSQL until a human-approved migration lands
— **BLOCKED, human action required**, not silently worked around. No new
migration was generated or altered this pass (none was needed — all fixes
were parameter-threading and permission-gate additions, zero schema
changes). Migration head state not re-verified this pass (no schema changes
made; re-verification deferred to a batch that touches migrations).

## Audit

**PARTIALLY VERIFIED — 1 systemic pattern found and closed this pass.**
`log_action`'s hash-chained `AuditLog` mechanism itself is unchanged and
was not modified. Found and fixed: 9 call sites across 2 domains
(`app/lims/services.py` ×4, `app/services/hospital_service.py` ×5) that
hard-coded `user_role="lab_tech"` / `user_role="hospital_staff"`
respectively, discarding the real, server-derived actor role on every
audited mutation. Both are now threaded from `current_user.role`, proven
with 29 new regression tests (17 LIMS + 12 Hospital) parametrized across
4 real roles each, negative-proofed via `git stash`/`pop` with md5-verified
byte-identical restoration. Confirmed (by inspection) not spoofable: no
LIMS or Hospital request schema declares a `role` field. 4 other
hard-coded-role sites found and triaged as **not** the same defect:
`patient_service.py`'s `user_role="system"` (a genuine system-internal
exception-handler event, not a discarded actor role), `register.py`'s and
`citizen_portal.py`'s `user_role="citizen"`/`"doctor"` (self-registration/
self-login routes where the hardcoded role always equals the actor's own
role by construction — there is no other actor these routes could log).
Not exhaustively swept beyond `user_role="..."` literal greps — other audit
call sites using a variable that still resolves to a wrong value would not
be caught by this method.

## Idempotency

**PARTIALLY VERIFIED.** `docs/security/IDEMPOTENCY_CLOSURE_STATUS.md`
records prior closures; a full per-endpoint idempotency-necessity audit
(order creation, sample creation, dispensing, transfusion, appointments,
referrals, certificates, API keys, external integrations) is explicitly
recorded there as **NOT STARTED**. `app/core/idempotency.py` remains
dormant, not activated this pass (no requirement surfaced that needed it;
LIMS routes already use their own `guard.claim()`/`guard.complete()`
idempotency mechanism, confirmed by direct reading of
`app/lims/routes.py`).

## Concurrency

**PARTIALLY VERIFIED.** `SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` documents
a named, cross-domain pattern ("unused OptimisticLockMixin, no
terminal-state guard") closed in 3+ domains with real-PostgreSQL proof
(`app/biomedical`, `app/command_center`, `app/public_health`), plus 2
domains (`blood_bank`, `critical_care`) confirmed already safe via a
different, pre-existing hardened pattern. `PAYMENTS_CAPTURE_REFUND_CAS_STATUS.md`
and `DEVICES_OUTBOX_CAS_STATUS.md` both record **FIXED — VERIFIED**
(real-Postgres-proven, negative-proofed). Not every domain has been
checked for this pattern — see the register's own "Domains not yet
checked" section.

## Transactions

**PARTIALLY VERIFIED.** One systemic pattern closed in a prior batch
(Hospital: 18 routes calling `db.add()`/`db.flush()` without a `db.commit()`
anywhere in the call path — writes never durably persisted despite a
200/201 response — see `AUTHORIZATION_GAP_REGISTER.md` GAP-7). Not
re-verified for new regressions this pass beyond confirming the 2 domains
touched this pass (LIMS, Hospital bed/OT) both already call `db.commit()`
correctly in every route this pass touched (confirmed by direct reading —
`app/lims/routes.py` and `app/routes/hospital.py` both commit after every
mutation this pass's fixes ran through).

## Clinical Safety

**PARTIALLY VERIFIED.** `test_results.py::verify_test_result` remains the
program's own reference example of a fully-correct clinical-safety mutation
(explicit role gate, atomic CAS update, `enforce_transition` state-machine
check, audit logged). LIMS's specimen/order/result state machine
(`app/lims/state_machine.py`) enforces transition legality server-side,
confirmed this pass by direct execution (the audit-role-threading tests
had to be corrected mid-pass when they attempted an illegal
`ordered → collected` transition and the state machine correctly rejected
it with a 409). ICU/transfusion safety: `test_icu_lab_workflow_p0.py`
exists and asserts independent-crossmatch + bedside-verification
requirements, but currently **fails** on this branch (pre-existing,
confirmed identical on unmodified HEAD in Batch 6 — not introduced by this
program, not yet root-caused or fixed by this program either). **BLOCKED
— human triage required** on whether that failure represents a real,
currently-broken clinical safety control.

## FHIR

**PARTIALLY VERIFIED.** `ehr_fhir.py`'s Observation read/search and
Provenance search routes are now permission-gated
(`results:read`/`audit:read`) with real negative proof (Batch 7). 109 of
115 total EHR/FHIR routes remain BLOCKED pending ADR-009 (see
Authorization above) — FHIR export authorization for those routes is
explicitly **not** claimed as verified. Tenant/patient-binding boundary
confirmed sound throughout (every route checked resolves the target
resource's `lab_id` server-side before returning data).

## LIMS

**VERIFIED (audit-role fix only) / PARTIALLY VERIFIED (overall).** This
pass: the 4 hard-coded `user_role="lab_tech"` audit sites are fixed and
proven (17 new tests, real state-machine execution, negative-proofed).
Order → Result → Release → FHIR journey itself was not re-driven this pass
(the directive's stated "8/8 PostgreSQL journey passed" evidence belongs to
the sibling branch, not this one — see the baseline note above); this
branch's own LIMS release-capability-gate and tenant-isolation test suites
(`test_lims_release_capability_gate.py`, `test_lims_tenant_isolation.py`,
26 tests total) pass on SQLite. **Real PostgreSQL LIMS journey proof on
this branch: UNKNOWN** — not run this pass.

## Pharmacy

**UNKNOWN.** Not touched this pass. Prior batches documented one
route-shadowing bug (`/pharmacy/batches/expiring` shadowed by
`/batches/{batch_id}`, P3, still open) and closed a boolean-filter defect
(Batch 5). No fresh forensic pass performed on Pharmacy this batch.

## Blood Bank

**PARTIALLY VERIFIED.** Confirmed already safe for the
"unused-OptimisticLockMixin" concurrency pattern in a prior batch (already
uses a hardened `_safely`-suffixed method convention). Not otherwise
re-audited this pass.

## Hospital

**PARTIALLY VERIFIED — 1 known BLOCKED.** This pass: 5 audit-role hardcode
sites fixed and proven (12 new tests). Prior batches: 3 P1s closed (a
shared entity-lookup helper's boolean-filter bug affecting 17 call sites;
an 18-route missing-`db.commit()` transaction-integrity bug). Still
BLOCKED: 13 of 14 tables lack Alembic migrations (human action required —
see Database above).

## Public Health

**VERIFIED** (concurrency only, per `PUBLIC_HEALTH_CONCURRENCY_STATUS.md`
— real-Postgres-proven, negative-proofed, zero regressions). Not otherwise
re-audited this pass.

## Command Center

**VERIFIED** (concurrency only, per `COMMAND_CENTER_CONCURRENCY_STATUS.md`
— real-Postgres-proven, negative-proofed, zero regressions). Not otherwise
re-audited this pass.

## NIAM

**PARTIALLY VERIFIED.** Extensive prior work: Platform Authority bootstrap
completion, TrustFramework state machine, Certificate authorization
runtime, Trust authorization runtime (all independently marked
**VERIFIED** in their own status docs with real HTTP/service-level proof).
Federation/Trust Authority's broader emergency-containment sign-off
question remains explicitly **BLOCKED** pending human policy decision
(`FEDERATION_TRUST_AUTHORITY_DECISION.md`) — not resolved by any batch,
correctly left open. Not re-verified this pass (no NIAM files touched).

## AI

**UNKNOWN.** Not touched this pass. No evidence gathered this session on
tenant/patient-context dropping, PHI leakage to external models, or AI-tool
authorization bypass for the `app/ai_fabric/` or `app/ai/` surfaces.

## Frontend

**UNKNOWN.** Not touched this pass. No evidence gathered this session on
frontend-authorization-as-security-boundary risks, demo/production mixing,
or hard-coded identifiers in `frontend-v3/`.

## Infrastructure

**UNKNOWN.** Not touched this pass. Config-level invariants (secrets
hard-fail on startup, `/metrics/prom` Bearer-gated in production) were
confirmed correct in Batch 6 (`config.py`, `metrics.py`) but not
re-verified this pass.

## Observability

**PARTIALLY VERIFIED.** Health/readiness endpoint set
(`/health`, `/health/live`, `/health/ready`, `/health/status`,
`/health/deep`) confirmed present in the live route enumeration this pass
(`app.openapi()` schema dump). Structured audit trail confirmed present
and hash-chained (`AuditLog.chain_hash`). Metrics endpoint confirmed
Bearer-gated in production (Batch 6). Request correlation (`X-Request-ID`)
not re-verified this pass. Logging content quality not re-audited this
pass.

## Recovery

**UNKNOWN.** Backup/restore, RPO/RTO, and degraded-mode behavior were not
evidenced this pass. `compliance.py::system_status` (Batch 6 finding) does
surface a `disaster_recovery` field sourced from a signed
`scripts/restore-test.sh` result file, which is evidence the mechanism
exists, but no restore test was executed this pass to produce fresh
evidence.

## CI/CD

**BLOCKED — external.** Every check on every push this program has made
(Batches 5-8) completes in ~3-4 seconds with no real runner dispatch — the
same signature described as NR-136 in the sibling branch's own tracking
(account-level billing/spending-limit restriction, external to this
repository's control). Not re-polled repeatedly this pass, per the
directive's own instruction. No CI check was weakened, no required check
was removed, and no workflow file was modified this pass.

## Performance

**NOT STARTED.** No performance-specific forensic pass (N+1, unbounded
queries, retry storms) was run this batch; this is a P3-tier concern per
this program's own P0-first prioritization and was not reached.

## Architecture Contradictions

**PARTIALLY VERIFIED.** One resolved this pass via ADR-009: EHR's clinical
resources are genuinely EHR/National-platform-owned, not a duplicate
representation of the legacy `Patient`/`LabResult` models — but the
National domain's own, more sophisticated authorization layer
(`app/national/security/*`) is confirmed dormant and never wired to any
live route, a real, documented architectural gap now recorded as a
decision point rather than silently patched over. No other architecture
contradiction was searched for this pass.

## Governance / Documentation

**PARTIALLY VERIFIED.** This program has maintained 5 living documents
across 8 batches (`AUTHORIZATION_COVERAGE_MATRIX.md`,
`AUTHORIZATION_GAP_REGISTER.md`, `LIVE_RUNTIME_SURFACE_MAP.md`,
`MUSTAFA_ACTIVE_REPAIR_QUEUE.md`, `SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md`)
plus `FINAL_ENGINEERING_CLOSURE_REPORT.md` and, this pass, this matrix and
`docs/national/ADR.md`'s ADR-009. No duplicate documents were created.

---

## Explicit non-claims

This document does **not** claim: authorization complete, security
complete, production ready, or national scale ready — for any category
above, including those marked VERIFIED (which are scoped, evidenced
closures of specific findings, not blanket domain sign-off).
