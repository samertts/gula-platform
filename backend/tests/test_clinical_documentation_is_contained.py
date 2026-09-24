"""NR-100 — /clinical/documentation is the medical record, stored in a dict.

`app/routes/clinical_documentation.py` is registered in `factory.py` and served.
It holds SOAP, progress, nursing, consultation, operation and emergency notes,
their electronic signatures, structured templates and version history. Every
handler declares `db: Session = Depends(get_db)`. The module makes **zero**
database calls: `_DOCUMENTS`, `_TEMPLATES` and `_VERSION_HISTORY` are
module-level dicts.

Worse than NR-098 in one specific way: `lab_id` was not recorded on a document
at all, so no reader could have scoped by it even in principle. Executed against
the pre-fix module, with lab 901 and lab 902:

    1. lab 901 LISTS  -> 2 documents, including lab 902's operation note with
       patient P-B-777 and findings "LAB-B: confidential operative findings"
    2. lab 901 FETCHES lab 902's operation note by id -> same findings
    3. lab 901 SIGNS  lab 902's clinical document -> is_signed=True,
       signed_by=11, a lab 901 user
    4. lab 901 reads lab 902's version history -> ['created', 'signed']

Step 3 is the serious one. An electronic signature is a legal attestation on a
medical record, and one organisation could apply it to another's operative note.

The fix stamps `lab_id` inside `_store_document` rather than at the six create
handlers, so a seventh cannot forget it, scopes every reader, and gates the
whole surface behind ENABLE_CLINICAL_DOCUMENTATION_STUB (default false) because
a signed operation note that disappears on the next deploy is a clinical records
problem rather than a missing feature. The scoping applies regardless of the
flag: a gate that can be flipped must not uncover a cross-tenant read.
"""

from __future__ import annotations

import ast
import contextlib
import pathlib
import types

import pytest
from app.routes import clinical_documentation as cd
from fastapi import HTTPException

_SOURCE = pathlib.Path(cd.__file__)


def _route_handlers() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    found: dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            call = dec.func if isinstance(dec, ast.Call) else dec
            if (
                isinstance(call, ast.Attribute)
                and isinstance(call.value, ast.Name)
                and call.value.id == "router"
            ):
                found[node.name] = node
    return found


DECLARED_HANDLERS = frozenset({
    "create_soap_note", "create_progress_note", "create_nursing_note",
    "create_consultation_note", "create_operation_note", "create_emergency_note",
    "list_documents", "get_document", "list_structured_templates",
    "create_structured_template", "sign_document", "get_document_version_history",
})


def test_the_handler_scan_still_sees_every_route():
    handlers = _route_handlers()
    assert set(handlers) == set(DECLARED_HANDLERS), (
        "the @router-decorated handler set changed. Update DECLARED_HANDLERS and "
        "confirm the new handler is gated and tenant-scoped.\n"
        f"  scanned not declared: {sorted(set(handlers) - DECLARED_HANDLERS)}\n"
        f"  declared not scanned: {sorted(DECLARED_HANDLERS - set(handlers))}"
    )
    served = {r.endpoint.__name__ for r in cd.router.routes}
    assert served == set(handlers), (
        f"router serves handlers the AST scan missed: {sorted(served - set(handlers))}"
    )


def test_every_handler_calls_the_gate_before_anything_else():
    missing = []
    for name, node in sorted(_route_handlers().items()):
        body = [s for s in node.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        first = body[0] if body else None
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Call)
            and isinstance(first.value.func, ast.Name)
            and first.value.func.id == "_require_enabled"
        ):
            missing.append(name)
    assert not missing, (
        f"these served handlers do not call _require_enabled() first: {missing}"
    )


def test_the_gate_is_off_unless_a_deployment_opts_in():
    import app.config as cfg

    assert hasattr(cfg, "ENABLE_CLINICAL_DOCUMENTATION_STUB")
    assert cfg.ENABLE_CLINICAL_DOCUMENTATION_STUB is False, (
        "ENABLE_CLINICAL_DOCUMENTATION_STUB must default to false: clinical "
        "documents written here are not persisted."
    )


def _tpl(name: str = "tpl") -> cd.StructuredTemplateCreate:
    return cd.StructuredTemplateCreate(name=name, document_type="general", template_content={})


def _calls(user):
    return {
        "create_soap_note": lambda: cd.create_soap_note(cd.SoapNoteCreate(patient_id="P"), user, None),
        "create_progress_note": lambda: cd.create_progress_note(cd.ProgressNoteCreate(patient_id="P"), user, None),
        "create_nursing_note": lambda: cd.create_nursing_note(cd.NursingNoteCreate(patient_id="P"), user, None),
        "create_consultation_note": lambda: cd.create_consultation_note(cd.ConsultationNoteCreate(patient_id="P"), user, None),
        "create_operation_note": lambda: cd.create_operation_note(cd.OperationNoteCreate(patient_id="P", procedure_name="X"), user, None),
        "create_emergency_note": lambda: cd.create_emergency_note(cd.EmergencyNoteCreate(patient_id="P"), user, None),
        "list_documents": lambda: cd.list_documents(None, None, None, 0, 50, user, None),
        "get_document": lambda: cd.get_document("CLN-DOC-000001", user, None),
        "list_structured_templates": lambda: cd.list_structured_templates(None, None, user, None),
        "create_structured_template": lambda: cd.create_structured_template(_tpl(), user, None),
        "sign_document": lambda: cd.sign_document(cd.SignDocumentRequest(document_id="CLN-DOC-000001"), user, None),
        "get_document_version_history": lambda: cd.get_document_version_history("CLN-DOC-000001", user, None),
    }


