from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.financial.canonical_models import FinancialPayment
from app.financial.models import FinPayment
from app.identity.models import Permission, RoleAssignment, RolePermission
from fastapi.testclient import TestClient


def _id(prefix: str) -> str:
    return (prefix + uuid4().hex.upper())[:26]


def _grant_finance_permissions(db, context):
    assignment = db.query(RoleAssignment).filter_by(account_id=context["account"].id, workspace_id=context["workspace"].id).one()
    keys = (
        "financial.payer.manage",
        "financial.coverage.write",
        "financial.eligibility.check",
        "financial.preauth.write",
        "financial.service.manage",
        "financial.bill.create",
        "financial.claim.write",
        "financial.claim.review",
        "financial.payment.write",
        "financial.payment.capture",
        "financial.refund.write",
    )
    for key in keys:
        permission = db.query(Permission).filter_by(permission_key=key).first()
        if permission is None:
            permission = Permission(id=_id("PERM"), uuid=str(uuid4()), permission_key=key, name=key, name_ar=key, resource="financial", action=key.rsplit(".", 1)[-1], sensitivity="high", status="active")
            db.add(permission)
            db.flush()
        if db.query(RolePermission).filter_by(role_id=assignment.role_id, permission_id=permission.id).first() is None:
            db.add(RolePermission(id=_id("RP"), role_id=assignment.role_id, permission_id=permission.id, status="active"))
    db.flush()


def test_finance_golden_path_is_minor_unit_safe_and_idempotent(client: TestClient, appointment_context, db):
    _grant_finance_permissions(db, appointment_context)
    workspace_id = appointment_context["workspace"].id
    patient_id = appointment_context["person"].id
    headers = {"Idempotency-Key": "fin-payer-1", "X-Request-ID": "fin-test-1"}

    payer = client.post("/api/v1/finance/payers", headers=headers, json={"workspace_id": workspace_id, "name": "Synthetic Government Payer", "payer_type": "GOVERNMENT"})
    assert payer.status_code == 201, payer.text
    payer_id = payer.json()["id"]
    assert client.post("/api/v1/finance/payers", headers=headers, json={"workspace_id": workspace_id, "name": "Synthetic Government Payer", "payer_type": "GOVERNMENT"}).json()["id"] == payer_id

    coverage = client.post("/api/v1/finance/coverages", headers={"Idempotency-Key": "fin-cov-1"}, json={"workspace_id": workspace_id, "member_id": patient_id, "payer_id": payer_id, "plan_code": "SYN-PLAN", "valid_from": "2025-01-01T00:00:00Z"})
    assert coverage.status_code == 201, coverage.text
    coverage_id = coverage.json()["id"]
    rejected_outcome = client.post("/api/v1/finance/eligibility/check", headers={"Idempotency-Key": "fin-elig-client-outcome"}, json={"workspace_id": workspace_id, "coverage_id": coverage_id, "synthetic_outcome": "ELIGIBLE"})
    assert rejected_outcome.status_code == 409 and rejected_outcome.json()["code"] == "FINANCIAL_PROVIDER_UNAVAILABLE"
    eligibility = client.post("/api/v1/finance/eligibility/check", headers={"Idempotency-Key": "fin-elig-1"}, json={"workspace_id": workspace_id, "coverage_id": coverage_id, "synthetic_outcome": "UNKNOWN"})
    assert eligibility.status_code == 201, eligibility.text
    assert eligibility.json()["status"] == "UNKNOWN"

    service = client.post("/api/v1/finance/services", headers={"Idempotency-Key": "fin-service-1"}, json={"workspace_id": workspace_id, "code": "SYN-CONSULT", "name": "Synthetic consultation", "currency": "IQD"})
    assert service.status_code == 201, service.text
    service_id = service.json()["id"]
    price = client.post("/api/v1/finance/prices", headers={"Idempotency-Key": "fin-price-1"}, json={"workspace_id": workspace_id, "service_id": service_id, "amount_minor": 1250, "currency": "IQD", "valid_from": "2025-01-01T00:00:00Z"})
    assert price.status_code == 201, price.text
    preauth = client.post("/api/v1/finance/preauthorizations", headers={"Idempotency-Key": "fin-preauth-1"}, json={"workspace_id": workspace_id, "member_id": patient_id, "payer_id": payer_id, "service_id": service_id, "clinical_indication": "Synthetic indication", "estimated_amount_minor": 1250, "currency": "IQD"})
    assert preauth.status_code == 201, preauth.text
    assert preauth.json()["status"] == "REQUESTED"

    bill = client.post("/api/v1/finance/bills", headers={"Idempotency-Key": "fin-bill-1"}, json={"workspace_id": workspace_id, "patient_person_id": patient_id, "currency": "IQD", "items": [{"service_id": service_id, "quantity": 1}], "coverage_id": coverage_id, "discount_minor": 50})
    assert bill.status_code == 201, bill.text
    bill_body = bill.json()
    assert bill_body["gross_minor"] == 1250
    assert bill_body["net_minor"] == 1200

    claim = client.post("/api/v1/finance/claims", headers={"Idempotency-Key": "fin-claim-1"}, json={"workspace_id": workspace_id, "bill_id": bill_body["id"], "payer_id": payer_id})
    assert claim.status_code == 201, claim.text
    claim_body = claim.json()
    submitted = client.post(f"/api/v1/finance/claims/{claim_body['id']}/transition", headers={"Idempotency-Key": "fin-claim-submit-1", "If-Match": "1"}, json={"workspace_id": workspace_id, "target_status": "SUBMITTED"})
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "SUBMITTED"

    payment = client.post("/api/v1/finance/payments", headers={"Idempotency-Key": "fin-pay-1"}, json={"workspace_id": workspace_id, "bill_id": bill_body["id"], "amount_minor": 1200, "currency": "IQD", "provider": "SYNTHETIC"})
    assert payment.status_code == 201, payment.text
    payment_body = payment.json()
    rejected_client_proof = client.post(f"/api/v1/finance/payments/{payment_body['id']}/capture", headers={"Idempotency-Key": "fin-capture-client-proof", "If-Match": "1"}, json={"workspace_id": workspace_id, "event_id": "synthetic-event-001", "nonce": "synthetic-nonce-001", "signature_valid": True})
    assert rejected_client_proof.status_code == 422
    captured = client.post(f"/api/v1/finance/payments/{payment_body['id']}/capture", headers={"Idempotency-Key": "fin-capture-1", "If-Match": "1"}, json={"workspace_id": workspace_id, "event_id": "synthetic-event-001", "nonce": "synthetic-nonce-001"})
    assert captured.status_code == 200, captured.text
    assert captured.json()["status"] == "CAPTURED"
    assert captured.json()["status"] != "PAID"

    sod_review = client.post(f"/api/v1/finance/claims/{claim_body['id']}/transition", headers={"Idempotency-Key": "fin-claim-self-review", "If-Match": "2"}, json={"workspace_id": workspace_id, "target_status": "UNDER_REVIEW"})
    assert sod_review.status_code == 403
    assert sod_review.json()["code"] == "CLAIM_SOD_REQUIRED"

    refund = client.post("/api/v1/finance/refunds", headers={"Idempotency-Key": "fin-refund-1", "If-Match": '"2"'}, json={"workspace_id": workspace_id, "payment_id": payment_body["id"], "amount_minor": 500, "currency": "IQD", "reason": "Synthetic correction"})
    assert refund.status_code == 201, refund.text
    assert refund.json()["status"] == "COMPLETED"
    over_refund = client.post("/api/v1/finance/refunds", headers={"Idempotency-Key": "fin-refund-over", "If-Match": '"3"'}, json={"workspace_id": workspace_id, "payment_id": payment_body["id"], "amount_minor": 800, "currency": "IQD", "reason": "Synthetic over-refund"})
    assert over_refund.status_code == 409
    assert over_refund.json()["code"] == "REFUND_EXCEEDS_PAYMENT"

    replay = client.post(f"/api/v1/finance/payments/{payment_body['id']}/capture", headers={"Idempotency-Key": "fin-capture-replay", "If-Match": "3"}, json={"workspace_id": workspace_id, "event_id": "synthetic-event-001", "nonce": "synthetic-nonce-001"})
    assert replay.status_code == 409
    assert replay.json()["code"] == "PAYMENT_REPLAY"


