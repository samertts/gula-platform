# Final Report 06 — Reliability & Operations (WS-F) + F-02/F-03/F-05 remediation

**Report ID:** PR-FINAL-06 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** HOLD / REJECT unchanged. Development evidence only. In-memory designs only — no filesystem, database, network or durable external anchor.

## 1. Classification

| Deliverable | Classification | Basis |
|---|---|---|
| WAL ordering, atomic snapshots, checksummed envelopes, deterministic restart recovery | **VERIFIED (in-memory)** | 58 focused tests incl. terminal-anchor tamper regressions |
| Idempotency, backup/restore, conflict resolution, retry/backoff, observability | **VERIFIED (in-memory)** | Focused suites + demo; deterministic, PII-free |
| Hash-chained audit log | **PARTIALLY VERIFIED** | Interior edits, reorders, first/middle/tail deletion detected via maintained anchor; coherent in-process rehash forgery is undetected and test-locked as a documented limitation |
| Durable / keyed / externally anchored audit and WAL | **NOT IMPLEMENTED** | Requires persistence + owner-approved migration; not fabricated |
| Production deployment / operations | **NOT IMPLEMENTED** | Owner-gated; no production wiring |

Overall workstream classification: **PARTIALLY VERIFIED** — design behaviour verified; durability/anchoring limits are honest and disclosed.

## 2. Findings remediated

### F-02 — MEDIUM — WAL tail truncation with recomputed unkeyed checksum replayed silently
- **Before:** the WAL envelope carried only schema/base_sequence/records/checksum. Dropping the last record and re-sealing the envelope produced a shorter but fully valid-looking WAL; `restore_from()` silently omitted the last write.
- **Fix (`durable.py`):** `wal_bytes()` seals authoritative `record_count = len(self._wal)` and `last_sequence = self._sequence` (from live bookkeeping, not the serialized records) into the envelope. `_replay_wal()` requires both to be present non-bool ints, `record_count == len(records)`, `last_sequence == base_sequence + record_count`, and the final replayed record's sequence `== last_sequence`; any mismatch raises `ChecksumMismatchError`. A naive truncate + re-seal leaves the anchors stale and is rejected. Legitimate restarts are unaffected.
- **Regression:** tail truncation with re-sealed envelope → `ChecksumMismatchError`; middle-drop control still rejected; missing/stale anchors rejected; legitimate 3-key restart still recovers all keys.

### F-03 — MEDIUM — `AuditLog.verify()` self-referential; tail deletion invisible
- **Before:** `head`/`count` were recomputed from `self._records`, and `verify()` passed them as expectations — popping the last record moved the expectations too.
- **Fix (`audit.py`):** append-only anchors `_anchored_head` (init `GENESIS_HASH`) and `_anchored_count` (init 0), updated **only** inside `append()` after the sealed record is appended. `head`/`count` properties return the anchors; `verify()` passes them as expectations. Tail deletion now yields `COUNT_MISMATCH`. Module + `head` docstrings rewritten to state exactly what is detected and what is not (no external/durable/keyed anchor → coherent in-process rehash forgery stays undetected).
- **Regression:** tail deletion → `ok is False` / `AuditFailure.COUNT_MISMATCH`; interior tamper → `HASH_MISMATCH`; coherent rehash forgery → strictly `ok is True` (locks in the documented limitation so it cannot be silently overclaimed).

### F-05 — LOW — `_check_key` accepted any non-empty string
- **Before:** error text said "synthetic reference" but no shape validation occurred (`put("12345678901", ...)` was accepted).
- **Fix:** `_check_key()` now calls `require_synthetic_id(key, field="key")`; non-`SYN-` keys raise `InvalidSyntheticReferenceError`. Unused direct import removed.
- **Regression:** non-SYN key rejected; `SYN-KEY-0001` still stores.

## 3. Files changed (this cycle)

`backend/app/health_core/reliability/durable.py`, `backend/app/health_core/reliability/audit.py`, `backend/tests/health_core/test_reliability_durable.py`, `backend/tests/health_core/test_reliability_audit.py`.

## 4. Verification

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_reliability_durable.py \
  tests/health_core/test_reliability_audit.py -q --tb=short
# 26 passed, 1 warning in 0.23s   (durable 14 + audit 12)
```
Area totals (authoritative JUnit): durable 14, audit 12, backup/idempotency 9, conflicts 9, performance 4, retry/metrics 10 = **58**. Ruff: `All checks passed!`. Demo confirms `WAL + restart -> committed state recovered`, `backup + restore -> data-equal=True`, `audit chain -> valid chain verified, tamper detected`.

## 5. Residual / blocked

- No durable filesystem/DB and no external keyed anchor — a coherent in-process rehash forgery remains undetected by design and is explicitly test-locked. This is why WS-F is PARTIALLY VERIFIED, not VERIFIED.
- Any real persistence/anchoring requires a separate owner-approved Migration Proposal; none was created, no DDL/DB access performed.

**End of final report 06.**
