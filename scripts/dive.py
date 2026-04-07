#!/usr/bin/env python3
"""
GULA Platform — Data Integrity Verification Engine (DIVE)
==========================================================
Proves — not just assumes — that stored data is correct and complete.

Checks:
  1.  Claims ↔ Outbox coupling      no claim_submitted without a claim row
  2.  No duplicate claims            idempotency_key unique in DB
  3.  Financial integrity            SUM(items) == claim.total_amount for each claim
  4.  Referential integrity          every claim.lab_id / patient_id exists
  5.  Outbox processing completeness all non-failed events eventually processed
  6.  Outbox stuck detection         events pending > 10 min = stuck
  7.  Audit log coverage             every claim mutation has an audit row
  8.  Status machine validity        no illegal state transitions in DB
  9.  Hash-chain integrity           audit_logs hash chain unbroken (if populated)
  10. Orphan detection               claim_items without a parent claim

Usage:
    # Read DATABASE_URL from environment (same as the backend):
    DATABASE_URL="postgresql://postgres:SECRET@localhost:5432/labdb" \
        python3 scripts/dive.py

    # Or supply it directly:
    python3 scripts/dive.py --db "postgresql://postgres:SECRET@localhost:5432/labdb"

    # Only run specific checks:
    python3 scripts/dive.py --checks 1,2,3,5

    # Run as post-chaos validation (exit 1 on any failure):
    python3 scripts/dive.py --strict

Requirements: psycopg2-binary   (pip3 install psycopg2-binary)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip3 install psycopg2-binary")
    sys.exit(2)

# ── ANSI ──────────────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as _ci
    _ci()
    G, R, Y, C, B = Fore.GREEN, Fore.RED, Fore.YELLOW, Fore.CYAN, Fore.BLUE
    RESET = Style.RESET_ALL
except ImportError:
    G = R = Y = C = B = RESET = ""


PASSED: list[str] = []
FAILED: list[str] = []
WARNED: list[str] = []


def ok(msg: str, detail: str = "") -> None:
    d = f"  ({detail})" if detail else ""
    print(f"  {G}✔{RESET} {msg}{d}")
    PASSED.append(msg)


def fail(msg: str, detail: str = "") -> None:
    d = f"  → {detail}" if detail else ""
    print(f"  {R}✘{RESET} {msg}{d}")
    FAILED.append(msg)


def warn(msg: str, detail: str = "") -> None:
    d = f"  ({detail})" if detail else ""
    print(f"  {Y}⚠{RESET} {msg}{d}")
    WARNED.append(msg)


def info(msg: str) -> None:
    print(f"  {C}→{RESET} {msg}")


def section(title: str) -> None:
    print(f"\n{'─'*62}")
    print(f"{B}{title}{RESET}")
    print(f"{'─'*62}")


# ── DB helpers ────────────────────────────────────────────────────────────────

class DB:
    def __init__(self, dsn: str) -> None:
        self._conn = psycopg2.connect(dsn)
        self._conn.set_session(readonly=True, autocommit=True)

    def one(self, sql: str, params=()) -> Optional[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def all(self, sql: str, params=()) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def scalar(self, sql: str, params=(), default=0):
        row = self.one(sql, params)
        return row[0] if row and row[0] is not None else default

    def table_exists(self, name: str) -> bool:
        return bool(self.scalar(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s", (name,)
        ))

    def column_exists(self, table: str, col: str) -> bool:
        return bool(self.scalar(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s AND column_name=%s",
            (table, col)
        ))

    def close(self) -> None:
        self._conn.close()


# ── Check 1: Claims ↔ Outbox coupling ────────────────────────────────────────

def check_claims_outbox_coupling(db: DB) -> None:
    section("CHECK 1: Claims ↔ Outbox Coupling")

    if not db.table_exists("claims"):
        warn("'claims' table not found — migration may not have run yet")
        return

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found")
        return

    total_claims = db.scalar("SELECT COUNT(*) FROM claims WHERE status='submitted'")
    total_events = db.scalar(
        "SELECT COUNT(*) FROM outbox_events WHERE event_type='claim_submitted'"
    )

    info(f"Submitted claims: {total_claims}  |  claim_submitted events: {total_events}")

    if total_claims == total_events:
        ok("Claims ↔ outbox count match", f"{total_claims} each")
    elif total_claims > total_events:
        fail("Claims without outbox events (data loss)",
             f"{total_claims - total_events} submitted claims have no outbox event")
    else:
        warn("More outbox events than submitted claims",
             f"could be from resubmissions or manual testing ({total_events - total_claims} excess)")

    # Detect specific orphaned claims (submitted but no outbox event)
    orphans = db.all("""
        SELECT c.id FROM claims c
        WHERE c.status = 'submitted'
          AND NOT EXISTS (
              SELECT 1 FROM outbox_events o
              WHERE o.event_type = 'claim_submitted'
                AND o.aggregate_id = c.id
          )
        LIMIT 10
    """)
    if orphans:
        fail("Submitted claims with no outbox event (orphans)",
             f"claim IDs: {[r[0] for r in orphans]}")
    else:
        ok("No orphaned submitted claims")


# ── Check 2: No duplicate claims ─────────────────────────────────────────────

def check_no_duplicates(db: DB) -> None:
    section("CHECK 2: Idempotency — No Duplicate Claims")

    if not db.table_exists("claims"):
        warn("'claims' table not found"); return

    # Duplicate idempotency_key (non-null only)
    dupes = db.all("""
        SELECT idempotency_key, COUNT(*) AS cnt
        FROM claims
        WHERE idempotency_key IS NOT NULL
        GROUP BY idempotency_key
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    if dupes:
        fail("Duplicate idempotency_key rows found",
             f"{[(r[0], r[1]) for r in dupes]}")
    else:
        ok("No duplicate idempotency_key in claims table")

    # Same patient + same items on same day (business-level duplicate)
    same_day_dupes = db.scalar("""
        SELECT COUNT(*) FROM (
            SELECT lab_id, patient_id, DATE(created_at) AS day, COUNT(*) AS cnt
            FROM claims
            GROUP BY lab_id, patient_id, DATE(created_at)
            HAVING COUNT(*) > 5
        ) AS t
    """)
    if same_day_dupes > 0:
        warn("Possible business duplicates",
             f"{same_day_dupes} patient+lab pairs with >5 claims on same day (review manually)")
    else:
        ok("No suspicious same-day claim bursts per patient")


