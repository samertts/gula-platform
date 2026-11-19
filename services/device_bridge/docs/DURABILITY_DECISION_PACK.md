# IA-040 — the device bridge keeps clinical results in memory, and what it would take not to

**STATUS: DISCOVERED, REPRODUCED, NEEDS_DECISION.** All preparatory work that can
be done without choosing a storage engine is done: the loss is measured, the
contract a durable store must satisfy is executable
(`tests/test_storage_durability_contract.py`), and the options below carry their
real consequences. What is missing is one decision, named exactly in §5.

## 1. The loss, measured

`app/storage/db.py` is a four-list dataclass:

```python
@dataclass
class InMemoryDB:
    results: list[dict[str, Any]] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    offline_queue: list[dict[str, Any]] = field(default_factory=list)
```

`app/main.py` instantiates it at module scope. Measured over HTTP against a real
uvicorn process, GULA unreachable:

```
ingested one haemoglobin result
log statuses  : ['received', 'processed', 'forward_failed', 'parsed']
before restart: results=1 logs=4 audit=2 offline-queue=1
after  restart: results=0 logs=0 audit=0 offline-queue=0
```

There is no `create_engine`, no `sqlite3`, no `psycopg`, no file write anywhere
under `app/storage/`, and the `device-bridge` service in `docker-compose.yml`
declares no volume. Deployment matches the code: nothing was meant to persist.

**Why this is worse than it looks.** The offline queue is the path a result takes
*when GULA is unreachable* — it exists for an outage. A restart is one of the
most likely events during an outage (the operator restarts the service, the
container is rescheduled, the host reboots after a power cut). So the store
designed for an outage does not survive the event that outage causes. And per
IA-041 the forward to GULA cannot currently succeed at all, which means **every**
result the bridge has ever accepted is in that queue, and every restart discards
all of them.

## 2. What the architecture already settles

- **Where.** The platform Constitution mandates *Local Storage First:
  PostgreSQL/MinIO/Redis before cloud storage*
  (`docs/constitution/COST_GOVERNANCE.md`). Nothing may go to a hosted service.
- **The edge precedent.** `edge_agent/gula_edge_agent/state.py` is the only other
  off-site component that persists anything. It uses an **encrypted file in a
  configurable state directory**, with a per-device Fernet key generated on first
  run and chmodded 0600. That is the platform's established answer for "a
  component outside the datacentre has to keep something across restarts".
- **PHI at rest is not optional.** This store holds `patient_id`, the patient
  name (the raw ASTM frame is kept verbatim in `raw_data`), test codes and
  values. CLAUDE.md's security invariants require patient identifiers encrypted
  at rest. The edge agent encrypts for exactly this reason. Any durable store
  here inherits that requirement **and its key management**, which the compose
  service currently has no provision for.

## 3. What the architecture does NOT settle

The engine. The edge agent's precedent covers a few kilobytes of key/value
state; this is four append-heavy collections of clinical records, written from an
async web app, read by four API endpoints. The precedent gives the *location* and
the *encryption posture*, not the storage model — and inventing one is exactly
what this document refuses to do.

## 4. Options, with their real costs

| | A — SQLite on a volume | B — encrypted JSONL on a volume | C — PostgreSQL |
|---|---|---|---|
| dependency | stdlib `sqlite3` | stdlib only | `asyncpg`/SQLAlchemy added to a 256 MB image |
| transactional | yes | no (append-only) | yes |
| concurrent writers | one process, WAL | needs a lock | yes |
| PHI at rest | needs app-level encryption or SQLCipher (not stdlib) | Fernet per record, mirrors edge_agent | Postgres TDE not configured; app-level as today |
| compose change | one named volume | one named volume | volume + `depends_on` + credentials |
| migrations | a schema this service owns, outside Alembic's tree | none | either a schema in the GULA DB or a second DB |
| survives host loss | no (volume is local) | no | yes (the DB is backed up) |
| matches edge precedent | partly | **closest** | no |
| failure mode if the store is unavailable | process cannot start | process cannot start | bridge is coupled to GULA's DB being up — which defeats the offline purpose |

Note on C: coupling the bridge's offline queue to the GULA database would mean
the queue that exists for "GULA is unreachable" requires GULA's database to be
reachable. That is a contradiction, not a trade-off, and it is the reason this
document does not simply recommend "use PostgreSQL because the Constitution says
PostgreSQL first" — the Constitution's ordering is about not reaching for hosted
SaaS, not about defeating an offline design.

## 5. The decision required

> **Which store backs `services/device_bridge`, and how is PHI encrypted at rest
> in it?**

Two coupled halves. The second cannot be deferred: an unencrypted durable store
is a new PHI-at-rest location, which is worse than the current loss in exactly
one respect — the loss is at least not a disclosure.

A recommendation, offered as a recommendation and not as a decision: **B**, an
encrypted append-only store on a named volume, reusing `edge_agent`'s Fernet
pattern and key handling. It is the only option that matches an existing,
reviewed precedent in this repository, adds no dependency to the image, keeps the
bridge independent of GULA's availability, and carries encryption by
construction rather than as a follow-up. Its weaknesses are real and stated:
no transactions, a lock needed for concurrent writes, and no survival of host
loss.

## 6. Preparatory work already done

- **The contract is executable.** `tests/test_storage_durability_contract.py`
  states, as tests, what any store must do: five collections preserved across a
  simulated process restart, append-only ordering, no loss of a queued item on a
  staging failure, and the four API endpoints reading what was written. It is
  parameterised over a store factory, so a durable implementation is validated by
  running the same suite with one added factory — no test rewriting.
- **The in-memory store is registered as the first implementation**, and the
  persistence cases are marked `xfail(strict=True)` against it. They pass today
  by failing, and they fail loudly the moment a store makes them pass, which is
  the cue to register the new factory and delete the xfail.
- **The restart probe is scripted** (§1), so the runtime proof is one command
  rather than a rediscovery.

## 7. What must NOT happen

Marking IA-040 closed because the tests are green. The suite is green *with the
persistence requirement declared as a known failure*. That is an honest record of
a gap, not its resolution.
