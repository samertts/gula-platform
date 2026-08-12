"""Clinical State Engine — GULA Platform
=======================================
Patient clinical state machine with hard-stop enforcement rules.

States (ordered by severity)
-----------------------------
  STABLE     — All results normal, patient may be discharged.
  MONITORING — One or more WARNING results; requires follow-up.
  CRITICAL   — One or more CRITICAL results; physician review mandatory.
  EMERGENCY  — Life-threatening pattern; immediate intervention required.

Transitions
-----------
  STABLE     → MONITORING  : any WARNING result
  MONITORING → CRITICAL    : any CRITICAL result
  CRITICAL   → EMERGENCY   : specific life-threatening patterns (see _EMERGENCY_RULES)
  * → STABLE               : only when ALL results return to NORMAL (explicit review)

Hard-stop rules
---------------
  CRITICAL + EMERGENCY → block result release until physician acknowledges.
  EMERGENCY            → auto-alert and mandatory re-test flag.

This module is stateless — it computes the state from the current evaluation
summary.  Persisting state changes to the DB is the caller's responsibility.

NOT a diagnostic tool — state is advisory and must be reviewed by a physician.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

# ── State constants ────────────────────────────────────────────────────────────
STATE_STABLE = "STABLE"
STATE_MONITORING = "MONITORING"
STATE_CRITICAL = "CRITICAL"
STATE_EMERGENCY = "EMERGENCY"

_STATE_RANK = {
    STATE_STABLE: 0,
    STATE_MONITORING: 1,
    STATE_CRITICAL: 2,
    STATE_EMERGENCY: 3,
}

# Severity → minimum state
_SEVERITY_TO_STATE = {
    "NORMAL": STATE_STABLE,
    "WARNING": STATE_MONITORING,
    "CRITICAL": STATE_CRITICAL,
    "UNKNOWN": STATE_MONITORING,  # unknown = treat conservatively
}

# ── Emergency pattern rules ────────────────────────────────────────────────────
# Each rule is a (test_key, condition_fn) pair.
# If ALL conditions in a rule match → EMERGENCY.
_EMERGENCY_RULES: list[dict] = [
    {
        "id": "glucose_critical_low",
        "description": "Severe hypoglycaemia (glucose < 40 mg/dL)",
        "description_ar": "انخفاض حاد وخطير في سكر الدم",
        "check": lambda vals: vals.get("glucose", 999) < 40,
    },
    {
        "id": "glucose_critical_high",
        "description": "Hyperglycaemic crisis (glucose > 500 mg/dL)",
        "description_ar": "أزمة ارتفاع سكر الدم",
        "check": lambda vals: vals.get("glucose", 0) > 500,
    },
    {
        "id": "severe_anaemia",
        "description": "Severe anaemia requiring immediate intervention (Hb < 6 g/dL)",
        "description_ar": "فقر دم شديد جداً يستوجب تدخلاً فورياً",
        "check": lambda vals: min(vals.get("hemoglobin", 99), vals.get("hb", 99)) < 6,
    },
    {
        "id": "critical_thrombocytopenia",
        "description": "Critical low platelets — bleeding risk (< 20 ×10³/µL)",
        "description_ar": "انخفاض حاد جداً في الصفائح الدموية — خطر نزيف",
        "check": lambda vals: vals.get("platelets", 999) < 20,
    },
    {
        "id": "critical_wbc_elevation",
        "description": "Extreme WBC elevation — possible leukaemia/sepsis (> 50 ×10³/µL)",
        "description_ar": "ارتفاع حاد جداً في كريات الدم البيضاء — احتمال إنتان أو سرطان دم",
        "check": lambda vals: vals.get("wbc", 0) > 50,
    },
    {
        "id": "acute_renal_failure",
        "description": "Acute renal failure pattern (creatinine > 8 mg/dL)",
        "description_ar": "نمط فشل كلوي حاد",
        "check": lambda vals: vals.get("creatinine", 0) > 8,
    },
]


# ── Output dataclass ───────────────────────────────────────────────────────────


@dataclass
class ClinicalStateResult:
    state: str
    previous_state: str | None
    transition_reason: str
    emergency_triggers: list[dict]
    hard_stops: list[str]  # actions that are BLOCKED in this state
    required_actions: list[str]  # actions that MUST be taken
    can_release_result: bool
    must_retest: bool
    alert_required: bool
    engine_version: str
    disclaimer: str = "هذا تحليل استرشادي فقط ولا يُغني عن رأي الطبيب المختص."

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "previous_state": self.previous_state,
            "transition_reason": self.transition_reason,
            "emergency_triggers": self.emergency_triggers,
            "hard_stops": self.hard_stops,
            "required_actions": self.required_actions,
            "can_release_result": self.can_release_result,
            "must_retest": self.must_retest,
            "alert_required": self.alert_required,
            "engine_version": self.engine_version,
            "disclaimer": self.disclaimer,
        }


# ── State computation ──────────────────────────────────────────────────────────


def _values_map(order_evaluation: dict) -> dict[str, float]:
    """Extract {test_key: value} from an evaluate_order() result."""
    vals: dict[str, float] = {}
    for r in order_evaluation.get("results", []):
        key = str(r.get("test", "")).lower().strip()
        v = r.get("value")
        if key and v is not None:
            with contextlib.suppress(TypeError, ValueError):
                vals[key] = float(v)
    return vals


def _check_emergency_rules(vals: dict[str, float]) -> list[dict]:
    """Return list of triggered emergency rules."""
    triggered = []
    for rule in _EMERGENCY_RULES:
        try:
            if rule["check"](vals):
                triggered.append(
                    {
                        "id": rule["id"],
                        "description": rule["description"],
                        "description_ar": rule["description_ar"],
                    },
                )
        except Exception:
            pass
    return triggered


def _hard_stops_for_state(state: str) -> list[str]:
    if state == STATE_EMERGENCY:
        return [
            "result_release",  # cannot send results to patient
            "discharge",  # cannot discharge patient
            "new_orders",  # cannot create new orders until emergency resolved
        ]
    if state == STATE_CRITICAL:
        return [
            "result_release_without_physician_ack",
            "discharge",
        ]
    if state == STATE_MONITORING:
        return [
            "discharge_without_followup",
        ]
    return []


def _required_actions_for_state(state: str, triggers: list[dict]) -> list[str]:
    if state == STATE_EMERGENCY:
        actions = [
            "notify_physician_immediately",
            "flag_for_retest",
            "escalate_to_supervisor",
        ]
        for t in triggers:
            actions.append(f"emergency_protocol:{t['id']}")
        return actions
    if state == STATE_CRITICAL:
        return [
            "notify_physician",
            "await_physician_acknowledgement",
        ]
    if state == STATE_MONITORING:
        return [
            "schedule_followup",
        ]
    return []


# ── Public API ─────────────────────────────────────────────────────────────────


def compute_patient_state(
    order_evaluation: dict,
    *,
    previous_state: str | None = None,
    engine_version: str = "v2.1",
) -> ClinicalStateResult:
    """Compute the clinical state from an evaluate_order() result.

    Args:
        order_evaluation: Dict returned by clinical_engine.evaluate_order().
        previous_state:   Patient's last known clinical state (for transition log).
        engine_version:   Engine version tag for audit trail.

    Returns:
        ClinicalStateResult with state, hard-stops, required actions, etc.

    """
    overall_sev: str = order_evaluation.get("overall_severity", "NORMAL")
    vals = _values_map(order_evaluation)

    # Derive base state from severity
    base_state = _SEVERITY_TO_STATE.get(overall_sev, STATE_MONITORING)

    # Check emergency rules (can escalate CRITICAL → EMERGENCY)
    emergency_triggers = _check_emergency_rules(vals)
    if emergency_triggers:
        state = STATE_EMERGENCY
        reason = f"Emergency rule(s) triggered: {', '.join(t['id'] for t in emergency_triggers)}"
    else:
        state = base_state
        reason = f"Derived from overall severity: {overall_sev}"

    # Never downgrade from a more severe previous state without explicit physician sign-off
    if previous_state and _STATE_RANK.get(previous_state, 0) > _STATE_RANK.get(state, 0):
        state = previous_state
        reason = f"Maintained previous state ({previous_state}) — no physician sign-off recorded"

    hard_stops = _hard_stops_for_state(state)
    required_actions = _required_actions_for_state(state, emergency_triggers)

    return ClinicalStateResult(
        state=state,
        previous_state=previous_state,
        transition_reason=reason,
        emergency_triggers=emergency_triggers,
        hard_stops=hard_stops,
        required_actions=required_actions,
        can_release_result=state not in (STATE_CRITICAL, STATE_EMERGENCY),
        must_retest=state == STATE_EMERGENCY,
        alert_required=state in (STATE_CRITICAL, STATE_EMERGENCY),
        engine_version=engine_version,
    )


def can_release_results(state_result: ClinicalStateResult) -> bool:
    """Hard-stop: return False if results must not be released to patient."""
    return state_result.can_release_result


def requires_physician_ack(state_result: ClinicalStateResult) -> bool:
    """Return True if physician acknowledgement is mandatory before proceeding."""
    return state_result.state in (STATE_CRITICAL, STATE_EMERGENCY)
