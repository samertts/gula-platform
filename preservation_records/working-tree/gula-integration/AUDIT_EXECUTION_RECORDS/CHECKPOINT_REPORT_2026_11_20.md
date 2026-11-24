# Unified checkpoint report — 2026-11-20

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`.
**Posture:** HOLD = TRUE · `production_ready_items = 0` · Stable v1.0.0 = NOT DECLARED · PRODUCTION READY = NOT AUTHORIZED.
**Scope:** read-only verification, independent document review, risk/status/documentation updates. No implementation, no new R4 package, no commit/push/PR, no production access.

---

## 1. Actual state after verification

| Check | Result |
|---|---|
| Branch / HEAD | `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549` — unchanged |
| Staged | 20 entries, all `R100`; name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` — unchanged |
| Working tree | 162 unstaged; untracked 661 at verification start → **664** after adding 3 checkpoint documents (packet review, unified report, SHA manifest); `git diff --check` exit 0 |
| Protected MD5s | `FINAL_DECISION.md` `effdfeaf…`; `MPI_FINAL_INDEPENDENT_AUDIT.md` `1a02c015…`; `MPI_INDEPENDENT_AUDIT_FINDINGS.md` `ea3969d0…` — all unchanged |
| Sibling repo | `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91` — unchanged |
| Backup branch | `backup/gula-integration-2026-11-20` on origin at `2206654…` — unchanged |
| PR #307 | OPEN, base `main`, head `execution/gula-national-completion-013`, `headRefOid f2f950ce7a7b65683f4bfcfede0b1b2a7f0f4fed` — untouched |
| `.env` at HEAD | ABSENT |
| `production_ready_items` | 0 (both occurrences in `status_registry.json`) |
| Forbidden operations | No `reset`, `clean`, `restore`, `stash`, `git add .`, `git add -A`, force-push, history rewrite, deletion or silent overwrite |

---

## 2. Independent review of P-02 / P-03

Fresh-context read-only reviewer (`ses_e0559f72bffesRsBJZ3S5M8a9w`), corroborated locally with
`git show HEAD:<path>`. Full report: `AUDIT_EXECUTION_RECORDS/PACKET_REVIEW_2026-11-20.md`.

| Packet | Verdict | Findings | Disposition |
|---|---|---|---|
| P-02 / AUD-F02 | **FAIL — NOT DECISION-READY** | 1 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW/INFO | Return to preparation; no implementation; no owner signature |
| P-03 / AUD-F03 | **FAIL — NOT DECISION-READY** | 1 CRITICAL, 6 HIGH, 4 MEDIUM, 2 LOW/INFO | Return to preparation; no implementation; no owner signature |

**Root cause in both:** the packets take their evidence from the **uncommitted working tree**, not HEAD.
At HEAD, `routes/ai.py` still constructs `AuditLog` directly, `audit_service.py` has 270 lines with no
isolation guard, `control_plane/routes.py` has 351 lines with no approval route and takes the actor
from the request body, and `/audit-log` is at `:309-327`. Both packets' decisive RED tests declare
SQLite although the guard is PostgreSQL-only. Additional gaps: unstated `/ai/interpret` failure
impact (P-02), undefined DB session/secret-access boundary/exactly-once claim and blank scope in the
owner text (P-03), missing explicit rejection criteria in both.

Adequate in both: R4/HOLD posture, status separation, no migration/dependency/hash-semantics change,
hunk-scoped rollback, accurate staged MD5, and explicit exclusion of commit/merge/release/deploy/
`PRODUCTION READY`/HOLD change. OD-001 remains the only accepted decision (engineering scope);
OD-002…OD-025 remain BLOCKED; no package-specific owner authorization for F02/F03 exists.

---

## 3. DeepSeek incident investigation

Full record: `AUDIT_EXECUTION_RECORDS/ENV_INCIDENT_REVIEW.md`.

| Field | Result |
|---|---|
| Provider / variable | **DeepSeek** — `DEEPSEEK_API_KEY`, `sk-` key family; value **never displayed** |
| Introducing commit | `d2863c3555ebc6ee67a68546b225660ab6abcd1d`, 2026-03-08; verified ancestor of `origin/main` |
| Presence at HEAD | ABSENT (removed in `2535bb1e`) |
| Rotation evidence | **ROTATION UNVERIFIED** — `git log -S DEEPSEEK_API_KEY -- .env` shows only introduction and removal; a digest-only comparison confirmed the value existed only in the introduction commit; the sole rotation reference is a generic runbook, not a dated provider-side revocation/replacement record |
| New exposure from this work | None; no provider connection, no value/digest printed, no history change |

**Owner action required:** revoke/invalidate at the provider console; issue a least-privilege
replacement with spend and network limits; update the secret store and every consumer; review usage
and billing over the exposure window; record rotation date, owner and provider key ID — never the
value. No history rewrite, force-push or deletion from published history.

