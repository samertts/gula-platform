"""The generic FHIR write surface: four P0-shaped hypotheses, four disproved.

IA-049 — DISCOVERED, REPRODUCED, four VERIFIED_NEGATIVE, one P3 recorded.

`ehr_fhir.py` serves `POST /fhir/{resource_type}`,
`PUT /fhir/{resource_type}/{resource_id}` and
`DELETE /fhir/{resource_type}/{resource_id}` — a generic write surface over nine
clinical EHR models, which no existing test covered. An AST sweep of all 29
handlers in the module found four with no tenant predicate in their own body:

    DELETE /{resource_type}/{resource_id}   fhir_delete_resource
    PUT    /{resource_type}/{resource_id}   fhir_update_resource
    GET    /Patient/{patient_id}/$everything  fhir_patient_everything
    GET    /metadata                          fhir_metadata

Each was attacked. All four are sound, and the reasons are pinned below so they
stay sound.

1. VERIFIED_NEGATIVE — the writes are NOT cross-tenant. Both handlers call
   `_get_fhir_resource_or_404(db, resource_type, resource_id, current_user)`,
   whose guard is two conditional branches:

       if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and ...
       if hasattr(record, "patient_id") and getattr(record, "patient_id", None):
           ehr_service.get_national_patient_or_404(db, record.patient_id, user.lab_id)

   A conditional guard is only as good as the condition. Measured: of the nine
   models reachable through these routes, **eight have no `lab_id` column at
   all**, so the first branch never fires — the entire surface rests on the
   second. And every one of the nine has `patient_id` **nullable=False**, so the
   second branch can never be skipped. `get_national_patient_or_404` filters
   `NationalPatient.lab_id == lab_id` and `is_deleted is False`, raising
   NotFoundError otherwise.

   The guarantee is therefore real but narrow, and it is pinned by column: a
   migration making any `patient_id` nullable would make the guard skippable on
   that model, and the test below fails before that ships.

2. VERIFIED_NEGATIVE — the delete is not a fake success. `fhir_delete_resource`
   sets `is_deleted`/`deleted_at`/`deleted_by` and returns
   `{"status": "deleted"}` with no `db.commit()` in the handler, and `get_db`
   does not commit either — it yields, rolls back on exception, and closes.
   That is the NR-064/NR-084 shape ("writes never commit", "reports 201 and
   discards every write"), so it was measured rather than reasoned about:

       DELETE status: 200 {"resourceType":"Condition","id":"COND-PROBE-1","status":"deleted"}
       commit calls during the request: 1
       is_deleted after the request: True

   The commit comes from `@audit_log(action="fhir.delete")`, which writes the
   audit row and commits — and its own docstring says the dependency rolls back
   an uncommitted clinical mutation if that fails. So the persistence of the
   clinical mutation is deliberate but *indirect*: it rides on the audit write.
   That is fragile, and the fragility is what the test pins — remove the
   decorator and the delete silently stops persisting.

3. VERIFIED_NEGATIVE — `$everything` is guarded. It delegates to
   `fhir_read_bundle`, which calls `get_national_patient_or_404` first. The AST
   sweep could not see that because it does not follow delegation; checking it
   is why this is a negative rather than a P0.

4. VERIFIED_NEGATIVE — `/metadata` returns a CapabilityStatement and no patient
   data, so it needs no tenant predicate.

P3 RECORDED, not fixed: `Observation`, `Patient` and `Procedure` are listed in
`_SUPPORTED_CREATE` and `_SUPPORTED_UPDATE`, but `_fhir_model_class` returns None
for all three, so every POST and PUT to them answers 422 — measured. The route
advertises support and then calls the type unknown. It stays a P3 because the
*external* claim is honest: the served CapabilityStatement advertises only
`read` and `search-type` for every resource and no write interaction at all, so
no partner is told these writes exist. Both outcomes are 422; only the message
differs. Changing the frozensets would also touch the batch path, which is not
worth it to improve an error string.
"""
from __future__ import annotations

import datetime

import pytest
from app.ehr.models import ConditionRecord
from app.national.domain.patient import Patient as NationalPatient
from app.routes.ehr_fhir import (
    _SUPPORTED_CREATE,
    _SUPPORTED_DELETE,
    _SUPPORTED_UPDATE,
    _fhir_model_class,
)

from tests.conftest import auth_headers

_GENERIC_TYPES = sorted(set(_SUPPORTED_CREATE) | set(_SUPPORTED_UPDATE) | set(_SUPPORTED_DELETE))


def _make_patient(db, lab_id: int, suffix: str) -> NationalPatient:
    patient = NationalPatient(
        id=f"PAT-{suffix}",
        lab_id=lab_id,
        health_number=f"HN-{suffix}",
        full_name="Probe Patient",
        first_name="Probe",
        last_name="Patient",
        date_of_birth=datetime.date(1990, 1, 1),
        gender="MALE",
        is_deleted=False,
    )
    db.add(patient)
    db.flush()
    return patient


