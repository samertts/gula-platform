# Historical `.env` incident — redacted review and required owner action

**Generated:** 2026-11-20 UTC · **Scope:** read-only Git history analysis
**Constraint honored:** no secret value, prefix, suffix or raw line is reproduced; no reuse of the
value; no history rewrite, force-push, file deletion from published history, or credential access.

## 1. Findings (redacted)

| Field | Record |
|---|---|
| Affected provider | **DeepSeek** — variable name `DEEPSEEK_API_KEY`; OpenAI-compatible `sk-`-prefixed key family |
| Introduced in | commit `d2863c3555ebc6ee67a68546b225660ab6abcd1d`, 2026-03-08, "Initial NHOP platform commit" |
| Classification | high-entropy credential-shaped value: length 35, 17 distinct characters, ≈3.95 bits/char, no placeholder marker. Two sibling values in the same file contain placeholder words and are not treated as live credentials. |
| Exposure status | `git merge-base --is-ancestor <commit> origin/main` → 0 (yes): the item has been on public `origin/main` since 2026-03-08, months before this workstream. |
| Current tree | `.env` **absent** from HEAD; it was removed in commit `2535bb1e` ("Security hardening: remove exposed ports, enforce secrets, add HTTPS"). |
| Rotation evidence in history | **ROTATION UNVERIFIED.** `git log -S DEEPSEEK_API_KEY -- .env` shows only the introduction commit `d2863c35` and removal commit `2535bb1e`. A redacted comparison script confirmed the variable exists with a value only in `d2863c35`; later `.env` revisions do not carry it. The only DeepSeek rotation reference is a generic dated runbook (`security-audit/2026-08-12/secret-rotation-runbook.md`), **not** a dated provider-side revocation/replacement record. Absence of the file is not evidence of rotation. |
| New exposure from this work | **None.** The single backup-branch push was at committed HEAD and introduced no credential. |

Method: the blob was piped into a local redaction script that emits only variable name, provider
attribution, shape class, length, distinct-character count and entropy — never the value. A second
local script compared only SHA-256 digests of the in-history values and printed a boolean equivalence
verdict (`BASELINE` / `SAME_VALUE_AS_BASELINE` / `DIFFERENT_VALUE`) — never a value or a digest.
Both scripts live outside the repository (`/tmp/opencode/`) and no output value or digest was written
to any repository file. No connection to the provider was made and no provider setting or key was
touched.

## 2. Live references (names only)

- `backend/app/ai_fabric/gateway.py:101-103` — provider config `DEEPSEEK_API_KEY`, `https://api.deepseek.com/v1`, models `deepseek-chat` / `deepseek-coder`.
- `ai/ai_service.py:8,26` — legacy top-level service reads `DEEPSEEK_API_KEY` and calls the DeepSeek endpoint.
- `security-audit/2026-08-12/secret-rotation-runbook.md` — existing provider rotation checklist (pre-existing document; not modified here).
- `docs/freeze/pi-005/RELEASE_NOTES.md:106` — documents the environment variable name.

## 3. Required owner action (NOT performed, NOT authorized here)

1. **Revoke/invalidate the exposed DeepSeek key at the provider dashboard immediately.** Treat it as
   compromised because it has been public since 2026-03-08. Do not reuse any part of the old value.
2. Issue a replacement key with least privilege, provider-side spend/usage limits and IP/domain
   restrictions where available.
3. Store the replacement only in the approved secret store / deployment environment; never in a
   tracked file. Rotate every deployment or clone that consumed the old key.
4. Review DeepSeek usage, billing and access logs for the exposure window for unauthorized activity;
   record findings in the incident register.
5. Record the rotation date, owner and provider key ID (not the value) in the security record.
6. **No history rewrite, no force-push, no deletion of the file from published history.** Any such
   action requires a separate owner decision and coordination across all clones and forks; it is
   prohibited by the current guardrails.

## 4. Gate decision

- **Status: `ROTATION UNVERIFIED`.** No trusted evidence of provider-side revocation or replacement
  was found in the repository or history. The owner must not assume the key is safe because the file
  was deleted from later commits.
- Worktree secret scan remains **PASS** (`AUDIT_EXECUTION_RECORDS/SECRET_SCAN_RECORD.md`).
- Required owner action sequence: (1) revoke/invalidate the exposed DeepSeek key at the provider
  console; (2) issue a least-privilege replacement with spend and network restrictions; (3) update
  the approved secret store and every consumer; (4) review provider usage and billing for the
  exposure window; (5) record rotation date, owner and provider key ID — never the value.
- This is a registered pre-existing incident requiring owner action, **not** a regression from this
  workstream and **not** a blocker for the already-verified P-13/P-15/P-16/P-01/P-04 engineering
  results. It remains open until the owner records rotation and exposure assessment.
- No `ACCEPTED` or `PRODUCTION READY` award is made here. HOLD unchanged; `production_ready_items = 0`.
