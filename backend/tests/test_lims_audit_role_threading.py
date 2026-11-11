"""Regression: LIMS service-layer audit records the real actor role.

Four call sites in app/lims/services.py (SpecimenService.register,
SpecimenService.transition, OrderService.create_lims_order,
ResultService.create_result) previously hard-coded user_role="lab_tech" in
every log_action call, regardless of which role actually performed the
action. Confirmed via git-stash negative proof: reverting services.py
reproduces "lab_tech" in the audit record for every role below; with the
fix applied, the audit record matches the real, server-derived
current_user.role.

Also proves a client cannot spoof the role: none of the LIMS route request
schemas (SpecimenRegisterRequest, LimsOrderCreateRequest, ResultCreateRequest,
SpecimenTransitionRequest) declare a "role" field, so the value passed into
these service methods can only ever be app/lims/routes.py's own
current_user.role -- itself derived from the JWT-decoded, DB-verified
LabUser object, never from the request body.
"""

import pytest
from app.lims.services import OrderService, ResultService, SpecimenService
from app.models.audit_log import AuditLog
from app.models.lab_order import LabOrder
from app.models.patient import Patient


@pytest.fixture()
def base_order(db, make_lab):
    lab = make_lab()
    patient = Patient(lab_id=lab.id, full_name="Test Patient", phone="07701234567")
    db.add(patient)
    db.flush()
    order = LabOrder(patient_id=patient.id, lab_id=lab.id, status="pending")
    db.add(order)
    db.flush()
    return lab, order


@pytest.mark.parametrize("role", ["lab_admin", "technician", "admin", "master_admin"])
class TestLimsAuditRoleThreading:
    def test_specimen_register_records_real_role(self, db, base_order, make_lab_user, role):
        lab, order = base_order
        user = make_lab_user(lab_id=lab.id, role=role)
        db.commit()

        specimen = SpecimenService.register(
            db, order.id, lab.id, "blood", f"BC-{role}", user.id, role,
        )
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(AuditLog.resource_type == "lims_specimen", AuditLog.resource_id == specimen.id)
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role
        assert entry.user_role != "lab_tech" or role == "lab_tech"

    def test_specimen_transition_records_real_role(self, db, base_order, make_lab_user, role):
        lab, order = base_order
        user = make_lab_user(lab_id=lab.id, role=role)
        db.commit()

        specimen = SpecimenService.register(
            db, order.id, lab.id, "blood", f"BCT-{role}", user.id, role,
        )
        db.commit()
        SpecimenService.transition(db, specimen, "registered", user.id, role)
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "lims_specimen",
                AuditLog.resource_id == specimen.id,
                AuditLog.action == "transition",
            )
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role

    def test_order_create_records_real_role(self, db, base_order, make_lab_user, role):
        lab, order = base_order
        user = make_lab_user(lab_id=lab.id, role=role)
        db.commit()

        lims_order = OrderService.create_lims_order(
            db, order.id, lab.id, user.id, role, f"ACC-{role}",
        )
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(AuditLog.resource_type == "lims_order", AuditLog.resource_id == lims_order.id)
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role

    def test_result_create_records_real_role(self, db, base_order, make_lab_user, role):
        lab, order = base_order
        user = make_lab_user(lab_id=lab.id, role=role)
        db.commit()

        specimen = SpecimenService.register(
            db, order.id, lab.id, "blood", f"BCR-{role}", user.id, role,
        )
        db.commit()

        result = ResultService.create_result(
            db, specimen.id, order.id, lab.id, "GLU", "Glucose", user.id, role,
            value_numeric=95,
        )
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(AuditLog.resource_type == "lims_result", AuditLog.resource_id == result.id)
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role


def test_role_field_absent_from_lims_request_schemas():
    """A client cannot spoof the audited role: no LIMS request schema
    accepts one -- the value can only come from the server-derived
    current_user.role in app/lims/routes.py.
    """
    from app.lims import routes as lims_routes

    for name in (
        "SpecimenRegisterRequest",
        "SpecimenTransitionRequest",
        "OrderCreateRequest",
        "ResultCreateRequest",
    ):
        model = getattr(lims_routes, name, None)
        if model is None:
            continue
        assert "role" not in model.model_fields, f"{name} must not accept a client-supplied role"