def _make_condition(db, patient_id: str, suffix: str) -> ConditionRecord:
    record = ConditionRecord(
        id=f"COND-{suffix}",
        patient_id=patient_id,
        clinical_status="active",
        verification_status="confirmed",
        code="Z00",
        code_display="Probe condition",
        is_deleted=False,
    )
    db.add(record)
    db.flush()
    return record


# ── 1. the guard rests entirely on patient_id, so pin patient_id ───────────


@pytest.mark.parametrize("resource_type", _GENERIC_TYPES)
def test_every_reachable_model_has_a_non_nullable_patient_id(resource_type):
    """`_get_fhir_resource_or_404`'s tenant check is conditional on
    `getattr(record, "patient_id", None)` being truthy. A nullable patient_id
    would let a row through with no tenant check at all."""
    model = _fhir_model_class(resource_type)
    if model is None:
        pytest.skip(f"{resource_type} has no model — see the P3 below")
    column = model.__table__.columns["patient_id"]
    assert column.nullable is False, (
        f"{model.__name__}.patient_id is now nullable, so a row with a null "
        "patient_id passes through _get_fhir_resource_or_404 with NO tenant "
        "check -- the generic FHIR write surface would be cross-tenant"
    )


def test_the_tenant_helper_filters_on_the_caller_lab():
    import inspect

    from app.services.ehr_service import get_national_patient_or_404

    source = inspect.getsource(get_national_patient_or_404)
    assert "NationalPatient.lab_id == lab_id" in source
    assert "NationalPatient.is_deleted.is_(False)" in source
    assert "raise NotFoundError" in source


def test_the_generic_handlers_still_route_through_the_guard():
    import inspect

    from app.routes.ehr_fhir import fhir_delete_resource, fhir_update_resource

    for handler in (fhir_update_resource, fhir_delete_resource):
        source = inspect.getsource(handler)
        assert "_get_fhir_resource_or_404(db, resource_type, resource_id, current_user)" in source, (
            f"{handler.__name__} no longer routes through the tenant guard"
        )


def test_another_tenant_cannot_read_update_or_delete_the_record(
    client, db, make_lab, make_lab_user,
):
    """The runtime proof, over HTTP: lab B holds a valid token and the exact id."""
    lab_a = make_lab()
    lab_b = make_lab()
    user_a = make_lab_user(lab_id=lab_a.id, role="admin")
    user_b = make_lab_user(lab_id=lab_b.id, role="admin")
    patient = _make_patient(db, lab_a.id, "XT1")
    record = _make_condition(db, patient.id, "XT1")

    headers_b = auth_headers(user_b.id, lab_b.id)
    assert client.get(f"/fhir/Condition/{record.id}", headers=headers_b).status_code in (403, 404)
    assert client.put(
        f"/fhir/Condition/{record.id}",
        json={"resourceType": "Condition", "id": record.id},
        headers=headers_b,
    ).status_code in (403, 404)
    assert client.delete(f"/fhir/Condition/{record.id}", headers=headers_b).status_code in (403, 404)

    db.expire_all()
    survivor = db.query(ConditionRecord).filter(ConditionRecord.id == record.id).first()
    assert survivor is not None and survivor.is_deleted is False, (
        "a cross-tenant DELETE soft-deleted the record"
    )

    # Positive control: the owning tenant can.
    assert client.get(
        f"/fhir/Condition/{record.id}", headers=auth_headers(user_a.id, lab_a.id),
    ).status_code == 200


