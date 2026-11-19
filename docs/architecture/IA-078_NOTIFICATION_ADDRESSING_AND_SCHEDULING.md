# IA-078 / IA-079 / IA-080 / IA-081 — the notification path, followed to the end

Found by following my own open item from IA-076: *"whether a critical
lab-result alert reaches a patient on a configured deployment is **not
measured** here, and should not be assumed from this fix."*

It does not. Here is why, in four parts.

| | Severity | Reachability | Status |
|---|---|---|---|
| **IA-078** critical alert addressed to a citizen UUID | P0 if wired | **latent** — no caller | FIXED `91efeb15` |
| **IA-079** `schedule_notification` ignores `schedule_at` | P1 | advertised capability | FIXED `9ea92e64` |
| **IA-080** national scheduler spends the delay as a timeout | P1 | served, `POST /schedules` | FIXED `9ea92e64` |
| **IA-081** served citizen endpoint with no writer anywhere | P2 | served, `GET …/notifications/{id}` | **RECORDED, not repaired** |

Negative proofs NP-AR, NP-AS, NP-AT, NP-AV — all restored byte-identically
(sha256).

---

## IA-078 — the address was not an address

```python
if channel != "in_app":
    return self._platform.send_notification(channel=channel, to=citizen_id, ...)
```

Measured against a **working** stub SMS gateway, so this is not a transport
failure:

```
result   NotificationResult(success=True, channel='sms', error=None)
gateway  {"to": "c7f3a1e2-9b44-4d10-8e55-0a1b2c3d4e5f",
          "text": "Potassium 7.9 mmol/L", "sender": null}
```

An internal identifier where a phone number belongs. The gateway answered 200,
so `raise_for_status()` passed, so the platform reported delivery.

> **A critical potassium was reported delivered and reached nobody, on a fully
> configured deployment.**

This is the layer IA-076 cannot help with. There, the transport honestly
reported having sent nothing. Here the transport genuinely succeeded and the
address was wrong, so **every honest signal in the stack said yes**. Honest
reporting of a wrong action is still a wrong action.

It did confirm IA-076's fix reaches this path. The same call with SMS
unconfigured now gives:

```
[SMS] NOT DELIVERED to c7f3a1e2-…: SMS_API_URL is not configured.
NotificationResult(success=False, channel='sms', error='Delivery failed')
```

where before `9cadde77..aa1931a6` it gave `success=True`.

### Why the repair is a refusal and not a lookup

`CitizenNotificationService` holds no citizen registry, no session and no
contact repository. Resolving an identifier to an address would mean deciding
*which* address — verified only? consented? primary? — which is policy, and
the standing brief forbids inventing it. So the address is the caller's to
supply, and a non-`in_app` channel without one raises rather than addressing an
identifier. `recipient_phone` is keyword-with-default on the `AlertService`
methods only so that no existing positional call is silently re-bound; omitting
it raises rather than texting a UUID. The `in_app` default path is untouched.

### Reachability: latent, said plainly

`AlertService` has **no caller anywhere**. `citizen_platform/integration.py`
constructs it on a line of its own and keeps nothing:

```python
notifications = CitizenNotificationService(notification_service=platform_notifications)
AlertService(notification_service=notifications)      # value discarded
```

An AST search across `app/` and `tests/` for every writer name
(`send_notification`, `broadcast_notification`, `send_critical_alert`,
`send_lab_result_alert`, `send_medication_alert`,
`send_appointment_reminder`) finds no call outside `notifications.py` itself.
The only other mention in the repository is a string in `app/ai/guardrails.py`'s
list of tool names.

So the severity is conditional, and saying so matters: **the first change that
wires a caller would have shipped the defect.**

---

## IA-079 and IA-080 — a schedule nothing could honour

### The root cause

`app/tasks/schema.py::TaskPayload` carries `task_id, type, payload,
retry_count, max_retries, timeout_s, enqueued_at` — **no `delay`, no `run_at`,
no `eta`** — and both queue implementations take `enqueue(task)` alone.
Nothing in this platform can hold a task until a future time.

### IA-079, `app/platform/notifications.py`

`schedule_notification` accepted `schedule_at` and ignored it. Measured with
`schedule_at=2027-01-01 09:00`: one immediate gateway POST, no trace of the
date anywhere, `success=True`. `PlatformRegistry` advertised the method as
*"Schedule a notification for later delivery."*

### IA-080, `app/national/notification_platform`

The same, with a twist that made it hard to see:

```python
delay_s = max(0, (scheduled_at - _now()).total_seconds())
await task_queue.enqueue(TaskPayload(..., timeout_s=int(delay_s) + 60))
```

The delay **is** computed — and then spent as the task's *timeout*, which is
how long a task may run, not when it may start. So the delivery task was
enqueued for immediate execution with an inflated timeout, a
`NotificationSchedule` row was persisted saying otherwise, and the route
answered **201** echoing the future date back to the caller.

