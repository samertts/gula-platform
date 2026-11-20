# 03 — Branch and Pull Request Graph — GULA-NATIONAL-COMPLETION-013

## Scope

Dependency and safety analysis of the requested PRs and their branches, including stacked relationships and migration revision collisions.

## Methodology

For each PR: REST metadata, base/head refs, mergeability, check-run conclusions, `compare/main...head`, and selective file/revision inspection. All calls read-only.

## Environment

See `02_GITHUB_REPOSITORY_INVENTORY.md`.

## Commands and exit codes

Representative commands; full list in `evidence/github_inventory_commands.md`. All exit codes 0 unless noted.

```bash
for n in 261 260 259 258 257 256 255 252 251 250 249 248 247 245 242 241 240; do
  gh api "repos/samertts/gula-platform/pulls/$n" --jq '{number,state,draft,base:.base.ref,head:.head.ref,head_sha:.head.sha,mergeable,mergeable_state,changed_files,additions,deletions,commits,updated_at}'
done
for n in ...; do
  sha=$(gh api "repos/samertts/gula-platform/pulls/$n" --jq .head.sha)
  gh api "repos/samertts/gula-platform/commits/$sha/check-runs" --jq '[.check_runs[] | {name,status,conclusion}]'
done
```

## Evidence paths

- `evidence/github_inventory_commands.md`
- `evidence/github_inventory_summary.json`
- `evidence/critical_defect_research.md`

## Findings

|  PR | Draft | Base ← Head                                  | Changed files | Checks (S/F/K) | Assessment                                           |
| --: | :---: | -------------------------------------------- | ------------: | -------------- | ---------------------------------------------------- |
| 261 |  yes  | main ← `claude/independent-audit-1`          |           394 | 14/16/3        | Valuable patch source; unsafe wholesale              |
| 260 |  yes  | #251 head ← design ref                       |            44 | 1/4/0          | Design reference only                                |
| 259 |  no   | main ← `claude/mustafa-parallel-engineering` |           261 | 1/21/5         | Substantial but failing; X-Role not a trust boundary |
| 258 |  yes  | #257 head ← pharmacy reconciliation          |           529 | 1/5/0          | Slice only                                           |
| 257 |  yes  | #256 head ← hospital migrations              |             3 | 1/4/0          | Targeted; conflicts with #261 revision               |
| 256 |  yes  | main ← NR-003 drug identity                  |             8 | 10/17/0        | Targeted; modifies historical migration              |
| 252 |  yes  | main ← ontology governance                   |            18 | 6/16/5         | Feature-flagged; not completion proof                |
| 251 |  yes  | main ← idempotency branch                    |            21 | 1/21/5         | Tenant-isolation defect source                       |
| 249 |  yes  | #245 head ← SQLite safety                    |            19 | 1/4/0          | Depends on #245                                      |
| 247 |  yes  | #241 head ← external ingestion               |           127 | 1/0/0          | Dirty/conflicted                                     |
| 245 |  yes  | main ← migration graph                       |           152 | 1/24/9         | Failing migration gate                               |
| 242 |  yes  | develop ← clinical safety                    |           296 | 1/17/6         | Wrong base for main delivery                         |
| 241 |  yes  | main ← mobile dependency audit               |           149 | 1/28/17        | Failing                                              |
| 240 |  yes  | main ← DDoS hardening clean                  |           398 | 1/30/23        | Dirty/conflicted                                     |

**Stacked chains:**

- `#251 → #260`
- `#255 → #256 → #257 → #258`
- `#245 → #249`
- `#241 → #247 → #250`
- `#261`, `#259`, `#252`, `#248` branch directly from `main` but are stale/divergent.
- `#242` bases on `develop`.

**Migration collision:** both #261 and #257 define Alembic revision `20260820_0003` with different filenames/content and repoint `20260820_0004`. They cannot both be applied.

## Verification state

`HUMAN APPROVAL REQUIRED` for any merge or retarget; `RECONCILED` for the dependency map as observed.

## Limitations

- PR bodies were reviewed for stated dependencies but not treated as test evidence.
- File-level review of all 394 #261 files was not performed; targeted patches were reviewed.

## Residual risks

- Cherry-picking from a stacked PR without its ancestors can produce incomplete migrations or missing contracts.
- No PR provides a green delivery baseline.

## Required actions

Do not merge PRs. Reimplement narrowly on the isolated branch, and cite PR patches only as prior attempted fixes in the findings register.
