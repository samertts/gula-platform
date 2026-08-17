#!/usr/bin/env python3
"""
SNDHS-lite Phase 1 — production-safe backfill.

Idempotent batched job that:

  1. Creates a ``visits`` row for every distinct
     (lab_orders.patient_id, calendar-day-of created_at) that does not
     already have one.
  2. Sets ``lab_orders.visit_id`` to the matching visit, in batches.
  3. Logs progress, totals, and elapsed time.
  4. Can be re-run any number of times — already-linked rows are
     skipped and existing visits are reused.

The script intentionally:

- Does NOT add the FK or UNIQUE constraint (that is migration step F).
- Does NOT update any other table.
- Never UPDATEs an order whose ``visit_id`` is already set.
- Holds a transaction only for the duration of one batch.
- Releases connections cleanly between batches.

Usage
-----
Inside the backend container:

    docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py
    docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --batch-size 2000
    docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --dry-run
    docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --max-batches 50

Operator runbook entry produced on success::

    sndhs_phase1_check OK total_orders=N linked=N visits_created=N elapsed=Ts

Exit codes
----------
- 0 → success (or dry-run completed)
- 1 → environment / connectivity error
- 2 → data integrity precondition not met (e.g. missing column)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager

# We import lazily so ``--help`` works without DB connectivity.

LOG_FMT = "%(asctime)s %(levelname)s sndhs.backfill %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("sndhs.backfill")


def _build_engine():
    """Use the existing app database URL.

    Falls back to ``DATABASE_URL`` env var if the app config import
    fails (e.g. running the script outside the app container)."""
    try:
        # Preferred path: reuse the app's tuned engine factory.
        from app.database import engine  # type: ignore
        return engine
    except Exception:  # pragma: no cover - operator path
        from sqlalchemy import create_engine
        url = os.getenv("DATABASE_URL")
        if not url:
            log.error("DATABASE_URL not set and app.database import failed")
            sys.exit(1)
        return create_engine(url, pool_pre_ping=True)


@contextmanager
def _conn(engine) -> Iterator:
    """One short-lived connection per batch — autocommit per statement
    via SQLAlchemy ``begin()`` blocks."""
    c = engine.connect()
    try:
        yield c
    finally:
        c.close()


def _check_preconditions(engine) -> None:
    """Fail fast with a clear message if the migration set has not run."""
    from sqlalchemy import inspect
    insp = inspect(engine)

    cols_patients = {c["name"] for c in insp.get_columns("patients")}
    cols_orders   = {c["name"] for c in insp.get_columns("lab_orders")}

    missing = []
    if "national_id"     not in cols_patients: missing.append("patients.national_id")
    if "sndhs_health_id" not in cols_patients: missing.append("patients.sndhs_health_id")
    if "identity_level"  not in cols_patients: missing.append("patients.identity_level")
    if "consent_flags"   not in cols_patients: missing.append("patients.consent_flags")
    if "visit_id"        not in cols_orders:   missing.append("lab_orders.visit_id")
    if not insp.has_table("visits"):           missing.append("visits (table)")
    if not insp.has_table("sndhs_audit_logs"): missing.append("sndhs_audit_logs (table)")

    if missing:
        log.error("Pre-conditions failed; missing: %s", ", ".join(missing))
        log.error("Run alembic upgrade head before this script.")
        sys.exit(2)


def _count_remaining(engine) -> int:
    from sqlalchemy import text
    with engine.connect() as c:
        return c.execute(text(
            "SELECT count(*) FROM lab_orders WHERE visit_id IS NULL"
        )).scalar() or 0


def _count_total_orders(engine) -> int:
    from sqlalchemy import text
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM lab_orders")).scalar() or 0


def _backfill_one_batch(engine, *, batch_size: int, dry_run: bool) -> int:
    """Process one batch.

    Strategy
    --------
    1. Select up to ``batch_size`` lab_orders with ``visit_id IS NULL``,
       locked with ``FOR UPDATE SKIP LOCKED`` so the script is
       concurrent-safe (multiple workers can run in parallel).
    2. For each (patient_id, day) pair, ensure a visit exists; reuse
       the visit if one was already created today for that patient.
    3. UPDATE the orders with their visit_id.

    Returns the number of orders processed in the batch.
    """
    from sqlalchemy import text

    with engine.begin() as c:
        # Pick a batch — SKIP LOCKED so parallel runs don't fight.
        rows = c.execute(text(
            "SELECT id, patient_id, lab_id, "
            "       date_trunc('day', created_at) AS day "
            "FROM lab_orders "
            "WHERE visit_id IS NULL "
            "ORDER BY id "
            "FOR UPDATE SKIP LOCKED "
            "LIMIT :n"
        ), {"n": batch_size}).fetchall()

        if not rows:
            return 0

        if dry_run:
            return len(rows)

        # Reuse-or-create visit per (patient_id, day) pair within batch.
        visits_cache: dict[tuple[int, str], str] = {}
        order_visit: list[tuple[str, int]] = []

        for row in rows:
            key = (row.patient_id, row.day.isoformat() if row.day else "")
            if key in visits_cache:
                vid = visits_cache[key]
            else:
                # Look for an existing visit that covers this order's day.
                # Idempotency: find an open visit for this patient on the
                # same calendar day; otherwise create one.
                existing = c.execute(text(
                    "SELECT id FROM visits "
                    "WHERE patient_id = :pid "
                    "  AND date_trunc('day', created_at) = :d "
                    "  AND visit_type = 'lab' "
                    "ORDER BY created_at ASC "
                    "LIMIT 1"
                ), {"pid": row.patient_id, "d": row.day}).first()

                if existing:
                    vid = str(existing.id)
                else:
                    new = c.execute(text(
                        "INSERT INTO visits (patient_id, visit_type, status, created_at) "
                        "VALUES (:pid, 'lab', 'open', :d) "
                        "RETURNING id"
                    ), {"pid": row.patient_id, "d": row.day}).first()
                    vid = str(new.id)

                visits_cache[key] = vid

            order_visit.append((vid, row.id))

        # Single UPDATE statement per batch via VALUES list keeps it tight.
        # Fall back to per-row update if VALUES isn't supported (sqlite).
        try:
            # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
            # Batch SQL contains generated bind parameter names only; row values stay in execute params.
            c.execute(
                text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                    "UPDATE lab_orders AS lo "
                    "SET visit_id = v.vid::uuid "
                    "FROM (VALUES " +
                    ",".join(f"(:vid_{i}, :oid_{i})" for i in range(len(order_visit))) +
                    ") AS v(vid, oid) "
                    "WHERE lo.id = v.oid::int AND lo.visit_id IS NULL"
                ),
                {
                    **{f"vid_{i}": v for i, (v, _) in enumerate(order_visit)},
                    **{f"oid_{i}": o for i, (_, o) in enumerate(order_visit)},
                },
            )
        except Exception:
            # Portable fallback (sqlite tests): per-row update.
            for vid, oid in order_visit:
                c.execute(
                    text(
                        "UPDATE lab_orders SET visit_id = :v "
                        "WHERE id = :o AND visit_id IS NULL"
                    ),
                    {"v": vid, "o": oid},
                )

        return len(rows)


def _emit_runbook_check(*, total_orders: int, linked: int,
                       visits_created: int, elapsed: float) -> None:
    msg = (
        "sndhs_phase1_check OK "
        f"total_orders={total_orders} linked={linked} "
        f"visits_created={visits_created} elapsed={elapsed:.2f}s"
    )
    log.info(msg)
    # Also emit a structured marker for log-pipeline consumers.
    log.info('{"event":"sndhs_phase1_check","status":"OK",'
             f'"total_orders":{total_orders},"linked":{linked},'
             f'"visits_created":{visits_created},"elapsed_s":{elapsed:.2f}'
             '}')


def main() -> int:
    p = argparse.ArgumentParser(
        description="SNDHS-lite Phase 1 backfill (idempotent, batched).",
    )
    p.add_argument("--batch-size", type=int, default=1000,
                   help="Rows processed per transaction (default 1000).")
    p.add_argument("--max-batches", type=int, default=0,
                   help="Stop after N batches (0 = run until done).")
    p.add_argument("--sleep-ms", type=int, default=50,
                   help="Sleep between batches (ms) to ease load.")
    p.add_argument("--dry-run", action="store_true",
                   help="Count work to do without modifying the DB.")
    args = p.parse_args()

    engine = _build_engine()
    _check_preconditions(engine)

    total_orders = _count_total_orders(engine)
    initial_remaining = _count_remaining(engine)
    log.info(
        "Starting Phase 1 backfill — total_orders=%d remaining=%d batch=%d dry_run=%s",
        total_orders, initial_remaining, args.batch_size, args.dry_run,
    )

    started = time.monotonic()
    visits_before = 0
    if not args.dry_run:
        from sqlalchemy import text
        with engine.connect() as c:
            visits_before = c.execute(text("SELECT count(*) FROM visits")).scalar() or 0

    processed = 0
    batches = 0
    while True:
        batch_n = _backfill_one_batch(
            engine, batch_size=args.batch_size, dry_run=args.dry_run,
        )
        if batch_n == 0:
            break
        processed += batch_n
        batches += 1
        log.info(
            "batch=%d processed=%d remaining≈%d",
            batches, processed,
            max(0, initial_remaining - processed),
        )
        if args.max_batches and batches >= args.max_batches:
            log.info("max-batches reached (%d); stopping early.", args.max_batches)
            break
        if args.sleep_ms:
            time.sleep(args.sleep_ms / 1000.0)

    elapsed = time.monotonic() - started

    if args.dry_run:
        log.info(
            "DRY-RUN complete — would-process=%d batches=%d elapsed=%.2fs",
            processed, batches, elapsed,
        )
        return 0

    # Verify final coverage (only meaningful if we ran to completion).
    final_remaining = _count_remaining(engine)
    from sqlalchemy import text
    with engine.connect() as c:
        visits_after = c.execute(text("SELECT count(*) FROM visits")).scalar() or 0

    visits_created = max(0, visits_after - visits_before)
    linked = total_orders - final_remaining

    if final_remaining == 0:
        _emit_runbook_check(
            total_orders=total_orders, linked=linked,
            visits_created=visits_created, elapsed=elapsed,
        )
    else:
        log.warning(
            "Backfill ended with %d unlinked rows. Re-run the script. "
            "DO NOT apply migration 20260505_0006 yet.",
            final_remaining,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
