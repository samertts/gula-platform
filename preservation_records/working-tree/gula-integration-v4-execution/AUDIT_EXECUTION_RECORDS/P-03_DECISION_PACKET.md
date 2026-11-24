# P-03 / AUD-F03 — independent owner decision packet

**Generated:** 2026-11-20 UTC (checkpoint reissue)
**Owner gate:** R4 — **explicit package-specific owner authorization AND scope decision required**
**Current status:** `PREPARED ONLY` · NOT `IMPLEMENTED` · NOT `TESTED` · NOT `INDEPENDENTLY REVIEWED` · NOT `ACCEPTED` · NOT `PRODUCTION READY`
**Posture:** HOLD · `production_ready_items = 0` · no commit / push / PR / merge / deploy

This packet is self-contained. The accelerated-completion mandate recorded in
`GULA_MASTER_EXECUTION_STATUS.md` §5 was used for P-01/P-04 only and is **not** authorization for
control-plane audit behavior. OD-001 is `ACCEPTED` for the defined SEC-015/F-01 engineering scope
only; OD-002…OD-025 remain `BLOCKED`.

---

## 1. Finding and evidence

| Field | Record |
|---|---|
| ID / severity | `AUD-F03` — MEDIUM, **ACTIVE** control plane |
| Source | `backend/app/control_plane/routes.py:317-400` (approval/deploy), `:403-413` (`/audit-log`); `backend/app/control_plane/release/manager.py:36-37,69-99` (in-memory `approved_by` / `deployed_by`, `logger.info` only); `backend/app/control_plane/config/secrets.py:59-67` (`access_audit_log()` with zero callers) |
| Defect | No canonical `log_action` call exists anywhere under `backend/app/control_plane`. Release approval, deployment and secret-access events exist only in process memory and logs; `/control-plane/audit-log` returns an empty list; `EnterpriseAudit` is never instantiated. |
| Impact | Governance decisions are not durable, tamper-evident, or restart-safe. Static reachability proven; no PHI or production action used. |
| Reference | `GULA_AUDIT_SECURITY_FINDINGS.md` AUD-F03. |

## 2. Required change (prepared, NOT applied)

1. **Scope decision first:** owner chooses which boundaries enter the canonical `audit_logs` trail:
   - (a) all three: approval, deployment, secret access *(recommended)*;
   - (b) approval and deployment only;
   - (c) a separate audit store (requires its own design, not covered by this packet);
   - (d) defer.
2. At each selected boundary, write exactly one canonical chained row via `log_action(...)` with:
   actor from the authenticated principal (never from the request body), action name
   (e.g. `control.release_approved`, `control.release_deployed`, `control.secret_accessed`),
   `resource_type`/`resource_id` identifying the release or secret reference, release version,
   decision/outcome, and a correlation ID. Keep existing in-memory `approved_by` / `deployed_by`
   fields for API responses only.
3. Wire `config/secrets.py::access_audit_log()` to the canonical writer if option (a) is selected;
   do not expose secret values in `details` — log the reference/key name and actor only.
4. Audit failure policy: **(fail closed recommended)**, consistent with OD-001's READ-COMMITTED-only
   enforcement; no write under non-READ-COMMITTED isolation. Buffered/outbox alternatives need a
   separate decision.
5. Reuse the existing `audit_logs` table: no migration, no schema change, no new dependency, no
   change to the canonical hash algorithm, no other domain touched.

## 3. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Control-plane approval/deploy requests fail when audit write fails | HIGH (availability) | Owner explicitly accepts fail-closed policy; narrow the failure boundary; structured error response. |
| Secret value or actor spoofing leaks into audit details | HIGH (privacy/security) | Actor from authenticated principal only; log key *name/reference*, never value; regression test asserts no value-like field in `details`. |
| Duplicate audit rows on retries | MEDIUM | Idempotency/correlation-ID test; exactly one row per successful action. |
| Audit volume growth on control-plane actions | LOW | Bound correlation details; no unbounded artifacts/config payloads in `details`. |
| Non-READ-COMMITTED session forks the chain | HIGH | Reuse canonical guard; assert refusal and zero rows in test. |
| Mixed provenance / unrelated control-plane work | MEDIUM | Edit only the selected boundary hunks; no staging or commit; preserve all other lines byte-for-byte. |
| False assurance if `/audit-log` remains inert | MEDIUM | After implementation, route reads canonical rows (this is part of the package, not a separate task). |

## 4. Test plan (R3, disposable isolated environment only)

**RED (must fail on current code):**
1. Drive `POST /control-plane/releases/{id}/approve` against the disposable DB → assert one chained
   `audit_logs` row with actor, version, decision and correlation ID. Current code writes none → RED.
2. Drive the deploy endpoint → assert one chained row; assert `verify_audit_chain(db)["verified"]`.
3. Call the secret-access boundary → assert one chained row containing the key *reference* and no
   value-like content.
4. GET `/control-plane/audit-log` → assert the new rows are returned.

**GREEN / negative:**
5. REPEATABLE READ / AUTOCOMMIT session at each boundary → assert guard refusal, zero rows, no
   success response.
6. Retry the same approval → assert no duplicate row (idempotency).
7. Forced audit failure → fail closed, no state transition persisted for approval/deploy.

**Related suites:** control-plane authorization, governance audit authorization, audit chain
integrity/anchor/bypass/positional/isolation, compliance integrity, P-01 legacy writer, P-04 verifier.
**Tooling:** Python 3.12 at `/tmp/opencode/gula-int-py312/bin/python`, synthetic SQLite fixtures,
ruff, `git diff --check`. No production DB, secret, daemon or deployment.

## 5. Acceptance conditions

**Engineering (to be earned, not assumed):**
- RED → GREEN demonstrated; related suites pass; ruff clean; `git diff --check` clean.
- Fresh-context independent review verdict with 0 CRITICAL/HIGH, recorded in `P-03_AFTER.md`.
- All review conditions cleared by regression tests before `INDEPENDENTLY REVIEWED` is claimed.
- Verified that no secret value appears in any audit `details` field.

**Owner (explicit, still outstanding):**
- Scope option (a)/(b)/(c)/(d) and failure-policy choice.
- Actor-attribution rule confirmation (authenticated principal is authoritative).
- Separate decision for commit/staging scope: no commit authority is implied by this package decision.

## 6. Owner decision requested

> "I authorize package P-03 / AUD-F03 with scope option __ and fail-closed policy, exactly as scoped
> in `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET.md`. The authenticated principal is the sole
> actor source and secret values are never written to audit details. This authorization covers this
> package only; it does not authorize a commit, staging change, merge, release, deployment,
> `PRODUCTION READY`, or a change to HOLD."

Alternative: *"P-03 is deferred; keep the finding open and the packet prepared."*

## 7. Rollback

Revert only the selected control-plane hunks. No migration (reusing `audit_logs`); no protected-file
change; 20 staged `R100` renames and staged MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` untouched.