def test_an_unauthenticated_write_is_refused(client, db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = _make_patient(db, lab.id, "NA1")
    record = _make_condition(db, patient.id, "NA1")
    del user

    assert client.delete(f"/fhir/Condition/{record.id}").status_code in (401, 403)
    assert client.put(
        f"/fhir/Condition/{record.id}", json={"resourceType": "Condition"},
    ).status_code in (401, 403)


# ── 2. the delete persists, and only because the audit decorator commits ───


def test_the_delete_actually_persists(client, db, make_lab, make_lab_user):
    """Measured, not reasoned about: neither the handler nor get_db commits."""
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = _make_patient(db, lab.id, "DEL1")
    record = _make_condition(db, patient.id, "DEL1")

    response = client.delete(
        f"/fhir/Condition/{record.id}", headers=auth_headers(user.id, lab.id),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    db.expire_all()
    fresh = db.query(ConditionRecord).filter(ConditionRecord.id == record.id).first()
    assert fresh.is_deleted is True, (
        "the endpoint reported a deletion that was not persisted"
    )
    assert fresh.deleted_at is not None
    # ConditionRecord has no `deleted_by` column, and the handler guards every
    # one of those three fields with hasattr -- so for this model the row records
    # *when* but not *who*. Attribution is not lost: @audit_log writes the actor
    # (user_id, lab_id, role) into the audit log for the same request, which is
    # the chain CLAUDE.md requires. Asserted here so the two halves stay
    # together: if the audit row stops being written, this is the only record of
    # who deleted the record, and there would be none.
    assert not hasattr(fresh, "deleted_by"), (
        "ConditionRecord now has a deleted_by column; assert it is populated"
    )


def test_neither_the_handler_nor_the_session_dependency_commits():
    """The reason the test above is not redundant: the persistence is indirect.

    If someone adds an explicit commit to the handler this test fails, which is
    fine -- it is the cue to re-read this finding, because the dependency the
    delete currently relies on would no longer be the only one.
    """
    import inspect

    from app.database import get_db
    from app.routes.ehr_fhir import fhir_delete_resource

    handler = inspect.getsource(fhir_delete_resource)
    assert "db.commit()" not in handler
    assert "commit" not in inspect.getsource(get_db)


def test_the_audit_decorator_is_what_commits_the_delete():
    """Pinned because it is load-bearing in a way its call site does not show:
    remove `@audit_log` from the delete and the soft-delete silently stops
    persisting -- a reported deletion that never happened."""
    import inspect

    from app.audit import audit_log
    from app.routes.ehr_fhir import fhir_delete_resource

    assert "db.commit()" in inspect.getsource(audit_log)
    assert getattr(fhir_delete_resource, "__wrapped__", None) is not None, (
        "fhir_delete_resource is no longer decorated; if @audit_log was removed, "
        "the soft-delete no longer commits"
    )


# ── 3 & 4. the other two unguarded-looking handlers ───────────────────────


def test_patient_everything_delegates_to_the_guarded_bundle_reader():
    import inspect

    from app.routes.ehr_fhir import fhir_patient_everything

    source = inspect.getsource(fhir_patient_everything)
    assert "fhir_read_bundle(patient_id, current_user, db)" in source

    bundle = inspect.getsource(
        __import__("app.routes.ehr_fhir", fromlist=["fhir_read_bundle"]).fhir_read_bundle,
    )
    assert "get_national_patient_or_404(db, bundle_id, current_user.lab_id)" in bundle


def test_everything_is_tenant_scoped_at_runtime(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    make_lab_user(lab_id=lab_a.id, role="admin")
    user_b = make_lab_user(lab_id=lab_b.id, role="admin")
    patient = _make_patient(db, lab_a.id, "EV1")

    response = client.get(
        f"/fhir/Patient/{patient.id}/$everything",
        headers=auth_headers(user_b.id, lab_b.id),
    )
    assert response.status_code in (403, 404)


def test_metadata_exposes_no_patient_data():
    import inspect

    from app.routes.ehr_fhir import fhir_metadata

    source = inspect.getsource(fhir_metadata)
    assert "get_capability_statement()" in source
    assert "db" not in inspect.signature(fhir_metadata).parameters, (
        "fhir_metadata now takes a database session; it is the one handler that "
        "needs no tenant predicate precisely because it touches no records"
    )


# ── the P3, recorded with the reason it stays a P3 ────────────────────────


def test_three_types_are_advertised_internally_without_a_model():
    advertised = {
        rt for rt in (_SUPPORTED_CREATE | _SUPPORTED_UPDATE) if _fhir_model_class(rt) is None
    }
    assert advertised == {"Observation", "Patient", "Procedure"}, (
        f"the advertised-without-a-model set changed: {advertised}"
    )


@pytest.mark.parametrize("resource_type", ["Observation", "Patient", "Procedure"])
def test_those_three_answer_422_rather_than_writing_anything(
    resource_type, client, make_lab, make_lab_user,
):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    headers = auth_headers(user.id, lab.id)
    body = {"resourceType": resource_type}

    assert client.post(f"/fhir/{resource_type}", json=body, headers=headers).status_code == 422
    assert client.put(
        f"/fhir/{resource_type}/some-id", json=body, headers=headers,
    ).status_code == 422


def test_the_capability_statement_claims_no_write_support():
    """Why the P3 is only a P3: the external contract under-claims rather than
    over-claims. If a write interaction is ever advertised, the three types
    above must be excluded first, and this test is the trigger to do it."""
    from app.fhir._capabilities import get_capability_statement

    statement = get_capability_statement()
    resources = statement["rest"][0]["resource"]
    assert resources, "the capability statement advertises no resources at all"
    for resource in resources:
        codes = {item["code"] for item in resource.get("interaction", [])}
        assert codes <= {"read", "search-type", "vread", "history-instance"}, (
            f"{resource['type']} now advertises {sorted(codes)}; before advertising "
            "create/update/delete, remove Observation, Patient and Procedure from "
            "_SUPPORTED_CREATE/_SUPPORTED_UPDATE -- they have no model and answer 422"
        )
