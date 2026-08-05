"""Phase 6 — Failure Manager.

Classify a failure as temporary, permanent, configuration, credential,
infrastructure, implementation, or knowledge. Retry automatically where safe
(transient), resume automatically where possible, and escalate only when
human action is required. Every failure and recovery is recorded for the
mission history.
"""

from __future__ import annotations

import re

from scripts.orchestrator.core import (
    FailureClass,
    FailureDecision,
)

# Signals that a failure is transient and safe to retry.
TRANSIENT_SIGNALS: tuple[re.Pattern, ...] = (
    re.compile(r"\btimeout\b", re.IGNORECASE),
    re.compile(r"\btimed\s+out\b", re.IGNORECASE),
    re.compile(r"\bconnection\s+(?:refused|reset|error)\b", re.IGNORECASE),
    re.compile(r"\btemporarily\s+unavailable\b", re.IGNORECASE),
    re.compile(r"\bbusy\b", re.IGNORECASE),
    re.compile(r"\brate.?limit", re.IGNORECASE),
    re.compile(r"\bnetwork\s+error\b", re.IGNORECASE),
    re.compile(r"\b503\b"),
    re.compile(r"\bretry\b", re.IGNORECASE),
)

CREDENTIAL_SIGNALS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:401|403)\b"),
    re.compile(r"\bunauthorized\b", re.IGNORECASE),
    re.compile(r"\bforbidden\b", re.IGNORECASE),
    re.compile(r"\bcredential\b", re.IGNORECASE),
    re.compile(r"\binvalid\s+(?:api.?key|token|password)\b", re.IGNORECASE),
    re.compile(r"\bauthentication\s+failed\b", re.IGNORECASE),
)

CONFIG_SIGNALS: tuple[re.Pattern, ...] = (
    re.compile(r"\bconfiguration\s+error\b", re.IGNORECASE),
    re.compile(r"\bunknown\s+(?:setting|option|env)\b", re.IGNORECASE),
    re.compile(r"\bmissing\s+(?:config|setting|variable)\b", re.IGNORECASE),
    re.compile(r"\bkeyerror\b", re.IGNORECASE),
)

INFRA_SIGNALS: tuple[re.Pattern, ...] = (
    re.compile(r"\bdocker\b", re.IGNORECASE),
    re.compile(r"\bkubernetes\b", re.IGNORECASE),
    re.compile(r"\bcontainer\b", re.IGNORECASE),
    re.compile(r"\bdatabase\s+unavailable\b", re.IGNORECASE),
    re.compile(r"\bdisk\s+full\b", re.IGNORECASE),
    re.compile(r"\boom\b", re.IGNORECASE),
    re.compile(r"\bconnection\s+to\s+postgres\b", re.IGNORECASE),
)

IMPLEMENTATION_SIGNALS: tuple[re.Pattern, ...] = (
    re.compile(r"\bassertion\b", re.IGNORECASE),
    re.compile(r"\battributeerror\b", re.IGNORECASE),
    re.compile(r"\btypeerror\b", re.IGNORECASE),
    re.compile(r"\bimporterror\b", re.IGNORECASE),
    re.compile(r"\bnameerror\b", re.IGNORECASE),
    re.compile(r"\bvalueerror\b", re.IGNORECASE),
    re.compile(r"\bcrash\b", re.IGNORECASE),
    re.compile(r"\bsegmentation\b", re.IGNORECASE),
)


def classify_failure(task_id: str, error: str) -> FailureDecision:
    """Deterministically classify a failure and choose the action."""
    for signals, cls, action, retry, human in (
        (TRANSIENT_SIGNALS, FailureClass.TEMPORARY, "retry", True, ""),
        (CREDENTIAL_SIGNALS, FailureClass.CREDENTIAL, "escalate", False, "rotate or supply credentials"),
        (CONFIG_SIGNALS, FailureClass.CONFIGURATION, "escalate", False, "correct the configuration"),
        (INFRA_SIGNALS, FailureClass.INFRASTRUCTURE, "escalate", False, "restore or provision infrastructure"),
        (IMPLEMENTATION_SIGNALS, FailureClass.IMPLEMENTATION, "resume_after_fix", False, ""),
    ):
        if any(sig.search(error) for sig in signals):
            return FailureDecision(
                task_id=task_id,
                error=error,
                failure_class=cls.value,
                action=action,
                retry_allowed=retry,
                human_action_required=human,
            )
    # No signal matched: deterministic default is permanent/escalate.
    return FailureDecision(
        task_id=task_id,
        error=error,
        failure_class=FailureClass.PERMANENT.value,
        action="escalate",
        retry_allowed=False,
        human_action_required="review the failure for the correct owner",
    )


def retry_allowed(decision: FailureDecision, attempt: int, max_attempts: int = 3) -> bool:
    """Retry only when safe AND under the attempt budget."""
    return decision.retry_allowed and attempt < max_attempts


def escalate(decision: FailureDecision) -> bool:
    """Escalation is required when human action is necessary."""
    return bool(decision.human_action_required) or decision.action == "escalate"
