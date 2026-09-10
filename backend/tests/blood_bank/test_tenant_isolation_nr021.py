"""NR-021: the blood bank must not serve one laboratory another's rows.

Every blood_bank_* table carries lab_id, and the service had no tenant context
at all: nine route-reachable methods queried without a lab filter, and two
mass-assigned a raw request dict onto models that carry lab_id, so a caller
could attribute a row to another laboratory.

These tests drive the service directly rather than the HTTP layer. The router
already enforces require_permission("system:admin"); the defect was that a
system:admin of one laboratory could read every laboratory. Exercising the
service is what actually pins the scoping.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from app.blood_bank.application.service import BloodBankService
from app.blood_bank.exceptions import BloodBankValidationError
from app.blood_bank.infrastructure.models import BloodDonorModel, BloodInventoryModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured"
)

LAB_A = 90021
LAB_B = 90022


@pytest.fixture()
def session() -> Any:
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL, future=True)
    with Session(engine) as s:
        for lab in (LAB_A, LAB_B):
            s.execute(
                text(
                    "INSERT INTO labs (id, name, is_active, created_at) "
                    "VALUES (:i, :n, true, now()) ON CONFLICT (id) DO NOTHING"
                ),
                {"i": lab, "n": f"NR-021 probe {lab}"},
            )
        s.flush()
        yield s
        # Some service methods commit, so a rollback alone would leave rows
        # behind. Remove the probe laboratories' rows explicitly, children
        # first, then roll back whatever is still open.
        s.rollback()
        for table in (
            "blood_bank_components", "blood_bank_donations",
            "blood_bank_donor_deferrals", "blood_bank_donors",
            "blood_bank_inventory",
        ):
            s.execute(
                text(f"DELETE FROM {table} WHERE lab_id IN (:a, :b)"),
                {"a": LAB_A, "b": LAB_B},
            )
        s.commit()


def _donor(session: Session, lab_id: int) -> BloodDonorModel:
    donor = BloodDonorModel(
        id=str(uuid.uuid4()), lab_id=lab_id, full_name=f"donor-{lab_id}",
        citizen_id=f"cit-{uuid.uuid4().hex[:10]}", blood_group="o", rh_factor="positive",
        status="active",
    )
    session.add(donor)
    session.flush()
    return donor


def _donation(session: Session, lab_id: int) -> str:
    """A real donation row: blood_bank_components has a foreign key to it.

    Built through the ORM rather than raw SQL so the model's defaults supply
    the NOT NULL columns instead of this fixture enumerating them.
    """
    from datetime import UTC, datetime

    from app.blood_bank.infrastructure.models import BloodDonationModel

    donor = _donor(session, lab_id)
    donation = BloodDonationModel(
        id=str(uuid.uuid4()), lab_id=lab_id, donor_id=donor.id,
        status="completed", collection_date=datetime.now(UTC),
    )
    session.add(donation)
    session.flush()
    return str(donation.id)


def _inventory(session: Session, lab_id: int) -> BloodInventoryModel:
    row = BloodInventoryModel(
        id=str(uuid.uuid4()), lab_id=lab_id, facility_id=f"fac-{lab_id}",
        blood_group="o", rh_factor="positive",
        component="whole_blood", quantity=7, reserved_quantity=0,
    )
    session.add(row)
    session.flush()
    return row


def test_lab_a_cannot_read_lab_b_inventory(session: Session) -> None:
    _inventory(session, LAB_A)
    _inventory(session, LAB_B)

    seen = BloodBankService(db=session, lab_id=LAB_A).get_inventory()
    assert seen, "lab A must still see its own inventory"
    assert all(r.id for r in seen)
    ids_b = {
        r.id for r in session.query(BloodInventoryModel).filter_by(lab_id=LAB_B).all()
    }
    assert not {r.id for r in seen} & ids_b, "lab A received lab B's inventory"


def test_lab_b_cannot_read_lab_a_inventory(session: Session) -> None:
    """Asserted in both directions: a filter keyed on the wrong side passes one."""
    _inventory(session, LAB_A)
    _inventory(session, LAB_B)

    seen = BloodBankService(db=session, lab_id=LAB_B).get_inventory()
    ids_a = {
        r.id for r in session.query(BloodInventoryModel).filter_by(lab_id=LAB_A).all()
    }
    assert seen
    assert not {r.id for r in seen} & ids_a, "lab B received lab A's inventory"


def test_a_service_without_a_laboratory_refuses_rather_than_returning_everything(
    session: Session,
) -> None:
    """Fail closed. An absent tenant context previously meant 'no filter'."""
    _inventory(session, LAB_A)
    unscoped = BloodBankService(db=session, lab_id=None)
    for call in (
        unscoped.get_inventory,
        unscoped.get_critical_inventory,
        unscoped.get_dashboard,
        lambda: unscoped.find_donors(),
    ):
        with pytest.raises(BloodBankValidationError):
            call()


def test_a_client_cannot_attribute_a_row_to_another_laboratory(session: Session) -> None:
    """The mass-assignment half: lab_id in the payload must not win."""
    donation_id = _donation(session, LAB_A)
    session.commit()
    service = BloodBankService(db=session, lab_id=LAB_A)
    component = service.process_component(
        {
            "lab_id": LAB_B,  # hostile: caller claims another tenant
            "donation_id": donation_id,
            "component": "plasma",
            "bag_identifier": f"bag-{uuid.uuid4().hex[:8]}",
        }
    )
    stored = session.execute(
        text("SELECT lab_id FROM blood_bank_components WHERE id = :i"),
        {"i": component.id},
    ).scalar_one()
    assert stored == LAB_A, "the client's lab_id overrode the authenticated one"


def test_a_client_cannot_reassign_a_donor_to_another_laboratory(session: Session) -> None:
    service = BloodBankService(db=session, lab_id=LAB_A)
    donor = service.register_donor(
        {
            "lab_id": LAB_B,
            "citizen_id": f"cit-{uuid.uuid4().hex[:10]}",
            "full_name": "hostile payload",
            "blood_group": "a",
            "rh_factor": "positive",
        }
    )
    stored = session.execute(
        text("SELECT lab_id FROM blood_bank_donors WHERE id = :i"), {"i": donor.id}
    ).scalar_one()
    assert stored == LAB_A


def test_lookup_by_id_does_not_cross_laboratories(session: Session) -> None:
    """An id is guessable; scoping must not depend on the id being secret."""
    from app.blood_bank.exceptions import DonorNotFoundError

    donor_b = _donor(session, LAB_B)
    with pytest.raises(DonorNotFoundError):
        BloodBankService(db=session, lab_id=LAB_A).get_donor(donor_b.id)


def test_the_dashboard_counts_only_the_callers_laboratory(session: Session) -> None:
    """An unscoped dashboard reports the country's blood supply to one lab."""
    _donor(session, LAB_A)
    _donor(session, LAB_B)
    _donor(session, LAB_B)

    a = BloodBankService(db=session, lab_id=LAB_A).get_dashboard()
    b = BloodBankService(db=session, lab_id=LAB_B).get_dashboard()
    assert a["total_donors"] >= 1
    assert b["total_donors"] >= 2
    combined = session.query(BloodDonorModel).filter(
        BloodDonorModel.lab_id.in_([LAB_A, LAB_B])
    ).count()
    assert a["total_donors"] < combined, "lab A counted lab B's donors"


