"""Minimal CDS Hooks discovery and critical-value advisory service.

The service is deliberately advisory only: it does not change records, order care,
or evaluate numerical thresholds.  A card is returned solely when the source
system has already marked an incoming laboratory result as critical.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(tags=["cds-hooks"])

_SERVICE_ID = "critical-value-alert"
_CRITICAL_FLAGS = {"critical", "crit", "c", "hh", "ll", "aa"}


def _code_text(observation: dict[str, Any]) -> str:
    code = observation.get("code")
    if isinstance(code, dict):
        return str(code.get("text") or "laboratory observation")
    return "laboratory observation"


def _is_source_marked_critical(observation: dict[str, Any]) -> bool:
    direct_flag = str(observation.get("flag") or "").strip().casefold()
    if direct_flag in _CRITICAL_FLAGS:
        return True
    interpretation = observation.get("interpretation") or []
    for item in interpretation:
        if not isinstance(item, dict):
            continue
        for coding in item.get("coding") or []:
            if isinstance(coding, dict) and str(coding.get("code") or "").strip().casefold() in _CRITICAL_FLAGS:
                return True
    return False


@router.get("/cds-services", summary="CDS Hooks discovery")
def cds_services(current_user: LabUser = Depends(get_current_user)) -> dict:
    """Discover authenticated, advisory CDS services exposed by GULA."""
    del current_user
    return {
        "services": [
            {
                "id": _SERVICE_ID,
                "hook": "order-sign",
                "title": "Critical laboratory value review",
                "description": (
                    "Returns an advisory card when the source observation is already "
                    "flagged as critical. Clinical review remains mandatory."
                ),
                "prefetch": {
                    "observation": "Observation?patient={{context.patientId}}&_count=20",
                },
            },
        ],
    }


@router.post("/cds-services/critical-value-alert", summary="Critical-value advisory CDS Hook")
def critical_value_alert(
    payload: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
) -> dict:
    """Return a non-blocking card only for source-marked critical laboratory values."""
    del current_user
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    prefetch = payload.get("prefetch") if isinstance(payload.get("prefetch"), dict) else {}
    observation = context.get("observation") or context.get("result") or prefetch.get("observation")
    if not isinstance(observation, dict) or not _is_source_marked_critical(observation):
        return {"cards": []}

    test_name = _code_text(observation)
    return {
        "cards": [
            {
                "summary": "Critical laboratory value requires clinical review",
                "detail": (
                    f"{test_name} is marked critical by the source system. "
                    "Clinical review of the patient context and local escalation protocol is required before acting."
                ),
                "indicator": "critical",
                "source": {"label": "GULA Clinical Safety", "url": "https://gula.health"},
                "suggestions": [
                    {
                        "label": "Open and review the source observation",
                        "actions": [],
                    },
                ],
            },
        ],
    }
