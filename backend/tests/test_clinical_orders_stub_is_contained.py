"""NR-098 — /clinical/orders is served, non-persistent, and was cross-tenant.

`app/routes/clinical_orders.py` is registered in `factory.py` and reachable by
any authenticated caller. Every handler declares `db: Session = Depends(get_db)`
and none of them uses it: the backing store is a module-level dict. Three
separate defects were measured on that one surface.

1. Cross-tenant read and mutation. `create_order` recorded `lab_id`; no reader
   consulted it. Executed against the pre-fix module: lab 901 listed lab 902's
   clinical orders, fetched one by id, and cancelled it. `_ORDER_TEMPLATES`,
   `_RECURRING_ORDERS` and `_STANDING_ORDER_ASSIGNMENTS` were shared the same
   way.

2. Route shadowing. `GET /{order_id}` was declared before `GET /templates`,
   `/recurring` and `/standing`, and Starlette resolves in declaration order, so
   all three reads were unreachable while the matching POSTs still accepted
   writes. A surface that is safe only because it is broken is not safe (§6):
   fixing the ordering without fixing the scoping would have opened three
   cross-tenant reads.

3. No persistence. A clinician can place a medication, radiology or procedure
   order, receive 201 with an id, and have that order exist in one worker's
   memory. That is a patient-safety problem, not a missing feature, so the whole
   surface is gated behind ENABLE_CLINICAL_ORDERS_STUB (default false).

These guards hold all three closed. They are structural, not behavioural only,
because the defect class is "a control exists but is not applied to every
reachable entry point" — so the check is coverage over the router's own route
table, and it fails for any handler added later that skips the gate.
"""

from __future__ import annotations

import ast
import pathlib
import types

import pytest
from app.routes import clinical_orders as co
from fastapi import HTTPException

_SOURCE = pathlib.Path(co.__file__)


def _route_handlers() -> dict[str, ast.FunctionDef]:
    """Every function in the module decorated with an `@router.<method>(...)`."""
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


#: The router's full handler set at the time these guards were written. It may
#: grow -- a new handler must appear here AND pass every guard below -- but the
#: count may never silently fall, which would mean a handler was deleted or the
#: decorator scan stopped seeing it.
DECLARED_HANDLERS = frozenset({
    "list_order_templates",
    "create_order_template",
    "create_recurring_order",
    "list_recurring_orders",
    "get_standing_orders_for_patient",
    "create_order",
    "list_orders",
    "get_order",
    "cancel_order",
    "complete_order",
})


def test_the_handler_scan_still_sees_every_route():
    """Guard the guard: a scan that finds nothing must not pass vacuously."""
    handlers = _route_handlers()
    assert set(handlers) == set(DECLARED_HANDLERS), (
        "the set of @router-decorated handlers changed. Update DECLARED_HANDLERS "
        "and confirm the new handler is gated and tenant-scoped.\n"
        f"  scanned but not declared: {sorted(set(handlers) - DECLARED_HANDLERS)}\n"
        f"  declared but not scanned: {sorted(DECLARED_HANDLERS - set(handlers))}"
    )
    # Every route object in the router must correspond to a scanned handler,
    # so the AST scan cannot miss a reachable entry point.
    served = {r.endpoint.__name__ for r in co.router.routes}
    assert served == set(handlers), (
        f"router serves handlers the AST scan did not find: {sorted(served - set(handlers))}"
    )


def test_every_handler_calls_the_gate_before_anything_else():
    """§6 control coverage: the gate must be on every entry point, not most."""
    missing: list[str] = []
    for name, node in sorted(_route_handlers().items()):
        body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        first = body[0] if body else None
        is_gate = (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Call)
            and isinstance(first.value.func, ast.Name)
            and first.value.func.id == "_require_enabled"
        )
        if not is_gate:
            missing.append(name)
    assert not missing, (
        "these handlers on the served /clinical/orders router do not call "
        f"_require_enabled() as their first statement: {missing}"
    )


def test_the_gate_is_off_unless_a_deployment_opts_in():
    import app.config as cfg

    assert hasattr(cfg, "ENABLE_CLINICAL_ORDERS_STUB")
    assert cfg.ENABLE_CLINICAL_ORDERS_STUB is False, (
        "ENABLE_CLINICAL_ORDERS_STUB must default to false: orders placed on this "
        "router are not persisted anywhere."
    )


def test_the_gate_refuses_every_handler_when_off(monkeypatch):
    """Behavioural companion to the AST guard, over the real route table."""
    monkeypatch.setattr("app.config.ENABLE_CLINICAL_ORDERS_STUB", False)
    user = types.SimpleNamespace(id=1, lab_id=901)

    calls = {
        "create_order": lambda: co.create_order(_order("P-1"), user, None),
        "list_orders": lambda: co.list_orders(None, None, None, None, 0, 50, user, None),
        "get_order": lambda: co.get_order("CLN-ORD-000001", user, None),
        "cancel_order": lambda: co.cancel_order("CLN-ORD-000001", user, None),
        "complete_order": lambda: co.complete_order("CLN-ORD-000001", user, None),
        "list_order_templates": lambda: co.list_order_templates(None, None, user, None),
        "create_order_template": lambda: co.create_order_template(_template(), user, None),
        "create_recurring_order": lambda: co.create_recurring_order(_recurring(), user, None),
        "list_recurring_orders": lambda: co.list_recurring_orders(None, None, user, None),
        "get_standing_orders_for_patient": lambda: co.get_standing_orders_for_patient("P-1", user, None),
    }
    # Every served handler must be covered by this table.
    assert set(calls) == {r.endpoint.__name__ for r in co.router.routes}

    for name, call in sorted(calls.items()):
        with pytest.raises(HTTPException) as exc:
            call()
        assert exc.value.status_code == 503, f"{name} returned {exc.value.status_code}, expected 503"


