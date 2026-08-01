#!/usr/bin/env python3
"""Re-encrypt encrypted values with a new ENCRYPTION_KEY after key rotation.

Rotation flow (scripts/rotate-secrets.sh -> rotate_encryption_key) calls this
script before writing the new key to .env so the application never observes
mixed keys: values are decrypted with the OLD key and re-encrypted with the
NEW key in one pass.

Conservative by design:
  - Only values that decrypt successfully with the OLD key are rewritten.
  - Non-Fernet values (e.g. plain HMAC hashes in sibling columns) are left
    untouched.
  - --dry-run performs no writes and prints a summary.
  - Each row update is committed in batches; failures are counted, reported
    and surfaced via a non-zero exit code so rotation can be rolled back.

Usage:
  scripts/reencrypt-encryption-key.py --old-key <fernet> --new-key <fernet> \
      [--table national_citizens] [--column national_id_hash] [--dry-run]

Environment:
  DATABASE_URL  PostgreSQL/other SQLAlchemy URL (required).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Callable
from typing import Any

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.security.encryption import decrypt_value, encrypt_value  # noqa: E402

logger = logging.getLogger("gula.reencrypt")

DEFAULT_TABLE = "national_citizens"
DEFAULT_COLUMN = "national_id_hash"


def reencrypt_value(old_key: str, new_key: str, value: str | None) -> str | None:
    """Re-encrypt a single value with the new key.

    Returns the re-encrypted token when the value is a Fernet token that
    decrypts with ``old_key``; otherwise returns the value unchanged.
    """
    if not value:
        return value
    try:
        plaintext = decrypt_value(value, old_key)
    except Exception:
        return value
    try:
        return encrypt_value(plaintext, new_key)
    except Exception:
        return value


def reencrypt_rows(
    engine: Any,
    table: str,
    column: str,
    old_key: str,
    new_key: str,
    dry_run: bool = False,
    batch_size: int = 200,
    fetch: Callable[[Any, str, str, Any, int], list[tuple]] | None = None,
    update: Callable[[Any, str, str, str, Any], None] | None = None,
) -> dict[str, int]:
    """Re-encrypt ``column`` in ``table`` in batches.

    ``fetch``/``update`` are injectable for tests without a live database.
    """
    fetch = fetch or _fetch_rows
    update = update or _update_row
    reencrypted = untouched = failed = 0
    last_id = None
    while True:
        with engine.begin() as conn:
            rows = fetch(conn, table, column, last_id, batch_size)
            for row_id, value in rows:
                new_value = reencrypt_value(old_key, new_key, value)
                if new_value is None:
                    failed += 1
                elif new_value == value:
                    untouched += 1
                else:
                    reencrypted += 1
                    if not dry_run:
                        update(conn, table, column, row_id, new_value)
        if not rows:
            break
        last_id = rows[-1][0]
        if len(rows) < batch_size:
            break
    return {"reencrypted": reencrypted, "untouched": untouched, "failed": failed}


def _fetch_rows(
    conn: Any,
    table: str,
    column: str,
    last_id: Any,
    batch_size: int,
) -> list[tuple]:
    from sqlalchemy import text

    if last_id is None:
        rows = conn.execute(
            text(f"SELECT id, {column} FROM {table} ORDER BY id LIMIT {batch_size}")
        ).fetchall()
    else:
        rows = conn.execute(
            text(
                f"SELECT id, {column} FROM {table} "
                f"WHERE id > :last_id ORDER BY id LIMIT {batch_size}"
            ),
            {"last_id": last_id},
        ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _update_row(
    conn: Any,
    table: str,
    column: str,
    row_id: Any,
    new_value: str,
) -> None:
    from sqlalchemy import text

    conn.execute(
        text(f"UPDATE {table} SET {column} = :v WHERE id = :id"),
        {"v": new_value, "id": row_id},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-key", default=os.getenv("ENCRYPTION_KEY_OLD", ""))
    parser.add_argument("--new-key", default=os.getenv("ENCRYPTION_KEY", ""))
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--column", default=DEFAULT_COLUMN)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    if not args.old_key or not args.new_key:
        logger.error(
            "Both --old-key and --new-key are required "
            "(or ENCRYPTION_KEY_OLD + ENCRYPTION_KEY)."
        )
        return 2
    if args.old_key == args.new_key:
        logger.error("Old and new keys are identical — nothing to do.")
        return 2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL is required.")
        return 2

    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ),
            {"t": args.table, "c": args.column},
        ).first()
    if not exists:
        logger.info(
            "Table %s.%s not present in this database — no re-encryption required.",
            args.table,
            args.column,
        )
        engine.dispose()
        return 0
    summary = reencrypt_rows(
        engine,
        args.table,
        args.column,
        args.old_key,
        args.new_key,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logger.info(
        "%s %s.%s: %d re-encrypted, %d untouched, %d failed",
        mode,
        args.table,
        args.column,
        summary["reencrypted"],
        summary["untouched"],
        summary["failed"],
    )
    engine.dispose()
    if summary["failed"]:
        logger.error("%d values failed to re-encrypt — rotation should be aborted.", summary["failed"])
        return 1
    return 0


if __name__ == "__main__":
    _venv_python = os.path.join(_REPO_ROOT, "backend", ".venv", "bin", "python")
    if os.path.exists(_venv_python) and os.path.abspath(_venv_python) != os.path.abspath(sys.executable):
        os.execv(_venv_python, [_venv_python, __file__, *sys.argv[1:]])
    sys.exit(main())
