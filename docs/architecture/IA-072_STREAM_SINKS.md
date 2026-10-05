# IA-072 — three stream sinks reported records they never delivered

**Severity** P2 · **Confidence** CONFIRMED · **Reachability** latent — exported, no consumer
**Fix status** FIXED — `514cc0c5`, local commit on `claude/independent-audit-1`, not pushed
**Negative proof** NP-AC / NP-AD, both restored byte-identically (sha256)
**Found by** the item IA-071 left open

---

## The defect

`app/health_data/streaming/sinks.py` declares four sinks against one interface:

```python
class Sink(ABC):
    async def write(self, records: list[dict[str, Any]]) -> int: ...
```

The return value is a **delivery count** — `WebSocketSink`, the one real
implementation, returns the number of records it actually sent. Three of the
four returned `len(records)` without delivering anything:

| Sink | Body | Verdict |
|------|------|---------|
| `PostgresSink` | log, `return len(records)` | **fake** — `self._connection_string` stored, never used |
| `ClickHouseSink` | log, `return len(records)` | **fake** — host/port stored, never used |
| `ObjectStoreSink` | build filename, `json.dumps`, log byte count, `return len(records)` | **fake** — nothing uploaded |
| `WebSocketSink` | iterate connections, `await conn.send`, drop failures, return delivered | **real** |

`ObjectStoreSink` is the one worth dwelling on. It did real-looking work —
constructed a plausible object key, serialised the batch, logged the exact byte
count — so its log line was *evidence* of an upload that never happened:

```
ObjectStoreSink: writing 2 records to streaming/events/batch_1759689600_2.json (118 bytes)
```

An operator reading that log has every reason to believe the data landed.

## Reachability

**Latent.** `grep` over `backend/` and `services/` finds no importer besides
the package's own `__init__` re-export. Nothing constructs these sinks.

So this is an exported surface that would have lost its first consumer's data
silently. Repaired now rather than after someone wires a health-data stream to
a sink that throws records away — which, given these are health records, is the
right time to do it.

## The repair

The three fake sinks raise `StreamSinkUnavailable`, naming the sink, the batch
size and the destination it could not reach, so an operator can see *what* was
refused:

```
PostgresSink.write cannot deliver 2 record(s) to 'stream_events': this sink is
declared but not implemented: it never connected to its destination and
reported the record count as if it had. See IA-072.
```

`WebSocketSink` is untouched. A test drives it with one working and one failing
connection and asserts both the honest count and that the failing connection
was dropped, so the one real sink cannot be quietly converted into a refusal
alongside the others.

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AC | `ObjectStoreSink.write` returns `len(records)` again | the two parametrised ObjectStoreSink tests + the AST ratchet (3 of 8) | sha256 OK |
| NP-AD | convert the real `WebSocketSink` to a refusal — an over-broad repair | `test_the_websocket_sink_still_delivers_and_counts_honestly` only (1 of 8) | sha256 OK |

## An error of mine, and what caught it

The first attempt at these proofs was **invalid, and destroyed the repair.**

I ran NP-AC, then `git checkout -- sinks.py` to restore — but `sinks.py` was
**not yet committed**. `git checkout --` restores to the committed state, so it
reverted the repair itself, not just the perturbation. NP-AD then "passed" with
all 8 tests failing, which I could have misread as a strong proof; in fact the
tests were failing because the fix was gone, not because of the perturbation.

The `sha256sum -c` check is what caught it:

```
backend/app/health_data/streaming/sinks.py: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
```

This is the second time in this audit that `git checkout --` has eaten
uncommitted work, and I had already written the rule down after the first:
**commit the code, then perturb it — never the reverse.** I did not follow my
own rule here. The repair was re-applied, committed as `514cc0c5`, and only
then re-perturbed.

The contrast between the invalid and valid NP-AD runs is itself the evidence
that the proof is now sound:

| Run | Result | Meaning |
|-----|--------|---------|
| invalid (repair absent) | 8 of 8 failed | measured nothing — everything was broken |
| valid (repair committed) | **1 of 8 failed** | isolated exactly the real-sink control |

A perturbation that fails *every* test is a warning sign, not a strong result.

## Suite state

`tests/verification/` — **896 passed**, 150 skipped, 2 xfailed.
`py_compile` clean, `flake8 --select=E9,F821,F811,F401` clean.

## What remains open

To make these sinks work: real client implementations (psycopg/asyncpg,
clickhouse-driver, an S3/MinIO client) plus configuration. Per the platform's
Free-First and Self-Hosted-First mandates, MinIO and self-hosted Postgres are
the indicated targets for the object store and the relational sink. Not written
here — that is build-out, not a defect repair.

Alternatively, **delete them.** Three unimplemented sinks with no consumer may
be better removed than preserved as refusals. That is a product decision, not
mine to take: deleting exported names could break something outside this
repository, and nothing in the brief authorises removing a public surface.
