# MPI Failure & Recovery Matrix — PROPOSED, NOT APPROVED

**Status:** `PROPOSED — NOT APPROVED`. Design preparation only; no production behaviour is active.
**Evidence base:** `MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` (SQLSTATEs `40P01`, `55P03`, `40001`,
`23505` observed; rollback / interruption / worker termination → no partial row; duplicate replay →
1 operation / 1 audit row). Items marked `INFERRED` are design reasoning, not measured results.
**Decision dependency:** D-MPI-1 `NEEDS_OWNER_DECISION`.
**Release:** HOLD. D-020 / D-021 `PENDING_APPROVAL`.

---

## 1. Retry policy (normative for the implementation tranche)

### 1.1 SQLSTATE classification

| SQLSTATE | Condition | Class | Retry? | Required action |
|---|---|---|---|---|
| `40001` | `serialization_failure` | transient | **Yes — bounded** | **Complete transaction restart**; never reuse a failed session or transaction |
| `40P01` | `deadlock_detected` | transient | **Yes — bounded** | Full rollback then fresh transaction; lock order already enforced by design |
| `55P03` | `lock_not_available` | transient | **Yes — bounded** | Roll back, re-acquire advisory lock from a clean transaction |
| `08000`, `08003`, `08006`, `08xxx` | connection exception | transient | **Yes — after reconciliation** | Reconnect, reconcile idempotency key, then decide replay (see §2.5–2.7) |
| `57014` | `query_canceled` (statement timeout) | contextual | bounded, only if clearly transient | Reconcile before replay; do not assume rollback |
| `23505` | `unique_violation` | **not a retryable error at the claim key** | No | Treat as idempotent replay: re-read and return the winning claim (`models.py:124`) |
| `23503` | `foreign_key_violation` | permanent | **No** | Reject; fix caller data or ownership; incident if unexpected |
| `23502` | `not_null_violation` | permanent | **No** | Reject |
| `23514` | `check_violation` | permanent | **No** | Reject |
| `22xxx` | data exception | permanent | **No** | Reject |
| `25P02` | `in_failed_sql_transaction` | programming error | No (as-is) | Roll back the failed transaction, then restart only if the root cause was transient |
| other `23xxx` | integrity constraint violation | permanent | **No** | Reject; no blind retry |

`23505` on an unrelated unique index is a permanent violation — only the documented idempotency key
is eligible for replay handling. Retrying a permanent integrity violation is prohibited.

### 1.2 Bounded retry parameters (`INFERRED`, to be validated in implementation)

- **Maximum attempts:** 3 total (initial + 2 restarts).
- **Backoff:** 25 ms, then 50 ms; small production jitter allowed. Tests use deterministic barriers
  and must not rely on random sleeps to create or resolve race conditions.
- **Lock/statement timeouts:** configured at the transaction/statement level so no attempt can block
  indefinitely; exact production values are an owner/operations decision (the isolated evaluation
  used 15 s / 30 s for benchmarks and 1 s for the lock-timeout proof — these are **not** production
  settings).
- **Full restart requirement:** for `40001`, `40P01` and any failure that leaves a transaction in a
  failed state, the entire outer transaction must be rolled back and rebuilt, including a fresh
  advisory-lock acquisition. A failed SQLAlchemy `Session`/`Transaction` must never be reused.
- **No duplicate audit:** every recovery path ends with an idempotency lookup; a second audit row for
  the same operation is a defect, never a retry outcome.

---

## 2. Scenario matrix

