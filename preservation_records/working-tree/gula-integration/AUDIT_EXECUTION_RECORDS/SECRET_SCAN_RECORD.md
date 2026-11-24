# SECRET / CREDENTIAL SCAN RECORD — Phase 1 preservation gate

**Generated:** 2026-11-20 UTC · **Repo:** `gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Method:** deterministic Python regex classifier over (a) full Git history, (b) all tracked files,
(c) all untracked non-excluded files, (d) binary detection via NUL-byte probe.
**Output policy:** counts and paths only — **no secret value, matched line, or context was printed.**

## 1. Pattern set

`github_token` (`gh[pousr]_…`), `openai_style` (`sk-…`), `aws_akia` (`AKIA…`),
`private_key` (`-----BEGIN … PRIVATE KEY-----`), `slack` (`xox…`), `jwt` (`eyJ…eyJ…`).
Placeholder heuristic: `your|example|placeholder|dummy|test|xxxx|changeme|api_key|here|fill|replace|sample|fake|redact`.

## 2. Results

| Scope | Files scanned | Binary | Placeholder hits | Review-required hits | Disposition |
|---|---:|---:|---:|---:|---|
| Full Git history (`git log --all`) | all commits | — | — | 20 raw matches | 19 classified as test fixtures / scanner literals / docs; 1 pre-existing committed `.env` (§3) |
| Tracked worktree | 6514 | 13 | 0 | 3 | 3 PEM header **literals only** — no `END` marker, no base64 body (docs/DEPLOYMENT.md:52; engineering/security/bandit.py:108-109) |
| Untracked worktree | 651 | 0 | 0 | 0 | clean |
| Binary files | 13 | 13 | 0 | 0 | binary NUL-probe included in tracked scan; no embedded high-entropy token |

**Worktree verdict: PASS.** No real credential, private key, token, PHI or secret was found in any
tracked or untracked file. All matches are documentation strings, scanner detection literals, or
test fixtures.

## 3. Pre-existing history item — registered, NOT introduced by this work

- A committed `.env` in commit `d2863c3555ebc6ee67a68546b225660ab6abcd1d`
  (`2026-03-08`, "Initial NHOP platform commit") contains one `sk-`-prefixed API-key-shaped value
  (35 chars, 17 distinct chars, 3.95 bits/char entropy, no placeholder word) under
  `DEEPSEEK_API_KEY`; two sibling values carry placeholder words.
- `git merge-base --is-ancestor d2863c35… origin/main` → **0 (yes)** — this commit is already on the
  public `origin/main` branch, 8+ months before this session. The backup-branch push performed in
  this work therefore introduced **no new exposure**.
- The file is **absent** from the current HEAD tree (`git cat-file -e HEAD:.env` → non-zero).
- **Owner action required (not performed, not authorized here):** rotate that provider key and
  assess exposure; any history purge would require an explicit owner decision and coordinated
  force-push across all clones — prohibited under the current no-history-rewrite / no-force-push
  guardrails. No value is reproduced in this record.

## 4. Gate decision

- **Further external push file-scope/history gate: PASS.** The Phase 1 delta introduces no secret.
  The single history item is pre-existing and already public; it is a registered known issue, not a
  regression from this work.
- No history rewrite, force-push, key rotation, credential output, or destructive Git operation was
  performed.
