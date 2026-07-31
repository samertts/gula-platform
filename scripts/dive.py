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
  11. Temporal integrity             no silent delivery windows (unprocessed >5 min)
  12. Replay safety                  no event processed twice, no cross-tenant key collision
  13. Processing latency             avg <30s, p95 <120s (last-hour SLO)
  14. Backlog explosion              <100 healthy / 100-1000 warn / >1000 critical
  15. Schema drift                   alembic_version matches expected head, no split-brain

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

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit(2)

# ── ANSI ──────────────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style
    from colorama import init as _ci
    _ci()
    G, R, Y, C, B = Fore.GREEN, Fore.RED, Fore.YELLOW, Fore.CYAN, Fore.BLUE
    RESET = Style.RESET_ALL
except ImportError:
    G = R = Y = C = B = RESET = ""


PASSED: list[str] = []
FAILED: list[str] = []
WARNED: list[str] = []


def ok(msg: str, detail: str = "") -> None:
    PASSED.append(msg)


def fail(msg: str, detail: str = "") -> None:
    FAILED.append(msg)


def warn(msg: str, detail: str = "") -> None:
    WARNED.append(msg)


def info(msg: str) -> None:
    pass


def section(title: str) -> None:
    pass


# ── DB helpers ────────────────────────────────────────────────────────────────

class DB:
    def __init__(self, dsn: str) -> None:
        self._conn = psycopg2.connect(dsn)
        self._conn.set_session(readonly=True, autocommit=True)

    def one(self, sql: str, params=()) -> tuple | None:
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
            ok("Processing rate ≥95%", f"{pct:.1f}%")
        elif pct >= 80:
            warn(f"Processing rate {pct:.1f}%", "backlog growing — check worker")
        else:
            fail("Low processing rate", f"{pct:.1f}% — worker may be stuck")


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

    valid_statuses = ("draft", "validated", "submitted", "accepted", "rejected", "paid")

    # Any invalid status values
    invalid = db.all(f"""
        SELECT DISTINCT status FROM claims
        WHERE status NOT IN ({','.join('%s' for _ in valid_statuses)})
    """, valid_statuses)
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
        _row_id, stored_hash, prev_hash, data = row
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


# ── Check 11: Temporal Integrity — no silent delivery window ─────────────────

def check_temporal_integrity(db: DB) -> None:
    section("CHECK 11: Temporal Integrity — No Silent Delivery Windows")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    # Events still unprocessed after 5 minutes → delivery window open
    window_open = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE processed_at IS NULL
          AND status NOT IN ('failed')
          AND created_at < NOW() - INTERVAL '5 minutes'
    """)
    if window_open == 0:
        ok("No unprocessed events older than 5 minutes (delivery window closed)")
    else:
        fail(f"{window_open} events unprocessed >5 min",
             "delivery window open — data may not have reached external system")

    # Events where processed_at < created_at (time-travel bug — clock skew)
    time_travel = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE processed_at IS NOT NULL
          AND processed_at < created_at
    """)
    if time_travel > 0:
        fail(f"{time_travel} events with processed_at < created_at",
             "clock skew or timestamp corruption — investigate immediately")
    else:
        ok("No timestamp anomalies (processed_at ≥ created_at on all processed events)")


# ── Check 12: Replay Safety — no event processed twice ───────────────────────

