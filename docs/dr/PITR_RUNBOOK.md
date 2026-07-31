# PITR Runbook — Point-in-Time Recovery

**Status:** Active procedure
**Owner:** Platform Operations (SRE)
**Automation:** `scripts/pitr-recover.sh`
**RPO target:** ≤ 1 hour (WAL archive) — RTO target: ≤ 30 minutes

## Purpose

Recover the GULA PostgreSQL database to a point in time using the WAL archive
(streamed to S3/MinIO). This is the standard response for logical corruption,
accidental destructive operations, or partial data loss.

## Prerequisites

- WAL archiving enabled (`archive_mode = on`) and archiving to `s3://gula-wal-archive/wal/` (or MinIO bucket).
- Daily base backups exist in `backups/daily/` (see `scripts/backup.sh`).
- The recovery host has: PostgreSQL binaries, `aws` CLI (or `mc` for MinIO),
  and network access to the archive bucket.
- Environment variables (usually in `.env` or exported by the operator):

| Variable | Purpose |
|---|---|
| `ARCHIVE_S3_BUCKET` | WAL archive bucket (default `gula-wal-archive`) |
| `ARCHIVE_S3_REGION` | Bucket region (default `me-central-1`) |
| `ARCHIVE_S3_ENDPOINT` | MinIO-compatible endpoint (empty = AWS S3) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Bucket credentials (or `mc` alias for MinIO) |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Database credentials |
| `PGDATA` | Data directory (default `pgdata`) |

## Procedure (automated)

```bash
# 1. Dry-run first — never skip this on a live environment
./scripts/pitr-recover.sh --dry-run

# 2. Verify the archive is intact
./scripts/pitr-recover.sh --verify   # lists base backup + latest WAL

# 3. Full recovery to the latest available WAL
./scripts/pitr-recover.sh            # defaults: restore latest

# 4. Recovery to a specific timestamp
./scripts/pitr-recover.sh --target-time "2026-07-31 14:30:00+03"
```

The script:
1. Selects the newest base backup from `backups/daily/`.
2. Restores it into a staging PostgreSQL instance.
3. Writes `recovery.conf` with `restore_command` pointing at the WAL archive.
4. Applies WAL until the target point, waits for the instance to come out of
   recovery, and verifies reachability.
5. Runs integrity verification (core tables + audit `chain_hash` chain).
6. Emits a PITR report with the exact recovery timestamp.

## After recovery (manual steps)

1. **Sync data back to the primary:**
   - Dump from the recovered instance: `pg_dump -U postgres labdb | gzip > sync.sql.gz`
   - Restore to primary: `gunzip -c sync.sql.gz | psql -U postgres labdb`
2. **Repoint the application:** update `DATABASE_URL` in `.env` (a backup copy
   is saved as `.env.pitr_bak_<TIMESTAMP>`), then restart the backend:
   `docker compose restart gula-backend`.
3. **Verify consistency** between the recovered instance and the primary:
   compare `SELECT count(*)` on `patients`, `lab_orders`, `lab_results`,
   `audit_logs`, and verify the audit chain (see `docs/validation/`).
4. **Restore service order:** redis, postgres, backend, frontend, gateway.
5. **Keep the recovered instance running** (read-only) for 24h as the rollback
   source, then stop and remove its data directory.
6. **Root-cause analysis:** document the incident in `docs/runbooks/` and add a
   regression test if the cause was preventable.

## Rollback

The recovery is non-destructive by design:
- The original primary is never modified during recovery.
- To abort: stop the staging instance (`pg_ctl -D <PGDATA>_pitr_<ts> stop -m fast`)
  and delete its data directory. The application keeps working on the original.

## Verification & testing

- Monthly drill: `./scripts/dr-test.sh` or the `drill` mode of `scripts/dr_recovery.sh`.
- After every major release: run `./scripts/pitr-recover.sh --verify` (read-only).
- Evidence for government audit: the generated PITR report includes timestamps,
  WAL applied, and audit-chain verification results.

## Related documents

- `docs/runbooks/database-down.md` — immediate database failure response
- `docs/ops/OPERATIONS_MANUAL.md` — full operations manual
- `docs/security/SECRET_MANAGEMENT.md` — credentials used by this runbook
