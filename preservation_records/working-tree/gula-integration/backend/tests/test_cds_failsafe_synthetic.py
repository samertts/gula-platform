"""Phase B (F-068 / D-023) — CDS fail-safe, synthetic data only.

Every patient, observation and value below is fictional. No real patient data,
no DB connection, no network, no mounted clinical route.

The nine permissive paths (one guideline comparison + eight risk factors) must
never convert missing/unparseable clinical data into a normal-looking result.
On failure: INDETERMINATE, no actionable recommendation, original values kept,
a warning is logged (audit hook), and evaluation never raises (emergency care
continues).

Evidence id: E-054 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from app.national.domain.observation import Observation
from app.national.domain.patient import Patient
from app.national.services.cds_engine import (
    STATUS_INDETERMINATE,
    ClinicalDecisionSupportEngine,
)


# ---------------------------------------------------------------------------
# scripted fake DB — each query() call consumes the next scripted result list.
# ---------------------------------------------------------------------------


class _FakeQuery:
    def __init__(self, rows: list[Any]):
        self._rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeDB:
    def __init__(self, *script: list[Any]):
        self._script = [list(rows) for rows in script]

    def query(self, model):
        return _FakeQuery(self._script.pop(0) if self._script else [])


def _patient() -> Patient:
    return Patient(id="SYNTH-P1", date_of_birth=date(1990, 1, 1))


def _obs(code: str, value: str | None, category: str = "vital-signs") -> Observation:
    return Observation(
        patient_id="SYNTH-P1",
        code=code,
        category=category,
        value_quantity=value,
        effective_datetime=datetime(2026, 11, 17, 10, 0, 0),
    )


@pytest.fixture
def engine() -> ClinicalDecisionSupportEngine:
    return ClinicalDecisionSupportEngine()


@pytest.fixture
def single_step_guideline(monkeypatch):
    """One synthetic hypertension guideline driven by observation 8480-6."""
    monkeypatch.setattr(
        ClinicalDecisionSupportEngine,
        "_get_guideline_registry",
        lambda self: {
            "synth_htn": {
                "id": "synth_htn",
                "name": "Synthetic hypertension follow-up",
                "description": "Synthetic guideline for fail-safe testing",
                "conditions": [{"code": "SYNTH-HTN"}],
                "steps": [
                    {
                        "name": "Blood pressure control",
                        "observation_code": "8480-6",
                        "threshold_value": "140",
                        "comparison": "<=",
                        "recommendation": "Review antihypertensive therapy",
                    }
                ],
            }
        },
    )


class TestGuidelineFailSafe:
    """The 'Target met' false-normal path (root cause of F-068)."""

    def _evaluate(self, engine, value: str | None):
        db = _FakeDB(
            [_patient()],                                  # patient lookup
            [_obs("SYNTH-HTN", None, "condition")],        # condition observations
            [_obs("8480-6", value)],                       # recent observation
        )
        return engine.evaluate_clinical_guidelines(db, "SYNTH-P1")

    def test_valid_input_target_met(self, engine, single_step_guideline):
        result = self._evaluate(engine, "130")
        rec = result[0]["recommendations"][0]
        assert rec["is_met"] is True
        assert rec["recommendation"] == "Target met"
        assert result[0]["overall_status"] is True
        assert result[0]["status"] == "DETERMINATE"

    def test_valid_input_not_met(self, engine, single_step_guideline):
        result = self._evaluate(engine, "160")
        rec = result[0]["recommendations"][0]
        assert rec["is_met"] is False
        assert rec["status"] == "NOT_MET"
        assert result[0]["overall_status"] is False

    def test_unparseable_value_is_indeterminate_not_target_met(self, engine, single_step_guideline, caplog):
        result = self._evaluate(engine, "not-a-number")
        rec = result[0]["recommendations"][0]
        assert rec["is_met"] is None
        assert rec["status"] == STATUS_INDETERMINATE
        assert rec["current_value"] == "not-a-number"          # original preserved
        assert "Target met" not in rec["recommendation"]
        assert "escalate" in rec["recommendation"].lower()
        assert result[0]["overall_status"] == STATUS_INDETERMINATE
        assert any("cds_indeterminate" in r.message for r in caplog.records)

    def test_missing_value_is_indeterminate(self, engine, single_step_guideline):
        result = self._evaluate(engine, None)
        assert result[0]["recommendations"][0]["is_met"] is None
        assert result[0]["overall_status"] == STATUS_INDETERMINATE

    def test_unknown_comparison_is_indeterminate(self, engine, monkeypatch):
        monkeypatch.setattr(
            ClinicalDecisionSupportEngine,
            "_get_guideline_registry",
            lambda self: {
                "synth": {
                    "id": "synth", "name": "Synthetic", "description": "",
                    "conditions": [{"code": "SYNTH"}],
                    "steps": [{
                        "name": "step", "observation_code": "8480-6",
                        "threshold_value": "140", "comparison": "~=?",
                        "recommendation": "do something",
                    }],
                }
            },
        )
        db = _FakeDB([_patient()], [_obs("SYNTH", None, "condition")], [_obs("8480-6", "130")])
        result = engine.evaluate_clinical_guidelines(db, "SYNTH-P1")
        assert result[0]["overall_status"] == STATUS_INDETERMINATE

    def test_emergency_continuity_no_exception_and_visible_state(self, engine, single_step_guideline):
        # The fail-safe withholds only the unreliable recommendation; it never
        # raises, never returns an empty "all fine" result, and never blocks.
        result = self._evaluate(engine, "garbage")
        assert isinstance(result, list) and result
        assert result[0]["status"] == STATUS_INDETERMINATE
        assert result[0]["message"]


class TestRiskScoreFailSafe:
    """The eight silent risk-factor exception paths."""

    @pytest.mark.parametrize("risk_type, code", [
        ("cardiovascular", "8480-6"),   # systolic BP
        ("diabetes", "1558-6"),         # fasting glucose
    ])
    def test_unparseable_factor_makes_score_indeterminate(self, engine, risk_type, code, caplog):
        db = _FakeDB(
            [_patient()],
            [_obs(code, "abc")],
        )
        result = engine.calculate_risk_score(db, "SYNTH-P1", risk_type)
        assert result["score"] is None
        assert result["risk_level"] == "indeterminate"
        assert result["status"] == STATUS_INDETERMINATE
        assert result["warnings"]
        markers = [f for f in result["factors"] if f.get("risk") == "indeterminate"]
        assert markers
        assert markers[0]["contribution"] is None
        assert markers[0]["value"] == "abc"                  # original preserved
        assert any("cds_indeterminate" in r.message for r in caplog.records)

    def test_valid_factors_produce_determinate_score(self, engine):
        db = _FakeDB([_patient()], [_obs("8480-6", "190")])
        result = engine.calculate_risk_score(db, "SYNTH-P1", "cardiovascular")
        assert isinstance(result["score"], float)
        assert result["status"] == "DETERMINATE"
        assert result["warnings"] == []
        assert result["risk_level"] in {"low", "moderate", "high", "very_high"}

    def test_cardiovascular_hba1c_bmi_paths_indeterminate(self, engine):
        # Multiple unparseable factors (HbA1c + BMI) are all preserved.
        db = _FakeDB(
            [_patient()],
            [_obs("4548-4", "bad"), _obs("39156-5", "also-bad")],
        )
        result = engine.calculate_risk_score(db, "SYNTH-P1", "diabetes")
        marked = {f["name"] for f in result["factors"] if f.get("risk") == "indeterminate"}
        assert {"hba1c", "bmi"}.issubset(marked)
        assert result["score"] is None

    def test_human_override_no_actionable_recommendation_on_failure(self, engine, single_step_guideline):
        # The engine issues no actionable order on indeterminate data; a human
        # clinician / override workflow (UI layer, out of scope here) stays in
        # control. We assert the engine never emits a treatment directive.
        db = _FakeDB([_patient()], [_obs("SYNTH-HTN", None, "condition")], [_obs("8480-6", "??")])
        result = engine.evaluate_clinical_guidelines(db, "SYNTH-P1")
        rec = result[0]["recommendations"][0]
        assert rec["recommendation"] != "Review antihypertensive therapy"  # step directive withheld
        assert rec["current_value"] == "??"  # data preserved for the human reviewer
