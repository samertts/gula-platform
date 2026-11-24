# P-15 Post-Change Package Record

Generated: 2026-11-20T18:05:11Z (UTC)

## Invariants
- branch: integration/gula-unification-v1
- HEAD: 2206654dc713ea2de8c564a3207dfe05fde23549
- protected sibling HEAD: f478676b6fc375338648dde46fbf076c015a3f91
- staged name-status MD5: 56c524d6ffe9872c3a3ac6eff8c8f203
- staged count: 20
- staged R100 count: 20
- unstaged count: 160
- untracked count: 644
- git diff --check exit: 0

## Protected MD5s
effdfeaf10234678d83b2668c4489552  GOVERNANCE/FINAL_DECISION.md
1a02c01563c93b07a7cdb92c0462bf36  GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md
ea3969d09aaf7b0b28a065838b44a594  GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md

## production_ready_items
480:    "production_ready_items": 0
600:  "production_ready_items": 0,

## Files changed by P-15
 M backend/app/routes/password_reset.py
?? backend/tests/test_p15_password_reset_audit_integrity.py
?? backend/tests/unit/test_session_revocation.py

## P-15 production diff
diff --git a/backend/app/routes/password_reset.py b/backend/app/routes/password_reset.py
index ed4420fd..44e34d75 100644
--- a/backend/app/routes/password_reset.py
+++ b/backend/app/routes/password_reset.py
@@ -1,6 +1,5 @@
 from __future__ import annotations
 
-import contextlib
 from datetime import datetime, timedelta
 
 from fastapi import APIRouter, Depends, HTTPException
@@ -47,10 +46,18 @@ async def forgot_password(
     token = secrets.token_urlsafe(32)
     user.reset_token = hash_password(token)
     user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
+    # P-15 / AUD-F17: the credential audit row shares the credential
+    # transaction. A guard refusal or DB error now propagates (fail closed)
+    # and rolls the token mutation back; it is never silently swallowed.
+    # No token or secret is passed to the audit trail.
+    log_action(
+        db,
+        action="password_reset_requested",
+        resource_type="password_reset",
+        resource_id=user.id,
+        user_id=user.id,
+    )
     db.commit()
-    if user:
-        with contextlib.suppress(Exception):
-            log_action(db, action="password_reset_requested", resource_type="password_reset", user_id=user.id)
     return {"message": "If the email exists, a reset link has been sent"}
 
 
@@ -71,9 +78,22 @@ async def reset_password(
     user.password_hash = hash_password(req.new_password)
     user.reset_token = None
     user.reset_token_expires = None
+    # P0-D: revoke all active sessions/tokens on password reset. Previously a
+    # stolen token remained valid after the reset. Bump before commit so any
+    # in-flight request observes the new version immediately.
+    from app.security.session import bump_perm_version
+    bump_perm_version(user, db, reason="password_reset")
+    # P-15 / AUD-F17: the completion audit row shares the credential
+    # transaction with the hash change, token clearing and perm-version bump.
+    # Any audit failure propagates (fail closed) and rolls all of it back.
+    log_action(
+        db,
+        action="password_reset_completed",
+        resource_type="password_reset",
+        resource_id=user.id,
+        user_id=user.id,
+    )
     db.commit()
-    with contextlib.suppress(Exception):
-        log_action(db, action="password_reset_completed", resource_type="password_reset", user_id=user.id)
     return {"message": "Password reset successful"}
 
 
@@ -88,6 +108,8 @@ async def change_password(
         raise HTTPException(status_code=400, detail="Current password is incorrect")
     current_user.password_hash = hash_password(req.new_password)
     from app.security.session import bump_perm_version
-    bump_perm_version(db, current_user.id)
+    # Correct call signature: (user, db, ...). The old (db, id) form raised a
+    # TypeError after the password was already written but before commit.
+    bump_perm_version(current_user, db, reason="password_change")
     db.commit()
     return {"message": "Password changed successfully"}

## New test files
194 backend/tests/test_p15_password_reset_audit_integrity.py

## P-15 independent review
**Verdict: PASS WITH CONDITIONS. CRITICAL: 0. HIGH: 0.**

Focused tests: 58 passed (6 new P-15 + 22 session-revocation + 30 auth
infrastructure), exit 0. Old defect confirmed from `git show HEAD`: both audit
calls were after `db.commit()` and inside `contextlib.suppress(Exception)`.
Verified audit-before-commit, canonical signature, no token/password/secret in
audit details, rate limiting and enumeration message unchanged, and that P0-D
session revocation was preserved (classified as pre-existing user work).

Conditions / residual items (none are CRITICAL or HIGH, none block progression):
- M1 (MEDIUM, VERIFICATION GAP) — only audit-writer failure was injected; no
  DB flush/commit failure, interruption, or retry test. The design is
  structurally atomic (single transaction + `get_db` rollback). The owner
  objective names interruption/retry, so this condition remains OPEN until the
  owner either accepts `fail closed` (no durable retry buffer) for this package
  or authorizes those extra tests / a durable retry path. NOT self-declared.
- L1 (LOW) — the new P-15 test file and the adapted session-revocation test are
  untracked. No staging or commit is authorized under the current mandate;
  they must be included in the eventual owner-gated commit or the regression
  coverage is lost.
- L2 (LOW) — on audit outage an existing user now errors while an unknown email
  returns 200 (availability oracle). R4 owner acceptance of this trade-off is
  NOT recorded; this remains OPEN.
- L3 (LOW) — AST guard `len(calls) == 2` is brittle; a future legitimate third
  audit call would fail the guard. Also note `change_password` still audits
  nothing (pre-existing, out of scope).
- INFO — P0-D publishes the perm-version to the store before commit; on P-15
  audit failure the DB rolls back but the store stays bumped, which fails safe
  (deny). Pre-existing, no action.

Status remains `TESTED` + `INDEPENDENTLY REVIEWED`. NOT `ACCEPTED`, NOT
`PRODUCTION READY`. No commit, staging, or production action performed.
