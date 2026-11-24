# Independent review — P-02 / P-03 REVISION 2 packets

**Date:** 2026-11-21 UTC · **Baseline:** committed HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Reviewed documents:**
- `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET_REV2.md`
- `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV2.md`

**Method:** two separate fresh-context, read-only reviewers (`ses_e053b401fffe697h0GGJuc6bt2` for P-02,
`ses_e053b401fffd6lsWshGOz6Kuhr` for P-03). All source evidence obtained with `git show HEAD:<path> |
nl -ba`; working-tree files were not used as evidence; no tests were run; no files, staging area,
protected MD5, commit or PR were changed by the reviews.

**Readiness bar:** decision-ready only with **zero CRITICAL and zero HIGH** findings and reproducible
HEAD evidence. Neither packet meets the bar. Both remain `PREPARED ONLY`; no implementation,
`ACCEPTED` or `PRODUCTION READY` status is awarded.

---

## 1. Verdicts

| Packet | Verdict | CRITICAL | HIGH | MEDIUM | LOW | INFO |
|---|---|---:|---:|---:|---:|---:|
| P-02 / AUD-F02 REV2 | **NOT DECISION-READY** | 0 | **1** | 1 | 4 | 1 |
| P-03 / AUD-F03 REV2 | **NOT DECISION-READY** | 0 | **1** | 4 | 2 | 1 |

---

## 2. P-02 / AUD-F02 REV2 — NOT DECISION-READY

### HIGH-1 — Proposed change omits the commit; it can persist zero alert rows
- `backend/app/services/audit_service.py:184-235` — `log_action` only calls `db.flush()` at `:225`,
  `:228`, `:231`; there is **no `db.commit()` anywhere in that file**.
- `backend/app/routes/ai.py:936-941` — `_write_critical_alert` opens a fresh `SessionLocal()`, calls
  the helper and closes the session in `finally`; it never commits.
- `backend/app/routes/ai.py:663` — the only commit today sits inside the `try` block that §4 step 1
  proposes replacing with `log_action(...)`.
- Consequence: an implementer replacing the whole block leaves the row flushed but uncommitted;
  `db2.close()` at `:941` discards it. The result would be **no tamper-evident alert at all**, worse
  than the current NULL-chain row. Acceptance test R1 would catch it but is UNVERIFIED and was not run.

### MEDIUM-1 — Anchor-file side effect on rollback not analyzed
`audit_service.py:233-234` writes an anchor checkpoint outside the DB transaction and before commit.
Under fail-closed rollback the anchor may reference a `chain_hash` for a row that was never committed.
No reconciliation or acceptance statement exists.

### LOW / INFO
- Test count: packet says 14 vs 15; HEAD `test_audit_anchor.py` has **14** `def test_` entries
  (`:61,83,99,115,131,146,163,193,211,241,267,302,317,342`).
- `_load_results_from_db` actually begins at `ai.py:864` (session at `:865`), not the cited `:880-912`.
- Endpoint shorthand `/ai/interpret` is wrong; HEAD route is `GET /api/ai/interpret/{token}`
  (`ai.py:841-847`, prefix at `:84`). R5 would 404 if taken literally.
- `GULA_AUDIT_SECURITY_FINDINGS.md` is absent at HEAD (working-tree-only); it is not HEAD evidence.
- Migration trigger range ends at `:104`, not `:101`; the substantive UPDATE/DELETE-only claim is correct.

### Adequate
HEAD defect and citations (`ai.py:50,641-667,934-943,945-947`; `audit_log.py:16-18,25-27`;
`audit_service.py:248-250`), no conflation with uncommitted guard code, fact/hypothesis separation,
UNVERIFIED PostgreSQL plan with no SQLite substitution, availability/retry/concurrency analysis,
measurable acceptance/rejection, status separation, and a single owner decision text with all exclusions.

### Exact corrections required before re-review (not applied — stop instruction)
1. Retain `db.commit()` at `ai.py:663` after `log_action(...)`; `log_action` only flushes.
2. Add an anchor-side-effect row and state the accepted reconciliation.
3. Specify `lab_id` resolution and null behavior deterministically.
4. Fix the four LOW inaccuracies (test count, function range, endpoint path, working-tree-only doc).

---