def test_the_gate_refuses_every_handler_when_off(monkeypatch):
    monkeypatch.setattr("app.config.ENABLE_CLINICAL_DOCUMENTATION_STUB", False)
    calls = _calls(types.SimpleNamespace(id=1, lab_id=901))
    assert set(calls) == {r.endpoint.__name__ for r in cd.router.routes}
    for name, call in sorted(calls.items()):
        with pytest.raises(HTTPException) as exc:
            call()
        assert exc.value.status_code == 503, f"{name} returned {exc.value.status_code}"


def test_the_templates_read_is_not_shadowed_by_the_document_read():
    """GET /{document_id} matches /templates, so declaration order decides."""
    gets = [r for r in cd.router.routes if "GET" in (getattr(r, "methods", None) or set())]
    for path, handler in {
        "/clinical/documentation/templates": "list_structured_templates",
        "/clinical/documentation/CLN-DOC-000001": "get_document",
    }.items():
        winner = next((r for r in gets if r.path_regex.match(path)), None)
        assert winner is not None, f"no GET route matches {path}"
        assert winner.endpoint.__name__ == handler, (
            f"GET {path} resolves to {winner.endpoint.__name__} (declared "
            f"{winner.path}), expected {handler}."
        )


@pytest.fixture
def opened(monkeypatch):
    monkeypatch.setattr("app.config.ENABLE_CLINICAL_DOCUMENTATION_STUB", True)
    monkeypatch.setattr(cd, "_DOCUMENTS", {})
    monkeypatch.setattr(cd, "_TEMPLATES", {})
    monkeypatch.setattr(cd, "_VERSION_HISTORY", {})
    return types.SimpleNamespace(
        a=types.SimpleNamespace(id=11, lab_id=901),
        b=types.SimpleNamespace(id=22, lab_id=902),
    )


def test_every_document_records_the_lab_that_created_it(opened):
    """Without this the readers below have nothing to scope by."""
    for make in (
        lambda u: cd.create_soap_note(cd.SoapNoteCreate(patient_id="P"), u, None),
        lambda u: cd.create_progress_note(cd.ProgressNoteCreate(patient_id="P"), u, None),
        lambda u: cd.create_nursing_note(cd.NursingNoteCreate(patient_id="P"), u, None),
        lambda u: cd.create_consultation_note(cd.ConsultationNoteCreate(patient_id="P"), u, None),
        lambda u: cd.create_operation_note(cd.OperationNoteCreate(patient_id="P", procedure_name="X"), u, None),
        lambda u: cd.create_emergency_note(cd.EmergencyNoteCreate(patient_id="P"), u, None),
    ):
        doc = make(opened.b)
        assert doc.get("lab_id") == 902, f"{doc['document_type']} has no lab_id"
        assert doc.get("created_by") == 22


def test_one_lab_cannot_list_another_labs_clinical_documents(opened):
    cd.create_nursing_note(cd.NursingNoteCreate(patient_id="P-A-111"), opened.a, None)
    cd.create_operation_note(
        cd.OperationNoteCreate(patient_id="P-B-777", procedure_name="Splenectomy",
                               findings="LAB-B: confidential"), opened.b, None)
    listed = cd.list_documents(None, None, None, 0, 50, opened.a, None)
    assert listed["total"] == 1
    assert [d["lab_id"] for d in listed["items"]] == [901]
    assert all("LAB-B" not in str(d.get("findings") or "") for d in listed["items"])


def test_one_lab_cannot_read_or_sign_another_labs_clinical_document(opened):
    foreign = cd.create_operation_note(
        cd.OperationNoteCreate(patient_id="P-B-777", procedure_name="Splenectomy",
                               findings="LAB-B: confidential"), opened.b, None)

    with pytest.raises(HTTPException) as exc:
        cd.get_document(foreign["id"], opened.a, None)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        cd.get_document_version_history(foreign["id"], opened.a, None)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        cd.sign_document(cd.SignDocumentRequest(document_id=foreign["id"]), opened.a, None)
    assert exc.value.status_code == 404


def test_a_foreign_lab_cannot_leave_a_signature_on_the_document(opened):
    """Separate from the 404s above so this state check is reachable even when
    the call does not raise -- an electronic signature is a legal attestation,
    and the thing that matters is whether one was applied, not which status
    code came back."""
    foreign = cd.create_operation_note(
        cd.OperationNoteCreate(patient_id="P-B-777", procedure_name="Splenectomy"),
        opened.b, None)

    with contextlib.suppress(HTTPException):
        cd.sign_document(cd.SignDocumentRequest(document_id=foreign["id"]), opened.a, None)

    stored = cd._DOCUMENTS[foreign["id"]]
    assert stored["is_signed"] is False, (
        "a foreign lab applied an electronic signature to this clinical document"
    )
    assert "signed_by" not in stored
    assert [v["action"] for v in cd._VERSION_HISTORY[foreign["id"]]] == ["created"]


def test_templates_are_tenant_scoped(opened):
    cd.create_structured_template(_tpl("A-tpl"), opened.a, None)
    cd.create_structured_template(_tpl("B-tpl"), opened.b, None)
    mine = cd.list_structured_templates(None, None, opened.a, None)
    assert [t["name"] for t in mine["items"]] == ["A-tpl"]
