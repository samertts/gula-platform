# Blood Bank Legacy Command Paths — Investigation

**Batch:** BATCH-2.5 §7 — **investigation only**. No Blood Bank rewrite, no
behaviour change, no method removed.
**Subject:** `process_component`, `record_transfusion`, `start_transfusion`,
`complete_transfusion` in `backend/app/blood_bank/application/service.py`.

---

## 1. Two generations of command in one service

`BloodBankService` carries a legacy command set and a later `*_safely` set that
was written to replace it. Both remain.

| Legacy method | Line | `*_safely` counterpart | Line |
|---|---|---|---|
| `process_component` | 202 | *(none)* | — |
| `issue_units` | 242 | `issue_units_safely` | 330 |
| `record_transfusion` | 289 | `record_transfusion_safely` | 483 |
| `start_transfusion` | 297 | `start_transfusion_safely` | 568 |
| `complete_transfusion` | 307 | `complete_transfusion_safely` | 597 |
| `perform_crossmatch` | 261 | *(none)* | — |

## 2. Reachability

Measured by call-site search across all of `backend/`.

| Method | Callers outside its own definition | Reachable from an HTTP route? |
|---|---|---|
| `process_component` | `api/routes.py:170`, one test | **YES** — `POST /components` |
| `record_transfusion` | **0** | no |
| `start_transfusion` | **0** | no |
| `complete_transfusion` | **0** | no |
| `issue_units` | **0** | no |
| `perform_crossmatch` | **0** | no |

The three transfusion methods and `issue_units`/`perform_crossmatch` are
**dead code**: no route, no service, no task, no test calls them. Only
`process_component` is live.

The `*_safely` counterparts all have callers (5, 2, 2, 2 respectively), so the
routed transfusion workflow already uses the safe generation.

## 3. What each legacy path bypasses

| Control | Legacy four | `*_safely` |
|---|---|---|
| Tenant isolation (`lab_id`) | **present** — `_scoped` / `_owned`, fixed under NR-021 | present |
| Row locking (`SELECT … FOR UPDATE`) | **absent** | present (20 call sites) |
| State machine (`transition()`) | **absent** — status assigned by direct attribute write | present |
| Audit log | **absent** | **also absent** — see §5 |

Concretely, `start_transfusion` does:

```python
model.status = TransfusionStatus.IN_PROGRESS.value
```

with no read of the current status at all. A transfusion in any state —
`cancelled`, `completed`, `reacted` — becomes `in_progress`. Its `*_safely`
counterpart calls `transition(model.status, IN_PROGRESS, entity="transfusion")`
under `with_for_update()`. That single line is the whole of NR-020's fix, and
the legacy path never had it.

`complete_transfusion` additionally sets `unit.status = "transfused"` directly,
skipping the `transition(unit.status, ComponentStatus.TRANSFUSED.value, …)`
check that its safe counterpart performs.

## 4. Concurrency

None of the four takes a row lock. Two concurrent
`complete_transfusion` calls on one transfusion both read, both write, and both
commit; the same holds for the blood unit they touch. The `*_safely` variants
serialise on `with_for_update()`.

Because the three transfusion methods are unreachable, this is currently a
latent risk, not a live one. `process_component` **is** reachable, but it only
inserts a new row and does not mutate shared state, so it has no lost-update
exposure.

## 5. A finding that is wider than these four methods

**No method in `backend/app/blood_bank/application/service.py` writes an audit
log entry.** A search for `audit` across the file returns nothing; the only
observability is `self._emit(...)` to an optional event bus, used once, and
`event_bus` is `None` unless a caller supplies one.

Security Invariant #2 of `CLAUDE.md` states that all mutations must write to
the audit log. The blood bank domain does not satisfy it — on the legacy paths
**or** on the `*_safely` paths. This is recorded as **NR-027** and is outside
this batch's authorisation to fix.

## 6. Assessment

| Method | Risk today | Why |
|---|---|---|
| `process_component` | **LOW** | reachable, but insert-only, tenant-scoped since NR-021, and no state transition is involved |
| `record_transfusion` | LATENT | unreachable; would create a transfusion with no audit entry |
| `start_transfusion` | **LATENT-HIGH** | unreachable; would force any transfusion into `in_progress` with no state check and no lock |
| `complete_transfusion` | **LATENT-HIGH** | unreachable; would complete any transfusion and mark its unit transfused, unchecked and unlocked |

## 7. Recommended disposition — proposed, not applied

1. **RETIRE** `record_transfusion`, `start_transfusion`, `complete_transfusion`,
   `issue_units`, `perform_crossmatch`. They are unreachable and each is
   strictly weaker than an existing counterpart. Retiring dead code is not a
   rewrite.
2. **KEEP** `process_component` and route it through the state machine when the
   NR-007 attribution lands — a component moving to `available` is a state
   transition that is currently unvalidated.
3. **NR-027** (missing audit coverage) is a separate, larger piece of work and
   needs its own authorisation.

Nothing in §7 is applied in this batch.
