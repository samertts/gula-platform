# GULA Change Provenance Resolution Report

**Directive:** GULA-PBR-2026-11-19, §5 (Priority P1)  
**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  
**HEAD (baseline):** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Date:** 2026-11-19  
**Method:** read-only — `git status`, `git diff -U0`, `git show`, cross-worktree file comparison, governance-report evidence search. No file was edited, staged, committed or reverted for this report.

---

## 1. Executive verdict

The two provenance-blocked files contain **four independently attributable workstreams** interleaved at hunk level. Every hunk has documentary ownership evidence in this repository. **No hunk is unattributed and no hunk appears in any sibling worktree** — all changes are unique to this working tree.

| ID | Workstream | Owner evidence | Status (this workstream's own award) |
|---|---|---|---|
| WS-1 | `AUDIT-POSITIONAL-001` / `SEC-001` — canonical audit call-site keyword conversion | `GULA_AUDIT_POSITIONAL_FIX_REPORT.md:44,57,59`; `GULA_SECURITY_AND_RISK_REGISTER.md:14` | `INDEPENDENTLY VERIFIED` (engineering scope), previously awarded |
| WS-2 | `AUDIT-BYPASS-001` / `SEC-014` — critical alert via canonical chained writer | `GULA_AUDIT_BYPASS_FIX_REPORT.md:29,40,51`; `GULA_SECURITY_AND_RISK_REGISTER.md:15` | `INDEPENDENTLY VERIFIED` (engineering scope), previously awarded |
| WS-3 | Team C clinical remediations `AUD-CLIN-001`, `AUD-CLIN-003`, `R-CLIN-003-A` | `GOVERNANCE/ADVERSARIAL_ASSURANCE/REMEDIATION_REGISTER.json:53-57,401-405`, `PHASE2_CLOSEOUT.md:26`, `INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md:16,98-109` | `INDEPENDENTLY VERIFIED` (engineering scope), previously awarded |
| WS-4 | Endpoint-authorization remediation `S-09` and `S-12` | `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md:85-86`; `GOVERNANCE/REMEDIATION_STAGE_REPORT.md:44,46` | `IMPLEMENTED` / `TESTED` (8/8 and 5/5 in-tree); no independent award located |

**Separation feasibility:** technically possible at hunk granularity (all hunks are line-disjoint), but **not executable under current authority** — this directive prohibits commits, staging changes, and merges, and each workstream requires its own provenance sign-off before any exact-path commit. Clean separation must not remove another workstream's changes merely to enable a commit. **Both files remain `BLOCKED` for commit.**

---

## 2. Exact-path change manifest

Line ranges are from `git diff -U0` against HEAD; new-side line numbers. Every hunk is preserved verbatim in the working tree.

### 2.1 `backend/app/lims/routes.py` (modified — 7 hunks, all accounted for)

| # | Hunk (new-side) | Change | Owning workstream | Evidence | Independent attribution |
|---|---|---|---|---|---|
| L1 | `+344,9` | `create_department`: 8 positional `log_action` args → keywords | WS-1 `AUDIT-POSITIONAL-001` | `GULA_AUDIT_POSITIONAL_FIX_REPORT.md:44` ("1 Pattern B + 1 canonical 8-arg call" in `lims/routes.py`), `:57` (canonical call converted to keywords) | Yes — report explicitly names this file and call |
| L2 | `+987,7 → +995,7` | `order_fhir_bundle`: 8 positional args → keywords (`lab_id`, details dict preserved) | WS-1 `AUDIT-POSITIONAL-001` | same report `:44,57` | Yes |
| L3 | `+1544 → +1552` | `list_quality_indicators`: add `Depends(get_current_user)` | WS-4 `S-12` | `PUBLIC_ENDPOINT_REGISTER.md:86` ("`/lims/quality/indicators`, `/…/evaluate` (2) … `Depends(get_current_user)` on both routes … `test_lims_quality_authorization.py` 5/5") | Yes — register names both routes and the exact fix |
| L4 | `+1560,0 → +1569` | `evaluate_indicator`: add `current_user: LabUser = Depends(get_current_user)` | WS-4 `S-12` | same as L3 | Yes |
| L5 | `+2163,0 → +2173,15` | `run_auto_validation`: compute `authoritative_status`, `changed` flag, persist every emitted flag, commit only when `changed` | WS-3 `AUD-CLIN-003` | `REMEDIATION_REGISTER.json:401-405` (`REM-CLIN-003`, linked `AUD-CLIN-003`); `PHASE2_CLOSEOUT.md:26` | Yes — in-file comment names `AUD-CLIN-003`; report names `run_auto_validation` |
| L6 | `+2167,0 → +2192,24` | `run_auto_validation`: `else` branch clearing stale `is_critical`/`is_abnormal`/`flag` on empty recomputed flags | WS-3 `R-CLIN-003-A` | `INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md:16,98-109` ("found by Team C", "VERIFY CORRECTED", explicit `else` branch in `run_auto_validation`); `PHASE2_CLOSEOUT.md:26` | Yes — in-file comment names `R-CLIN-003-A`; Team C report names the exact branch |
| L7 | `+2182 → +2230,8` | `process_critical_alert`: commit when `outcome.status == "notification_pending"` | WS-3 `AUD-CLIN-001` | `REMEDIATION_REGISTER.json:53-57` (`REM-CLIN-001`, linked `AUD-CLIN-001`, "durable outbox and honest status"); in-file comment names `AUD-CLIN-001` | Yes |

Cross-check: `GULA_AUDIT_POSITIONAL_FIX_REPORT.md:59` explicitly records that the "pre-existing, unrelated clinical-alert fix in `lims/routes.py` (lines ~1541+, AUD-CLIN-003/AUD-CLIN-001) was preserved untouched" — direct contemporaneous evidence that WS-1 and WS-3 are distinct workstreams.

### 2.2 `backend/app/routes/ai.py` (modified — 6 hunks, all accounted for)

| # | Hunk (new-side) | Change | Owning workstream | Evidence | Independent attribution |
|---|---|---|---|---|---|
| A1 | `+54,0 → +55,2` | imports `require_ai_operator` and `log_action` (one line per workstream: WS-4 and WS-2) | WS-4 (`require_ai_operator`) + WS-2 (`log_action`) | `PUBLIC_ENDPOINT_REGISTER.md:85`; `GULA_AUDIT_BYPASS_FIX_REPORT.md:40,51` | Yes — each import maps to a different hunk's workstream |
| A2 | `+337 → +339` | `/operations`: `dependencies=[Depends(require_ai_operator)]` | WS-4 `S-09` | `PUBLIC_ENDPOINT_REGISTER.md:85` ("`GET /api/ai/operations`, `/api/ai/providers`, `/api/ai/dataset/status` (3) … `require_ai_operator` … `test_ai_platform_authorization.py` 8/8") | Yes |
| A3 | `+339 → +341` | `list_operations` docstring amended "(operator-only)" | WS-4 `S-09` | same as A2 (documentation accompanying the guard) | Yes |
| A4 | `+346 → +348,5` | `/providers`: multi-line decorator with `Depends(require_ai_operator)` | WS-4 `S-09` | same as A2 | Yes |
| A5 | `+644 → +650,8` | `_emit_critical_alert` docstring replaced — documents `AUDIT-BYPASS-001` and canonical chaining | WS-2 `AUDIT-BYPASS-001` | `GULA_AUDIT_BYPASS_FIX_REPORT.md:29,40` | Yes — in-file comment names the finding |
| A6 | `+646,16 → +659,11` | `_emit_critical_alert`: direct `AuditLog(...)` construction (NULL `chain_hash`) replaced with `log_action(...)` + dict details | WS-2 `AUDIT-BYPASS-001` | `GULA_AUDIT_BYPASS_FIX_REPORT.md:15,29,40` | Yes — the report describes this exact transformation |

Contemporaneous separation evidence: `GULA_AUDIT_BYPASS_FIX_REPORT.md:51` records "The unrelated, pre-existing `require_ai_operator` route changes in the same file (lines ~52/~339) were **left untouched** — out of scope", and `:88` repeats that they remain "unrelated uncommitted work — out of scope, untouched".

---

## 3. Cross-worktree ownership check

The same regions were inspected in every linked worktree (read-only):

| Worktree | HEAD | `require_ai_operator` in `ai.py` | `log_action` in `ai.py` | `AUD-CLIN-*` / `R-CLIN-003-A` markers in `lims/routes.py` | `Depends(get_current_user)` on quality routes |
|---|---|---|---|---|---|
| `gula-platform` | `f478676b` | 0 | 0 | 0 | absent |
| `gula-demo-preview` | `f6772ee6` | 0 | 0 | 0 | absent |
| `gula-showcase-security` | `60988833` | 0 | 0 | 0 | absent |
| `gula-wave-b` | `77a964d0` | 0 | 0 | 0 | absent |
| `gula-integration` (this) | `2206654d` | present | present | present | present |

**Conclusion:** no hunk in either blocked file can be reassigned to a sibling worktree. Attribution rests on the in-repository governance evidence cited in §2, not on worktree provenance. `/tmp/opencode/wt-pre20` is a prunable detached worktree and was not used as evidence.

No git commit in `--all` history references any of the six workstream identifiers (`git log --all --grep=...` returned empty for each), confirming all changes are uncommitted working-tree state.

---

## 4. Clean-separation analysis

| Question | Determination |
|---|---|
| Are hunks line-disjoint? | **Yes.** `git diff -U0` shows 7 + 6 disjoint hunks; no two workstreams edit the same line. |
| Can hunk-level separation be done without rewriting work? | **Technically yes** — patch-level staging (`git add -p`) could isolate hunks; the working tree, tests and AST guards would remain intact because staging does not remove working-tree content. |
| Is separation authorized now? | **No.** GULA-PBR-2026-11-19 §16 prohibits commits, pushes, merges, PRs and broad staging. All work stays uncommitted. |
| Would separation alone unblock a commit? | **No.** The positional-call AST guard (`test_audit_positional_regression.py`) validates the whole tree; staging a subset does not change that. Each workstream's owner must sign off on its own hunk set. |
| May WS-1/WS-2 hunks be extracted by discarding WS-3/WS-4? | **No** — explicitly prohibited ("Never remove another workstream's changes merely to enable a commit"). |
| Is any workstream's ownership still ambiguous? | **No** for WS-1/WS-2/WS-3/WS-4. WS-4's *individual contributor* is not named in the evidence; its owning *workstream* (`S-09`/`S-12`) and tests are documented. This does not block attribution, but an owner sign-off is still required before any commit. |

**Final commit status:** `BLOCKED` for both files. No staging, commit, push, merge or PR performed. All changes preserved byte-for-byte in the working tree.

---

## 5. Strict status classification

| Item | Status |
|---|---|
| Change-level provenance established for all 13 hunks | `IMPLEMENTED` (documentary evidence assembled from in-repository reports; this report is not a new independent review award) |
| Clean hunk-level separation technically possible | `IMPLEMENTED` (analysis only) |
| Exact-path commit of either file | `BLOCKED` (no-commit authority + owner sign-off required) |
| Owner sign-off for WS-4 `require_ai_operator` / `S-12` | `BLOCKED` (owner-gated; no approval invented) |

---

## 6. Non-claims

No `PRODUCTION READY`. No `INDEPENDENTLY VERIFIED` award is self-granted by this report for the underlying fixes (their awards were made previously by fresh-context reviewers and are cited). No clinical, legal, regulatory, ministerial or release approval. No owner authorization claimed. No commit, push, merge, PR, deployment, production DB/Redis access, real PHI, or secrets. Standing release decision remains **HOLD**; Stable v1.0.0 is **NOT declared**.
