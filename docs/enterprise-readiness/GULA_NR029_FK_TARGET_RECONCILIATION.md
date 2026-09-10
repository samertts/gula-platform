# NR-029 — Foreign Keys Naming Tables That Exist Nowhere

**Batch:** BATCH-2.7 · **Status: RESOLVED — VERIFIED**
**Migrations created: 0. Schema changes: 0. Tables created: 0.**

---

## 1. What it turned out to be

Not missing tables. **The ORM named the class instead of the table.**

| ORM class | Its `__tablename__` | What the foreign keys said |
|---|---|---|
| `IdentityAuthority` | `niam_gov_authorities` | `niam_identity_authorities` ✗ |
| `UserSession` | `niam_sessions` | `niam_user_sessions` ✗ |

Both classes exist. Both tables exist. Both foreign keys **already exist in
PostgreSQL**, pointing at the real tables — the migrations were right the whole
time and only the ORM was wrong.

## 2. The three declarations

| # | Model | Table | FK column | Named | Real target | File |
|---|---|---|---|---|---|---|
| 1 | `TrustFramework` | `niam_trust_frameworks` | `authority_id String(26)` | `niam_identity_authorities.id` | `niam_gov_authorities.id` | `app/identity/trust/models.py:35` |
| 2 | `IdentityProofing` | `niam_trust_proofing` | `authority_id String(26)` | `niam_identity_authorities.id` | `niam_gov_authorities.id` | `app/identity/trust/models.py:126` |
| 3 | `AdaptiveMFASession` | `niam_adaptive_mfa_sessions` | `session_id String(100)` | `niam_user_sessions.id` | `niam_sessions.id` | `app/identity/adaptive_auth/models.py:75` |

## 3. Migration history — the proof

`20260723_0002_niam_completion_tables.py` created all three declaring tables and
wrote the correct targets:

```python
sa.Column("authority_id", sa.String(length=26),
          sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), ...)   # ×6
sa.Column("session_id", sa.String(length=100),
          sa.ForeignKey("niam_sessions.id", ondelete="SET NULL"), ...)
```

And the constraints are live in a database migrated to head:

```
niam_trust_frameworks.authority_id      -> niam_gov_authorities
niam_trust_proofing.authority_id        -> niam_gov_authorities
niam_adaptive_mfa_sessions.session_id   -> niam_sessions
```

**No migration is missing.** The names `niam_identity_authorities` and
`niam_user_sessions` appear in no `create_table` anywhere in the 106 migrations.

## 4. Per-declaration record

**#1 and #2 — `authority_id`**
Reachable operation: identity trust framework and proofing services.
Consumer: `app/identity/trust/`. Column type `String(26)`, physical
`varchar(26)`, target PK `varchar(26)` — exact match.
Intent: reference the governance authority that issued the framework or
verified the proofing. → **REPAIR**

**#3 — `session_id`**
Reachable operation: adaptive MFA challenge bound to a login session.
Consumer: `app/identity/adaptive_auth/`. Column `String(100)`, physical
`varchar(100)`, target PK `varchar(26)`.
The width difference is pre-existing in the physical schema and PostgreSQL
accepts it; the ORM mirrors the deployed column, so **the width was left
alone**. Only the target name changed. → **REPAIR**

## 5. Action taken

Three words changed. No migration, no schema change, no column change:

```python
ForeignKey("niam_identity_authorities.id", ...)  →  ForeignKey("niam_gov_authorities.id", ...)   # ×2
ForeignKey("niam_user_sessions.id", ...)         →  ForeignKey("niam_sessions.id", ...)          # ×1
```

The alternatives the batch forbade were all wrong anyway: creating the tables
would have duplicated `niam_gov_authorities` and `niam_sessions`; deleting the
foreign keys would have discarded relationships PostgreSQL is already enforcing.

## 6. Verification

`backend/tests/test_alembic_metadata_registry.py::test_every_foreign_key_names_a_table_that_exists`
— `PHANTOM_FK_TARGETS` is now the empty set, so a fourth such declaration fails
the build rather than being absorbed.

## 7. Consequence

**One of NR-023's three blockers is closed.** Remaining: NR-006 (one table-name
collision) and NR-030 (physical tables with no ORM owner).