Nor would a poller have rescued it: the only reader of `NotificationSchedule`
is the `GET /schedules` listing, and `find_due_schedules` belongs to
`background_platform` and a different repository.

### Why refusal rather than building the scheduler

Building the missing primitive means choosing retry, visibility and recurrence
semantics for a path that carries medication reminders, appointments and
results. That is not a decision to make while passing through. A future or
recurring schedule is refused with the gap named; an immediate send still
works; the served route returns **501** rather than a 500 or a false 201.

Both refusals name the same missing primitive, from one constant each, and a
test asserts both mention `TaskPayload` and `delay` — two refusals that drift
apart are worse than one.

### A defect in my own earlier repair

`PlatformRegistry.get_capabilities` did:

```python
entry["available"] = available          # the MODULE's flag
```

overwriting a capability's own declaration with the module-level default. A
module that works overall therefore republished its broken capability as
available — **the same fake-success shape, introduced by the fix for it
(IA-058)**. The more specific statement now wins, and never the other way
round: an unavailable module makes every capability unavailable, and a
capability may declare itself unavailable inside a working module.

---

## IA-081 — a served endpoint that can only return nothing

`GET /citizen-platform/notifications/{citizen_id}` is registered and reads
`self._notifications`, the per-process dict the writer methods append to. With
no writer anywhere (above), it answers:

```json
{"notifications": [], "total": 0, "unread_count": 0}
```

and can never answer anything else. **A client cannot distinguish that from a
citizen who genuinely has no notifications** — which is exactly why 200 +
empty is worse than an error here, and what the standing brief means by
*"Never make an endpoint return 200 + empty data."* Same shape as
IA-014/IA-015.

Two further properties were measured: the store is a dict on the instance, so
an alert written by one gunicorn worker is invisible to a request served by
another (default `WEB_CONCURRENCY=3`), and it is gone on restart.

**Not repaired.** Whether citizen notifications should be persisted, and in
which table, is a schema and product decision, and the migration policy makes
it a new revision that needs review. The tests pin every part of the
measurement — the dict, the absence of writers, the discarded construction —
and each says what to re-read if it fires, so the gap cannot close or widen
silently.

---

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AR | remove the wrapper's refusal of a future `schedule_at` | `test_a_future_schedule_is_refused_not_sent_now` | sha256 OK |
| NP-AS | restore `timeout_s=int(delay_s)+60` and drop the national refusal | 3, incl. 2 behavioural | sha256 OK |
| NP-AT | restore `entry["available"] = available` in the registry | `test_the_capability_listing_no_longer_advertises_scheduling` | sha256 OK |
| NP-AV | pass `citizen_id` as the address again and drop the refusal | **7**, incl. `test_a_critical_alert_with_a_phone_number_reaches_that_number` | sha256 OK |

NP-AV is the one that matters. The test that caught it hardest asserts the
address **the gateway actually received**, not the result flag — the result
flag read `True` throughout the defect, so a test written against it would
have passed in both states.

## Two tests that documented fictions

`tests/test_national_notification_platform.py::TestSchedule::
test_schedule_notification` scheduled for `+2h` and then checked only the
returned `timezone` and `recurring` flag — never that delivery was deferred.
So it passed while the notification was sent at once. It documented the
fiction without examining it. Rewritten as three tests: the refusal, a positive
control that a non-future schedule still queues, and the recurring refusal.

(The same pattern as IA-064's `test_ia064_two_messages_with_no_patient_identifier_collapse_into_one_patient`,
which asserted the collision. A test can pin a defect two ways: by asserting
it, or by asserting around it.)

## Suite state

`backend/tests/` — **3721 passed**, 191 skipped, 2 xfailed. Three failures
remain, all three caused by the uncommitted migration files the session's
permission classifier blocks (`20260820_0003`, `20260910_0001`,
`20260820_0004`); isolated by setting those files aside — `tests/migrations/`
and `test_migration_resilience.py` then give 18 passed, 0 failed — and the
files restored with sha256 verified.

## Still open

* **IA-081**, above, by decision rather than oversight.
* The migration patch now also needs
  `backend/tests/migrations/test_migration_corpus_completeness.py`'s
  `KNOWN_UNCREATED_FK_TARGETS` ledger updated: `20260820_0003` creates
  `hospital_operation_theaters`, so the ledger's expectation that it is still
  uncreated is correct today and wrong once the migration lands. That is the
  IA-054 guard working, and the two must move together.
* `NotificationSender.send_push` imports `firebase_admin` lazily; whether that
  dependency is in the production image was not checked.
* Recipient addresses and phone numbers are still logged in the clear on both
  the refusal and the delivered paths, as before. That is six log statements
  across `shared/notifications/sender.py` and was not changed here.