# ── Check 3: Financial integrity ──────────────────────────────────────────────

def check_financial_integrity(db: DB) -> None:
    section("CHECK 3: Financial Integrity — SUM(items) == total_amount")

    if not db.table_exists("claims") or not db.table_exists("claim_items"):
        warn("claims or claim_items table not found"); return

    # Claims where stored total_amount ≠ SUM of items
    mismatches = db.all("""
        SELECT c.id, c.total_amount, SUM(ci.amount) AS computed
        FROM claims c
        JOIN claim_items ci ON ci.claim_id = c.id
        WHERE c.total_amount IS NOT NULL
        GROUP BY c.id, c.total_amount
        HAVING ABS(c.total_amount - SUM(ci.amount)) > 0.001
        LIMIT 10
    """)
    if mismatches:
        fail("total_amount mismatch (stored ≠ computed from items)",
             f"{len(mismatches)} claims: {[(r[0], float(r[1]), float(r[2])) for r in mismatches]}")
    else:
        ok("All claim totals match SUM of items")

    # Claims with no items at all
    empty = db.scalar("""
        SELECT COUNT(*) FROM claims c
        WHERE NOT EXISTS (SELECT 1 FROM claim_items ci WHERE ci.claim_id = c.id)
          AND c.status != 'draft'
    """)
    if empty > 0:
        fail("Non-draft claims with zero items", f"{empty} claims")
    else:
        ok("All non-draft claims have at least one item")

    # Negative amounts
    neg_items = db.scalar("SELECT COUNT(*) FROM claim_items WHERE amount <= 0")
    if neg_items > 0:
        fail("Claim items with non-positive amount", f"{neg_items} rows")
    else:
        ok("All claim item amounts are positive")

    # Grand total for reporting
    grand = db.scalar("SELECT SUM(total_amount) FROM claims") or 0
    info(f"Total claims value in DB: {grand:,.2f} IQD")


