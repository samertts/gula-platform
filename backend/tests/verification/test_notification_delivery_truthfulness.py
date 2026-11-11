"""An unconfigured notification channel reported every message as delivered.

IA-076 / IA-077, found by following the delegation out of
``app/notifications/service.py``: ``NotificationService`` looked clean because
the effect happens one level down, in ``shared/notifications/sender.py``.

Three of the five channels returned ``True`` when their vendor was not
configured:

    send_email      not self._smtp_host        -> True
    send_sms        not self._sms_api_url      -> True
    send_whatsapp   not self._whatsapp_api_url -> True
    send_push       not self._fcm_key          -> False   <- correct
    send_ntfy       not self._ntfy_base_url    -> False   <- correct

The two correct ones are in the same class, so ``True`` was not a considered
design decision about development ergonomics. It was a defect, and the
contrast inside one file is the evidence.

``SMTP_HOST``, ``SMS_API_URL`` and ``WHATSAPP_API_URL`` appear in neither
``.env.example`` nor ``config.py`` — they are read with ``os.getenv(..., "")``
in the sender alone — so **unconfigured is the default state of every
deployment**, not an edge case.

WHAT IT COST. ``NotificationService._run_with_circuit`` raises on a falsey
return, so ``False`` is already a channel the service handles; ``True`` was
converted into ``NotificationResult(success=True, error=None)`` and travelled
up unchallenged. ``POST /auth/verification/request`` (registered in
``factory.py``'s ``core_routes``) then discarded the result entirely and
answered 202 "a verification code has been sent" having sent nothing.

IA-077, the second defect on the same lines. The unconfigured SMS and WhatsApp
paths logged ``Body=%s`` with ``body[:50]``. The verification message is
``Your GULA verification code is 847213. It expires in 15 minutes.`` — the
first fifty characters are the one-time code, logged beside the recipient's
phone number. Anyone able to read application logs could take over any account
by calling ``/auth/verification/request`` and reading the log. On the clinical
channels the same line would carry the result value. The body is no longer
logged on any refusal path.

The repair keeps the ``-> bool`` contract and returns ``False``, matching the
two channels that were already right, so no caller changes shape.
"""
from __future__ import annotations

import ast
import logging
import pathlib

import pytest

SENDER = (
    pathlib.Path(__file__).resolve().parents[3]
    / "shared" / "notifications" / "sender.py"
)

#: Every channel on ``NotificationSender``, with the attribute that gates it.
#: Pinned as an exact mapping: a channel added without a refusal test fails
#: ``test_the_channel_ledger_matches_the_class``, so this suite cannot go stale
#: by a new ``send_*`` method quietly appearing beside it.
CHANNELS = {
    "send_email": "_smtp_host",
    "send_sms": "_sms_api_url",
    "send_whatsapp": "_whatsapp_api_url",
    "send_push": "_fcm_key",
    "send_ntfy": "_ntfy_base_url",
}

#: Arguments for each channel, so one parametrised test can drive all five.
CALLS = {
    "send_email": ("patient@example.test", "CRITICAL result", "Potassium 7.9 mmol/L"),
    "send_sms": ("+9647700000000", "Your GULA verification code is 847213."),
    "send_whatsapp": ("+9647700000000", "Potassium 7.9 mmol/L"),
    "send_push": ("device-token", "CRITICAL result", "Potassium 7.9 mmol/L"),
    "send_ntfy": ("Potassium 7.9 mmol/L",),
}


def _unconfigured_sender():
    """A sender with no vendor configured for any channel.

    Constructed with explicit empty strings and with the environment ignored,
    so the test does not depend on what happens to be exported in CI.
    """
    from shared.notifications.sender import NotificationSender

    sender = NotificationSender()
    for attribute in CHANNELS.values():
        setattr(sender, attribute, "")
    return sender


# --------------------------------------------------------------------------
# positive control: the corpus is real
# --------------------------------------------------------------------------

def test_the_channel_ledger_matches_the_class():
    """Without this, every test below could pass over an empty set.

    Ratchets both ways: a new ``send_*`` channel fails here until it is added
    to CHANNELS with its gate, and removing one fails too.
    """
    from shared.notifications.sender import NotificationSender

    found = {
        name for name in dir(NotificationSender)
        if name.startswith("send_") and callable(getattr(NotificationSender, name))
    }
    assert found == set(CHANNELS), (
        f"channel set changed: only in class {sorted(found - set(CHANNELS))}, "
        f"only in ledger {sorted(set(CHANNELS) - found)}. Add the new channel "
        f"to CHANNELS and CALLS so it is covered by the refusal tests."
    )


# --------------------------------------------------------------------------
# IA-076 — no channel may claim a delivery it did not make
# --------------------------------------------------------------------------

@pytest.mark.parametrize("channel", sorted(CHANNELS))
def test_an_unconfigured_channel_does_not_report_delivery(channel):
    sender = _unconfigured_sender()
    result = getattr(sender, channel)(*CALLS[channel])
    assert result is False, (
        f"{channel} returned {result!r} with {CHANNELS[channel]} empty. A "
        f"channel with no vendor configured has delivered nothing, and must "
        f"not report that it has."
    )


@pytest.mark.parametrize("channel", sorted(CHANNELS))
def test_a_refusal_says_which_setting_is_missing(channel, caplog):
    """A bare False is honest but unactionable; the operator needs the name."""
    sender = _unconfigured_sender()
    with caplog.at_level(logging.DEBUG, logger="gula.notifications"):
        getattr(sender, channel)(*CALLS[channel])
    assert caplog.text.strip(), f"{channel} refused silently"
    assert "configured" in caplog.text


