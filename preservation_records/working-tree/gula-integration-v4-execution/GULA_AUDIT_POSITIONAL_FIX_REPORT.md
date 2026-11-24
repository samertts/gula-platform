# GULA AUDIT POSITIONAL-ARGUMENT FIX — EVIDENCE REPORT

**Finding:** `AUDIT-POSITIONAL-001` (P1, audit-integrity regression)
**Directive:** Supreme Autonomous Completion & National Release Directive — 2026-11-19
**Repository:** `gula-integration` only. Sibling `gula-platform` untouched (HEAD `f478676b6fc375338648dde46fbf076c015a3f91`).
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`
**Release position:** **HOLD**. Stable v1.0.0 **NOT declared**. No `PRODUCTION READY` awarded.

---

## 1. Finding (root cause)

Canonical function `backend/app/services/audit_service.py:184`:

```
log_action(db, action, resource_type, resource_id=None, user_id=None,
           user_role=None, lab_id=None, details=None, ip_address=None)
```

Commit `aae20c89` (2026-08-13) inserted `lab_id` immediately before `details`. Call sites authored 2026-07-14…16 pass arguments positionally and were written against an incorrect mental model of the signature (missing `resource_type`, `user_role`, or misplaced `lab_id`). Result under the current signature:

- entity IDs landed in `resource_type` (a required string column),
- lab IDs landed in `user_role`,
- detail strings/dicts landed in `lab_id`,
- `details` was silently `NULL`.

The immutable, tamper-evident audit log is a protected GULA feature; wrong `resource_type`/`user_role`/`lab_id` breaks audit scoping, compliance export, FHIR provenance and tenant-isolation evidence.

---

## 2. Scope (fresh AST inventory)

AST scan of `backend/app/**/*.py` found **50** `log_action` calls with >2 positional args across 8 files:

| File | Broken calls | Pattern |
|---|---:|---|
| `backend/app/nhdw/services.py` | 24 | Pattern A (6/5 args) |
| `backend/app/nursing/coordination.py` | 8 | Pattern C (7 args) |
| `backend/app/services/hospital_service.py` | 5 | Pattern A (6/5 args) |
| `backend/app/lims/services.py` | 4 | Pattern B (7 args) |
| `backend/app/nursing/services.py` | 3 | Pattern C |
| `backend/app/nhdw/offline.py` | 2 | Pattern A, dict details |
| `backend/app/nursing/medication.py` | 2 | Pattern C |
| `backend/app/lims/routes.py` | 2 | 1 Pattern B + 1 canonical 8-arg call |

Note: an earlier note recorded 26 calls in `nhdw/services.py`; the authoritative fresh AST scan reports 24 (total still 50). The extra canonical 8-arg call in `lims/routes.py` was semantically correct but is converted to keywords to allow a strict structural guard.

---

## 3. Fix applied (uncommitted)

All 50 calls converted to explicit keyword arguments. Semantic mapping derived from the canonical signature, the historical signature at authorship commits (`git show`/`git blame`), and each enclosing function's parameters:

- **Pattern A** (hospital/nhdw): `resource_type` derived from action namespace (e.g. `"hospital"`, `"nhdw_admission"`); `resource_id`, `lab_id`, `user_id` from positional slots 3–5; `details` from slot 6 where present.
- **Pattern B** (lims): original `resource_type`, `resource_id`, `user_id`, `user_role="lab_tech"`, `details` preserved; the phantom `lab_id` slot removed (it held the detail string).
- **Pattern C** (nursing): `resource_type`, `resource_id`, `user_id`, `lab_id` from slot 5, `details` from slot 6.
- **Canonical 8-arg call** (`lims/routes.py`): converted to keywords with identical values (no semantic change).

The canonical `log_action` signature itself is **unchanged** (keyword callers elsewhere depend on it). No file outside the 8 call-site files was modified for this fix. A pre-existing, unrelated clinical-alert fix in `lims/routes.py` (lines ~1541+, AUD-CLIN-003/AUD-CLIN-001) was preserved untouched.

**Byte-minimality proof:** a skeleton comparison that replaces every `log_action(...)` span with a sentinel found the non-call content of all 8 files byte-identical before vs after. `git diff --check` exit 0.

---

## 4. Regression tests

New file `backend/tests/unit/test_audit_positional_regression.py` — 11 tests:

1. Whole-tree structural guard: zero `log_action` calls with >2 positional args anywhere in `backend/app` (`IMPLEMENTED`, AST scan confirms 0 offenders).
2. Per-call-site keyword guard: every fixed call has a string-constant `resource_type`; `user_role` never holds a dict/list.
3. Behavioural proof: keyword args populate the correct `AuditLog` columns, including dict→JSON serialisation, string passthrough, and chain-hash computation. All payloads synthetic.

---

## 5. Verification status

| Check | Status | Evidence |
|---|---|---|
| `py_compile` on 8 files | `TESTED` | exit 0 |
| `ruff check` on 8 files | `TESTED` | "All checks passed!" (exit 0) |
| `git diff --check` | `TESTED` | exit 0 |
| Focused regression tests (11) | `TESTED` | `11 passed in 163.19s`, exit 0 |
| Related existing tests (38) | `TESTED` | `38 passed in 162.52s`, exit 0 — includes AUD-CLIN-003, LIMS tenant isolation, compliance integrity, nursing read gate |
| Full backend suite | `TESTED` | `5134 passed / 28 skipped / 1 failed (14m53s)` — `/tmp/opencode/auditfix_full_suite.log`; all 11 new tests passed. The single failure is `test_ai_benchmark.py::test_cosine_similarity_throughput` (`949/s < 2000/s`), a pure CPU-throughput benchmark with **no audit/log_action involvement`; it ran concurrently with the independent reviewer's pytest process. Isolated re-run: `1 passed`, `7289 ops/s` — confirmed environmental/flaky, not a regression. No failing test was deleted or weakened. |
| Fresh-context independent adversarial review | `INDEPENDENTLY VERIFIED` | Fresh-context reviewer, read-only, PASS on all 7 checks (diff scope, semantic mapping, whole-tree AST scan of 2,045 files, details typing, 11 focused tests `11 passed / 0 failed in 208.63s`, falsification, protected artifacts); exact verdict: `INDEPENDENTLY VERIFIED (engineering scope)`. Not self-awarded. |
| Secret / PHI scan on changed lines | `TESTED` | no secret/PHI patterns in added lines or test file |
| Protected MD5s unchanged | `IMPLEMENTED` | all 3 exact matches |
| Staged `R100` renames intact | `IMPLEMENTED` | 20 × R100, 0 content changes |

