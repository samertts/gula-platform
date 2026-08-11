# GULA — Change Control

**Document class:** AUTHORITATIVE change-control record + policy
**Date:** 2026-08-11
**Scope:** Governs every change to the GULA platform repository across all
programs/waves. Supersedes nothing; complements PROGRAM-MIGRATION-001 and
ADR-037.

---

## 1. Change Classification

| Class | Definition | Gate |
|---|---|---|
| **A — Audit/read-only** | Inspect, scan, verify, document. No production file modified. | None (log only) |
| **B — Doc/planning** | New/updated planning documents under `docs/`, `.ai/`, reports. | None (log only) |
| **C — Behavior-preserving refactor** | Renames, moves, archive-first migrations. Runtime/API unchanged. | Program Director + verification cycle |
| **D — Behavior-changing fix** | Bug fix, security fix, feature. Runtime/API/DB behavior changes. | PD approval + ADR if architectural + full test suite |
| **E — Destructive** | Delete data, drop DB, breaking API, license change, paid service, credential exposure. | **Explicit PD + human approval; never automatic** |

## 2. Change Control Board / Ownership

- **Program Director (PD):** approves Wave starts (Wave B and beyond of the
  successor program require PD approval; branch `wave-b/B1-abac-route-enforcement`
  remains unmerged until then).
- **Autonomous agents:** may execute Classes A–C autonomously under the
  constitution; must STOP for Class D/E and for any wave entry.
- **Concurrent sessions:** their branches/worktrees/stash are protected. No
  `reset --hard`, `clean -fd`, `checkout -- .`, `restore .`, force-push, rebase,
  or branch deletion. Never modify files another session owns.

## 3. Change Record

### Audit session 2026-08-11 (this program set)

| # | Class | Change | Commit | Notes |
|---|---|---|---|---|
| CR-1 | A | Full repository audit (DISCOVER→VERIFY→AUDIT→CLASSIFY→MAP→PLAN→STOP) | — | Read-only; zero production changes |
| CR-2 | B | `GULA_CURRENT_REPOSITORY_STATE.md` | PENDING | Evidence: S1–S9, C1–C4, risks R-01..R-14 |
| CR-3 | B | `GULA_MASTER_GAP_MATRIX.md` | PENDING | 7 surfaces, priority P0–P3 |
| CR-4 | B | `GULA_TARGET_ARCHITECTURE.md` | PENDING | Target blueprint |
| CR-5 | B | `GULA_APPLICATION_ECOSYSTEM.md` | PENDING | Web/Android/iOS/Desktop/store/experimental |
| CR-6 | B | `GULA_MASTER_EXECUTION_PLAN.md` | PENDING | Waves 0–17, PD-gated |
| CR-7 | B | `GULA_RISK_REGISTER.md` | PENDING | R-01 CRITICAL, 5 HIGH, 7 MEDIUM, 2 LOW + governance |
| CR-8 | B | `GULA_DEPENDENCY_GRAPH.md` | PENDING | L0–L3 layers + risks |
| CR-9 | B | `GULA_CHANGE_CONTROL.md` | PENDING | This document |
| CR-10 | B | `GULA_FINAL_REPORT.md` | PENDING | 15-point deliverable |

**Non-goals of this session (explicitly NOT changed):**
- No production code, routes, models, migrations, or workflows modified.
- No branch created/deleted; no push performed.
- No `git stash` content touched (`stash@{0}` preserved).
- Concurrent branches (`manus/admin-workspace-20260811`, `security-hardening-demo-alignment`, `wave0-audit-hardening-20260811`) untouched; `origin/main` NOT merged.

## 4. Commit Procedure (for pending docs)

1. Scope: the 7 planning docs + change control + final report (10 files) only.
2. Stage exactly those files; verify `git status` shows nothing else.
3. Commit message (Conventional Commits):
   `docs(program): add GULA repository audit program set (state, gap, target, execution, risk, dependency, change control, report)`.
4. No code, no workflows, no secrets in this commit.
5. Do NOT push; await PD review (branch `remediate-security-001`).

## 5. Wave Gate Checklist (used for every wave)

- [ ] PD approval recorded
- [ ] Scope frozen (no silent creep)
- [ ] Impact analysis (OpenAPI/frontend/consumers/permissions/models)
- [ ] Behavior preserved (Classes C) or change documented (Class D)
- [ ] Regression suite green (backend 5,089 + frontend 122 + architecture gate)
- [ ] Migration Impact Report (PROGRAM-MIGRATION-001) where applicable
- [ ] Single `git revert` restores prior state
- [ ] Wave report written; STOP for next approval

## 6. Escalation

- Any CRITICAL risk (score ≥20) → immediate PD review (current: R-01 iOS).
- Any Class E intent → human approval, never autonomous.
- Security finding HIGH+ in production surface → fix in Wave 1 before any
  store-facing or production expansion.

---

*This register is append-only in spirit: new changes append new CR entries.
Companion: `GULA_MASTER_EXECUTION_PLAN.md` (wave gates), `GULA_RISK_REGISTER.md`.*
