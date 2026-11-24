# Independent review — P-02 / P-03 REVISION 3 decision packets

**Date:** 2026-11-21 UTC · **Baseline:** committed HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
(`integration/gula-unification-v1`).
**Reviewed documents:**
- `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET_REV3.md`
- `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET_REV3.md`

**Method:** two separate fresh-context, read-only reviewers — `ses_e01f69590ffe15PDFmi5WcQgck` for P-02 and
`ses_e01f6958fffeJ0AsVji9wnN1k8` for P-03. All source evidence was obtained with
`git show HEAD:<path> | nl -ba` at the SHA above; working-tree files were not used as evidence.
No tests were run; no file, staging area, reference, commit, protected MD5 or PR was changed by either
review. The REV2 review (`AUDIT_EXECUTION_RECORDS/PACKET_REVIEW_2026_11_21.md`) supplied the exact
correction list that REV3 was required to resolve.

**Readiness bar:** decision-ready only with **zero CRITICAL and zero HIGH** findings and reproducible
HEAD evidence. A PASS verdict is a statement about the *packet*, not about implementation, owner
acceptance, release or production readiness.

---

## 1. Verdicts

| Packet | Verdict | CRITICAL | HIGH | MEDIUM | LOW | INFO |
|---|---|---:|---:|---:|---:|---:|
| P-02 / AUD-F02 REV3 | **DECISION-READY** | 0 | **0** | 0 | 2 | 0 |
| P-03 / AUD-F03 REV3 | **DECISION-READY** | 0 | **0** | 0 | 0 | 0 |

Both packets retain the literal status `PREPARED ONLY` · NOT `IMPLEMENTED` · NOT `TESTED` · NOT
`INDEPENDENTLY REVIEWED` as an *implementation* status. The independent packet review recorded here
does not change that implementation status: `INDEPENDENTLY REVIEWED` is reserved for a completed
change-set with RED/GREEN evidence, and no RED/GREEN evidence exists for either R4 packet. Both
PostgreSQL test plans remain **UNVERIFIED**; no SQLite substitution was offered or performed.

---

## 2. P-02 / AUD-F02 REV3 — DECISION-READY

### 2.1 Prior findings resolved

| Prior finding (REV2 review) | REV3 resolution | HEAD verification |
|---|---|---|
| **HIGH-1** — proposed change omitted `db.commit()`; zero alert rows could persist | §4 step 1 mandates retaining `db.commit()` at `ai.py:663` immediately after `log_action(...)`; reinforced in §2.3, test R7 and §8 owner confirmation | `audit_service.py:225,228,231` flush only, no commit anywhere in the file; `ai.py:940-941` closes the session |
| **MEDIUM-1** — anchor-file side effect on rollback not analyzed | §5 adds the side-effect row and an accepted reconciliation; §7/§8 require explicit owner acceptance | `audit_service.py:233-234`; `verify_audit_chain` at `:238-268` reads `audit_logs` only |
| Correction 3 — deterministic `lab_id` | §4 step 1 resolves `LabOrder.lab_id` (`:29`, `nullable=False`), passes `lab_id=None` only when unresolvable, never fabricates; R4 asserts the contract | `backend/app/models/lab_order.py:29` |
| Four LOW inaccuracies | Test count **14** with exact `def test_` lines (§3); `_load_results_from_db` `:864-912` / session `:865` (§2.1); `GET /api/ai/interpret/{token}` (`:841-847`, prefix `:84`) used throughout; `GULA_AUDIT_SECURITY_FINDINGS.md` labelled working-tree-only and absent at HEAD (§1, §3) | All citations reproduced at HEAD |
| Migration trigger range | Cites `20250322_0002:73-104` | Trigger UPDATE/DELETE-only claim correct |

### 2.2 New findings — 2 LOW, non-blocking

