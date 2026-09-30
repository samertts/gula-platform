# Independent agent — scope, isolation and method

**Worktree:** `/home/user/gula-audit` · **Branch:** `claude/independent-audit-1` ·
**Base:** `203c85aa` on `claude/autonomous-run-1`.

## A disclosure that matters for reading these findings

This agent and the agent that produced commits up to `203c85aa` on
`claude/autonomous-run-1` are **the same session**. The brief that created this
role describes a "primary agent" owning NR-164; NR-164 does not exist in this
lane's register, which ends at NR-089. NR-164 belongs to the **sibling lane**,
`claude/p0-2-pharmacy-reconciliation` (PR #258), which is a different branch in a
different container.

So "independent" here means one thing honestly and not another:

* **Honest:** this pass works in its own worktree, touches no file the sibling
  lane owns, and re-derives every claim from the code rather than from the
  register.
* **Not claimed:** independence from the author of `claude/autonomous-run-1`.
  Where a finding concerns that lane's own work it is marked SELF-REVIEW, because
  a second look by the same author is worth less than a second author and saying
  otherwise would be the kind of false assurance this whole register exists to
  prevent.

## Method

Every finding below was reached the same way, and the order is deliberate:

1. a cheap structural sweep to locate candidates;
2. **reading the candidate**, because three of this pass's five leads died there;
3. measuring the *effective* path — for routes that means the served OpenAPI
   surface and router-level dependencies, never the route signature;
4. only then a severity.

The three leads that died are recorded in `findings.md` as verified negatives
rather than dropped. A sweep that reports only what survived is a sweep whose
false-positive rate you cannot see.

## Isolation actually held

`git worktree list` shows two trees on two branches. Nothing outside
`/home/user/gula-audit` was written during this pass. No push, no force-push, no
history rewrite, no branch checkout in the other tree.
