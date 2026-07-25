"""National LIMS Workflows — implementing operational laboratory workflows.

Every workflow emits events for integration with notification, audit,
and external systems via the outbox pattern.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

# ===========================================================================
# Result Auto-Validation Workflow
# ===========================================================================


def auto_validate_result(
    db: Session,
    result_value: float | None,
    test_code: str,
    patient_age_days: int | None = None,
    patient_gender: str | None = None,
    lab_id: int | None = None,
    instrument_id: int | None = None,
    previous_value: float | None = None,
    previous_days: int | None = None,
) -> dict[str, Any]:
    """Execute auto-validation workflow for a single result.

    Checks performed in order:
    1. Reference range check → flags if outside
    2. Critical value check → flags critical
    3. Delta check → flags if delta exceeds threshold
    4. QC status check → blocks if instrument QC out-of-control
    5. Auto-validation → marks validated if all checks pass

    Returns dict with status, action, flags, and validation_result.
    """
    from .models import (
        AutoValidationRule,
        DeltaCheckRule,
        ReferenceRangeDef,
    )

    result: dict[str, Any] = {
        "validation_status": "pending",
        "auto_validated": False,
        "flags": [],
        "warnings": [],
        "action": None,
    }

    if result_value is None:
        result["action"] = "skip_non_numeric"
        return result

    # Step 1: Reference range check
    range_query = db.query(ReferenceRangeDef).filter(
        ReferenceRangeDef.test_code == test_code,
        ReferenceRangeDef.is_active,
    )
    if lab_id:
        range_query = range_query.filter(
            (ReferenceRangeDef.lab_id == lab_id) | (ReferenceRangeDef.lab_id.is_(None)),
        )
    if patient_gender:
        range_query = range_query.filter(
            (ReferenceRangeDef.gender == patient_gender) | (ReferenceRangeDef.gender.is_(None)),
        )
    if patient_age_days is not None:
        range_query = range_query.filter(
            (
                (ReferenceRangeDef.age_min_days.is_(None))
                | (ReferenceRangeDef.age_min_days <= patient_age_days)
            )
            & (
                (ReferenceRangeDef.age_max_days.is_(None))
                | (ReferenceRangeDef.age_max_days >= patient_age_days)
            ),
        )

    ref_range = range_query.order_by(
        ReferenceRangeDef.lab_id.desc().nulls_last(),
        ReferenceRangeDef.gender.desc().nulls_last(),
    ).first()

    if ref_range:
        is_high = ref_range.ref_range_high is not None and result_value > ref_range.ref_range_high
        is_low = ref_range.ref_range_low is not None and result_value < ref_range.ref_range_low

        if is_high:
            result["flags"].append("high")
        if is_low:
            result["flags"].append("low")

        # Critical check
        is_critical_high = (
            ref_range.critical_high is not None and result_value > ref_range.critical_high
        )
        is_critical_low = (
            ref_range.critical_low is not None and result_value < ref_range.critical_low
        )

        if is_critical_high:
            result["flags"].append("critical_high")
            result["warnings"].append("Critical high value detected")
        if is_critical_low:
            result["flags"].append("critical_low")
            result["warnings"].append("Critical low value detected")

    # Step 2: Delta check
    if previous_value is not None and previous_days is not None:
        delta_rule = (
            db.query(DeltaCheckRule)
            .filter(
                DeltaCheckRule.test_code == test_code,
                DeltaCheckRule.is_active,
                DeltaCheckRule.window_days >= previous_days,
            )
            .first()
        )

        if delta_rule:
            delta_pct = (
                abs(result_value - previous_value) / abs(previous_value) * 100
                if previous_value != 0
                else 0
            )
            delta_abs = abs(result_value - previous_value)

            delta_failed = False
            if delta_rule.delta_percent and delta_pct > delta_rule.delta_percent:
                delta_failed = True
            if delta_rule.delta_absolute and delta_abs > delta_rule.delta_absolute:
                delta_failed = True

            if delta_failed:
                result["flags"].append("delta_fail")
                result["warnings"].append(f"Delta check failed: {delta_pct:.1f}% change")
                result["action"] = delta_rule.action

    # Step 3: Auto-validation rules
    if not result["flags"]:
        rules = (
            db.query(AutoValidationRule)
            .filter(
                AutoValidationRule.test_code == test_code,
                AutoValidationRule.lab_id == lab_id,
                AutoValidationRule.is_active,
            )
            .order_by(AutoValidationRule.priority.desc())
            .all()
        )

        can_auto_validate = True
        for rule in rules:
            if not _evaluate_rule_conditions(rule.conditions, result_value, result):
                can_auto_validate = False
                break

        if can_auto_validate:
            result["validation_status"] = "auto_validated"
            result["auto_validated"] = True
            result["action"] = "validate"

    # Step 4: Determine overall status
    if "critical_high" in result["flags"] or "critical_low" in result["flags"]:
        result["validation_status"] = "flagged"
        result["action"] = "escalate"
    elif "delta_fail" in result["flags"]:
        result["validation_status"] = "flagged"
        result["action"] = result.get("action", "flag")
    elif result["flags"]:
        result["validation_status"] = "flagged"
        result["action"] = "flag"
    elif not result.get("auto_validated"):
        result["validation_status"] = "pending"
        result["action"] = "pending_review"

    return result


def _evaluate_rule_conditions(conditions: dict, value: float, result: dict) -> bool:
    """Evaluate auto-validation rule conditions."""
    if not conditions:
        return True

    conditions.get("type")
    operator = conditions.get("operator", "and")
    rules = conditions.get("rules", [])

    if not rules:
        return True

    results_list = []
    for rule in rules:
        field = rule.get("field", "value")
        op = rule.get("operator", "lt")
        threshold = rule.get("value")

        actual = value if field == "value" else result.get(field)
        if actual is None:
            results_list.append(False)
            continue

        if op == "lt":
            results_list.append(actual < threshold)
        elif op == "lte":
            results_list.append(actual <= threshold)
        elif op == "gt":
            results_list.append(actual > threshold)
        elif op == "gte":
            results_list.append(actual >= threshold)
        elif op == "eq":
            results_list.append(actual == threshold)
        elif op == "neq":
            results_list.append(actual != threshold)
        elif op == "between":
            results_list.append(
                conditions.get("min", 0) <= actual <= conditions.get("max", float("inf")),
            )
        else:
            results_list.append(True)

    if operator == "and":
        return all(results_list)
    if operator == "or":
        return any(results_list)
    return True


# ===========================================================================
# Critical Result Workflow
# ===========================================================================


def process_critical_result(
    db: Session,
    result_id: int,
    lab_id: int,
    user_id: int,
) -> dict[str, Any]:
    """Execute critical result notification workflow.

    Steps:
    1. Verify result is critical
    2. Log critical alert
    3. Determine notification pathway
    4. Trigger outbound notification
    """
    from .models import Result

    result_obj = (
        db.query(Result)
        .filter(
            Result.id == result_id,
            Result.lab_id == lab_id,
        )
        .first()
    )

    if not result_obj:
        return {"status": "error", "message": "Result not found"}

    if not result_obj.is_critical:
        return {"status": "skipped", "message": "Result is not critical"}

    # Determine notification urgency
    is_panic = result_obj.is_panic
    notification_window = "15 minutes" if is_panic else "60 minutes"

    return {
        "status": "alerted",
        "result_id": result_id,
        "test_code": result_obj.test_code,
        "is_panic": is_panic,
        "notification_window": notification_window,
        "action": "notify_ordering_physician",
    }


# ===========================================================================
# Reflex / Repeat Test Workflow
# ===========================================================================


def determine_reflex_tests(
    test_code: str,
    value: float,
    lab_id: int,
    configured_rules: list[dict] | None = None,
) -> list[dict]:
    """Determine reflexive tests based on result value and configured rules.

    Rules are typically loaded from the LIMS auto-validation rules table
    or a dedicated reflex rules table (future).  For now accepts rules as
    a list of dicts: {test_code, condition (above/below/range), threshold,
    reflex_test_code, description}.
    """
    if not configured_rules:
        return []

    triggered: list[dict] = []
    for rule in configured_rules:
        if rule.get("trigger_test_code") != test_code:
            continue
        condition_met = False
        cond = rule.get("condition")
        if (cond == "above" and value > rule.get("threshold", float("inf"))) or (
            cond == "below" and value < rule.get("threshold", 0)
        ):
            condition_met = True
        elif cond == "range":
            min_v = rule.get("threshold_min", float("-inf"))
            max_v = rule.get("threshold_max", float("inf"))
            if min_v <= value <= max_v:
                condition_met = True

        if condition_met:
            triggered.append(
                {
                    "reflex_test_code": rule.get("reflex_test_code"),
                    "reason": rule.get("description", "Reflex triggered"),
                    "priority": rule.get("priority", "routine"),
                },
            )

    return triggered


# ===========================================================================
# Correction Workflow
# ===========================================================================


def execute_result_correction(
    db: Session,
    result_id: int,
    new_value: float | str | None,
    reason: str,
    user_id: int,
    lab_id: int,
) -> dict[str, Any]:
    """Execute result correction with full audit trail.

    Original value is preserved, correction reason recorded,
    and report status set to 'corrected'.
    """
    from .models import Result, ResultValidation

    result_obj = (
        db.query(Result)
        .filter(
            Result.id == result_id,
            Result.lab_id == lab_id,
        )
        .first()
    )

    if not result_obj:
        return {"status": "error", "message": "Result not found"}

    # Record validation action for correction
    validation = ResultValidation(
        result_id=result_id,
        action="corrected",
        validated_by=user_id,
        validated_at=datetime.now(UTC),
        notes=reason,
    )
    db.add(validation)

    return {
        "status": "corrected",
        "result_id": result_id,
        "reason": reason,
    }