---

## 4. Open risks ordered by severity

| # | Severity | Risk | Status |
|---|---|---|---|
| 1 | HIGH | Exposed DeepSeek key, `ROTATION UNVERIFIED` | Owner action required |
| 2 | HIGH | Mixed provenance (20 staged R100 + 162 modified + 661 untracked) | Blocks commit/push/PR |
| 3 | HIGH | P-02/P-03 packets FAIL — evidence baseline is working tree, not HEAD | Rewrite + re-review required |
| 4 | MEDIUM | P-02 fail-closed impact reaches `/ai/interpret` before interpretation | Owner trade-off pending |
| 5 | MEDIUM | P-03 actor attribution, DB session, secret boundary, exactly-once unverified | Packet correction required |
| 6 | MEDIUM | 16 AUD-F findings open; 6/29 ≈ 20.7% is not completion | No completion claim |
| 7 | MEDIUM | Package residuals (P-13/P-15/P-16/P-01/P-04) | Open acceptance conditions |
| 8 | LOW | P-04 count/verify TOCTOU and session-error mapping | Acceptance-only residual; code frozen |
| 9 | LOW | P-13/P-15 fail-closed/idempotency owner decisions unsigned | Owner decision pending |
| 10 | INFO | PR #307 OPEN/untouched; backup branch preserved | No action |

Register: `GULA_SECURITY_AND_RISK_REGISTER.md` §5.

---

## 5. Decisions required from owner

1. **Do not sign P-02 / P-03 as written.** Direct a documentation-only rewrite against HEAD plus a
   fresh re-review; no implementation authorization yet.
2. After correction: P-02 failure policy (a) fail closed / (b) separate outbox design package, with
   explicit acceptance of the `/ai/interpret` trade-off.
3. After correction: P-03 scope (a)/(b)/(d), actor rule, failure policy and action-name taxonomy.
4. Approve a file-scope separation plan for the mixed-provenance tree before any commit/push/Draft PR.
5. Execute and record the DeepSeek key rotation, usage/billing review and exposure assessment.
6. Separately accept P-13/P-15/P-16/P-01/P-04 if desired — `ACCEPTED` is never implied by a
   `PASS WITH CONDITIONS` engineering review; no `PRODUCTION READY` is authorized.

---

## 6. Evidence and tests actually executed this checkpoint

| Check | Command / method | Result |
|---|---|---|
| Focused regression files (P-13, P-15, P-16, P-01, P-04) | `ENV=test PYTHONPATH=..:/home/samertts/workspace/projects/gula-integration /tmp/opencode/gula-int-py312/bin/python -m pytest tests/test_f01_legacy_audit_writer.py tests/test_f04_audit_verifier_chain.py tests/test_p13_financial_audit_integrity.py tests/test_p15_password_reset_audit_integrity.py tests/test_p16_mpi_identity_integrity.py -q` | **40 passed, 0 failed**, 92.48 s, exit 0 (11 pre-existing `utcnow()` DeprecationWarnings, no failures) |
| Git invariants | `git rev-parse`, `git diff --cached --name-status`, `git diff --check`, `md5sum`, `git ls-remote`, `gh pr view 307` | all values in §1 verified |
| DeepSeek history | redacted/digest-only local scripts in `/tmp/opencode/`, `git log -S`, `git merge-base --is-ancestor` | `ROTATION UNVERIFIED`; no value printed |
| Packet review | independent fresh-context reviewer + `git show HEAD:` corroboration | both FAIL, see §2 |
| SHA-256 manifests | `sha256sum` over created/modified checkpoint documents | additive manifest created (see §7) |

No full suite, no integration suite, no production service and no external provider API was used in
this checkpoint. Earlier package tests (8/8, 6/6, 11/11, 9/9, 6/6 and related suites) remain the
evidence recorded in the individual AFTER records; they are not re-claimed as newly executed here.

---

## 7. Allowed next-stage work

- Rewrite `P-02_DECISION_PACKET.md` / `P-03_DECISION_PACKET.md` as **documentation only** against an
  explicit baseline, then request a fresh independent review.
- Continue read-only analysis and documentation of the remaining AUD-F findings and the 11
  pre-acceptance reports.
- Update the status register and scorecard after each owner decision.
- Do **not** implement F02/F03 or any R4 package; do **not** edit P-04 code/tests after review;
  do **not** change audit/identity/privacy behavior outside approved scope.
- Do **not** commit, push, create a Draft PR, modify PR #307, merge, deploy, or change HOLD.

**Termination conditions:** HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED ·
PRODUCTION READY NOT AUTHORIZED. No failed check hidden; no audit-completion or platform-completion
claim made.