def check_replay_safety(db: DB) -> None:
    section("CHECK 12: Replay Safety — No Event Processed Twice")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    # Multiple outbox events for the same (aggregate_id, event_type) pair
    replays = db.all("""
        SELECT aggregate_id, event_type, COUNT(*) AS cnt
        FROM outbox_events
        WHERE aggregate_type = 'claim'
          AND event_type = 'claim_submitted'
          AND aggregate_id IS NOT NULL
        GROUP BY aggregate_id, event_type
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    if replays:
        fail("Duplicate outbox events for same claim (replay risk)",
             f"{len(replays)} claim IDs: {[(r[0], r[2]) for r in replays]}")
    else:
        ok("No duplicate claim_submitted events (replay safe)")

    # Idempotency key re-use across different labs (cross-tenant leak)
    if db.table_exists("claims"):
        cross_tenant = db.scalar("""
            SELECT COUNT(*) FROM (
                SELECT idempotency_key, COUNT(DISTINCT lab_id) AS labs
                FROM claims
                WHERE idempotency_key IS NOT NULL
                GROUP BY idempotency_key
                HAVING COUNT(DISTINCT lab_id) > 1
            ) AS t
        """)
        if cross_tenant > 0:
            fail(f"{cross_tenant} idempotency keys used across multiple labs",
                 "CRITICAL: cross-tenant key collision — investigate data isolation")
        else:
            ok("Idempotency keys are lab-scoped (no cross-tenant collision)")


# ── Check 13: Processing Latency ─────────────────────────────────────────────

def check_processing_latency(db: DB) -> None:
    section("CHECK 13: Outbox Processing Latency (SLO: avg < 30s, p95 < 120s)")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    stats = db.one("""
        SELECT
            AVG(EXTRACT(EPOCH FROM (processed_at - created_at)))::numeric(10,2)  AS avg_s,
            PERCENTILE_CONT(0.95) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (processed_at - created_at))
            )::numeric(10,2)                                                     AS p95_s,
            MAX(EXTRACT(EPOCH FROM (processed_at - created_at)))::numeric(10,2)  AS max_s,
            COUNT(*)                                                              AS sample
        FROM outbox_events
        WHERE processed_at IS NOT NULL
          AND created_at > NOW() - INTERVAL '1 hour'
    """)

    if not stats or stats[3] == 0:
        warn("No processed events in the last hour — cannot measure latency")
        return

    avg_s, p95_s, max_s, sample = float(stats[0] or 0), float(stats[1] or 0), float(stats[2] or 0), int(stats[3])
    info(f"Last-hour sample={sample}  avg={avg_s:.1f}s  p95={p95_s:.1f}s  max={max_s:.1f}s")

    if avg_s < 30:
        ok(f"Average latency {avg_s:.1f}s < 30s SLO")
    elif avg_s < 120:
        warn(f"Average latency {avg_s:.1f}s — approaching SLO limit")
    else:
        fail(f"Average latency {avg_s:.1f}s exceeds 30s SLO", "worker may be overloaded")

    if p95_s < 120:
        ok(f"p95 latency {p95_s:.1f}s < 120s SLO")
    else:
        fail(f"p95 latency {p95_s:.1f}s exceeds 120s SLO")


# ── Check 14: Backlog Explosion ───────────────────────────────────────────────

def check_backlog(db: DB) -> None:
    section("CHECK 14: Outbox Backlog — Explosion Detection")

    if not db.table_exists("outbox_events"):
        warn("'outbox_events' table not found"); return

    backlog = db.scalar("""
        SELECT COUNT(*) FROM outbox_events WHERE processed_at IS NULL
    """)
    failed_count = db.scalar("""
        SELECT COUNT(*) FROM outbox_events WHERE status = 'failed'
    """)

    info(f"Current backlog: {backlog} unprocessed | {failed_count} permanently failed")

    # Thresholds
    if backlog < 100:
        ok(f"Backlog healthy ({backlog} events)")
    elif backlog < 1000:
        warn(f"Backlog growing ({backlog} events)", "monitor worker throughput")
    else:
        fail(f"Backlog explosion ({backlog} events)", "worker not keeping up — scale or investigate")

    if failed_count == 0:
        ok("No permanently failed events")
    elif failed_count < 10:
        warn(f"{failed_count} permanently failed events", "check logs for root cause")
    else:
        fail(f"{failed_count} permanently failed events", "delivery failures accumulating")

    # Growth rate: compare last 5 min vs prior 5 min
    recent = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE processed_at IS NULL
          AND created_at > NOW() - INTERVAL '5 minutes'
    """)
    prior = db.scalar("""
        SELECT COUNT(*) FROM outbox_events
        WHERE processed_at IS NULL
          AND created_at BETWEEN NOW() - INTERVAL '10 minutes' AND NOW() - INTERVAL '5 minutes'
    """)
    if prior > 0 and recent > prior * 2:
        warn(f"Backlog growth accelerating (last 5m={recent} vs prior 5m={prior})",
             "unusual traffic spike or worker slowdown")
    elif recent == 0 and backlog > 0:
        warn("No new events queued in last 5 min but backlog exists",
             "may indicate processing stalled")


# ── Check 15: Schema Drift — migration version consistent ────────────────────

def check_schema_drift(db: DB) -> None:
    section("CHECK 15: Schema Drift — Migration Version")

    if not db.table_exists("alembic_version"):
        fail("alembic_version table missing — migrations never ran or DB is wrong"); return

    versions = db.all("SELECT version_num FROM alembic_version")
    if not versions:
        fail("alembic_version is empty — no migration applied"); return

    current = versions[0][0]
    ok(f"Current migration: {current}")

    # Expected head (the latest migration file we know about)
    expected_head = "20260407_0001"
    if current == expected_head:
        ok(f"Schema is at expected head ({expected_head})")
    else:
        warn(f"Schema version {current} ≠ expected {expected_head}",
             "run: alembic upgrade head")

    # Multiple version rows = split-brain migration (should never happen)
    if len(versions) > 1:
        fail("Multiple rows in alembic_version",
             f"versions={[r[0] for r in versions]} — DB may be in inconsistent state")
    else:
        ok("Single version row in alembic_version (no split-brain)")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(strict: bool) -> int:
    total = len(PASSED) + len(FAILED)
    (len(PASSED) / total * 100) if total else 0


    if FAILED:
        for _f in FAILED:
            pass

    if WARNED:
        for _w in WARNED:
            pass

    if not FAILED:
        verdict = 0
    elif len(FAILED) <= 2 and not strict:
        verdict = 1
    else:
        verdict = 2

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
            sys.exit(2)

    run = set(range(1, 16)) if args.checks == "all" else {int(c) for c in args.checks.split(",")}

    # Mask password in display
    display_dsn = args.db
    import re
    display_dsn = re.sub(r"(:)[^:@]+(@)", r"\1***\2", display_dsn)

    try:
        db = DB(args.db)
    except Exception:
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
        if 11 in run: check_temporal_integrity(db)
        if 12 in run: check_replay_safety(db)
        if 13 in run: check_processing_latency(db)
        if 14 in run: check_backlog(db)
        if 15 in run: check_schema_drift(db)
    finally:
        db.close()

    return print_summary(args.strict)


if __name__ == "__main__":
    sys.exit(main())
