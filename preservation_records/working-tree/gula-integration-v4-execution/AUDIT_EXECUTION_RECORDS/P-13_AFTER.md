# P-13 Post-Change Package Record

Generated: 2026-11-20T17:37:14Z (UTC)

## Invariants
- branch: integration/gula-unification-v1
- HEAD: 2206654dc713ea2de8c564a3207dfe05fde23549
- protected sibling HEAD: f478676b6fc375338648dde46fbf076c015a3f91
- staged name-status MD5: 56c524d6ffe9872c3a3ac6eff8c8f203
- staged count: 20
- staged R100 count: 20
- unstaged count: 160
- untracked count: 642
- git diff --check exit: 0

## Protected MD5s
effdfeaf10234678d83b2668c4489552  GOVERNANCE/FINAL_DECISION.md
1a02c01563c93b07a7cdb92c0462bf36  GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md
ea3969d09aaf7b0b28a065838b44a594  GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md

## production_ready_items
480:    "production_ready_items": 0
600:  "production_ready_items": 0,

## Files changed by P-13 (unstaged)
backend/app/financial/routes.py

## New test file (untracked)
-rw-r--r-- 1 samertts samertts 7623 Nov 20 20:36 backend/tests/test_p13_financial_audit_integrity.py

## P-13 source diff
diff --git a/backend/app/financial/routes.py b/backend/app/financial/routes.py
index c0674296..58e8ee74 100644
--- a/backend/app/financial/routes.py
+++ b/backend/app/financial/routes.py
@@ -308,18 +308,24 @@ def create_transaction(
         created_at=datetime.utcnow(),
     )
     db.add(txn)
-    db.commit()
-    db.refresh(txn)
+    # P-13 / AUD-F15: the audit row and the financial mutation must share one
+    # transaction. Flush to materialize the PK, write the canonical audit row
+    # with the canonical keyword names, then commit exactly once. If the audit
+    # write fails, the request dependency rolls the uncommitted money move back:
+    # no committed-but-unaudited transaction and no retry-driven double charge.
+    db.flush()
     log_action(
         db=db,
         action="financial.transaction.created",
-        entity_type="fin_transaction",
-        entity_id=str(txn.id),
+        resource_type="fin_transaction",
+        resource_id=txn.id,
         lab_id=current_user.lab_id,
         user_id=current_user.id,
         details={"amount": amount, "type": transaction_type},
     )
-    return {"id": txn.id, "status": "pending", "amount": amount, "description": description}
+    response = {"id": txn.id, "status": "pending", "amount": amount, "description": description}
+    db.commit()
+    return response
 
 
 @router.get("/transactions")
@@ -364,17 +370,20 @@ def run_billing_cycle(
 ):
     _check_enabled()
     results = BillingService.run_billing_cycle(db)
-    db.commit()
+    # P-13 / AUD-F15: same atomicity rule as create_transaction. A billing
+    # cycle has no single entity id, so resource_id is explicitly NULL.
     log_action(
         db=db,
         action="financial.billing.cycle_run",
-        entity_type="fin_billing_cycle",
-        entity_id="",
+        resource_type="fin_billing_cycle",
+        resource_id=None,
         lab_id=current_user.lab_id,
         user_id=current_user.id,
         details={"invoices_generated": len(results)},
     )
-    return {"invoices_generated": len(results), "invoices": results}
+    response = {"invoices_generated": len(results), "invoices": results}
+    db.commit()
+    return response
 
 
 # ── Reports ────────────────────────────────────────────────────────────

## Independent review (fresh-context reviewer, read-only)

**Verdict: PASS WITH CONDITIONS. CRITICAL: 0. HIGH: 0.**

Verified: canonical keywords (`resource_type`/`resource_id`), ast scan 203 calls /
0 invalid keywords; flush -> audit -> build-response -> single commit on both
paths; `get_db` rollback on exception; no post-commit lazy loads; feature flag
unchanged (default false); no money/charging-policy changes; tests fail against
old code. Focused tests 7/7 at time of review (8/8 after M1 test was added);
related financial tests 82/82 plus 134/134 in the combined related-path run.

Conditions / residual items (none are CRITICAL or HIGH, none block progression):
- M1 (MEDIUM) — initially, no empirical test forced the REAL canonical writer
  to fail. ADDRESSED: added `test_p13_real_canonical_audit_failure_rolls_back_money`,
  which patches `audit_service.AuditLog` to raise after the money flush; 8/8 pass.
- M1b — PostgreSQL branch of `log_action` not exercised by P-13 tests (SQLite
  only). Recorded as unverified by this package; covered by shared audit-isolation
  tests. No PostgreSQL production service was accessed.
- L1 (LOW, residual) — no idempotency key on `create_transaction`; a retry after
  a lost *successful* response could create a second transaction. Pre-existing,
  explicitly outside mandate scope (no charging-policy change). Register in the
  Known Issues Register.
- L2 (LOW) — tests call route functions directly; production rollback is verified
  by reading `get_db`, not by an HTTP-level test.
- I1 (INFO, pre-existing, out of scope) — `PricingService.create_rule` writes no
  audit row. Register in Known Issues Register.
- I3 (INFO, pre-existing) — `_write_anchor()` writes outside the DB transaction
  every 100th entry; a post-audit commit failure could leave an orphan anchor.

Status remains `TESTED` + `INDEPENDENTLY REVIEWED`. NOT `ACCEPTED`, NOT
`PRODUCTION READY`. No commit, staging, or production action performed.
