# IA-076 / IA-077 — three notification channels reported deliveries they never made, and logged the verification code while doing it

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** reachable, `POST /auth/verification/request`
**Fix status** FIXED — `aa1931a6` on `claude/independent-audit-1`
**Negative proofs** NP-AI, NP-AJ, NP-AK, NP-AL — all restored byte-identically (sha256)
**Found by** following a delegation instead of reporting the delegator

---

## How it was found

The name-independent behavioural sweep flagged `app/notifications/service.py`'s
`NotificationService`: eight `send_*` methods, no `httpx`, no `smtplib`. That
was a **false positive** — the class delegates to `get_sender()`. The real
effect happens one level down, in `shared/notifications/sender.py`, and a sweep
that reports the delegator finds nothing there.

Following the delegation found two defects on the same three lines.

## IA-076 — an unconfigured channel claimed success

```
send_email      not self._smtp_host        -> True     <- defect
send_sms        not self._sms_api_url      -> True     <- defect
send_whatsapp   not self._whatsapp_api_url -> True     <- defect
send_push       not self._fcm_key          -> False    <- already correct
send_ntfy       not self._ntfy_base_url    -> False    <- already correct
```

**The two correct ones are in the same class.** That is the evidence that
`True` was not a considered decision about development ergonomics but a
defect: the same author, in the same file, returned `False` twice.

### Unconfigured was the default, not an edge case

`SMTP_HOST`, `SMS_API_URL` and `WHATSAPP_API_URL` appeared in neither
`.env.example` nor `config.py`. They were read only here:

```python
self._smtp_host = smtp_host or os.getenv("SMTP_HOST", "")
```

So nothing told an operator the variables existed, and every deployment ran
with all three empty. Reproduced with the environment stripped:

```
smtp_host  = ''      send_email    -> True
sms_url    = ''      send_sms      -> True
wa_url     = ''      send_whatsapp -> True
                     send_push     -> False
                     send_ntfy     -> False
```

### What it cost

`NotificationService._run_with_circuit` raises on a falsey return, so `False`
was already a channel the service handled. `True` became:

```
NotificationResult(success=True, channel='email',
                   recipient='patient@example.test', error=None)
```

and travelled up unchallenged. Two consumers were measured:

* **`POST /auth/verification/request`** — registered in `factory.py`'s
  `core_routes`. It **discarded the result entirely** and answered 202
  *"If the account exists, a verification code has been sent."* having sent
  nothing. A user on a deployment with no mail vendor could never verify an
  account, and no operator signal said why.
* **`integration/connectors/email.py`** — checked `result.success` correctly,
  and so faithfully reported `{"success": true}` about nothing. It needs no
  change now; the repair propagates.

## IA-077 — the refusal path logged the one-time code

The unconfigured SMS and WhatsApp branches logged the body:

```python
logger.info("[SMS] To=%s Body=%s (API not configured, logged only)", to, body[:50])
```

`_issue_code` builds the message as:

```python
f"Your GULA verification code is {code}. It expires in 15 minutes."
```

The first fifty characters are *"Your GULA verification code is 847213. It
expires"* — the complete code. Observed:

```
LOG| [SMS] To=+9647701234567 Body=Your GULA verification code is 847213. It expires  (API not configured, logged only)
```

> **The one-time code and the phone number, together, in the application log.**
> Anyone able to read logs could take over any account by calling
> `/auth/verification/request` for its identifier and reading the next line.

On the clinical channels the same statement would have carried the result
value instead. The body is no longer logged on any refusal path.

## The repair

| | |
|---|---|
| contract | unchanged, still `-> bool`; the three channels return `False`, matching the two that were already right, so no caller changes shape |
| refusal message | names the missing variable (`SMTP_HOST is not configured`) at ERROR, so it is actionable rather than a bare `False` |
| body | never logged on a refusal path |
| the route | binds the result and records the failure server-side; the **client response stays generic**, because distinguishing "delivery failed" from "no such account" would reveal which identifiers exist |
| `.env.example` | the twelve variables are documented, with the consequence of leaving them empty stated |