---

## 6. Non-claims

No `INDEPENDENTLY VERIFIED` award is made in this report. No `PRODUCTION READY`. No owner / MoH / regulator / clinical / legal approval. No release, deployment, merge, or v1.0.0 declaration. No production DB/Redis access. No real PHI. No commit of this change (exact-path commit remains gated by mixed-provenance review).

---

## 7. Finalization

**Verdict:** `INDEPENDENTLY VERIFIED` — engineering scope only, granted by a fresh-context independent adversarial reviewer (not self-awarded). All 7 review checks PASS; exactly 50/50 broken call sites corrected; zero residues for this finding.

**Residuals observed by reviewer but out of scope / pre-existing (not introduced by this fix):**
- LIMS specimen calls never set `lab_id` although the enclosing function has it.
- `hospital_service.py` bed/OT calls pass `resource_id=str(...)`.
Both unchanged by this fix and recorded here, not silently adjudicated.

**Commit status:** `BLOCKED` — the complete fix cannot be committed by exact path because `backend/app/lims/routes.py` carries pre-existing mixed-provenance clinical-alert changes (AUD-CLIN-003/AUD-CLIN-001). Committing the other 7 files alone would leave the AST guard failing on the uncommitted `lims/routes.py` calls. All changes remain in the working tree, preserved and verified; no commit, push, merge or deployment performed. Resolution requires provenance sign-off on the pre-existing `lims/routes.py` work.

**Final non-claims:** No `PRODUCTION READY`. No owner / MoH / regulator / clinical / legal approval. No release, v1.0.0 declaration, deployment or protected-branch merge. Standing decision remains **HOLD**.
