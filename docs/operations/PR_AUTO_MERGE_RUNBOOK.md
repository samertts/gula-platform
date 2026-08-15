# Pull Request Auto-Merge Runbook

## Purpose

GULA uses an opt-in GitHub Actions workflow to request GitHub auto-merge after the repository's CI pipeline succeeds. The workflow does not bypass branch protection, required reviews, required status checks, conversation resolution, or deployment policies. It also does not merge or deploy during a dry run.

## Policy gate

A pull request is eligible only when all of the following are true:

| Gate | Requirement |
|---|---|
| Target | The base branch is `main`. |
| Source | The head branch belongs to `samertts/gula-platform`, not an untrusted fork. |
| State | The pull request is open and not a draft. |
| Intent | The pull request has the explicit `automerge-approved` label. |
| Quality | The triggering `CI Pipeline` run completed successfully. |
| Governance | GitHub branch protection still decides whether the pull request can merge. |

The label is an explicit opt-in signal. It is not a substitute for a human review when `main` requires an approving review from someone other than the last person who pushed.

## Dry-run procedure

The default manual mode is `dry-run`. It evaluates a pull request and writes an eligibility report to the Actions summary without requesting auto-merge:

```bash
gh workflow run "Opt-in PR Auto-Merge" \
  --repo samertts/gula-platform \
  --ref feat/fhir-interoperability-20260815 \
  -f pull_request=209 \
  -f mode=dry-run
```

Review the run under **Actions → Opt-in PR Auto-Merge**. The summary must show the expected base branch, source repository, open/non-draft state, label state, and `Production merge/deploy performed | false`.

## Arming auto-merge

After a successful dry run, a maintainer may explicitly arm auto-merge:

```bash
gh workflow run "Opt-in PR Auto-Merge" \
  --repo samertts/gula-platform \
  --ref feat/fhir-interoperability-20260815 \
  -f pull_request=209 \
  -f mode=arm
```

Alternatively, the workflow can arm a qualifying pull request automatically after a successful `CI Pipeline` run when the `automerge-approved` label is present. GitHub remains authoritative: if required reviews or any other protected-branch condition are not satisfied, the pull request stays open.

## Safety boundaries

The workflow uses the minimum repository token permissions needed to inspect pull requests and request GitHub auto-merge. It does not use `--admin`, force pushes, direct writes to `main`, `pull_request_target`, or production credentials. It does not alter branch protection settings and it does not perform a production deployment.

For a healthcare production repository, keep at least one independent approval, the complete security and migration gates, and conversation resolution enabled on `main`. Use this runbook as an operational convenience, not as a replacement for review or release governance.

## Troubleshooting

If the workflow reports `missing explicit automerge-approved label`, add the label only after the change has passed review. If it reports that the base is not `main`, do not arm it; create or retarget the pull request correctly. If it reports a missing review after auto-merge is requested, ask an authorized maintainer to review the latest commit. A new push may invalidate or require a fresh approval depending on the active branch rule.