**Development is unaffected.** `request_verification` already returns
`demo_code` when `DEMO_MODE or not IS_PRODUCTION`, so the "logged only" path
was never the development affordance it looked like — the code was already
available without it.

**One consequence to note.** `NotificationService` runs deliveries through a
circuit breaker with `failure_threshold=10`. On a deployment with no vendor
configured, the notification circuit will now open after ten attempts. That is
correct — the channel genuinely is unavailable — and it is what `send_push`
already caused. It is recorded here because it is a visible behaviour change.

## Three existing tests asserted the defect

`tests/notifications/test_notification_sender.py` contained:

```python
def test_send_email_smtp_not_configured_logs_only(self, caplog):
    ...
    assert result is True
    assert "SMTP not configured" in caplog.text
```

and the same for SMS and WhatsApp. The expectation *was* the defect, pinned by
a passing test. They are corrected, with the reason written into each
docstring, rather than deleted or worked around.

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AI | `send_email` returns `True` again | 4, incl. `test_no_refusal_branch_in_the_source_returns_true` and the `NotificationService` propagation test | sha256 OK |
| NP-AJ | restore **only** the `body[:50]` log, keeping `return False` | 3, all IA-077 guards | sha256 OK |
| NP-AK | discard the delivery result in the route again | `test_the_verification_route_no_longer_discards_the_delivery_result` | sha256 OK |
| NP-AL | delete the real SMTP send, so the method always returns `False` | 3, incl. `test_a_configured_channel_still_succeeds` | sha256 OK |

**NP-AJ and NP-AL are the two that matter.** NP-AJ kept `return False` and
restored only the logging, proving the IA-077 guards are independent of the
IA-076 ones rather than riding on them. NP-AL proves the repair is not
"return `False` always" — deleting the delivery code fails the positive
control.

The suite also carries a **positive control**,
`test_the_channel_ledger_matches_the_class`, which asserts the five `send_*`
methods found on the class equal the pinned ledger. Without it every
parametrised test could pass over an empty set, and a sixth channel added with
`return True` would be covered by nothing.

## A second defect the suite found on its own

Running `tests/verification/` and `tests/notifications/` together failed
`test_no_module_is_loaded_under_two_names` — the NR-087/088/081 guard:

```
modules live under both app.* and backend.app.*:
['backend.app._compat', 'backend.app.integration',
 'backend.app.integration.connectors', 'backend.app.integration.connectors.ntfy'],
expected exactly ['backend.app._compat']
```

Cause: `tests/notifications/test_ntfy_connector.py` imported
`from backend.app.integration.connectors.ntfy import ...` while everything
else imports `app....`. Both spellings resolve, so the connector was loaded
twice with separate module state — meaning **the connector registry the test
saw was not the registry the application saw**, which is exactly the failure
mode that guard was written for. One line.

I first said my new test file caused this failure. That was wrong: I had
changed the set of directories, not just the file. It reproduces with my file
ignored entirely, so it is pre-existing and was merely surfaced here.

## Suite state

`tests/verification/` + `tests/notifications/` — **961 passed**, 151 skipped,
2 xfailed, **0 failed**. `py_compile` and `pyflakes` clean on every changed
file. One pre-existing `F401` (`pytest` imported unused in the sender tests)
was removed on the way past.

## Still open

* The other notification consumers were not individually exercised.
  `citizen_platform/notifications.py::send_critical_alert` routes through a
  different service object (`_notification_service.send_notification`) which
  this work did not trace to a transport. Whether a critical lab-result alert
  reaches a patient on a configured deployment is **not measured here**, and
  should not be assumed from this fix.
* `NotificationSender.send_push` imports `firebase_admin` lazily. Whether that
  dependency is installed in the production image was not checked.
* The recipient address and phone number are still logged in the clear on both
  the refusal and the delivered paths, as they were before. That is a wider
  change across six log statements and was not made here; it is worth a
  decision separately.
