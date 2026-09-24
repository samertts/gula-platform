# Event contract

**PROGRAM-EXT-001, Phase 6.** Normative.

Events are how a domain tells the rest of the platform something happened
without anyone reading its tables. That is the whole purpose; every rule below
follows from it.

## 1. The envelope

`app/kernel/event_bus/events.py::Event`. One envelope, platform-wide.

| Field | Meaning |
| --- | --- |
| `name` | stable, dotted, past tense: `pharmacy.batch_received` |
| `version` | the **schema** version of `data`; what a consumer pins |
| `id` | unique per event, generated if absent |
| `timestamp` | when it happened |
| `source` | the publishing capability |
| `correlation_id` | follows a whole interaction across services |
| `causation_id` | the single event immediately upstream of this one |
| `tenant_id` | whose data this concerns |
| `actor_id`, `actor_type` | who caused it |
| `resource_type`, `resource_id` | what it is about |
| `provenance` | producing capability, release, deployment |
| `data` | the payload, whose shape `version` pins |

Everything from `actor_id` down was added by PROGRAM-EXT-001, additively with
defaults, so every existing publisher still constructs unchanged.

## 2. Correlation is not causation

`correlation_id` groups everything belonging to one interaction.
`causation_id` names the one event that directly produced this one.

Conflating them flattens an event graph into a list, and the first time anyone
needs to answer "what triggered this?" the answer is gone. Use:

```python
child = Event(name="pharmacy.stock_adjusted", data={...})
child.caused_by(parent)   # sets causation_id, inherits correlation_id and tenant_id
```

## 3. Versioning

* A **backward-compatible** change (adding an optional field) keeps `version`.
* A **breaking** change (removing a field, changing a type, changing meaning)
  increments `version`. Both versions are then published until every consumer
  has moved.
* An event **name** never changes meaning. A new meaning is a new name.
* Register schemas with `kernel.event_bus.versioning.EventVersioning`; migrate
  with `EventVersioning.migrate`.

## 4. Rules for consumers

1. **Never read another domain's tables.** If the event does not carry what you
   need, ask the publisher to add it (a compatible change) or call its API.
   Reaching into its schema couples you to its migrations.
2. **Pin the version you understand.** An unrecognised version goes to the dead
   letter queue, not through a best-effort parse.
3. **Assume at-least-once.** The outbox guarantees delivery, not uniqueness.
   Handlers must be idempotent on `id`.
4. **An event is not authorization.** Receiving an event tells you something
   happened; it does not tell you the recipient may see it. Apply your own
   checks before exposing anything derived from it.

## 5. Rules for publishers

1. Publish **after** the transaction commits, through the outbox
   (`app/tasks/` — the Outbox pattern), never inside a request's transaction.
2. Carry `tenant_id` on every tenant-scoped event. A consumer cannot infer it.
3. Do not put secrets, credentials, raw national IDs or full clinical payloads
   in `data`. Publish a reference (`resource_type` + `resource_id`) and let an
   authorized consumer fetch what it is allowed to see.
4. Populate `provenance` with the capability and release. When a malformed
   event appears in production, the question is always "which deployment
   produced this", and a name alone cannot answer it.

## 6. Uniqueness

Event names are unique platform-wide. Two capabilities publishing
`document.created` with different payloads is indistinguishable to a consumer
and is blocked by `test_no_two_capabilities_declare_the_same_event_name`.

## 7. What was not changed

The existing bus, outbox, inbox, dead-letter queue, retry queue, replay and
snapshot machinery in `app/kernel/event_bus/` is untouched. It works; this
document gives it a contract, not a rewrite.
