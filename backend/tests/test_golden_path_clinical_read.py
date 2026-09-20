"""NR-137 / NR-135 — the Golden Path, executed: log in, then read a patient.

WHAT THIS PROVES, AND WHY IT DID NOT EXIST
------------------------------------------
NR-135 made NIAM the canonical identity a legacy login produces. NR-137 gave the
resulting session the workspace its membership entitles it to, fail closed. Both
were recorded as implemented, and NR-137's own status said the remaining gap out
loud:

    "The end-to-end clinical read is NOT yet proven -- that needs a seeded
     organization, facility, membership and ClinicalLabFacilityBinding."

It had not been proven because the existing clinical-gateway tests build their
context from `SimpleNamespace` fakes -- `account = SimpleNamespace(id="account-1")`
and so on. That is the exact shape NR-064 was about: a workflow tested only
through a fake session, which cannot fail the way the real one does. Nothing had
ever asked a real login for a real token and handed it to the real gateway.

This does. A real `POST /login`, the token it actually mints, and a real
`GET /api/v1/clinical/patients` against PostgreSQL migrated to head.

WHAT IT TAKES TO PROVISION ONE CLINICAL USER
--------------------------------------------
**Twenty-one rows across five domains.** `ClinicalGatewayContextResolver`,
`ClinicalAuthorizationContextService` and `AuthorizationDecisionService` between
them require every link in this chain to be present, active and mutually
consistent before a single patient row is read:

    legacy         Lab -> LabUser (active, lab_id > 0)
    identity       Person -> IdentityRecord (active) -> Account (active)
                   -> LegacyAccountLink (lab_user, migrated)
    organization   NIAMOrganization (active) -> EnterprisePortal
                   -> NIAMAdminBranch -> NIAMAdminFacility (same organization)
    workspace      Workspace (active, organization_id + facility_id)
                   + Membership (active, covering)
                   + Employment -> Assignment (active, dated, carrying both
                     clinical resource ids)
    bridge         ClinicalLabFacilityBinding (active; legacy_lab_id,
                   niam_organization_id and niam_facility_id must all match)
    operational    Tenant -> Organization -> Facility (all active)
    grant          Role -> RolePermission -> RoleAssignment (scoped to the
                   organization; `patients.read` itself is already in the
                   catalog, seeded by the migration chain)

Two of those were discovered only by executing it, and only PostgreSQL knew:
`niam_admin_branches.portal_id` is NOT NULL with a foreign key to
`niam_admin_portals` that the ORM column does not declare, and
`niam_assignments.employment_id` requires a real `niam_employments` row. A
reader working from the ORM alone would have got the chain wrong.

**No script, fixture or document in this repository provisions that chain**, and
that -- not the binding code, which NR-137 already wrote -- is why the read had
never been executed end to end. `scripts/generate_demo_data.py` builds a
national demo ecosystem but does not construct this chain. So this module is
also the executable statement of what a real deployment must provision, which is
a thing the platform did not previously have written down anywhere.

NEGATIVE-PROVED
---------------
Setting the `RoleAssignment` to `revoked` -- one field, everything else intact --
turns `test_b` and `test_c` into 403s. Restored byte-identical afterwards.

WHAT IT DELIBERATELY DOES NOT CLAIM
-----------------------------------
It does not claim a login auto-provisions any of the above. It does not, by
design: `legacy_session_bridge` says so in its own docstring --

    "It does not create canonical accounts ... provisioning is left to the
     governed path and recorded as NR-137. This module binds what already
     exists."

So an unprovisioned `lab_user` logging in gets a legacy-only token and the
NIAM-protected surface refuses it with 401. `test_a_*` below pins exactly that,
because it is the documented fail-closed behaviour and a future change that
started auto-provisioning accounts at login would be walking through two review
gates. The Golden Path is what happens *after* the governed path has run, and
that is what the rest of this module proves.
"""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta

import pytest

SCHEMA_DATABASE_URL = (
    os.environ.get("GULA_SCHEMA_DATABASE_URL")
    or os.environ.get("MIGRATION_DATABASE_URL", "")
)
if not SCHEMA_DATABASE_URL:
    pytest.skip(
        "GULA_SCHEMA_DATABASE_URL/MIGRATION_DATABASE_URL is not configured; the "
        "Golden Path is only meaningful against a database migrated to head",
        allow_module_level=True,
    )

