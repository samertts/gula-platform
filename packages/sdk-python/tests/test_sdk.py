"""GULA SDK — unit tests.

Run with:
    cd packages/sdk-python && python -m pytest tests/ -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from gula_sdk import (
    GulaClient,
    GulaAuthError,
    GulaConflictError,
    GulaNotFoundError,
    GulaValidationError,
    IncompatibleTransfusionError,
    Patient,
    LabOrder,
    LabResult,
    Claim,
)
from gula_sdk.models import BloodDonor, InventorySummary


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return GulaClient(
        base_url="https://test.gula.iq",
        api_key="sk-gula-test-key",
        lab_id=1,
        verify_ssl=False,
    )


def _mock_response(data: dict, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.text = json.dumps(data)
    resp.headers = {}
    return resp


# ── Patient tests ─────────────────────────────────────────────────────────────

class TestPatientModels:
    def test_patient_from_dict_basic(self):
        p = Patient.from_dict({
            "id": 1, "full_name": "أحمد محمد", "phone": "07801234567",
            "blood_type": "A+", "gender": "M", "lab_id": 1,
        })
        assert p.id == 1
        assert p.full_name == "أحمد محمد"
        assert p.blood_type == "A+"

    def test_patient_from_dict_optional_fields(self):
        p = Patient.from_dict({
            "id": 2, "full_name": "Test", "phone": "07901234567",
            "blood_type": None, "gender": "F", "lab_id": 2,
            "national_id": "1234567890123",
        })
        assert p.national_id == "1234567890123"
        assert p.blood_type is None

    def test_patient_extra_fields_preserved(self):
        p = Patient.from_dict({
            "id": 3, "full_name": "X", "phone": "0780000",
            "blood_type": "O-", "gender": "M", "lab_id": 1,
            "some_future_field": "value",
        })
        assert p.extra.get("some_future_field") == "value"


class TestCreatePatient:
    def test_create_patient_success(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 42, "full_name": "علي أحمد", "phone": "07801234567",
            "blood_type": "B+", "gender": "M", "lab_id": 1,
        })) as mock_req:
            patient = client.create_patient("علي أحمد", "07801234567", "M")
            assert patient.id == 42
            assert patient.full_name == "علي أحمد"
            body = mock_req.call_args.kwargs["json"]
            assert body["full_name"] == "علي أحمد"
            assert body["lab_id"] == 1  # default from client

    def test_create_patient_conflict(self, client):
        with patch.object(client._http, "request", return_value=_mock_response(
            {"detail": "phone already exists"}, 409
        )):
            with pytest.raises(GulaConflictError):
                client.create_patient("Duplicate", "07801234567", "M")

    def test_create_patient_auth_error(self, client):
        with patch.object(client._http, "request", return_value=_mock_response(
            {"detail": "Not authenticated"}, 401
        )):
            with pytest.raises(GulaAuthError):
                client.create_patient("X", "07801234567", "M")

    def test_create_patient_validation_error(self, client):
        with patch.object(client._http, "request", return_value=_mock_response(
            {"detail": [{"loc": ["body", "phone"], "msg": "invalid format"}]}, 422
        )):
            with pytest.raises(GulaValidationError) as exc_info:
                client.create_patient("X", "invalid-phone", "M")
            assert exc_info.value.status_code == 422


# ── Order tests ───────────────────────────────────────────────────────────────

class TestLabOrder:
    def test_order_from_dict(self):
        o = LabOrder.from_dict({
            "id": 10, "patient_id": 42, "lab_id": 1,
            "status": "pending", "barcode": "GUL-0000010",
            "priority": "urgent",
        })
        assert o.barcode == "GUL-0000010"
        assert o.priority == "urgent"

    def test_create_order_success(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 10, "patient_id": 42, "lab_id": 1,
            "status": "pending", "barcode": "GUL-0000010", "priority": "routine",
            "ordered_tests": [{"test_type_id": 1}, {"test_type_id": 3}],
        })):
            order = client.create_order(patient_id=42, test_type_ids=[1, 3])
            assert order.id == 10
            assert len(order.ordered_tests) == 2

    def test_create_order_patient_not_found(self, client):
        with patch.object(client._http, "request", return_value=_mock_response(
            {"detail": "Patient not found"}, 404
        )):
            with pytest.raises(GulaNotFoundError):
                client.create_order(patient_id=9999, test_type_ids=[1])


# ── Result tests ──────────────────────────────────────────────────────────────

class TestLabResult:
    def test_result_from_dict(self):
        r = LabResult.from_dict({
            "id": 5, "order_id": 10, "test_type_id": 1,
            "value": "4.5", "unit": "x10³/μL",
            "status": "completed", "interpretation": "normal",
        })
        assert r.value == "4.5"
        assert r.interpretation == "normal"

    def test_submit_result_success(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 5, "order_id": 10, "test_type_id": 1,
            "value": "12.5", "unit": "g/dL",
            "status": "completed", "interpretation": "normal",
            "ai_interpretation": "Haemoglobin within normal range",
        })):
            result = client.submit_result(
                order_id=10, test_type_id=1, value="12.5", unit="g/dL"
            )
            assert result.id == 5
            assert result.ai_interpretation is not None

    def test_submit_result_duplicate_conflict(self, client):
        with patch.object(client._http, "request", return_value=_mock_response(
            {"detail": "result already exists"}, 409
        )):
            with pytest.raises(GulaConflictError):
                client.submit_result(order_id=10, test_type_id=1, value="4.5")


# ── Claim tests ───────────────────────────────────────────────────────────────

class TestClaim:
    def test_claim_from_dict(self):
        c = Claim.from_dict({
            "id": 100, "patient_id": 42, "order_id": 10,
            "amount": 25000.0, "currency": "IQD",
            "status": "pending_review",
            "fraud_score": 0.12, "fraud_decision": "approve",
        })
        assert c.amount == 25000.0
        assert c.fraud_decision == "approve"
        assert c.fraud_score == 0.12

    def test_submit_claim_success(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 100, "patient_id": 42, "order_id": 10,
            "amount": 25000.0, "currency": "IQD",
            "status": "approved",
            "fraud_score": 0.05, "fraud_decision": "approve",
        })):
            claim = client.submit_claim(
                patient_id=42, order_id=10, amount=25000,
                insurance_id="INS-001234",
            )
            assert claim.fraud_decision == "approve"

    def test_submit_claim_with_diagnosis_codes(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 101, "patient_id": 42, "order_id": 10,
            "amount": 50000.0, "currency": "IQD",
            "status": "pending_review",
            "fraud_score": 0.65, "fraud_decision": "review",
        })) as mock_req:
            claim = client.submit_claim(
                patient_id=42, order_id=10, amount=50000,
                diagnosis_codes=["E11.9", "I10"],
            )
            assert claim.fraud_decision == "review"
            body = mock_req.call_args.kwargs["json"]
            assert body["diagnosis_codes"] == ["E11.9", "I10"]


# ── Blood network tests ───────────────────────────────────────────────────────

class TestBloodNetwork:
    def test_donor_from_dict(self):
        d = BloodDonor.from_dict({
            "id": 7, "full_name": "محمد", "blood_type": "O-",
            "gender": "M", "eligible": True, "eligibility_reason": "مؤهل",
        })
        assert d.blood_type == "O-"
        assert d.eligible is True

    def test_get_inventory(self, client):
        with patch.object(client._http, "request", side_effect=[
            _mock_response({"A+/RBC": {"available": 10, "blood_type": "A+", "component": "RBC"}}),
            _mock_response([]),
        ]):
            inv = client.get_inventory()
            assert len(inv.items) == 1


# ── Idempotency key tests ─────────────────────────────────────────────────────

class TestIdempotencyKeys:
    def test_same_inputs_same_key(self):
        k1 = GulaClient._make_idempotency_key("patient", "07801234567", "Ahmed")
        k2 = GulaClient._make_idempotency_key("patient", "07801234567", "Ahmed")
        assert k1 == k2

    def test_different_inputs_different_key(self):
        k1 = GulaClient._make_idempotency_key("patient", "07801234567", "Ahmed")
        k2 = GulaClient._make_idempotency_key("patient", "07801234568", "Ahmed")
        assert k1 != k2

    def test_idempotency_key_sent_in_header(self, client):
        with patch.object(client._http, "request", return_value=_mock_response({
            "id": 1, "full_name": "Test", "phone": "07801234567",
            "blood_type": None, "gender": "M", "lab_id": 1,
        })) as mock_req:
            client.create_patient("Test", "07801234567", "M",
                                   idempotency_key="my-custom-key")
            headers = mock_req.call_args.kwargs.get("headers", {})
            assert headers.get("Idempotency-Key") == "my-custom-key"


# ── Retry and resilience tests ────────────────────────────────────────────────

class TestRetry:
    def test_retries_on_500(self, client):
        """Should retry on 500 and succeed on second attempt."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response({"detail": "Internal Server Error"}, 500)
            return _mock_response({
                "id": 1, "full_name": "Test", "phone": "07801234567",
                "blood_type": None, "gender": "M", "lab_id": 1,
            }, 200)

        with patch.object(client._http, "request", side_effect=side_effect):
            with patch("gula_sdk.client.time.sleep"):  # skip actual sleep
                p = client.create_patient("Test", "07801234567", "M")
                assert p.id == 1
                assert call_count == 2

    def test_incompatible_transfusion_not_retried(self, client):
        """IncompatibleTransfusionError must propagate immediately, never retry."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return _mock_response(
                {"detail": "⛔ INCOMPATIBLE TRANSFUSION: donor A+ → recipient O-"}, 422
            )

        with patch.object(client._http, "request", side_effect=side_effect):
            with pytest.raises(IncompatibleTransfusionError):
                client._request("POST", "/gbn/transfusions", json={})
            assert call_count == 1


# ── Context manager tests ─────────────────────────────────────────────────────

def test_client_context_manager():
    with GulaClient("https://test.gula.iq", "sk-test") as c:
        assert c is not None
    # After __exit__, should not error on close


def test_ping_true_on_ok(client):
    with patch.object(client, "health", return_value={"status": "ok"}):
        assert client.ping() is True


def test_ping_false_on_network_error(client):
    from gula_sdk.exceptions import GulaNetworkError
    with patch.object(client, "health", side_effect=GulaNetworkError("timeout")):
        assert client.ping() is False
