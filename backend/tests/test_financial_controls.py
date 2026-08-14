from __future__ import annotations

from tests.conftest import auth_headers


def test_financial_control_maker_checker_and_apply(
    client,
    make_lab,
    make_lab_user,
):
    lab = make_lab("Control Lab")
    requester = make_lab_user(lab.id, role="finance_operator")
    approver = make_lab_user(lab.id, role="finance_controller")
    applier = make_lab_user(lab.id, role="finance_controller")

    payload = {
        "institution_id": lab.id,
        "control_type": "provider_approval",
        "resource_type": "payment_provider",
        "resource_id": "provider-sandbox-1",
        "requested_action": "approve_for_advisory_routing",
        "reason": "Quarterly provider review completed",
    }
    headers = {**auth_headers(requester.id, lab.id, "finance_operator"), "Idempotency-Key": "control-e2e-001", "X-Request-ID": "req-e2e-001"}

    created = client.post("/payments/controls/requests", json=payload, headers=headers)
    assert created.status_code == 201
    control = created.json()
    assert control["status"] == "REQUESTED"
    assert control["external_operation"] is False
    assert control["requested_by"] == requester.id

    replay = client.post("/payments/controls/requests", json=payload, headers=headers)
    assert replay.status_code == 201
    assert replay.json()["id"] == control["id"]

    self_approval = client.post(
        f"/payments/controls/requests/{control['id']}/approve",
        headers=auth_headers(requester.id, lab.id, "finance_operator"),
    )
    assert self_approval.status_code == 403

    approved = client.post(
        f"/payments/controls/requests/{control['id']}/approve",
        headers=auth_headers(approver.id, lab.id, "finance_controller"),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["approved_by"] == approver.id

    same_approver_apply = client.post(
        f"/payments/controls/requests/{control['id']}/apply",
        headers=auth_headers(approver.id, lab.id, "finance_controller"),
    )
    assert same_approver_apply.status_code == 403

    applied = client.post(
        f"/payments/controls/requests/{control['id']}/apply",
        headers=auth_headers(applier.id, lab.id, "finance_controller"),
    )
    assert applied.status_code == 200
    assert applied.json()["status"] == "APPLIED"
    assert applied.json()["applied_by"] == applier.id
    assert applied.json()["external_operation"] is False


def test_financial_control_requires_tenant_isolation_and_specialized_roles(
    client,
    make_lab,
    make_lab_user,
):
    lab_a = make_lab("Tenant A")
    lab_b = make_lab("Tenant B")
    operator_a = make_lab_user(lab_a.id, role="finance_operator")
    auditor_b = make_lab_user(lab_b.id, role="finance_auditor")
    operator_headers = auth_headers(operator_a.id, lab_a.id, "finance_operator")

    denied_operator = client.post(
        "/payments/controls/requests",
        json={
            "institution_id": lab_b.id,
            "control_type": "rail_activation",
            "resource_type": "payment_rail",
            "resource_id": "rail-other-1",
            "requested_action": "enable_advisory_route",
            "reason": "Cross-tenant request must be denied",
        },
        headers={**operator_headers, "Idempotency-Key": "cross-tenant-001"},
    )
    assert denied_operator.status_code == 403

    missing_permission = client.post(
        "/payments/controls/requests",
        json={
            "institution_id": lab_b.id,
            "control_type": "rail_activation",
            "resource_type": "payment_rail",
            "resource_id": "rail-other-2",
            "requested_action": "enable_advisory_route",
            "reason": "Auditor cannot request changes",
        },
        headers={**auth_headers(auditor_b.id, lab_b.id, "finance_auditor"), "Idempotency-Key": "auditor-request-001"},
    )
    assert missing_permission.status_code == 403


def test_financial_control_summary_is_tenant_scoped_and_currency_precise(
    client,
    db,
    make_lab,
    make_lab_user,
):
    from decimal import Decimal

    from app.payments.models import PaymentInvoice

    lab = make_lab("Metrics Lab")
    auditor = make_lab_user(lab.id, role="finance_auditor")
    db.add(
        PaymentInvoice(
            institution_id=lab.id,
            invoice_number="GULA-METRIC-001",
            status="PARTIALLY_PAID",
            currency="IQD",
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("40.00"),
            refunded_amount=Decimal("5.00"),
        )
    )
    db.flush()

    response = client.get(
        f"/payments/controls/summary?institution_id={lab.id}",
        headers=auth_headers(auditor.id, lab.id, "finance_auditor"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "IQD"
    assert body["billed_amount"] == "100.00"
    assert body["collected_amount"] == "40.00"
    assert body["outstanding_amount"] == "60.00"
    assert body["refunded_amount"] == "5.00"
    assert body["external_provider_calls"] == 0
    assert body["live_operation_enabled"] is False
    assert "No forecast" in body["limitations"][0]