| Scenario | Detection | Transaction outcome | Retry allowed | Recovery |
|---|---|---|---|---|
| **Duplicate request** (sequential replay) | Idempotency lookup finds existing claim / original `MergeAudit` (`resolver.py:475-488`) | No new mutation; original result returned | N/A — not an error | Return original audit row and outcome; no new audit entry |
| **Concurrent duplicate request** | Row locks + advisory lock serialize; second transaction observes committed state after lock wait, or receives `23505` on `uq_identity_claims_lab_patient` | One `applied`, one `replayed`; 1 operation / 1 audit row (`TEST_VERIFIED`) | `23505` → replay handling, not error retry | Re-read by key and return winner; never insert a second audit row |
| **Conflicting idempotency payload** | Payload hash differs for an existing key (`INFERRED`: comparison rule to be defined in MPI-05) | Request rejected; no identity or audit mutation | **No** | Caller must correct payload or use a new key; incident metric; no partial state |
| **Lock timeout (`55P03`)** | SQLSTATE from `SELECT … FOR UPDATE` or advisory-lock acquisition | Waiting transaction aborted; holder unaffected (`TEST_VERIFIED`) | **Yes, bounded**, from a clean transaction | Roll back, re-acquire advisory lock first, rebuild full transaction, retry ≤2 |
| **Deadlock victim (`40P01`)** | SQLSTATE; PostgreSQL selects victim | Victim transaction fully rolled back; connection usable afterwards (`TEST_VERIFIED`) | **Yes, bounded**, full restart | Fresh transaction with approved lock order (advisory → citizen id ASC); re-run idempotency lookup |
| **Serialization failure (`40001`)** | SQLSTATE on commit or during SERIALIZABLE work | Transaction aborted | **Yes, bounded**, complete restart | Discard session/transaction; rebuild from idempotency lookup; never reuse failed transaction; note SERIALIZABLE alone is not the chosen chain protection |
| **Connection lost before COMMIT** | Driver/connection error; server aborts uncommitted transaction | Rollback; no partial row (`TEST_VERIFIED` for interruption/worker termination) | **Yes** | Reconnect, reconcile by key, re-execute full transaction |
| **Connection lost during COMMIT** | Connection error with **in-doubt** commit outcome; outcome cannot be inferred from the client error | **Indeterminate until reconciled** — never assume rollback or success | **No blind replay**; retry only after reconciliation | Reconnect, query by idempotency key and audit index; if committed → return original; if absent → re-execute once in a fresh transaction |
| **Connection lost after COMMIT but before response** | Client sees error; server has committed | Committed exactly once | **No replay mutation** | Idempotency lookup returns the original merge/audit row; client may safely repeat the request |
| **Response lost after successful COMMIT (`expire_on_commit=True`)** | Failure on post-commit attribute reads at `api.py:171-175` after `db.commit()` at `api.py:168` (`database.py:242`) | Commit succeeded; response not delivered | **No replay mutation** | Return the already-committed result from values captured before commit, or reconcile by idempotency key; never re-merge. This window exists today and is unhandled (`VERIFIED_IN_SOURCE`) |
| **Retry with swapped ULID arguments** | Same logical pair supplied in reverse order; current lookup key requires `(primary, secondary)` order and does not deduplicate (`resolver.py:475-488`) | Without a fix, a full re-merge is attempted and rejected by validation; no audit row is created | No — reject as a caller error | Normalize the pair for lookup in MPI-05; do not treat as a new merge. No DB unique constraint protects the merge pair today |
| **Audit insertion failure** | Exception from `_write_audit()` (`resolver.py:517-527`) or constraint violation | SAVEPOINT rollback; no orphan audit row (`TEST_VERIFIED` for failure after audit insert) | Only if classified transient (`40001`/`40P01`/`55P03`) | Rebuild transaction from idempotency lookup; permanent constraint errors are rejected |
| **Hash verification failure** | `verify_merge_audit_chain()` returns `valid=false` with errors (`resolver.py:175-208`); in-transaction segment check (MPI-08) | SAVEPOINT rollback; chain evidence preserved | **No** | Raise incident; preserve audit rows and verifier output; owner-defined fork-response policy (D-MPI-3/4). Verification is detection only |
| **Version conflict** | Optimistic guard rowcount 0 / stale version, or lock wait timeout on version row | SAVEPOINT rollback; no partial increment | **Yes, bounded** | Re-read current version, re-validate business rule, retry ≤2; atomic-increment path needs no re-read when only the new value matters |
| **Process termination during merge** | Child/worker death, connection drop | Uncommitted transaction aborted by PostgreSQL; no partial row (`TEST_VERIFIED`) | **Yes, after reconciliation** | Supervisor/client reconnects, reconciles by idempotency key, re-executes or returns original result |

---

## 3. Reconciliation algorithm (used by all connection-loss paths)

1. Open a **new** connection and a **fresh** transaction.
2. Acquire the transaction-scoped advisory lock first (approved primary mechanism).
3. Look up the idempotency key (claim key for resolve; primary/secondary + event for merge).
4. If an original audit row or completed claim exists → return it; **do not write**.
5. If no record exists → re-execute the operation once under the same lock order.
6. If the reconciliation query itself fails transiently → apply the bounded retry policy; never
   treat an in-doubt commit as a failed write.

Steps 2–3 are `INFERRED` design requirements derived from the tested idempotency + lock model; the
full merge transaction under the advisory lock is `NOT_MEASURED`.

---

## 4. Invariants that no recovery path may violate

- At most **one** `MergeAudit` row per successful merge operation.
- No identity claim may be repointed without its audit row in the same outer transaction.
- No `SAVEPOINT RELEASE` is represented as a commit.
- No failed transaction is reused.
- No permanent integrity violation is retried.
- No partial merge survives a rollback, interruption or worker termination.
- No real patient data or credential is written to logs or diagnostics during recovery.

**STOP — PROPOSED — NOT APPROVED. Await explicit owner approval of D-MPI-1 and a separate
implementation authorization.**