| Sev | Location | Reviewer observation and exact correction |
|---|---|---|
| LOW-1 | REV3 §5, "Anchor-file side effect" row — wording "the next successful canonical write at the same anchor interval refreshes the checkpoint" | Overstated at HEAD. `_write_anchor` (`audit_service.py:115-124`) **appends** to the monthly file (`open(..., "a")`, `:121-122`) and never replaces a prior checkpoint; on PostgreSQL `nextval` (`:218-220`) is non-transactional, so a rolled-back ID is not reused. Correct wording: a later anchor write **appends a new line**, and `get_latest_anchor()` (`:127-181`) returns it as the latest checkpoint while the stale line persists in the file. The anchor is additionally surfaced at `backend/app/routes/compliance.py:962`, so "advisory ... only" is slightly broad. The decisive reconciliation claim — `verify_audit_chain` (`:238-268`) reads `audit_logs` exclusively and never the anchor — is accurate. |
| LOW-2 | REV3 §4 step 1 — "using the order already loaded by `_load_results_from_db` (`:864-912`)" | The `order` loaded at `ai.py:893` is **discarded**: the function returns only `(order_id, results_data, patient_context)` at `:912`, and the proposed change is scoped to `:641-667` only. The deterministic mechanism should be stated as the packet already states it — a **targeted lookup in the audit session** — or the sentence must acknowledge that reusing the loaded order would widen scope beyond the helper. Explicit `lab_id=None` behavior and test R4 are unaffected. |

**Disposition of LOW notes:** recorded here verbatim, not applied to the reviewed artifact. Editing
`P-02_DECISION_PACKET_REV3.md` after its independent review would change the artifact's SHA-256 and
invalidate the verdict against the exact document hash; the next packet revision must adopt both
wording corrections. Neither note affects the decision bar (zero CRITICAL/HIGH).

### 2.3 Confirmed adequate by the reviewer

`ai.py:50,84,641-667,663,664-667,841-847,864-912,934-943,936-941,945-947`; `audit_log.py:16-18,25-27`;
`lab_order.py:29`; `audit_service.py:184-235,198-202,203-213,215,218-220,222-225,226-231,233-234,238-250`;
migration `20250322_0002:73-104`; 14 `test_audit_anchor.py` entries at the exact cited lines;
`conftest.py:28,93-150`. Negative claims reproduced: no `log_action` import in `ai.py`, no isolation
guard (`AuditChainIsolationError` / `READ COMMITTED`) anywhere, zero `critical_result_alert` /
`log_action` occurrences in the named AI test files, and absence at HEAD of
`GULA_AUDIT_SECURITY_FINDINGS.md`, `test_audit_bypass_regression.py` and the proposed future PG test file.

---

## 3. P-03 / AUD-F03 REV3 — DECISION-READY

The reviewer identified **no new findings** (0 CRITICAL / 0 HIGH / 0 MEDIUM / 0 LOW). All eight prior
findings were verified as resolved:

| Prior finding (REV2 review) | REV3 resolution | HEAD verification |
|---|---|---|
| **HIGH-1** — concurrent chain integrity asserted but not guaranteed | §2 records the full race residual (unlocked head read, `nextval` before `add`, `verify_audit_chain`, append-only triggers); T9 moved to `P-03-CONCURRENCY` and removed from acceptance (§4, §6 T9, §7, §8); no single-process GREEN presented as multi-worker evidence | `audit_service.py:106-112,218-225,238-270`; migration `:76-104` |
| **MEDIUM-1** — undisclosed second deployment surface | §1 B2, §7 and §8 D1(e) disclose `POST /control-plane/fleet/deploy` as out of B2 unless selected | `routes.py:211-226` → `fleet/provisioning.py:36-64`, swallow `:60-62` |
| **MEDIUM-2** — inaccurate T2 prediction | T2 now predicts unhandled `ValueError` → HTTP 500; swallow scoped to `asyncio.sleep` only | `manager.py:82-83` before `try` at `:89-97`; `except` at `:95-97`; `routes.py:292-306` has no handler |
| **MEDIUM-3** — absent D5 target, reader/writer mislabel | §4 step 5 defines a new canonical `query_audit_logs` in `audit_service.py` as authorized D5 scope; §1 B4 separates stale query helper from stale writer | `audit_service.py` exposes only `log_action` / `verify_audit_chain`; `audit.py:50-69` → `shared/audit/service.py:65+`; writer `:26-62` |
| **MEDIUM-4** — fail-closed availability undisclosed | Disclosed in §2, §4 step 2, §5 actor row, §7 and §8 D3/decision text | Consistent across all sections |
| LOW — "No DB session source exists" | §1 now states `get_db` is already in the dependency graph via `get_current_user` — wiring, not new infrastructure | `dependencies.py:10,39`; `routes.py:17,26-27` |
| LOW — missing body-spoofing row and extra rejection paths | §5 adds the body-spoofing row and permission-version (401) + deactivated-lab (403) paths | `routes.py:294-299`; `dependencies.py:87-95,97-104` |
| LOW — staged-state rollback wording | §7 explicitly labels it "Operational constraint (working-tree state, not HEAD evidence)" | Compliant with the evidence rule |

