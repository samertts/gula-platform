# WS-05 Survey — Reliability & Offline-first

**Document:** 10 · **Status:** `TESTED` (in-memory) / `BLOCKED` (durable external anchor).

## Surface
`backend/app/health_core/reliability/` (11 modules), 6 reliability test files; offline sync engine (`test_offline_sync.py`, E-055: 31 passed).

## Verified evidence (prior cycle, unchanged)
- F-02: WAL envelope authoritative `record_count` + `last_sequence`; stale anchors rejected.
- F-03: append-only `AuditLog` head/count anchors; tail deletion → `COUNT_MISMATCH`.
- F-05: `_check_key` calls `require_synthetic_id`; non-SYN keys rejected.
- Retry/backoff, WAL, snapshot, conflict handling tested (26 reliability tests).
- Offline conflict strategy is **honest `CONFLICT_QUARANTINE`** — no CRDT claim; no lost updates; idempotent.
- Source classification (`FINAL_06_RELIABILITY.md`): in-memory only, no durable/keyed external anchor. This program records the in-memory implementation as `TESTED`; the durable anchor is `BLOCKED`.

## Gaps
| Gap | Classification | Route |
|---|---|---|
| Durable/keyed external audit anchor | `BLOCKED` | persistence/migration owner |
| Crash durability of offline queue | `NOT IMPLEMENTED` | E-055 boundary disclosure; Phase B adds in-process replay evidence only, not production crash durability |
| RPO / RTO | `NOT IMPLEMENTED` | no production rehearsal; no value is claimed |

## Program action
Preserve F-02/F-03/F-05 regressions; no durability claim beyond in-memory boundary.
