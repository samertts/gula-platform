from datetime import UTC, datetime, timedelta

import pytest
from app.chronic_care.alerts import AlertOrchestrator
from app.chronic_care.baselines import build_baseline, evaluate_against_baseline
from app.chronic_care.care_plans import CarePlan, CarePlanState, InvalidCarePlanTransition


def test_baseline_warms_up_and_detects_personal_deviation():
    warming = build_baseline("heart_rate", [70, 71, 72], min_samples=7)
    assert warming.status == "warming_up"
    assert not evaluate_against_baseline(warming, 150).is_anomaly

    ready = build_baseline(
        "heart_rate", ([70, 71, 72, 69, 70, 73, 71, 72, 70, 71] * 3), min_samples=7
    )
    evaluation = evaluate_against_baseline(ready, 110)
    assert evaluation.is_anomaly is True
    assert evaluation.requires_clinician_review is True
    assert evaluation.severity in {"moderate", "high"}


def test_alerts_are_quality_gated_and_deduplicated():
    baseline = build_baseline("spo2", ([97, 98, 97, 98, 97, 98, 97, 98] * 4), min_samples=7)
    evaluation = evaluate_against_baseline(baseline, 88)
    orchestrator = AlertOrchestrator(cooldown_minutes=30)
    now = datetime.now(UTC)

    assert orchestrator.evaluate(10, evaluation, now=now, signal_quality=0.5) is None
    first = orchestrator.evaluate(10, evaluation, now=now, corroborated=True)
    assert first is not None
    assert first.escalation_level == "clinician"
    assert (
        orchestrator.evaluate(10, evaluation, now=now + timedelta(minutes=5), corroborated=True)
        is None
    )
    assert len(orchestrator.open_alerts(10)) == 1


def test_care_plan_requires_explicit_clinician_approval_and_version():
    plan = CarePlan(
        patient_id=1, condition_code="hypertension", goals=[{"code": "bp", "target": "<140/90"}]
    )
    plan.transition(CarePlanState.PENDING_REVIEW, actor_id=20)
    with pytest.raises(InvalidCarePlanTransition):
        plan.transition(CarePlanState.ACTIVE, actor_id=20)
    plan.transition(CarePlanState.ACTIVE, actor_id=20, clinician_approved=True)
    current_version = plan.version
    plan.update_goals([{"code": "bp", "target": "<135/85"}], expected_version=current_version)
    with pytest.raises(InvalidCarePlanTransition):
        plan.update_goals([{"code": "bp", "target": "<130/80"}], expected_version=current_version)
