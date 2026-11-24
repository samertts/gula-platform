# GECS — ACTIVATION BASELINE (Phase 0, captured before any modification)

**Task:** GECS Approval Activation & Controlled Execution · **Date:** 2026-11-17
**Purpose:** prove the state at the moment D-001…D-004 approval authority was granted, so every
later change is attributable. Read-only capture; nothing cleaned or reordered.

## 1. Repository identity

| Item | Value |
|---|---|
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` |
| Branch | `integration/gula-unification-v1` |
| Commits this session | 0 (none made) |
| Modified (unstaged) | 80 |
| Renamed (staged, R100) | 20 — the `workflow_runtime` → `archive/legacy/workflow_runtime/` set |
| Untracked | 91 (89 pre-existing + `ARCHITECTURE_DECISION_PACKAGE_W1.md` + `GOVERNANCE/GECS/`) |
| Staged content edits | 0 |

## 2. Evidence fingerprints (re-verified at baseline, before activation)

| File | md5 |
|---|---|
| `GOVERNANCE/W1_CHECKPOINT.md` | `ab863d68ec57a1e36a615e02e7afe044` |
| `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md` | `e7b13d1746945c7dfb78cc39880ddeba` |
| `GOVERNANCE/UNIFICATION_BLOCKERS.md` | `04c022794605a288c1956f6b50c68d74` |
| `GOVERNANCE/ADR_DECISION_REQUEST.md` | `0b533cc4126d35355bb0ef990e9fe9c2` |
| `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` (HOLD ×2, lines 13/361) |
| `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md` | `9b466620e0925cac381a99cbd5b10372` — **will change only by §A11 approval annotation** |

## 3. GECS registry state at baseline (before activation)

| Registry | md5 | Rows |
|---|---|---|
| `WORK_REGISTRY.md` | `39871535bbb02ea70fc7523eb7eb8ff3` | 42 (VERIFIED 13 · IN_PROGRESS 7 · BLOCKED 11 · PENDING_APPROVAL 4 · NOT_STARTED 6 · FAILED 1) |
| `FINDINGS_REGISTRY.md` | `266c4606a5d532d82681443d34eddb4f` | 64 |
| `DECISION_REGISTRY.md` | `705dc05241aae3575d724e9d53201a2a` | 22 — **D-001…D-004 all `PENDING_APPROVAL — NOT APPROVED`** |
| `EVIDENCE_REGISTRY.md` | `fd8b229984527cd671add401be2c00b1` | 40 |
| `BLOCKER_REGISTRY.md` | `5ee10484dcc0190b6bd94018f3f8581c` | 36 (B-001…B-004 OPEN) |
| `PHASE_GATES.md` | `0e9174c804db44ad83b95cb4cc71d903` | 12 (G-01 NOT MET) |
| `CHANGE_CONTROL.md` | `329c609bd3c3c957915f3eeb96766d23` | CC-001, CC-002 |
| `DUPLICATE_PREVENTION.md` | `9e302392da797c9fc20490d50a6e23e8` | 7-step protocol |
| `MASTER_CONTROL.md` | `c5a701531d0380bbd8bd41e63f99cfd5` | release HOLD; scope category A |
| `GECS_CHECKPOINT.md` | `4839d14f93bb1ccf8d6097312ff95657` | audit PASS |

## 4. Prior external evidence (volatile, unchanged by this capture)

Strict suite: run#1 `753 passed / 119 failed / 0 skipped` (273.09 s, exit 1) · run#2 `750 / 122` ·
SQLite control `872 / 0` (exit 0) · schema fingerprint
`3b2d9499d019503bf1ff5644f713cd5f272705f544862d8022887a516f973568` (zero-DDL sentinel) ·
harness `/tmp/opencode/strict-w1/` + `/tmp/opencode/remediation/w1/`.

## 5. Unexpected-change watch

Any working-tree delta **not** attributable to (a) prior uncommitted unification/security work,
(b) `GOVERNANCE/` files created/updated by this task, is classified and preserved untouched, and
the affected phase stops per mandate §12. Baseline counts above are the comparison anchor.

## 6. Authority granted at this checkpoint

Per the OpenCode task instruction (§1): **project-owner approval of D-001, D-002, D-003, D-004**
with the six recording conditions. Explicitly **not** granted: D-020, D-021, Platform-Core
refactoring, architecture changes beyond the four decisions, any irreversible action.