def test_finance_rejects_patient_idor_and_uses_nonlegacy_payment_table(client: TestClient, appointment_context, db):
    _grant_finance_permissions(db, appointment_context)
    workspace_id = appointment_context["workspace"].id
    payer = client.post("/api/v1/finance/payers", headers={"Idempotency-Key": "fin-idor-payer"}, json={"workspace_id": workspace_id, "name": "Synthetic IDOR Payer", "payer_type": "SELF_PAY"})
    assert payer.status_code == 201
    denied = client.post("/api/v1/finance/coverages", headers={"Idempotency-Key": "fin-idor-coverage"}, json={"workspace_id": workspace_id, "member_id": _id("OTHER"), "payer_id": payer.json()["id"], "plan_code": "SYN-PLAN", "valid_from": "2025-01-01T00:00:00Z"})
    assert denied.status_code == 403
    assert denied.json()["code"] == "PATIENT_CONTEXT_DENIED"
    assert FinancialPayment.__tablename__ != FinPayment.__tablename__
    assert FinancialPayment.__tablename__ == "core_financial_payments"


def test_finance_provider_unavailable_is_pending_not_paid(client: TestClient, appointment_context, db):
    _grant_finance_permissions(db, appointment_context)
    workspace_id = appointment_context["workspace"].id
    service = client.post("/api/v1/finance/services", headers={"Idempotency-Key": "fin-service-pending"}, json={"workspace_id": workspace_id, "code": "SYN-EMERGENCY", "name": "Synthetic emergency service", "currency": "IQD"})
    service_id = service.json()["id"]
    price = client.post("/api/v1/finance/prices", headers={"Idempotency-Key": "fin-price-pending"}, json={"workspace_id": workspace_id, "service_id": service_id, "amount_minor": 100, "currency": "IQD", "valid_from": (datetime.now(UTC) - timedelta(days=1)).isoformat()})
    assert price.status_code == 201, price.text
    bill = client.post("/api/v1/finance/bills", headers={"Idempotency-Key": "fin-bill-pending"}, json={"workspace_id": workspace_id, "patient_person_id": appointment_context["person"].id, "currency": "IQD", "items": [{"service_id": service_id, "quantity": 1}]})
    assert bill.status_code == 201, bill.text
    payment = client.post("/api/v1/finance/payments", headers={"Idempotency-Key": "fin-pay-pending"}, json={"workspace_id": workspace_id, "bill_id": bill.json()["id"], "amount_minor": 100, "currency": "IQD", "provider": "SYNTHETIC", "provider_available": False})
    assert payment.status_code == 201, payment.text
    assert payment.json()["status"] == "PENDING"