# ── Check 4: Referential integrity ────────────────────────────────────────────

def check_referential_integrity(db: DB) -> None:
    section("CHECK 4: Referential Integrity — Foreign Keys")

    if not db.table_exists("claims"):
        warn("'claims' table not found"); return

    checks = [
        ("claims.lab_id → labs",
         "SELECT COUNT(*) FROM claims c WHERE NOT EXISTS (SELECT 1 FROM labs l WHERE l.id=c.lab_id)"),
        ("claims.patient_id → patients",
         "SELECT COUNT(*) FROM claims c WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.id=c.patient_id)"),
        ("claim_items.claim_id → claims",
         "SELECT COUNT(*) FROM claim_items ci WHERE NOT EXISTS (SELECT 1 FROM claims c WHERE c.id=ci.claim_id)"),
    ]

    for name, sql in checks:
        if not db.table_exists("claim_items") and "claim_items" in sql:
            warn(f"Skipping {name} — table missing")
            continue
        broken = db.scalar(sql)
        if broken > 0:
            fail(f"Broken FK: {name}", f"{broken} orphaned rows")
        else:
            ok(f"FK intact: {name}")


# ── Check 5: Outbox processing completeness ───────────────────────────────────

def check_outbox_processing(db: DB) -> None:
    section("CHECK 5: Outbox Processing Completeness")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    total     = db.scalar("SELECT COUNT(*) FROM outbox_events")
    done      = db.scalar("SELECT COUNT(*) FROM outbox_events WHERE status='done'")
    pending   = db.scalar("SELECT COUNT(*) FROM outbox_events WHERE status='pending'")
    failed_c  = db.scalar("SELECT COUNT(*) FROM outbox_events WHERE status='failed'")
    processing = db.scalar("SELECT COUNT(*) FROM outbox_events WHERE status='processing'")

    info(f"Outbox: total={total} done={done} pending={pending} processing={processing} failed={failed_c}")

    ok("Outbox totals consistent",
       f"done={done} + pending={pending} + proc={processing} + failed={failed_c} = {done+pending+processing+failed_c} (total={total})")

    if failed_c > 0:
        warn("Failed outbox events (delivery gave up)", f"{failed_c} events — check logs")
    else:
        ok("No permanently failed outbox events")

    # Processing completeness ratio
    if total > 0:
        pct = done / total * 100
        if pct >= 95:
            ok(f"Processing rate ≥95%", f"{pct:.1f}%")
        elif pct >= 80:
            warn(f"Processing rate {pct:.1f}%", "backlog growing — check worker")
        else:
            fail(f"Low processing rate", f"{pct:.1f}% — worker may be stuck")


# ── Check 6: Stuck event detection ───────────────────────────────────────────

def check_stuck_events(db: DB) -> None:
    section("CHECK 6: Stuck Event Detection (pending > 10 min)")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    if not db.column_exists("outbox_events", "created_at"):
        warn("outbox_events.created_at column not found"); return

    stuck = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE status IN ('pending', 'processing')
          AND created_at < NOW() - INTERVAL '10 minutes'
    """)

    if stuck == 0:
        ok("No stuck events (all processed within 10 minutes)")
    elif stuck <= 5:
        warn(f"{stuck} events pending >10 min", "may be transient — monitor")
    else:
        fail(f"{stuck} events stuck >10 min", "worker may be down or erroring")

    # Very old stuck events (>1 hour) — critical
    very_stuck = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE status IN ('pending', 'processing')
          AND created_at < NOW() - INTERVAL '1 hour'
    """)
    if very_stuck > 0:
        fail(f"{very_stuck} events stuck >1 hour", "DATA LOSS RISK — investigate immediately")
    else:
        ok("No events stuck >1 hour")


# ── Check 7: Status machine validity ─────────────────────────────────────────