Additional HEAD checks reproduced by the reviewer: schema mismatch (`models/audit_log.py:13-27` versus
stale `entity_type` / `entity_id` / `previous_hash` / `timestamp`), taxonomy actions (`audit.py:12-23`),
SDK null-audit wiring (`sdk.py:50,60-61`), secret accessors (`secrets.py:29-33,44-57,59-67`), and the
negative claims (no `log_action` under control_plane; no `set_audit` / `access_audit_log` callers; no
control-plane test file; no canonical query helper). The anchor/rollback residual inherited from
canonical `log_action` is tracked under P-02 and was not re-raised here.

---

## 4. Disposition

- **P-02 REV3:** DECISION-READY for an owner decision. Do not implement, sign as accepted or mark
  production ready. Owner must explicitly select (a) or (b), accept the endpoint-level availability
  trade-off and the §5 anchor reconciliation.
- **P-03 REV3:** DECISION-READY for an owner decision. Do not implement, sign as accepted or mark
  production ready. Owner must choose D1–D5 separately, explicitly accept fail-closed availability if
  D3=(a), understand that `/control-plane/fleet/deploy` is unaudited unless D1=(e), and that T9 is
  deferred to `P-03-CONCURRENCY`.
- No package-specific R4 owner authorization exists for either finding. OD-001 remains `ACCEPTED`
  only for SEC-015/F-01 engineering scope; OD-002…OD-025 remain `BLOCKED`. F02/F03 remain
  R4-blocked; no implementation, commit, stage change, push, Draft PR, merge or deploy.
- The original packets and REV2 packets remain unchanged. REV3 documents are new, untracked,
  documentation-only artifacts with a separate additive SHA-256 manifest; no existing SHA registry
  was modified.
- Stale earlier language in tracked documents — `GULA_MASTER_EXECUTION_STATUS.md` §5.6,
  `GULA_MASTER_COMPLETION_SCORECARD.md` §2.1/§5 and `GULA_SECURITY_AND_RISK_REGISTER.md` §5 rows 3–5 —
  still records the **2026-11-20** FAIL verdict. This report is additive and supersedes only those
  *decision-readiness* assertions; those tracked files were deliberately not edited, preserving the
  mixed-provenance working tree. All other statements there (HOLD, `production_ready_items = 0`,
  Stable v1.0.0 NOT DECLARED, PRODUCTION READY NOT AUTHORIZED) remain in force.

### State invariants re-verified after the reviews

| Invariant | Value |
|---|---|
| HEAD / branch | `2206654dc713ea2de8c564a3207dfe05fde23549` / `integration/gula-unification-v1` |
| Staged | 20 entries, all `R100`; name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` |
| Unstaged | 162 modified paths (unchanged) |
| Untracked | 671 paths — baseline 664, plus prior checkpoint documents and exactly the two new REV3 packets |
| `git diff --check` | exit 0 |
| Protected MD5s | `effdfeaf10234678d83b2668c4489552`, `1a02c01563c93b07a7cdb92c0462bf36`, `ea3969d09aaf7b0b28a065838b44a594` — all unchanged |
| Sibling `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` — unchanged |
| `production_ready_items` | 0 |
| Governance posture | HOLD TRUE · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED |
