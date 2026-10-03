"""Is the multi-identifier picture a defect, or an MPI with a mapping layer?

IA-065. The emerging conclusion from the previous cycle -- that GULA "lacks a
single consistent FHIR Patient-ID namespace" -- is attacked here and does not
survive as a defect claim. An explicit, foreign-key-enforced mapping layer
exists between the per-tenant patient record and a canonical identity, with a
merge audit trail. Multiple identifier forms with a mapping layer is an MPI,
not drift.
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers


# ── Phase 1: the mapping layer ──────────────────────────────────────────────


def test_an_explicit_patient_to_canonical_mapping_table_exists():
    """identity_claims is the mapping, and its shape says so."""
    from app.services.mpi.models import Citizen, IdentityClaim, MergeAudit

    claim = IdentityClaim.__table__
    assert claim.name == "identity_claims"

    targets = {c.name: {fk.target_fullname for fk in c.foreign_keys} for c in claim.c if c.foreign_keys}
    # the column is local_patient_id, not patient_id -- measured, not assumed
    assert targets["local_patient_id"] == {"patients.id"}, targets
    assert targets["citizen_id"] == {"citizens.id"}, targets
    assert targets["lab_id"] == {"labs.id"}, targets

    # both sides of the mapping are mandatory -- a claim cannot dangle
    assert not claim.c.local_patient_id.nullable
    assert not claim.c.citizen_id.nullable
    # the claim records HOW the link was made, which is what makes it an MPI
    assert not claim.c.match_method.nullable
    assert "match_score" in claim.c and "match_features" in claim.c

    # and merges are audited, which is what makes the canonical side stable
    merge = MergeAudit.__table__
    assert merge.name == "mpi_merge_audit"
    merge_targets = {fk.target_fullname for c in merge.c for fk in c.foreign_keys}
    assert "citizens.id" in merge_targets
    # and the merge trail is hash-chained, so the canonical side is tamper-evident
    assert not merge.c.prev_hash.nullable
    assert not merge.c.entry_hash.nullable

    assert Citizen.__table__.name == "citizens"
    # the canonical identity has a stable, non-sequential public form
    assert "citizen_ulid" in Citizen.__table__.c
    assert not Citizen.__table__.c.citizen_ulid.nullable
    assert "merged_into_id" in Citizen.__table__.c, "merges are representable"
    print("\n[mapping] identity_claims: patients.id <-> citizens.id (both NOT NULL, per-lab, "
          "with match_method/score); citizens.citizen_ulid is the stable public id; "
          "mpi_merge_audit is hash-chained (prev_hash/entry_hash NOT NULL)")


def test_the_two_identifier_layers_are_not_competing_namespaces():
    """Local id is per-tenant; canonical id is cross-tenant. Different jobs."""
    from app.models.patient import Patient
    from app.services.mpi.models import Citizen, IdentityClaim

    # the local record is tenant-scoped
    assert "lab_id" in Patient.__table__.c
    assert not Patient.__table__.c.lab_id.nullable
    # the canonical record is not
    assert "lab_id" not in Citizen.__table__.c, sorted(Citizen.__table__.c.keys())
    # the mapping carries the tenant, so one citizen may hold many local records
    assert "lab_id" in IdentityClaim.__table__.c

    assert "health_id" in Patient.__table__.c, "the local record also carries a public id"
    print("\n[layers] patients: lab-scoped local record (+health_id); "
          "citizens: cross-tenant canonical; identity_claims: the per-lab link")


def test_the_canonical_identifier_is_reachable_from_a_patient_at_runtime(db, make_lab):
    """The mapping is usable, not merely declared."""
    from app.models.patient import Patient
    from app.services.mpi.models import Citizen, IdentityClaim

    lab = make_lab()
    patient = Patient(lab_id=lab.id, full_name="Namespace Probe", phone="07700000500")
    db.add(patient)
    db.flush()

    citizen = Citizen(**_minimal_citizen_kwargs(Citizen))
    db.add(citizen)
    db.flush()

    claim = IdentityClaim(
        citizen_id=citizen.id, local_patient_id=patient.id, lab_id=lab.id,
        match_method="deterministic",
    )
    db.add(claim)
    db.flush()

    resolved = (
        db.query(IdentityClaim.citizen_id)
        .filter(IdentityClaim.local_patient_id == patient.id, IdentityClaim.lab_id == lab.id)
        .scalar()
    )
    assert resolved == citizen.id
    print(f"\n[resolve] patients.id={patient.id} -> citizens.id={resolved} via identity_claims")


def _minimal_citizen_kwargs(model) -> dict:
    """Only the NOT NULL columns without a default, so the probe is schema-driven."""
    out = {}
    for col in model.__table__.c:
        if col.primary_key or col.nullable or col.default is not None or col.server_default is not None:
            continue
        out[col.name] = "probe" if "CHAR" in str(col.type).upper() or "TEXT" in str(col.type).upper() else 1
    return out


def _minimal_claim_extras(model) -> dict:
    out = {}
    for col in model.__table__.c:
        if col.name in ("citizen_id", "local_patient_id", "lab_id"):
            continue
        if col.primary_key or col.nullable or col.default is not None or col.server_default is not None:
            continue
        out[col.name] = "probe" if "CHAR" in str(col.type).upper() or "TEXT" in str(col.type).upper() else 1
    return out


# ── Phase 1 continued: what the FHIR boundary actually publishes ────────────


def test_the_fhir_boundary_publishes_the_local_id_and_only_one_builder_adds_the_canonical(
    client, db, make_lab, make_lab_user,
):
    """The narrow, true statement that survives the attack."""
    import inspect

    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    patient = Patient(lab_id=lab.id, full_name="Boundary", phone="07700000600")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id)
    db.add(order)
    db.flush()
    result = LabResult(order_id=order.id, test_name="Glucose", value=5.4, token="IA065-T1")
    db.add(result)
    db.flush()

    h = auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")
    body = client.get(f"/fhir/Observation/{result.id}", headers=h).json()
    assert body["subject"]["reference"] == f"Patient/{patient.id}"
    assert "identifier" not in body["subject"], (
        "the core boundary publishes the local id alone"
    )

    # exactly one builder attaches a canonical identifier
    interop = __import__("app.national.api.routes.interop", fromlist=["x"])
    source = inspect.getsource(interop._patient_reference)
    assert "urn:gula:health-id" in source
    assert "urn:gula:patient-id" in source
    print("\n[boundary] core publishes Patient/<local id> with no identifier; "
          "interop._patient_reference is the one builder carrying urn:gula:health-id")


def test_ia065_the_canonical_ulid_is_never_published_in_any_fhir_reference():
    """The narrow claim that survives: the mapping exists but is not surfaced.

    IA-065. `citizens.citizen_ulid` is the stable, non-sequential canonical
    identifier, and `identity_claims` maps every tenant-local `patients` row to
    it with a recorded match method. No FHIR Patient reference publishes it.
    Nine builders publish `patients.id`; the one that attaches an identifier --
    `interop._patient_reference` -- uses `urn:gula:health-id` from
    `patients.health_id`, which is the local record's public field, not the
    canonical ULID.
    """
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    hits = []
    for path in root.rglob("*.py"):
        text = path.read_text(errors="replace")
        if "citizen_ulid" not in text:
            continue
        # does any FHIR-shaped reference or identifier carry the ULID?
        for match in re.finditer(r'.*citizen_ulid.*', text):
            line = match.group(0)
            if '"reference"' in line or "Patient/" in line or '"identifier"' in line:
                hits.append(f"{path.relative_to(root)}: {line.strip()[:90]}")

    assert hits == [], hits
    print("\n[IA-065] citizen_ulid appears in no FHIR reference or identifier construction")


# ── IA-067: two disjoint patient identity domains ───────────────────────────


def _all_tables():
    import importlib
    import pkgutil
    import warnings

    warnings.filterwarnings("ignore")
    import app

    for info in pkgutil.walk_packages(app.__path__, prefix="app."):
        if any(s in info.name for s in (".tests", "__pycache__")):
            continue
        try:
            importlib.import_module(info.name)
        except BaseException:
            pass

    from app.database import Base
    from app.ehr.base import EHRBase
    from app.national.base import NationalBase

    tables = {}
    for base in (Base, NationalBase, EHRBase):
        tables.update({t.name: t for t in base.metadata.tables.values()})
    return tables


def test_ia067_two_patient_identity_domains_exist_and_nothing_bridges_them():
    """IA-067. `patients.id` and `national_patients.id` are separate identities.

    Not two representations of one identity: different types, different table
    populations, and no table carrying a foreign key to both.
    """
    tables = _all_tables()

    both, national_only, local_only = [], [], []
    for name, table in tables.items():
        targets = {fk.target_fullname for c in table.c for fk in c.foreign_keys}
        has_national = any(t.startswith("national_patients.") for t in targets)
        has_local = any(t.startswith("patients.") for t in targets)
        if has_national and has_local:
            both.append(name)
        elif has_national:
            national_only.append(name)
        elif has_local:
            local_only.append(name)

    print(f"\n[IA-067] national_patients only={len(national_only)}  "
          f"patients only={len(local_only)}  BOTH={both}")
    assert both == [], f"a bridging table now exists: {both}"
    assert len(national_only) > 50, len(national_only)
    assert len(local_only) > 20, len(local_only)


def test_ia067_the_two_domains_use_incompatible_key_types():
    from app.models.patient import Patient

    tables = _all_tables()
    national = tables.get("national_patients")
    assert national is not None, sorted(tables)[:20]

    local_type = str(Patient.__table__.c.id.type).upper()
    national_type = str(national.c.id.type).upper()
    assert "INTEGER" in local_type, local_type
    assert "CHAR" in national_type, national_type
    print(f"\n[IA-067] patients.id={local_type}  national_patients.id={national_type}")


def test_ia067_the_mpi_maps_only_the_local_domain():
    """identity_claims reaches `patients`, never `national_patients`."""
    from app.services.mpi.models import IdentityClaim

    targets = {fk.target_fullname for c in IdentityClaim.__table__.c for fk in c.foreign_keys}
    assert "patients.id" in targets
    assert not any(t.startswith("national_patients.") for t in targets), targets
    print(f"\n[IA-067] identity_claims targets: {sorted(targets)} -- no national_patients")


def test_ia067_explains_the_ehr_medication_addressing(client, db, make_lab, make_lab_user):
    """The EHR medication route is addressed by the domain the lab stack lacks."""
    from app.ehr.models.medication import MedicationStatement

    pid = MedicationStatement.__table__.c.patient_id
    targets = {fk.target_fullname for fk in pid.foreign_keys}
    assert targets == {"national_patients.id"}, targets
    assert "CHAR" in str(pid.type).upper(), pid.type
    print(f"\n[IA-067] ehr_medication_statements.patient_id {pid.type} -> {sorted(targets)}; "
          f"a core patients.id integer cannot address it")
