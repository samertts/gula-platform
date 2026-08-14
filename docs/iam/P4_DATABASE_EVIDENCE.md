# P4 Database Evidence

**Safety boundary:** No production database was contacted or modified in this remediation batch.

## Repository evidence

The current repository baseline is `d736e4f166fae20e4084847c3d7d5c8fc6dfeff6`. The repository migration chain records Alembic head `20260814_0008`. The account-request migration creates `niam_account_creation_requests` with foreign keys to `niam_accounts`, a unique request UUID, and a unique idempotency-key hash. Earlier NIAM migrations contain foreign keys, unique constraints and indexes for accounts, memberships, workspaces, roles, permissions, devices and audit/security tables.

## CI evidence

GitHub CI has a PostgreSQL migration/schema gate in the required workflows. A passing CI schema gate proves that the checked commit can run the tested migration/schema path in that CI environment; it does not prove the state of a production database.

## Local migration-test result

The local security-audit migration test was attempted. The test skipped two migration suites because no migration database URL was available and failed the security-audit schema assertion against the local/default database because the expected `niam_audit_entries`, `niam_consents` and `niam_security_incidents` tables were absent. This is not converted into a PASS or repaired by mutating a database. The correct classification is environment/database evidence required.

| Evidence item | Current state |
|---|---|
| Alembic repository head | `20260814_0008` |
| Migration files and declared constraints | Available for review |
| CI PostgreSQL migration/schema gate | Required CI evidence exists; latest branch checks must be re-run after remediation PR |
| Live Alembic version table | `LIVE_DATABASE_UNVERIFIED` |
| Live PostgreSQL schema | `LIVE_DATABASE_UNVERIFIED` |
| Live foreign keys/unique constraints/indexes | `LIVE_DATABASE_UNVERIFIED` |
| Live transaction state | `LIVE_DATABASE_UNVERIFIED` |
| Production data modification | Not performed |

## Required read-only verification

An authorized read-only environment must provide the database endpoint through the approved mechanism, then verify the Alembic version table, schema tables, foreign keys, unique constraints, indexes, migration transaction state and application/runtime commit alignment. Any unavailable item remains `LIVE_DATABASE_UNVERIFIED`; no inference from source or CI may replace it.