## 3. P-03 / AUD-F03 REV2 — NOT DECISION-READY

### HIGH-1 — Concurrent chain integrity asserted but not guaranteed; remedy excluded by scope
- T9 (`:85`) requires two concurrent approvals to produce valid chained rows; §7 (`:104`) requires
  RED→GREEN for T1–T10; §4 (`:56`) forbids schema/hash/design changes and proposes no serialization.
- HEAD `audit_service.py:106-112` reads the chain head with an unlocked
  `SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1`; `:218-225` reserves `nextval` and
  computes `chain_hash` from that read before `db.add()/db.flush()`. Two concurrent writers can read
  the same predecessor and produce a chain that `verify_audit_chain` (`:238-268`) rejects.
- Append-only triggers (`20250322_0002_perf_indexes_audit_protection.py:76-104`) block in-place repair.
- A single-process T9 GREEN would not detect the multi-worker race; the acceptance evidence would be
  misleading. Either add explicit serialization/locking to the authorized scope or move T9 to a
  separate design package.

### MEDIUM-1 — Second deployment surface undisclosed
HEAD `control_plane/routes.py:211-226` (`POST /control-plane/fleet/deploy`) →
`fleet/provisioning.py:36-64` mutates in-memory state and swallows exceptions at `:60-62`. It is OUT
of B2 unless explicitly selected; an owner choosing D1=(a) could believe all deployment is covered.

### MEDIUM-2 — T2 predicted failure mode inaccurate
Without `approve_first`, `ReleaseManager.deploy` raises `ValueError` at `manager.py:82-83` outside the
`try` at `:89-97`; `routes.py:292-306` has no handler → unhandled 500. The swallow at `:95-97` only
wraps `asyncio.sleep`.

### MEDIUM-3 — D5 implementation target absent; B4 wording mislabels reader as writer
`log_action` has no companion filter-query helper at HEAD (`audit_service.py:184-270` exposes only
`log_action` and `verify_audit_chain`). `EnterpriseAudit.query()` (`control_plane/audit.py:60-69`)
calls the stale shared **query helper**, not writer.

### MEDIUM-4 — Fail-closed availability trade-off undisclosed
An unavailable audit database would block approval/deployment requests (no audit row → no state
transition). The owner must accept this or defer to a separate outbox package.

### LOW / INFO
- "No DB session source exists" is overstated: `get_db` is in the dependency graph via `get_current_user`
  (`security/dependencies.py:39`; `control_plane/routes.py:26-27`); the route handler itself receives no Session.
- Actor table omits an explicit body-spoofing row and rejection paths at `dependencies.py:87-104`.
- Staged-R100/MD5 rollback wording is working-tree state, not HEAD evidence; label as operational constraint.

### Adequate
All other cited line ranges accurate; negative claims confirmed by HEAD-wide grep (no `log_action`
under control_plane, no `set_audit` callers, no `access_audit_log` callers, no standalone approval or
rollback route, no control-plane tests); schema mismatch confirmed; B1–B4 separation; no working-tree
behavior presented as HEAD; PostgreSQL plan marked UNVERIFIED with no substitution; D1–D6 independent
with deferral and full exclusion wording.

### Exact corrections required before re-review (not applied — stop instruction)
1. Add concurrency residual and either serialize within scope or move T9 to a separate package.
2. Disclose `/control-plane/fleet/deploy` as out of B2 unless selected.
3. Correct T2 predicted failure to unhandled `ValueError` → 500.
4. Define a new canonical query helper target for D5 and fix B4 reader/writer wording.
5. Disclose fail-closed availability loss for approval/deploy.
6. Add body-spoofing actor row and the additional rejection paths.
7. Relabel staged-state rollback wording as operational constraint.

---

## 4. Disposition

- **P-02:** NOT DECISION-READY — return to preparation; do not sign, do not implement.
- **P-03:** NOT DECISION-READY — return to preparation; do not sign, do not implement.
- No package-specific owner authorization exists for either finding. OD-001 remains the only accepted
  decision (SEC-015/F-01 engineering scope); OD-002…OD-025 remain BLOCKED.
- The original packets and the REV2 packets are retained unchanged as evidence. No new revision was
  produced after this review, per the instruction to stop if either packet fails.
- HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED.
