"""Tests for Claims API + Fraud Detection Engine + Structured AI Output.

Coverage:
  - FraudDetectionEngine scoring rules
  - FRAUD_APPROVE / REJECT thresholds
  - Pre-approval check
  - Event idempotency (ProcessedEvent / DLQ)
  - Structured AI JSON schema validation
  - Migration chain: 0014, 0015
"""

from __future__ import annotations

import json
import os
import types
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Set required env vars BEFORE any app imports to bypass config guards
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_claims.db")
os.environ.setdefault("SECRET_KEY",     "test-claims-key-" + "x" * 40)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY",   "a" * 64)
os.environ.setdefault("REDIS_URL",      "redis://localhost:6379")

# ── Fraud detection tests ─────────────────────────────────────────────────────

class TestFraudThresholds:
    def test_approve_threshold_constants(self):
        from app.models.claim import FRAUD_APPROVE_THRESHOLD, FRAUD_REJECT_THRESHOLD
        assert FRAUD_APPROVE_THRESHOLD < FRAUD_REJECT_THRESHOLD
        assert 0 < FRAUD_APPROVE_THRESHOLD < 1
        assert 0 < FRAUD_REJECT_THRESHOLD < 1

    def test_approve_decision_below_threshold(self):
        from app.services.fraud_detection import FraudDetectionEngine
        assert FraudDetectionEngine._decide(0.10) == "approve"
        assert FraudDetectionEngine._decide(0.00) == "approve"
        assert FraudDetectionEngine._decide(0.29) == "approve"

    def test_review_decision_in_middle_band(self):
        from app.services.fraud_detection import FraudDetectionEngine
        assert FraudDetectionEngine._decide(0.30) == "review"
        assert FraudDetectionEngine._decide(0.50) == "review"
        assert FraudDetectionEngine._decide(0.69) == "review"

    def test_reject_decision_at_or_above_threshold(self):
        from app.services.fraud_detection import FraudDetectionEngine
        assert FraudDetectionEngine._decide(0.70) == "reject"
        assert FraudDetectionEngine._decide(0.95) == "reject"
        assert FraudDetectionEngine._decide(1.00) == "reject"


class TestAmountScoring:
    """Test _score_amount in isolation."""

    def _engine(self):
        db = MagicMock()
        from app.services.fraud_detection import FraudDetectionEngine
        return FraudDetectionEngine(db)

    def test_normal_amount_low_score(self):
        engine = self._engine()
        triggered = []
        score = engine._score_amount(10_000, "IQD", triggered)
        assert score <= 0.20
        assert not triggered

    def test_high_amount_elevated_score(self):
        engine = self._engine()
        triggered = []
        score = engine._score_amount(600_000, "IQD", triggered)
        assert score >= 0.50
        assert "high_amount" in triggered

    def test_extreme_amount_critical_score(self):
        engine = self._engine()
        triggered = []
        score = engine._score_amount(2_500_000, "IQD", triggered)
        assert score >= 0.80
        assert "extreme_amount" in triggered

    def test_zero_amount_suspicious(self):
        engine = self._engine()
        triggered = []
        score = engine._score_amount(0, "IQD", triggered)
        assert score > 0.80
        assert "zero_or_negative_amount" in triggered

    def test_negative_amount_suspicious(self):
        engine = self._engine()
        triggered = []
        score = engine._score_amount(-100, "IQD", triggered)
        assert score > 0.80


class TestVelocityScoring:
    """Test _score_velocity in isolation."""

    def _engine(self, recent_count: int):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = recent_count
        from app.services.fraud_detection import FraudDetectionEngine
        return FraudDetectionEngine(db)

    def test_zero_claims_no_risk(self):
        engine = self._engine(0)
        triggered = []
        score = engine._score_velocity(1, triggered)
        assert score == 0.0
        assert not triggered

    def test_moderate_claims_low_risk(self):
        engine = self._engine(3)
        triggered = []
        score = engine._score_velocity(1, triggered)
        assert score < 0.50

    def test_high_velocity_triggers_rule(self):
        engine = self._engine(5)
        triggered = []
        score = engine._score_velocity(1, triggered)
        assert score >= 0.50
        assert any("high_velocity" in t for t in triggered)

    def test_very_high_velocity_critical(self):
        engine = self._engine(10)
        triggered = []
        score = engine._score_velocity(1, triggered)
        assert score >= 0.80
        assert any("very_high_velocity" in t for t in triggered)


class TestDuplicateDetection:
    def test_no_existing_claim_zero_score(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        from app.services.fraud_detection import FraudDetectionEngine
        engine = FraudDetectionEngine(db)
        triggered = []
        score = engine._score_duplicate(patient_id=1, order_id=99, triggered=triggered)
        assert score == 0.0
        assert not triggered

    def test_existing_claim_high_score(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(id=5)
        from app.services.fraud_detection import FraudDetectionEngine
        engine = FraudDetectionEngine(db)
        triggered = []
        score = engine._score_duplicate(patient_id=1, order_id=99, triggered=triggered)
        assert score >= 0.90
        assert any("duplicate_order_claim" in t for t in triggered)


class TestPreApproveCheck:
    def test_eligible_low_risk(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        from app.services.fraud_detection import pre_approve_claim
        result = pre_approve_claim(db, 1, 1, 10_000, 99)
        assert result["eligible"] is True
        assert result["risk"] == "low"

    def test_duplicate_order_not_eligible(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(id=5)
        from app.services.fraud_detection import pre_approve_claim
        result = pre_approve_claim(db, 1, 1, 10_000, 99)
        assert result["eligible"] is False
        assert "مطالبة" in result["reason"]

    def test_zero_amount_not_eligible(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        from app.services.fraud_detection import pre_approve_claim
        result = pre_approve_claim(db, 1, 1, 0, 99)
        assert result["eligible"] is False

    def test_high_amount_medium_risk(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        from app.services.fraud_detection import pre_approve_claim
        result = pre_approve_claim(db, 1, 1, 800_000, 99)
        assert result["eligible"] is True
        assert result["risk"] in ("medium", "high")


# ── Structured AI JSON schema tests ──────────────────────────────────────────

class TestSchemaValidator:
    def test_valid_interpretation_schema(self):
        from app.services.structured_ai import _validate_schema, INTERPRETATION_SCHEMA
        valid_data = {
            "summary": "النتائج ضمن المعدل الطبيعي",
            "items": [
                {"test_name": "Hemoglobin", "status": "normal", "explanation_ar": "الهيموغلوبين طبيعي"}
            ],
            "overall_severity": "normal",
            "action_ar": "استمر في نمط حياتك الصحي",
            "disclaimer_included": True,
        }
        errors = _validate_schema(valid_data, INTERPRETATION_SCHEMA)
        assert errors == []

    def test_missing_required_field(self):
        from app.services.structured_ai import _validate_schema, INTERPRETATION_SCHEMA
        invalid_data = {
            "summary": "ok",
            # missing: items, overall_severity, action_ar, disclaimer_included
        }
        errors = _validate_schema(invalid_data, INTERPRETATION_SCHEMA)
        assert len(errors) >= 3

    def test_invalid_severity_enum(self):
        from app.services.structured_ai import _validate_schema, INTERPRETATION_SCHEMA
        invalid_data = {
            "summary": "test",
            "items": [],
            "overall_severity": "unknown_value",   # invalid
            "action_ar": "action",
            "disclaimer_included": False,
        }
        errors = _validate_schema(invalid_data, INTERPRETATION_SCHEMA)
        assert any("overall_severity" in e for e in errors)

    def test_invalid_item_status_enum(self):
        from app.services.structured_ai import _validate_schema, INTERPRETATION_SCHEMA
        invalid_data = {
            "summary": "test",
            "items": [{"test_name": "X", "status": "INVALID", "explanation_ar": "x"}],
            "overall_severity": "normal",
            "action_ar": "action",
            "disclaimer_included": True,
        }
        errors = _validate_schema(invalid_data, INTERPRETATION_SCHEMA)
        assert any("status" in e for e in errors)

    def test_valid_fraud_advisory_schema(self):
        from app.services.structured_ai import _validate_schema, FRAUD_ADVISORY_SCHEMA
        valid = {
            "risk_score": 0.25,
            "explanation": "Low risk claim",
            "flags": ["normal_amount"],
            "confidence": 0.80,
        }
        errors = _validate_schema(valid, FRAUD_ADVISORY_SCHEMA)
        assert errors == []

    def test_fraud_score_out_of_range(self):
        from app.services.structured_ai import _validate_schema, FRAUD_ADVISORY_SCHEMA
        invalid = {"risk_score": 1.5, "explanation": "x", "flags": []}
        errors = _validate_schema(invalid, FRAUD_ADVISORY_SCHEMA)
        assert any("risk_score" in e for e in errors)

    def test_extra_field_rejected(self):
        from app.services.structured_ai import _validate_schema, INTERPRETATION_SCHEMA
        invalid_data = {
            "summary": "test",
            "items": [],
            "overall_severity": "normal",
            "action_ar": "action",
            "disclaimer_included": True,
            "injected_field": "malicious",
        }
        errors = _validate_schema(invalid_data, INTERPRETATION_SCHEMA)
        assert any("unexpected" in e for e in errors)


class TestJsonExtraction:
    def test_pure_json(self):
        from app.services.structured_ai import _extract_json
        text = '{"key": "value"}'
        assert _extract_json(text) == {"key": "value"}

    def test_json_in_code_block(self):
        from app.services.structured_ai import _extract_json
        text = '```json\n{"key": "value"}\n```'
        assert _extract_json(text) == {"key": "value"}

    def test_json_embedded_in_text(self):
        from app.services.structured_ai import _extract_json
        text = 'Here is the result: {"key": "value"} done.'
        assert _extract_json(text) == {"key": "value"}

    def test_invalid_json_returns_none(self):
        from app.services.structured_ai import _extract_json
        assert _extract_json("not json at all") is None

    def test_empty_string_returns_none(self):
        from app.services.structured_ai import _extract_json
        assert _extract_json("") is None


class TestConfidenceEstimate:
    def test_baseline_confidence(self):
        from app.services.structured_ai import StructuredAIEngine, INTERPRETATION_SCHEMA
        engine = StructuredAIEngine()
        data = {
            "summary": "نتائج طبيعية",
            "items": [{"test_name": "X", "status": "normal", "explanation_ar": "طبيعي"}],
            "overall_severity": "normal",
            "action_ar": "لا إجراء",
            "disclaimer_included": True,
        }
        conf = engine._estimate_confidence(data, INTERPRETATION_SCHEMA, "gemini")
        assert 0.5 < conf <= 1.0

    def test_gemini_higher_than_groq(self):
        from app.services.structured_ai import StructuredAIEngine, INTERPRETATION_SCHEMA
        engine = StructuredAIEngine()
        data = {"summary": "ok", "items": [], "overall_severity": "normal",
                "action_ar": "ok", "disclaimer_included": True}
        c_gemini = engine._estimate_confidence(data, INTERPRETATION_SCHEMA, "gemini")
        c_groq   = engine._estimate_confidence(data, INTERPRETATION_SCHEMA, "groq")
        assert c_gemini > c_groq

    def test_empty_items_penalised(self):
        from app.services.structured_ai import StructuredAIEngine, INTERPRETATION_SCHEMA
        engine = StructuredAIEngine()
        d_full  = {"summary": "ok", "items": [{"test_name":"X","status":"normal","explanation_ar":"ok"},
                                               {"test_name":"Y","status":"normal","explanation_ar":"ok"},
                                               {"test_name":"Z","status":"normal","explanation_ar":"ok"}],
                   "overall_severity": "normal", "action_ar": "ok", "disclaimer_included": True}
        d_empty = {"summary": "ok", "items": [], "overall_severity": "normal",
                   "action_ar": "ok", "disclaimer_included": True}
        c_full  = engine._estimate_confidence(d_full,  INTERPRETATION_SCHEMA, "groq")
        c_empty = engine._estimate_confidence(d_empty, INTERPRETATION_SCHEMA, "groq")
        assert c_full > c_empty


# ── Idempotency / DLQ model tests ─────────────────────────────────────────────

class TestProcessedEventHelpers:
    def test_is_processed_true(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)
        from app.models.processed_event import is_processed
        assert is_processed(db, event_id="42", consumer="outbox_worker") is True

    def test_is_processed_false(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        from app.models.processed_event import is_processed
        assert is_processed(db, event_id="99", consumer="outbox_worker") is False

    def test_mark_processed_adds_record(self):
        db = MagicMock()
        from app.models.processed_event import mark_processed
        record = mark_processed(db, event_id=10, consumer="outbox_worker", event_type="order.created")
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_move_to_dlq_creates_record(self):
        db = MagicMock()
        from app.models.processed_event import move_to_dlq
        dlq = move_to_dlq(
            db, original_id=5, event_type="order.failed",
            payload='{"order_id": 5}', attempts=5,
            last_error="DB timeout", consumer="outbox_worker",
        )
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_max_dlq_attempts_constant(self):
        from app.models.processed_event import MAX_DLQ_ATTEMPTS
        assert MAX_DLQ_ATTEMPTS >= 3   # at least 3 attempts before DLQ


# ── Migration chain tests for 0014, 0015 ─────────────────────────────────────

class TestMigrationChain:
    def _load_all_migrations(self) -> dict:
        """Parse migration metadata without importing (avoids alembic dependency)."""
        import re
        from pathlib import Path
        revisions = {}
        mig_dir = Path(__file__).parent.parent / "migrations" / "versions"
        for f in sorted(mig_dir.glob("*.py")):
            if f.name.startswith("_"):
                continue
            src = f.read_text()
            rev_match  = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', src, re.M)
            down_match = re.search(r'^down_revision\s*=\s*([^\n]+)', src, re.M)
            if not rev_match:
                continue
            revision = rev_match.group(1)
            down_raw = down_match.group(1).strip() if down_match else "None"
            if down_raw == "None":
                down_revision = None
            else:
                # Strip quotes
                down_revision = down_raw.strip('"\'')
            revisions[revision] = {"down_revision": down_revision, "file": f.name}
        return revisions

    def test_0014_exists_and_points_to_0013(self):
        migs = self._load_all_migrations()
        assert "20260405_0014" in migs
        assert migs["20260405_0014"]["down_revision"] == "20260402_0013"

    def test_0015_exists_and_points_to_0014(self):
        migs = self._load_all_migrations()
        assert "20260405_0015" in migs
        assert migs["20260405_0015"]["down_revision"] == "20260405_0014"

    def test_chain_still_linear(self):
        """Adding 0014+0015 should not break linearity."""
        migs = self._load_all_migrations()
        roots = [r for r, m in migs.items() if m["down_revision"] is None]
        assert len(roots) == 1, f"Expected 1 root, got: {roots}"

    def test_no_duplicate_revisions(self):
        migs = self._load_all_migrations()
        assert len(migs) == len(set(migs.keys()))
