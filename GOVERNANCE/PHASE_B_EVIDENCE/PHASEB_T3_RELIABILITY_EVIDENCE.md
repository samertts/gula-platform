# PHASE B / M6 — T3 Reliability Evidence: Durable Event Queue

Scope: synthetic (`SYN-`) in-process reliability design harness only. No runtime wiring,
no production data, no external persistence.

Start-of-session environment check: branch `integration/gula-unification-v1`,
HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — verified before any edit.
No prohibited file was edited (`factory.py`, `main.py`, `GOVERNANCE/NATIONAL_INTEGRATION/`,
reports 13/14 untouched; no git staging, commit, push, stash, merge or checkout).

## Files owned and delivered

| File | Status |
|---|---|
| `backend/app/health_core/reliability/durable_queue.py` (new) | IMPLEMENTED |
| `backend/tests/unit/test_reliability_durable_queue.py` (new, 19 tests) | TESTED |
| `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_T3_RELIABILITY_EVIDENCE.md` (new) | IMPLEMENTED |

No existing file was modified. The existing reliability modules
(`durable.py`, `idempotency.py`, `retry.py`, `sync_conflicts.py`, `audit.py`,
`backup.py`, `hashing.py`, `metrics.py`, `errors.py`, `__init__.py`) were read-only.

## Implementation summary

| Capability | Status | Evidence in code |
|---|---|---|
| Idempotency by `idempotency_key` (`event_id`) | IMPLEMENTED | `enqueue` deduplicates by event id; committed/resolved keys recorded on `COMMIT`/`RESOLVE`; `processed_keys` / `processed_key_count` exposed; duplicate `process`, `begin`, `commit` return `DUPLICATE` / `ALREADY_COMMITTED` with no second handler call |
| At-least-once delivery with bounded retry + injected backoff | IMPLEMENTED | `begin -> deliver -> commit`; `QueueConfig(max_attempts, backoff_delays_ms)`; `FakeClock`/`RecordingSleeper` injected in tests; every attempt logged with attempt number, clock tick, outcome, delay, error type + error digest |
| Dead letter after exhaustion | IMPLEMENTED | typed `DeadLetterRecord` with `reason = max_attempts_exhausted`, attempt count and payload digest; no raw payload or exception text |
| Append-only, checksummed, hash-chained event log | IMPLEMENTED | `LogEntry` with SHA-256 field hash + previous-hash link; `log_bytes()` sealed envelope with authoritative `record_count`, `last_sequence`, `anchored_head`; `LOG_OPERATIONS` allow-list |
| Crash + replay recovery | IMPLEMENTED | `simulate_crash()` drops all derived state and retains only log bytes; `recover()` verifies before rebuilding, then redelivers only `IN_FLIGHT` events with registered handlers and commits them; committed events never redelivered |
| Conflict quarantine + explicit, idempotent resolution | IMPLEMENTED | `VERSION_CONFLICT` (different version, or same version with different payload digest) creates a structured `ConflictRecord`; no overwrite until `resolve_take_local` / `resolve_take_remote` / `resolve_manual`; repeat with same choice is `DUPLICATE` / `already_resolved`, different choice is `REJECTED` / `conflict_already_decided` |
| Typed results and fail-closed validation | IMPLEMENTED | every command returns a frozen result dataclass with `QueueStatus` + `QueueReason`; malformed id/key/scope/version/payload produce `MISSING_EVENT_ID`, `MISSING_ENTITY_KEY`, `MALFORMED_EVENT`, `NON_SERIALIZABLE_PAYLOAD` and append nothing |
| Tenant / facility scoping | IMPLEMENTED | scope checked at `begin`, `deliver`, `commit` and resolution; foreign events are never committed or written into local entity-version state; scope is part of the quarantine key and log record |
| Runtime integration | BLOCKED | explicitly out of scope for this subagent (`factory.py` / `main.py` are forbidden to edit); no wiring was attempted |
| Independent review | NOT IMPLEMENTED | Not claimed by this agent; reserved for the independent reviewer. No `INDEPENDENTLY VERIFIED` label self-awarded |
| Production readiness | BLOCKED | `PRODUCTION READY` is unattainable while the anchor is in-process; see below |

## Boundary and durability limitation

The "log" is a canonical-JSON byte buffer held in this process. A crash is simulated by
clearing derived dictionaries and replaying those bytes. There is no filesystem, database,
broker, network, keyed signature, external monotonic sequence or cross-process anchor.
**This is an in-process model, not production-grade durability, and no durability claim is made.**

- Durable/keyed external anchor (signed or MAC'd, tenant-scoped, externally sequenced):
  **BLOCKED** — requires owner-authorized production design and infrastructure.
- Payload recovery after replay: **BLOCKED** by design; the log stores only a SHA-256
  payload digest, so replayed `QueueEvent` objects carry an empty payload and their
  original digest. Recovering payload content safely requires the keyed external anchor.
- Handler callables are process-local and are not serialized into the log; a new process
  must re-register handlers by event type before `recover()` can redeliver. In that case
  the event is reported in `RecoveryResult.pending_redelivery` instead of being silently dropped.
- The chain is unsigned; a coherent rehash forgery by an actor who can rewrite both the
  log bytes and the in-process anchors is out of detection scope (same boundary as the
  existing `audit.py` design). Tampering and truncation by field edits, checksum omission
  or record removal with recomputed checksums/anchors are detected and rejected.

## Tests executed — exact results

Toolchain: `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python`,
`ENV=test PYTHONPATH=.:.. PYTHONDONTWRITEBYTECODE=1`, run from `backend/`.

1. Focused suite:

```
python -m pytest tests/unit/test_reliability_durable_queue.py -q --tb=short
19 passed, 1 warning in 0.99s
```

Coverage of the nine requested scenarios: duplicate event processed once (side-effect
count 1); transient failure retried with attempt trace `[1,2,3]`, deterministic clock
ticks and backoff `(2, 4)`; exhaustion dead-lettered with typed reason; crash before
commit redelivers exactly the in-flight event and not the committed one; crash after
commit triggers no redelivery; version conflict quarantined with resolution idempotent
and entity version unchanged until explicit resolution; malformed events rejected with
reason codes and zero log appends; tampered and truncated (re-checksummed) logs rejected
on replay with derived state untouched; foreign tenant and foreign facility events
rejected at begin/deliver/commit/process with no local state mutation. Additional tests
cover manual resolution, same-version/different-payload quarantine, fresh-instance
restore from exported bytes, pending redelivery without a handler, log no-PII property,
config determinism and resolution survival across replay.

2. Lint:

```
ruff check backend/app/health_core/reliability/durable_queue.py backend/tests/unit/test_reliability_durable_queue.py
All checks passed!
```

3. Health Core regression suite:

```
python -m pytest tests/health_core -q --tb=short
21 failed, 752 passed, 1 warning in 13.16s
```

At session start, before any T3 edit, the identical command reported
`773 passed, 1 warning in 9.86s`. Concurrent agents created new untracked modules under
`backend/app/health_core/terminology/`, `backend/app/health_core/audit_anchor/` and
`backend/app/health_core/fhir_http/` during this session; the 21 non-satisfying tests are
in `test_terminology_provenance.py`, `test_terminology_validators.py` (16 parametrized LOINC
cases) and `test_quality_review_static.py`, all of which assert the previous source state
(e.g. LOINC check digit `NOT_VERIFIED_OFFLINE`) and belong to other agents' scope.

Control run: with both T3 files temporarily moved out of the tree (then restored), the
same command reported the identical `21 failed, 752 passed, 1 warning in 9.46s`.
Therefore the delta from the start-of-session 773 is attributable to concurrent
cross-agent changes, and zero failures are attributable to the T3 files. No T3 file is
imported by any test under `tests/health_core/`.

## Security implications

- Tenant/facility isolation: scope is checked on every state-changing command and
  resolution; the entity-version key is `(tenant_id, facility_id, entity_key)`, so a
  foreign tenant cannot commit into this queue's state or overwrite another tenant's
  version. Resolution is additionally scope-checked.
- No PII in logs: only synthetic `SYN-` references, event type, version and SHA-256
  digests are appended. Raw payloads are never logged; exception text is reduced to
  exception type plus a 16-character SHA-256 prefix. A dedicated test asserts that a
  marker in the payload and a marker in an exception message do not appear in `log_bytes()`.
- Integrity is hash-chained and checksummed with authoritative terminal anchors;
  verification happens before any state rebuild, and a rejected log leaves derived
  state unchanged, avoiding silent corruption. The chain is unkeyed and process-local —
  a keyed anchor remains **BLOCKED**.
- Fail-closed input validation: missing id/key, non-synthetic identifiers, non-positive
  versions, non-object/non-JSON-serializable payloads and wrong scope are rejected with
  typed reason codes before any log append or side effect.
- Synthetic-only fixtures: `require_synthetic_id` rejects real-identifier-shaped inputs;
  broad string checks for `event_type` are limited to non-empty synthetic labels.

## Dependencies

- No new third-party dependency.
- Reuses existing public APIs (read-only): `canonical_json_bytes`, `sha256_hex`,
  `sealed_envelope`, `decode_checked_envelope`, `require_synthetic_id`,
  `GENESIS_HASH` (hash chain), `ChecksumMismatchError`, `InvalidSyntheticReferenceError`.
- No dependency on `factory.py`, `main.py`, database, Redis, or any network service.
- Branch HEAD was re-verified as the expected commit at session start; no git operation
  was performed by this subagent.

## Phase B integration addendum

The reference above to `backend/app/health_core/fhir_http/` describes concurrent
untracked work observed during this agent's session, not a dependency of this
artifact. That package was later relocated to `app/interoperability/fhir_http/`.
No reliability evidence, result or number is changed by this addendum.
