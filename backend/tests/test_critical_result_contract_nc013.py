"""NC013-C01 — explicit critical-result identity contract."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.contracts.events import EVENT_REGISTRY
from app.lims.workflows import process_critical_result, process_critical_result_from_event
from app.services.critical_alerts import get_critical_alerts
from app.services.critical_result_contract import (
    LAB_RESULT_STORE,
    LIMS_RESULT_STORE,
    AmbiguousResultReference,
    critical_result_ref,
    extract_critical_result_ref,
)


class FakeQuery:
    def __init__(self, result: object) -> None:
        self.result = result

    def join(self, *_args: object, **_kwargs: object) -> FakeQuery:
        return self

    def filter(self, *_args: object, **_kwargs: object) -> FakeQuery:
        return self

    def first(self) -> object:
        return self.result


class FakeDB:
    def __init__(self, result: object) -> None:
        self.result = result

    def query(self, _model: object) -> FakeQuery:
        return FakeQuery(self.result)


def test_reference_builder_and_extractor_round_trip() -> None:
    ref = critical_result_ref(lab_result_id=42)
    assert ref == {"result_store": LAB_RESULT_STORE, "lab_result_id": 42}
    assert extract_critical_result_ref(ref) == (LAB_RESULT_STORE, 42)

    ref = critical_result_ref(lims_result_id=7)
    assert ref == {"result_store": LIMS_RESULT_STORE, "lims_result_id": 7}
    assert extract_critical_result_ref(ref) == (LIMS_RESULT_STORE, 7)


def test_legacy_bare_result_id_is_rejected() -> None:
    with pytest.raises(AmbiguousResultReference):
        extract_critical_result_ref({"result_store": LAB_RESULT_STORE, "result_id": 42})


def test_process_critical_result_requires_explicit_store() -> None:
    outcome = process_critical_result(FakeDB(None), 42, 1, 1)
    assert outcome["status"] == "error"
    assert "result_store is required" in outcome["message"]


def test_process_core_lab_result_uses_lab_namespace() -> None:
    result = SimpleNamespace(id=42, flag="critical", test_name="GLU")
    outcome = process_critical_result(
        FakeDB(result), 42, 1, 1, result_store=LAB_RESULT_STORE,
    )
    assert outcome["status"] == "alerted"
    assert outcome["result_store"] == LAB_RESULT_STORE
    assert outcome["lab_result_id"] == 42
    assert "result_id" not in outcome


def test_process_lims_result_uses_lims_namespace() -> None:
    result = SimpleNamespace(id=7, is_critical=True, is_panic=False, test_code="GLU")
    outcome = process_critical_result(
        FakeDB(result), 7, 1, 1, result_store=LIMS_RESULT_STORE,
    )
    assert outcome["status"] == "alerted"
    assert outcome["result_store"] == LIMS_RESULT_STORE
    assert outcome["lims_result_id"] == 7
    assert outcome["notification_window"] == "60 minutes"


def test_event_consumer_fails_closed_on_ambiguous_payload() -> None:
    outcome = process_critical_result_from_event(FakeDB(None), {"result_id": 42}, 1, 1)
    assert outcome["status"] == "error"
    assert "ambiguous" in outcome["message"]


def _violates_event_not_schema(payload: dict, schema: dict) -> bool:
    """Evaluate the registry's `not.anyOf` clause without a JSON Schema engine."""
    return any(
        all(key in payload for key in branch["required"])
        for branch in schema["not"]["anyOf"]
    )


def test_event_registry_rejects_bare_and_dual_result_ids() -> None:
    for event_name in ("ResultPublished", "ResultAmended", "CriticalAlertTriggered"):
        payload = EVENT_REGISTRY[event_name]["payload"]
        assert "result_id" not in payload["properties"]
        assert payload["properties"]["result_store"]["enum"] == [LAB_RESULT_STORE, LIMS_RESULT_STORE]

        bare = {"result_id": 42}
        dual = {"result_store": LAB_RESULT_STORE, "lab_result_id": 42, "lims_result_id": 7}
        single = {"result_store": LAB_RESULT_STORE, "lab_result_id": 42}
        assert _violates_event_not_schema(bare, payload) is True
        assert _violates_event_not_schema(dual, payload) is True
        assert _violates_event_not_schema(single, payload) is False


class _AlertQuery:
    def __init__(self, result: object) -> None:
        self.result = result

    def join(self, *_args: object, **_kwargs: object) -> _AlertQuery:
        return self

    def options(self, *_args: object, **_kwargs: object) -> _AlertQuery:
        return self

    def filter(self, *_args: object, **_kwargs: object) -> _AlertQuery:
        return self

    def order_by(self, *_args: object, **_kwargs: object) -> _AlertQuery:
        return self

    def all(self) -> list[object]:
        return [self.result]


class _AlertDB:
    def __init__(self, result: object) -> None:
        self.result = result

    def query(self, _model: object) -> _AlertQuery:
        return _AlertQuery(self.result)


def test_critical_alert_api_payload_is_namespaced() -> None:
    patient = SimpleNamespace(id=9, full_name="Synthetic Person", phone="+9647000000000")
    order = SimpleNamespace(id=3, patient=patient, doctor_name="Synthetic Clinician")
    result = SimpleNamespace(
        id=42,
        test_name="potassium",
        value=7.5,
        unit="mEq/L",
        normal_range_low=3.5,
        normal_range_high=5.1,
        flag="critical",
        order_id=3,
        order=order,
        created_at=datetime.now(UTC),
    )

    body = get_critical_alerts(_AlertDB(result), 1)
    alert = body["alerts"][0]
    assert alert["result_store"] == LAB_RESULT_STORE
    assert alert["lab_result_id"] == 42
    assert "result_id" not in alert


def test_order_creation_critical_event_is_namespaced(monkeypatch) -> None:
    from app.core.events import RESULT_CRITICAL
    from app.services import order_service

    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        order_service.events,
        "emit",
        lambda name, payload: emitted.append((name, payload)),
    )

    order = SimpleNamespace(id=11, patient_id=9, lab_id=1)
    order_service._emit_order_events(
        order,
        "Synthetic Person",
        "+9647000000000",
        1,
        1,
        [
            {
                "test_name": "potassium",
                "value": 7.5,
                "lab_result_id": 42,
                "message": "critical potassium",
            },
        ],
    )

    critical = [payload for name, payload in emitted if name == RESULT_CRITICAL]
    assert len(critical) == 1
    assert critical[0]["result_store"] == LAB_RESULT_STORE
    assert critical[0]["lab_result_id"] == 42
    assert critical[0]["patient_name"] == "Synthetic Person"
    assert "result_id" not in critical[0]
