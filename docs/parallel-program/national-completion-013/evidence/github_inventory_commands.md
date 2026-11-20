# GitHub inventory commands — read-only

All commands were executed with `gh api` against `samertts/gula-platform`. No command modified repository settings, branches, PRs, issues, or local files.

```bash
gh api repos/samertts/gula-platform --jq '{full_name,private,default_branch,size,stargazers_count,forks_count,open_issues_count,created_at,updated_at,pushed_at,license:.license.spdx_id,archived,disabled}'
gh api repos/samertts/gula-platform/git/ref/heads/main --jq '{ref:.ref,sha:.object.sha,type:.object.type}'
gh api repos/samertts/gula-platform/commits/main --jq '{sha:.sha,date:.commit.committer.date,message:.commit.message}'
gh api repos/samertts/gula-platform/branches/main/protection --jq '{url:.url,required_status_checks:.required_status_checks,enforce_admins:.enforce_admins.enabled,required_pull_request_reviews:.required_pull_request_reviews,restrictions:.restrictions}'
gh api --paginate 'repos/samertts/gula-platform/branches?per_page=100' --jq '.[] | [.name,.commit.sha,.protected] | @tsv'
gh api --paginate 'repos/samertts/gula-platform/pulls?state=open&per_page=100' --jq 'length'
gh api --paginate 'repos/samertts/gula-platform/issues?state=open&per_page=100' --jq 'map(select(has("pull_request")|not)) | length'
gh api --paginate 'repos/samertts/gula-platform/actions/workflows?per_page=100' --jq '.workflows[] | [.id,.name,.state,.path] | @tsv'
gh api 'repos/samertts/gula-platform/actions/runs?per_page=50' --jq '.workflow_runs[] | [.id,.created_at,.name,.event,.status,.conclusion,.head_branch,.head_sha[0:7]] | @tsv'
sha=$(gh api repos/samertts/gula-platform/git/ref/heads/main --jq .object.sha)
gh api --paginate "repos/samertts/gula-platform/commits/$sha/check-runs?per_page=100" --jq '.check_runs[] | {name,status,conclusion}'
for n in 261 260 259 258 257 256 255 252 251 250 249 248 247 245 242 241 240; do
  gh api "repos/samertts/gula-platform/pulls/$n" --jq '[.number,.state,(.draft|tostring),.base.ref,.head.ref,.head.sha,(.mergeable|tostring),.mergeable_state,(.commits|tostring),(.changed_files|tostring),(.additions|tostring),(.deletions|tostring),.updated_at] | @tsv'
  sha=$(gh api "repos/samertts/gula-platform/pulls/$n" --jq .head.sha)
  gh api --paginate "repos/samertts/gula-platform/commits/$sha/check-runs?per_page=100" --jq '.check_runs[] | {name,status,conclusion}'
  gh api "repos/samertts/gula-platform/compare/main...$sha" --jq '[.status,(.ahead_by|tostring),(.behind_by|tostring),(.total_commits|tostring)] | @tsv'
done
gh api --paginate 'repos/samertts/gula-platform/releases?per_page=100' --jq '.[] | [.tag_name,.name,(.draft|tostring),(.prerelease|tostring),.published_at,.html_url] | @tsv'
gh api --paginate 'repos/samertts/gula-platform/tags?per_page=100' --jq '.[] | [.name,.commit.sha] | @tsv'
```

Observed failures on `main` HEAD included: Backend Tests, Migration Check, PostgreSQL migration/schema gate, Security and tenant isolation regression, Frontend v3 gates, Constitution Compliance, Prettier, Ruff Format, Secret Scan, Dependency Review, Python Dependency Audit, Build Linux, `foundation-ci`.

Nightly Build runs on 2026-11-17 through 2026-11-20 all reported `startup_failure`. Security Hardening on 2026-11-16 failed at `Gitleaks history scan` and `Audit pinned manifest`.