def test_the_service_turns_a_refusal_into_an_unsuccessful_result():
    """The defect's reach: what a caller one level up actually saw."""
    from app.notifications.service import NotificationService

    service = NotificationService()
    result = service.send_email("patient@example.test", "CRITICAL", "K 7.9")
    assert result.success is False, (
        "NotificationService reported success for a message no vendor was "
        "configured to send."
    )
    assert result.error, "an unsuccessful result must carry a reason"


def test_a_configured_channel_still_succeeds():
    """The other half of the ratchet: the repair is not 'return False always'.

    Without this, deleting the delivery code entirely would pass every test
    above.
    """
    from unittest.mock import MagicMock, patch

    from shared.notifications.sender import NotificationSender

    sender = NotificationSender(
        smtp_host="smtp.example.test",
        smtp_from="noreply@example.test",
    )
    with patch("shared.notifications.sender.smtplib.SMTP") as smtp:
        smtp.return_value.__enter__.return_value = MagicMock()
        assert sender.send_email("patient@example.test", "S", "B") is True
    assert smtp.called, "the configured path must actually open an SMTP session"


# --------------------------------------------------------------------------
# IA-077 — a refusal must not log the message body
# --------------------------------------------------------------------------

@pytest.mark.parametrize("channel", sorted(CHANNELS))
def test_a_refusal_never_logs_the_message_body(channel, caplog):
    """The code and the clinical value are both in the body.

    Driven with a body that carries a recognisable secret, so this is a
    behavioural check and not a reading of the source.
    """
    sender = _unconfigured_sender()
    marker = "847213-POTASSIUM-7.9"
    args = list(CALLS[channel])
    args[-1] = f"Your GULA verification code is {marker}. It expires in 15 minutes."

    with caplog.at_level(logging.DEBUG, logger="gula.notifications"):
        getattr(sender, channel)(*args)

    assert marker not in caplog.text, (
        f"{channel} logged the message body on its refusal path. On the SMS "
        f"and WhatsApp channels that body is a one-time verification code; on "
        f"the clinical channels it is a result value."
    )
    assert "verification code" not in caplog.text


def test_no_refusal_branch_in_the_source_returns_true():
    """An AST ratchet over the guard bodies themselves.

    The behavioural tests above cover the five channels that exist today. This
    one covers the shape, so the pattern cannot come back in a sixth: inside
    any ``if not self._<gate>:`` block, ``return True`` is forbidden.
    """
    tree = ast.parse(SENDER.read_text())
    gates = set(CHANNELS.values())
    offenders: list[str] = []

    for method in ast.walk(tree):
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)):
                continue
            operand = test.operand
            if not (isinstance(operand, ast.Attribute) and operand.attr in gates):
                continue
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Return)
                    and isinstance(inner.value, ast.Constant)
                    and inner.value.value is True
                ):
                    offenders.append(f"{method.name} (not self.{operand.attr})")

    assert not offenders, (
        f"these guards return True when the channel is unconfigured, which "
        f"reports a delivery that did not happen: {sorted(set(offenders))}"
    )


def test_no_refusal_branch_in_the_source_logs_a_body():
    """The IA-077 shape ratchet, beside the behavioural one.

    Inside an ``if not self._<gate>:`` block, no logging call may be passed
    the method's ``body`` or ``message`` parameter — including sliced, which
    is how the leak was written (``body[:50]``).
    """
    tree = ast.parse(SENDER.read_text())
    gates = set(CHANNELS.values())
    offenders: list[str] = []

    def mentions_body(node: ast.AST) -> bool:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in {"body", "message"}:
                return True
        return False

    for method in ast.walk(tree):
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)):
                continue
            operand = test.operand
            if not (isinstance(operand, ast.Attribute) and operand.attr in gates):
                continue
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr in {
                        "debug", "info", "warning", "error", "critical", "exception",
                    }
                    and any(mentions_body(arg) for arg in inner.args)
                ):
                    offenders.append(f"{method.name} (not self.{operand.attr})")

    assert not offenders, (
        f"these refusal paths log the message body, which carries one-time "
        f"codes and clinical values: {sorted(set(offenders))}"
    )


# --------------------------------------------------------------------------
# the reachable caller
# --------------------------------------------------------------------------

def test_the_verification_route_no_longer_discards_the_delivery_result():
    """``/auth/verification/request`` answered 202 having sent nothing.

    The client response stays generic on purpose — telling the caller that
    delivery failed would reveal that the identifier exists — so the check is
    that the result is inspected at all, and that the failure is recorded
    server-side.
    """
    route = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "routes" / "verification.py"
    )
    tree = ast.parse(route.read_text())

    issue = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_issue_code"
    )

    sends = [
        n for n in ast.walk(issue)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"send_email", "send_sms"}
    ]
    assert sends, "the verification code is no longer sent at all"

    # every send must be bound to a name rather than evaluated and dropped
    bare = [
        n for n in ast.walk(issue)
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute)
        and n.value.func.attr in {"send_email", "send_sms"}
    ]
    assert not bare, (
        "the delivery result is discarded, so the route cannot know whether "
        "the code it promised to send was sent"
    )

    source = ast.get_source_segment(route.read_text(), issue) or ""
    assert ".success" in source, "the bound result is never inspected"