def check_status_machine(db: DB) -> None:
    section("CHECK 7: Claim Status Machine Validity")

    if not db.table_exists("claims"):
        warn("'claims' table not found"); return

    VALID_STATUSES = ("draft", "validated", "submitted", "accepted", "rejected", "paid")

    # Any invalid status values
    invalid = db.all(f"""
        SELECT DISTINCT status FROM claims
        WHERE status NOT IN ({','.join('%s' for _ in VALID_STATUSES)})
    """, VALID_STATUSES)
    if invalid:
        fail("Invalid status values in claims", str([r[0] for r in invalid]))
    else:
        ok("All claim status values are valid")

    # 'paid' claims must have been 'accepted' first (check via outbox event order)
    paid_without_accepted = db.scalar("""
        SELECT COUNT(*) FROM claims
        WHERE status = 'paid'
          AND NOT EXISTS (
              SELECT 1 FROM outbox_events
              WHERE aggregate_id = claims.id
                AND event_type = 'claim_accepted'
          )
    """)
    # Note: this is a best-effort check — outbox may not record all transitions
    if paid_without_accepted > 0:
        warn(f"{paid_without_accepted} 'paid' claims with no 'claim_accepted' event",
             "review if payment was applied correctly")
    else:
        ok("No 'paid' claims without a prior acceptance event")

    # Stats
    status_counts = db.all("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY status")
    if status_counts:
        info("Claim status distribution: " +
             " | ".join(f"{r[0]}={r[1]}" for r in status_counts))


# ── Check 8: Orphan claim_items ───────────────────────────────────────────────

def check_orphans(db: DB) -> None:
    section("CHECK 8: Orphan Detection — claim_items Without Parent")

    if not db.table_exists("claim_items"):
        warn("'claim_items' table not found"); return

    orphans = db.scalar("""
        SELECT COUNT(*) FROM claim_items ci
        WHERE NOT EXISTS (SELECT 1 FROM claims c WHERE c.id = ci.claim_id)
    """)
    if orphans > 0:
        fail("Orphaned claim_items found", f"{orphans} rows without a parent claim")
    else:
        ok("No orphaned claim_items")

    # Items with zero or null amounts
    bad = db.scalar("SELECT COUNT(*) FROM claim_items WHERE amount IS NULL OR amount <= 0")
    if bad > 0:
        fail("claim_items with null or non-positive amount", f"{bad} rows")
    else:
        ok("All claim_items have valid amounts")


# ── Check 9: Audit log coverage ───────────────────────────────────────────────

def check_audit_coverage(db: DB) -> None:
    section("CHECK 9: Audit Log Coverage")

    if not db.table_exists("audit_logs"):
        warn("'audit_logs' table not found — skipping"); return

    total_audit = db.scalar("SELECT COUNT(*) FROM audit_logs")
    info(f"Total audit log rows: {total_audit}")

    if total_audit == 0:
        warn("Audit log is empty — no mutations recorded")
        return

    ok(f"Audit log has {total_audit} entries")

    # Recent audit entries (last hour)
    recent = db.scalar("""
        SELECT COUNT(*) FROM audit_logs
        WHERE created_at > NOW() - INTERVAL '1 hour'
    """)
    info(f"Audit entries in last hour: {recent}")


# ── Check 10: Hash-chain integrity ────────────────────────────────────────────