# --- BATCH-2.7: the one route-reachable method the original fix missed --------


def test_a_blood_request_cannot_be_filed_against_another_laboratory(session: Session) -> None:
    """NR-021 residue.

    create_blood_request was the last route-reachable method still mass-assigning
    the raw request body onto a TenantEntity. blood_bank_requests.lab_id is NOT
    NULL, so a caller who put lab_id in the payload had it written verbatim and
    filed a blood request against another laboratory. Every other create path
    already went through _owned().
    """
    from app.blood_bank.infrastructure.models import BloodRequestModel

    service = BloodBankService(db=session, lab_id=LAB_A)
    created = service.create_blood_request({
        "lab_id": LAB_B,                     # the attacker-supplied tenant
        "patient_id": "cross-tenant-probe",
        "blood_group": "O",
        "units_requested": 1,
    })

    stored = session.query(BloodRequestModel).filter(
        BloodRequestModel.id == created.id
    ).one()
    assert stored.lab_id == LAB_A, (
        "a client-supplied lab_id was written to a tenant-scoped table; the "
        "server context must decide ownership"
    )


def test_a_blood_request_still_refuses_a_missing_tenant_context(session: Session) -> None:
    """Fail closed: no laboratory context means no write, not an unscoped one."""
    from app.blood_bank.exceptions import BloodBankValidationError

    with pytest.raises(BloodBankValidationError):
        BloodBankService(db=session, lab_id=None).create_blood_request({
            "patient_id": "no-tenant-probe", "blood_group": "O", "units_requested": 1,
        })