pytestmark = pytest.mark.integration

PASSWORD = "GoldenPath!Probe1"


@pytest.fixture(scope="module")
def engine():
    from sqlalchemy import create_engine

    eng = create_engine(SCHEMA_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture(scope="module")
def app_client(engine):
    """The real application, driven over HTTP, reading the migrated PostgreSQL.

    Two things here are not incidental.

    **The lifespan must run.** `ReadinessMiddleware` answers 503 on every
    non-whitelisted path until the startup guard sets `system_ready`, so
    entering the `TestClient` context manager is what makes this module test a
    clinical read rather than a 503.

    **`DATABASE_URL` cannot be set from here.** `backend/tests/conftest.py` pins
    it to in-memory SQLite for the whole suite, and `app.database` builds its
    engine at import time, long before a module fixture runs -- so an
    `os.environ` write here changes nothing and the app would answer
    `no such table: lab_users`. The other PostgreSQL guards in this suite avoid
    the problem by never touching the app; this one has to, because the token
    and the gateway are the subject. So `get_db` is overridden to hand every
    route a session on *this* module's engine, which is the same seam
    `conftest` itself uses, pointed at a different database.
    """
    os.environ["GULA_CLINICAL_GATEWAY_MODE"] = "ON"  # read per-request, not at import
    from app.database import get_db
    from app.factory import create_app
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session, configure_mappers

    application = create_app()
    configure_mappers()

    def _override_get_db():
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client
    finally:
        application.dependency_overrides.clear()


def _new_lab_user(db, *, suffix: str):
    """The legacy half: a laboratory and an active user who can authenticate."""
    from app.models.lab import Lab
    from app.models.lab_user import LabUser
    from app.security.auth import hash_password

    lab = Lab(name=f"Golden Path Lab {suffix}", is_active=True)
    for attr, value in (
        ("email", f"lab_{suffix}@goldenpath.test"),
        ("phone", "07700000000"),
        ("address", "Baghdad"),
        ("city", "Baghdad"),
        ("license_number", f"GP-{suffix}"),
    ):
        if hasattr(lab, attr):
            setattr(lab, attr, value)
    db.add(lab)
    db.flush()

    user = LabUser(
        lab_id=lab.id,
        email=f"goldenpath_{suffix}@goldenpath.test",
        name="Golden Path User",
        password_hash=hash_password(PASSWORD),
        role="lab_technician",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return lab, user


# ── the documented fail-closed precondition ─────────────────────────────────

def test_a_an_unprovisioned_login_is_refused_by_the_canonical_surface(app_client, engine):
    """A legacy user with no canonical account gets a legacy-only token.

    This is `legacy_session_bridge`'s stated contract, not a defect: it binds
    what already exists and never creates canonical accounts, because the
    direct account-creation route is fail-closed at 410 behind a review-gated
    intake. The login still succeeds -- authentication is not taken down by the
    absence of a link -- and the NIAM-protected surface refuses the token.

    Pinned because the failure mode of a future change here is silent
    auto-provisioning, which would walk straight through two review gates.
    """
    from sqlalchemy.orm import Session

    suffix = uuid.uuid4().hex[:8]
    with Session(engine) as db:
        _, user = _new_lab_user(db, suffix=suffix)
        email = user.email
        db.commit()

    login = app_client.post("/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, f"legacy authentication broke: {login.text[:300]}"
    token = login.json()["access_token"]

    read = app_client.get(
        "/api/v1/clinical/patients", headers={"Authorization": f"Bearer {token}"},
    )
    assert read.status_code == 401, (
        "an unprovisioned account reached the clinical gateway; the bridge is "
        f"supposed to leave it legacy-only. Got {read.status_code}: {read.text[:300]}"
    )


# ── the governed provisioning, executed ─────────────────────────────────────

@pytest.fixture(scope="module")
def provisioned(engine):
    """The sixteen rows that stand between a credential and a patient row.

    Written out longhand rather than hidden behind a helper, because the point
    of this fixture is to *be* the answer to "what does a real deployment have
    to create?". Every field set below is one the resolver chain actually reads.
    """
    from app.identity.admin.models import EnterprisePortal
    from app.identity.models.account import Account, AccountStatus, AccountType
    from app.identity.models.administrative_structure import (
        NIAMAdminBranch,
        NIAMAdminFacility,
    )
    from app.identity.models.assignment import Assignment
    from app.identity.models.authorization import (
        CatalogStatus,
        Permission,
        Role,
        RoleAssignment,
        RoleAssignmentStatus,
        RolePermission,
    )
    from app.identity.models.employment import Employment
    from app.identity.models.identity import IdentityRecord, IdentityType
    from app.identity.models.legacy_account_link import (
        LegacyAccountLink,
        LegacyAccountLinkSource,
        LegacyAccountLinkStatus,
    )
    from app.identity.models.membership import Membership, MembershipStatus
    from app.identity.models.niam_organization import NIAMOrganization
    from app.identity.models.person import Person
    from app.identity.models.workspace import Workspace, WorkspaceStatus, WorkspaceType
    from app.models.clinical_scope import (
        ClinicalLabFacilityBinding,
        ClinicalLabFacilityBindingStatus,
    )
    from app.models.organization import Facility, Organization
    from app.models.patient import Patient
    from app.models.tenant import Tenant
    from sqlalchemy.orm import Session

    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(tz=None)

    with Session(engine) as db:
        # 1-2. legacy tenant and the user who authenticates
        lab, lab_user = _new_lab_user(db, suffix=suffix)

        # 3. a patient in that laboratory, so a successful read has something
        #    to return and an empty list cannot be mistaken for success
        patient = Patient(
            lab_id=lab.id,
            full_name=f"Golden Path Patient {suffix}",
            phone=f"0770{suffix[:7]}",
            gender="M",
        )
        db.add(patient)

        # 4-6. canonical identity: person -> identity -> account
        person = Person(
            uuid=str(uuid.uuid4()), given_name="Golden", family_name="Path", is_active=True,
        )
        db.add(person)
        db.flush()

        identity = IdentityRecord(
            uuid=str(uuid.uuid4()),
            person_id=person.id,
            identity_type=IdentityType.national_id.value
            if hasattr(IdentityType, "national_id") else "national_id",
            issued_at=now,
            status="active",
            is_active=True,
        )
        db.add(identity)
        db.flush()

        account = Account(
            uuid=str(uuid.uuid4()),
            identity_id=identity.id,
            account_type=AccountType.individual.value
            if hasattr(AccountType, "individual") else "individual",
            status=AccountStatus.active.value,
            email=lab_user.email,
            is_active=True,
            is_locked=False,
        )
        db.add(account)
        db.flush()

        # 7. the link the bridge reads, and the ONLY thing tying the legacy
        #    credential to the canonical account. Status must be `migrated`.
        db.add(LegacyAccountLink(
            source_kind=LegacyAccountLinkSource.lab_user.value,
            legacy_account_id=lab_user.id,
            canonical_account_id=account.id,
            source_fingerprint=f"gp-{suffix}",
            rollback_token=f"gp-rollback-{suffix}",
            status=LegacyAccountLinkStatus.migrated.value,
            mapping_version=1,
        ))

        # 8-10. canonical organization -> branch -> facility
        niam_org = NIAMOrganization(
            uuid=str(uuid.uuid4()),
            org_id=f"GP-ORG-{suffix}",
            name_en="Golden Path Organization",
            name_ar="منظمة المسار الذهبي",
            org_type="laboratory",
            status="active",
            is_active=True,
        )
        db.add(niam_org)
        db.flush()

        # A branch cannot exist without a portal: `niam_admin_branches.portal_id`
        # is NOT NULL and PostgreSQL enforces a foreign key to
        # `niam_admin_portals`, which the ORM's own column does not declare.
        # The chain is seventeen rows, not sixteen, and only the database says so.
        portal = EnterprisePortal(
            uuid=str(uuid.uuid4()),
            portal_id=f"GP-PORTAL-{suffix}",
            organization_id=niam_org.id,
            name="Golden Path Portal",
            portal_type="organization",
            status="active",
            is_active=True,
        )
        db.add(portal)
        db.flush()

        branch = NIAMAdminBranch(
            uuid=str(uuid.uuid4()),
            branch_id=f"GP-BR-{suffix}",
            portal_id=portal.id,
            organization_id=niam_org.id,
            name_en="Golden Path Branch",
            name_ar="فرع المسار الذهبي",
            status="active",
            is_active=True,
        )
        db.add(branch)
        db.flush()

        niam_facility = NIAMAdminFacility(
            uuid=str(uuid.uuid4()),
            facility_id=f"GP-FAC-{suffix}",
            branch_id=branch.id,
            organization_id=niam_org.id,
            name_en="Golden Path Facility",
            name_ar="منشأة المسار الذهبي",
            facility_type="laboratory",
            status="active",
            is_active=True,
        )
        db.add(niam_facility)
        db.flush()

        # 11-13. operational scope: tenant -> organization -> facility.
        #        The gateway resolves tenant_id through this chain, and refuses
        #        with cross_tenant_scope if any link is inactive.
        tenant = Tenant(
            tenant_id=f"GP-TEN-{suffix}",
            name_en="Golden Path Tenant",
            name_ar="مستأجر المسار الذهبي",
            is_active=True,
        )
        db.add(tenant)
        db.flush()

        # The attribute names differ from the column names here: the ORM maps
        # `organization_id` as `org_id` and `organization_type` as `org_type`.
        op_org = Organization(
            org_id=f"GP-OPORG-{suffix}",
            name_en="Golden Path Operational Org",
            name_ar="المنظمة التشغيلية",
            org_type="laboratory",
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(op_org)
        db.flush()

        op_facility = Facility(
            facility_id=f"GP-OPFAC-{suffix}",
            name_en="Golden Path Operational Facility",
            name_ar="المنشأة التشغيلية",
            facility_type="laboratory",
            organization_id=op_org.id,
            is_active=True,
        )
        db.add(op_facility)
        db.flush()

        # 14. the workspace the session will be bound to
        workspace = Workspace(
            uuid=str(uuid.uuid4()),
            workspace_key=f"gp-ws-{suffix}",
            workspace_type=WorkspaceType.facility.value
            if hasattr(WorkspaceType, "facility") else "facility",
            name="Golden Path Workspace",
            status=WorkspaceStatus.active.value,
            owner_account_id=account.id,
            organization_id=niam_org.id,
            facility_id=niam_facility.id,
        )
        db.add(workspace)
        db.flush()

        # 15. the membership that entitles the account to act in it. NR-137
        #     binds nothing without this, and grants nothing beyond it.
        membership = Membership(
            uuid=str(uuid.uuid4()),
            membership_key=f"gp-mb-{suffix}",
            account_id=account.id,
            identity_id=identity.id,
            organization_id=niam_org.id,
            facility_id=niam_facility.id,
            workspace_id=workspace.id,
            relationship_type="employee",
            scope_type="facility",
            source="administrative_provisioning",
            status=MembershipStatus.active.value,
            is_active=True,
        )
        db.add(membership)
        db.flush()

        # 19-21. the grant. The permission catalog is already seeded by the
        # migration chain -- `patients.read` and `orders.read` both exist and are
        # active -- which is why the gateway denied with PERMISSION_MISSING and
        # not PERMISSION_UNKNOWN. What is missing in a fresh deployment is the
        # role that carries the permission and the assignment that gives it to
        # this account, scoped to this organization.
        role = Role(
            uuid=str(uuid.uuid4()),
            role_key=f"gp-clinical-reader-{suffix}",
            name="Golden Path Clinical Reader",
            scope_type="facility",
            status=CatalogStatus.active.value,
        )
        db.add(role)
        db.flush()

        read_permission = db.query(Permission).filter(
            Permission.permission_key == "patients.read",
            Permission.status == CatalogStatus.active.value,
        ).one()
        db.add(RolePermission(
            role_id=role.id,
            permission_id=read_permission.id,
            status=CatalogStatus.active.value,
        ))

        db.add(RoleAssignment(
            uuid=str(uuid.uuid4()),
            assignment_key=f"gp-ra-{suffix}",
            account_id=account.id,
            membership_id=membership.id,
            role_id=role.id,
            organization_id=niam_org.id,
            facility_id=niam_facility.id,
            scope_type="facility",
            status=RoleAssignmentStatus.active.value,
        ))

        # 16. the reviewed bridge from the legacy lab to the canonical scope
        db.add(ClinicalLabFacilityBinding(
            legacy_lab_id=lab.id,
            facility_resource_id=op_facility.id,
            niam_organization_id=niam_org.id,
            niam_facility_id=niam_facility.id,
            status=ClinicalLabFacilityBindingStatus.active.value,
            mapping_version=1,
        ))

        # and the active assignment the authorization service proves against.
        # `niam_assignments.employment_id` is a foreign key to `niam_employments`,
        # so the chain is eighteen rows: an assignment cannot exist without the
        # employment it belongs to.
        employment = Employment(
            uuid=str(uuid.uuid4()),
            person_id=person.id,
            organization_id=niam_org.id,
            employment_type="full_time",
            position="Laboratory Technician",
            status="active",
            start_date=date.today() - timedelta(days=2),
        )
        db.add(employment)
        db.flush()

        db.add(Assignment(
            uuid=str(uuid.uuid4()),
            employment_id=employment.id,
            person_id=person.id,
            organization_id=niam_org.id,
            facility_id=niam_facility.id,
            clinical_organization_resource_id=op_org.id,
            clinical_facility_resource_id=op_facility.id,
            role_id="lab_technician",
            assignment_type="clinical",
            status="active",
            start_date=date.today() - timedelta(days=1),
            is_active=True,
        ))

        db.commit()

        return {
            "email": lab_user.email,
            "lab_id": lab.id,
            "lab_user_id": lab_user.id,
            "account_id": account.id,
            "workspace_id": workspace.id,
            "patient_name": patient.full_name,
        }


def test_b_a_provisioned_login_reaches_the_clinical_read(app_client, provisioned):
    """The Golden Path. Log in, then read a patient -- over HTTP, end to end.

    Every earlier proof of this path used `SimpleNamespace` for the account,
    the session, the workspace and the scope. This one uses none: the token is
    the one `/login` minted, the workspace context is the one NR-137's binding
    created from the seeded membership, and the rows come out of PostgreSQL.
    """
    login = app_client.post(
        "/login", json={"email": provisioned["email"], "password": PASSWORD},
    )
    assert login.status_code == 200, f"login failed: {login.text[:400]}"
    token = login.json()["access_token"]

    read = app_client.get(
        "/api/v1/clinical/patients", headers={"Authorization": f"Bearer {token}"},
    )
    assert read.status_code == 200, (
        "the Golden Path is still blocked. This is the whole finding, so the "
        f"body matters: {read.status_code} {read.text[:600]}"
    )

    # The positive control. A 200 carrying an empty list would satisfy the
    # assertion above while proving nothing -- the standing lesson that a probe
    # which returns nothing looks exactly like a passing check. The seeded
    # patient has to actually come back.
    body = read.json()
    # The gateway projects a minimal field set: `display_name`, never the
    # legacy `full_name`. Reading the wrong key would make an empty list and
    # a full one indistinguishable.
    names = [item.get("display_name") for item in body["items"]]
    assert provisioned["patient_name"] in names, (
        "the read succeeded but did not return the seeded patient, so the 200 "
        f"proves only that nothing raised: {read.text[:600]}"
    )


def test_c_the_gateway_read_is_still_scoped_to_the_bound_laboratory(app_client, provisioned, engine):
    """The negative control, and the one that matters clinically.

    A gateway that returned every patient in the database would also pass
    `test_b`. This seeds a second laboratory with its own patient, and requires
    that the first account's read does not see it -- the scope comes from the
    binding, not from the request.
    """
    from app.models.patient import Patient
    from sqlalchemy.orm import Session

    other = uuid.uuid4().hex[:8]
    with Session(engine) as db:
        other_lab, _ = _new_lab_user(db, suffix=other)
        db.add(Patient(
            lab_id=other_lab.id,
            full_name=f"Other Lab Patient {other}",
            phone=f"0771{other[:7]}",
            gender="F",
        ))
        db.commit()

    login = app_client.post(
        "/login", json={"email": provisioned["email"], "password": PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    read = app_client.get(
        "/api/v1/clinical/patients", headers={"Authorization": f"Bearer {token}"},
    )
    assert read.status_code == 200, read.text[:400]
    body = read.json()
    # The gateway projects a minimal field set: `display_name`, never the
    # legacy `full_name`. Reading the wrong key would make an empty list and
    # a full one indistinguishable.
    names = [item.get("display_name") for item in body["items"]]

    assert provisioned["patient_name"] in names, "the positive control stopped holding"
    assert not any(name and name.startswith("Other Lab Patient") for name in names), (
        f"the clinical gateway returned another laboratory's patient: {names}"
    )