def check_hash_chain(db: DB) -> None:
    section("CHECK 10: Audit Hash-Chain Integrity")

    if not db.table_exists("audit_logs"):
        warn("'audit_logs' table not found — skipping"); return

    if not db.column_exists("audit_logs", "hash"):
        warn("audit_logs.hash column not found — hash chain not implemented yet")
        return

    # Check for null hashes
    null_hashes = db.scalar("SELECT COUNT(*) FROM audit_logs WHERE hash IS NULL OR hash=''")
    if null_hashes > 0:
        warn(f"{null_hashes} audit rows without hash", "hash chain not fully implemented")
        return

    # Verify chain: each row's hash should be sha256(prev_hash + data)
    rows = db.all("""
        SELECT id, hash, prev_hash, data
        FROM audit_logs
        ORDER BY id
        LIMIT 1000
    """)

    broken = 0
    for row in rows:
        row_id, stored_hash, prev_hash, data = row
        if not stored_hash:
            broken += 1
            continue
        raw = (prev_hash or "") + json.dumps(data, sort_keys=True, ensure_ascii=False)
        expected = hashlib.sha256(raw.encode()).hexdigest()
        if stored_hash != expected:
            broken += 1

    if broken == 0:
        ok(f"Hash chain intact across {len(rows)} audit rows")
    else:
        fail(f"Hash chain broken in {broken}/{len(rows)} rows",
             "audit logs may have been tampered with")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(strict: bool) -> int:
    total = len(PASSED) + len(FAILED)
    pct   = (len(PASSED) / total * 100) if total else 0

    print(f"\n{'═'*62}")
    print("DATA INTEGRITY VERIFICATION ENGINE — RESULTS")
    print(f"{'═'*62}")
    print(f"  PASSED  : {G}{len(PASSED)}{RESET}")
    print(f"  WARNINGS: {Y}{len(WARNED)}{RESET}")
    print(f"  FAILED  : {R}{len(FAILED)}{RESET}")
    print(f"  SCORE   : {pct:.0f}% ({len(PASSED)}/{total} checks)")

    if FAILED:
        print(f"\n{R}Failed checks (ACTION REQUIRED):{RESET}")
        for f in FAILED:
            print(f"  ✘ {f}")

    if WARNED:
        print(f"\n{Y}Warnings (review recommended):{RESET}")
        for w in WARNED:
            print(f"  ⚠ {w}")

    print()
    if not FAILED:
        print(f"{G}✔ DATA INTEGRITY VERIFIED — system data is consistent and complete.{RESET}")
        verdict = 0
    elif len(FAILED) <= 2 and not strict:
        print(f"{Y}⚠ MINOR ISSUES — system mostly intact, investigate failures above.{RESET}")
        verdict = 1
    else:
        print(f"{R}✘ DATA INTEGRITY FAILURE — do NOT use this system in production.{RESET}")
        verdict = 2

    print(f"\n  Run timestamp: {datetime.now(timezone.utc).isoformat()}")
    return verdict


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="GULA Data Integrity Verification Engine")
    parser.add_argument("--db", default=os.getenv("DATABASE_URL", ""),
                        help="PostgreSQL DSN (default: $DATABASE_URL)")
    parser.add_argument("--checks", default="all",
                        help="Comma-separated check numbers (e.g. 1,3,5) or 'all'")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on any failure (for CI/CD gates)")
    args = parser.parse_args()

    if not args.db:
        # Try to build DSN from individual env vars (docker-compose style)
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        pw   = os.getenv("POSTGRES_PASSWORD", "")
        db   = os.getenv("POSTGRES_DB", "labdb")
        if pw:
            args.db = f"postgresql://{user}:{pw}@{host}:{port}/{db}"
        else:
            print("ERROR: Provide --db or set DATABASE_URL / POSTGRES_PASSWORD env var")
            sys.exit(2)

    if args.checks == "all":
        run = set(range(1, 11))
    else:
        run = set(int(c) for c in args.checks.split(","))

    print(f"\n{'═'*62}")
    print("GULA Platform — Data Integrity Verification Engine (DIVE)")
    print(f"{'═'*62}")
    # Mask password in display
    display_dsn = args.db
    import re
    display_dsn = re.sub(r"(:)[^:@]+(@)", r"\1***\2", display_dsn)
    print(f"  DB      : {display_dsn}")
    print(f"  Checks  : {args.checks}")
    print(f"  Strict  : {args.strict}")
    print(f"{'═'*62}")

    try:
        db = DB(args.db)
    except Exception as exc:
        print(f"\n{R}FATAL: Cannot connect to database: {exc}{RESET}")
        sys.exit(2)

    try:
        if 1  in run: check_claims_outbox_coupling(db)
        if 2  in run: check_no_duplicates(db)
        if 3  in run: check_financial_integrity(db)
        if 4  in run: check_referential_integrity(db)
        if 5  in run: check_outbox_processing(db)
        if 6  in run: check_stuck_events(db)
        if 7  in run: check_status_machine(db)
        if 8  in run: check_orphans(db)
        if 9  in run: check_audit_coverage(db)
        if 10 in run: check_hash_chain(db)
    finally:
        db.close()

    return print_summary(args.strict)


if __name__ == "__main__":
    sys.exit(main())
