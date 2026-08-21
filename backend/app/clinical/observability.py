"""Privacy-preserving operational metrics for clinical command safety.

This module intentionally records only low-cardinality, allow-listed labels.  It
never accepts patient identifiers, user identifiers, resource identifiers,
idempotency keys, request bodies, free-text reasons, or clinical values.
"""
from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Final

_ALLOWED_OUTCOMES: Final[frozenset[str]] = frozenset({"claimed", "completed", "rejected"})
_ALLOWED_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "audit_write_failed",
        "authorization_denied",
        "clinical_version_conflict",
        "duplicate_command",
        "idempotency_race",
        "invalid_state_transition",
        "missing_idempotency_key",
        "missing_if_match",
        "validation_failed",
        "workflow_rejected",
        "unknown",
    }
)


def _safe_label(value: str | None, *, fallback: str = "unknown", maximum: int = 96) -> str:
    """Return a bounded label without preserving untrusted free text."""
    if not value:
        return fallback
    normalized = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value).lower())
    return normalized[:maximum] or fallback


def reason_code(reason: str | None) -> str:
    """Map untrusted exception text to a finite reason code without exporting it."""
    message = (reason or "").casefold()
    if "audit" in message:
        return "audit_write_failed"
    if "idempotency" in message or "already processed" in message or "already claimed" in message:
        return "duplicate_command"
    if "version" in message or "if-match" in message or "stale" in message:
        return "clinical_version_conflict"
    if "permission" in message or "authority" in message or "forbidden" in message:
        return "authorization_denied"
    if "state" in message or "transition" in message or "cannot be" in message:
        return "invalid_state_transition"
    if "required" in message or "invalid" in message or "must" in message:
        return "validation_failed"
    return "workflow_rejected" if message else "unknown"


class ClinicalSafetyMetrics:
    """Process-local counters exported through the existing Prometheus endpoint.

    Prometheus must apply `rate()` to the exported counter values.  Counter
    resets after a process restart are expected and safe for this operational
    signal.  The append-only audit ledger remains the forensic source of truth.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._commands: Counter[tuple[str, str, str, str]] = Counter()
        self._audit_failures: Counter[tuple[str, str]] = Counter()

    def record_command(
        self,
        *,
        operation: str,
        resource_type: str,
        outcome: str,
        reason: str | None = None,
    ) -> None:
        outcome_label = outcome if outcome in _ALLOWED_OUTCOMES else "rejected"
        if outcome_label == "rejected":
            code = reason if reason in _ALLOWED_REASON_CODES else reason_code(reason)
        else:
            code = "none"
        key = (_safe_label(operation), _safe_label(resource_type), outcome_label, code)
        with self._lock:
            self._commands[key] += 1

    def record_audit_failure(self, *, operation: str, resource_type: str) -> None:
        key = (_safe_label(operation), _safe_label(resource_type))
        with self._lock:
            self._audit_failures[key] += 1

    def snapshot(self) -> tuple[dict[tuple[str, str, str, str], int], dict[tuple[str, str], int]]:
        with self._lock:
            return dict(self._commands), dict(self._audit_failures)

    def reset_for_test(self) -> None:
        with self._lock:
            self._commands.clear()
            self._audit_failures.clear()


clinical_safety_metrics = ClinicalSafetyMetrics()


def prometheus_lines() -> list[str]:
    """Render only bounded, privacy-safe clinical command counters."""
    commands, audit_failures = clinical_safety_metrics.snapshot()
    lines = [
        "",
        "# HELP gula_clinical_command_total Clinical command outcomes without patient or actor identifiers",
        "# TYPE gula_clinical_command_total counter",
    ]
    for (operation, resource_type, outcome, reason), value in sorted(commands.items()):
        lines.append(
            "gula_clinical_command_total"
            f'{{operation="{operation}",resource_type="{resource_type}",outcome="{outcome}",reason_code="{reason}"}} {value}'
        )
    lines += [
        "",
        "# HELP gula_clinical_audit_write_failure_total Clinical audit write failures; any positive value is safety-critical",
        "# TYPE gula_clinical_audit_write_failure_total counter",
    ]
    for (operation, resource_type), value in sorted(audit_failures.items()):
        lines.append(
            "gula_clinical_audit_write_failure_total"
            f'{{operation="{operation}",resource_type="{resource_type}"}} {value}'
        )
    return lines
