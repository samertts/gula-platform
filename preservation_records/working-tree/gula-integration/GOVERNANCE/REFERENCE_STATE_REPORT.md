# Reference State Report

**Program:** GULA Stable v1.0.0 — Continuation
**Report date:** 2026-11-15T10:35:32Z (2026-11-15 13:35:32 +03)
**Scope:** Re-establish the actual state of `gula-integration` from the filesystem before further work.
**Result:** **PASS for state verification.** The repository, backup, and reported full-suite evidence are present and internally consistent. Full-suite execution was not re-run for this initial snapshot; the source tree has no backend/test/shared/migration file newer than the retained log.

> This report is evidence, not certification. All changes remain uncommitted and unpushed.

## 1. Repository identity

| Check | Observed | Status |
|---|---|---|
| Integration worktree | `/home/samertts/workspace/projects/gula-integration` | PASS |
| Branch | `integration/gula-unification-v1` | PASS |
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | PASS |
| Tracked files in worktree | 6465 | INFO |
| Staged entries | 20 (`R100` renames, 0 content changes) | PASS |
| Unstaged modified files | 32 | PASS (preserved) |
| Untracked entries | 160 | PASS (preserved) |
| Worktrees registered | 6, including the primary repository and integration worktree | PASS |
| Prunable worktree | `/tmp/opencode/wt-pre20` (missing gitdir) | INFO — not touched |

### Staged changes
All 20 staged entries are rename-only archive moves into `archive/legacy/workflow_runtime/`:
- `backend/app/identity/workflows/{engine,models}.py`
- `backend/app/national/workflow_runtime/**` (17 files)
- `backend/app/platform/workflow.py`

The staged diff is `20 files changed, 0 insertions(+), 0 deletions(-)`.

### Unstaged changes
32 modified tracked files, concentrated in:
- workflow/search/PDF integration (`factory.py`, `identity/api/router.py`, `capabilities/search_service/*`, `document_intelligence/*`, `national/document_platform/*`);
- NR-003/NR-009/NR-010 migration repairs;
- full-suite fixes (`blood_bank/domain/state_machine.py`, `tests/test_niam_v2.py`, `tests/test_document_intelligence.py`);
- communication/circuit-breaker/notification integration (`shared/circuit_breaker.py`, `shared/notifications/__init__.py`, `platform/notifications.py`);
- database bridge/model registration (`database.py`, `models/__init__.py`, `identity/base.py`, `identity/models/audit.py`).

No staged or unstaged content was reverted, cleaned, or reset.

### Untracked changes
160 untracked entries are preserved, including:
- `GLOSI/` (governance, registry, tools, tests, decision records, reports);
- `GOVERNANCE/` reports/evidence;
- ported backend domains/tests/migrations/scripts;
- `shared/communication*` and Telegram notification modules.

No untracked file was removed.

## 2. Primary repository protection

| Check | Observed | Status |
|---|---|---|
| Primary path | `/home/samertts/workspace/projects/gula-platform` | PASS |
| Branch | `remediate-security-001` | PASS |
| HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | PASS |
| Dirty entries | 0 | PASS |

The primary worktree was not modified during this verification. All implementation work is confined to `gula-integration`.

## 3. Recovery backup

| Check | Observed | Status |
|---|---|---|
| Path | `$HOME/GULA_RECOVERY_BACKUP_20261114_190243` | PASS |
| Size | 136 MB | PASS |
| Readable | Yes | PASS |
| Manifest | `SHA256SUMS.txt`, 12 entries | PASS |
| Checksums | `sha256sum -c SHA256SUMS.txt` — all 12 OK | PASS |
| Contents include | all-refs bundle, showcase archive, patch files, commit/status snapshots | PASS |

Backup was not modified.

## 4. Reported full backend suite

| Check | Observed | Status |
|---|---|---|
| Log | `/tmp/opencode/full_suite_integration_2.log` | PASS |
| Log timestamp | 2026-11-15 13:25:08 +03 | INFO |
| Log size | 31,248 bytes | INFO |
| SHA-256 | `03dd5d263f24e9e909ce90008a1f24629ebf25f7b90655b4cd3c459b824a1479` | PASS |
| Collected | 3,162 items | PASS |
| Result line | `3135 passed, 27 skipped, 165 warnings in 577.65s` | PASS |
| Failure/error line | None in retained summary | PASS |
| Source newer than log | 0 files under `backend/app`, `backend/tests`, `shared`, `backend/migrations` | PASS |
| Exit code in log | Not embedded; success is evidenced by the pytest summary | INFO |

**Interpretation:** the retained log is consistent with the current source tree and reports a successful run of 3,135 passing and 27 skipped tests. It is not a substitute for the final post-change suite run, which remains required.

## 5. Test-tree inventory (initial comparison)

Compared `.py` test files under `backend/tests` between the local primary worktree (`f478676b`) and the integration worktree:

| Measure | Count |
|---|---:|
| Local test files | 282 |
| Integration test files | 254 |
| Common paths | 154 |
| Byte-identical | 34 |
| Modified | 120 |
| Local-only | 128 |
| Integration-only | 100 |

Reference counts previously reported were 146 local-only and 120 modified. The modified count matches. The local-only count differs (128 vs 146), so the reference values are **not** accepted as current. Full reconciliation, including which local-only tests must be ported with preserved features, is tracked separately.

No test file has been deleted by this verification.

## 6. Current status summary

| Area | Status | Evidence |
|---|---|---|
| Repository state | PASS | branch/HEAD/status/worktrees recorded above |
| Primary repository untouched | PASS | clean at `f478676b` |
| Backup integrity | PASS | manifest checksums all OK |
| Reported full-suite evidence | PASS (validated, not re-run) | log hash/summary; no source newer |
| Full-suite post-change validation | NOT RUN | required before final assessment |
| MIG-EXISTING | BLOCKED / NOT VERIFIED | no supported snapshot identified yet |
| Frontend-v3 integration | NOT RUN | no frontend merge performed yet |
| GOC | DISCOVERY IN PROGRESS | no runtime code created |
| Security certification | NOT CLAIMED | human review outstanding |

## 7. Exact commands used

```bash
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git diff --cached --stat
git diff --stat
git ls-files --others --exclude-standard | wc -l
git worktree list --porcelain

git -C /home/samertts/workspace/projects/gula-platform branch --show-current
git -C /home/samertts/workspace/projects/gula-platform rev-parse HEAD
git -C /home/samertts/workspace/projects/gula-platform status --porcelain=v1

du -sh "$HOME/GULA_RECOVERY_BACKUP_20261114_190243"
cd "$HOME/GULA_RECOVERY_BACKUP_20261114_190243" && sha256sum -c SHA256SUMS.txt

tail -25 /tmp/opencode/full_suite_integration_2.log
sha256sum /tmp/opencode/full_suite_integration_2.log
find backend/app backend/tests shared backend/migrations -type f \
  -newer /tmp/opencode/full_suite_integration_2.log -print | wc -l
```

---
_Report generated from filesystem evidence. All work remains uncommitted and unpushed._