def test_literal_paths_are_declared_before_the_parameterised_one():
    """Otherwise /{order_id} swallows /templates, /recurring and /standing."""
    gets = [r for r in co.router.routes if "GET" in (getattr(r, "methods", None) or set())]
    expected = {
        "/clinical/orders/templates": "list_order_templates",
        "/clinical/orders/recurring": "list_recurring_orders",
        "/clinical/orders/standing": "get_standing_orders_for_patient",
        "/clinical/orders/CLN-ORD-000001": "get_order",
    }
    for path, handler in expected.items():
        winner = next((r for r in gets if r.path_regex.match(path)), None)
        assert winner is not None, f"no GET route matches {path}"
        assert winner.endpoint.__name__ == handler, (
            f"GET {path} resolves to {winner.endpoint.__name__} (declared {winner.path}), "
            f"expected {handler}. Literal paths must be declared before /{{order_id}}."
        )


# ── behavioural tenant isolation, with the gate opened explicitly ──────────────


def _order(patient_id: str, notes: str = "") -> co.ClinicalOrderCreate:
    return co.ClinicalOrderCreate(
        patient_id=patient_id, order_type="medication",
        order_name="Vancomycin 1g IV", notes=notes,
    )


def _template() -> co.OrderTemplateCreate:
    return co.OrderTemplateCreate(name="tpl", order_type="lab", order_name="CBC")


def _recurring() -> co.RecurringOrderCreate:
    return co.RecurringOrderCreate(
        patient_id="P-1", order_type="lab", order_name="CBC",
        frequency="daily", interval_days=1, start_date="2026-01-01",
    )


@pytest.fixture
def opened(monkeypatch):
    """Open the gate and give each test empty, isolated stores."""
    monkeypatch.setattr("app.config.ENABLE_CLINICAL_ORDERS_STUB", True)
    monkeypatch.setattr(co, "_FAKE_ORDERS", {})
    monkeypatch.setattr(co, "_ORDER_TEMPLATES", {})
    monkeypatch.setattr(co, "_RECURRING_ORDERS", {})
    monkeypatch.setattr(co, "_STANDING_ORDER_ASSIGNMENTS", {})
    return types.SimpleNamespace(
        a=types.SimpleNamespace(id=1, lab_id=901),
        b=types.SimpleNamespace(id=2, lab_id=902),
    )


def test_one_lab_cannot_list_another_labs_clinical_orders(opened):
    co.create_order(_order("P-A-111", "LAB-A: confidential"), opened.a, None)
    co.create_order(_order("P-B-777", "LAB-B: confidential"), opened.b, None)

    listed = co.list_orders(None, None, None, None, 0, 50, opened.a, None)
    assert listed["total"] == 1
    assert [o["lab_id"] for o in listed["items"]] == [901]
    assert all("LAB-B" not in (o.get("notes") or "") for o in listed["items"])


def test_one_lab_cannot_read_or_mutate_another_labs_clinical_order(opened):
    foreign = co.create_order(_order("P-B-777", "LAB-B: confidential"), opened.b, None)

    for fn in (co.get_order, co.cancel_order, co.complete_order):
        with pytest.raises(HTTPException) as exc:
            fn(foreign["id"], opened.a, None)
        # 404, not 403: the caller must not learn the order exists.
        assert exc.value.status_code == 404, f"{fn.__name__} leaked {exc.value.status_code}"

    assert co._FAKE_ORDERS[foreign["id"]]["status"] == "pending", (
        "a foreign lab changed the clinical status of this order"
    )


def test_the_sub_resource_stores_are_tenant_scoped_too(opened):
    co.create_order_template(
        co.OrderTemplateCreate(name="A-tpl", order_type="lab", order_name="CBC"), opened.a, None)
    co.create_order_template(
        co.OrderTemplateCreate(name="B-tpl", order_type="lab", order_name="CBC"), opened.b, None)
    assert [t["name"] for t in co.list_order_templates(None, None, opened.a, None)["items"]] == ["A-tpl"]

    co.create_recurring_order(_recurring(), opened.a, None)
    co.create_recurring_order(_recurring(), opened.b, None)
    mine = co.list_recurring_orders(None, None, opened.a, None)
    assert mine["total"] == 1
    assert mine["items"][0]["lab_id"] == 901

    co._STANDING_ORDER_ASSIGNMENTS["S-1"] = {"patient_id": "P-1", "lab_id": 902, "is_active": True}
    assert co.get_standing_orders_for_patient("P-1", opened.a, None)["total"] == 0
