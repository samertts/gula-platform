from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.lims.routes import (
    OrderCreateRequest,
    ResultCreateRequest,
    SpecimenRegisterRequest,
    create_lims_order,
    create_result,
    process_critical_alert,
    register_specimen,
)
from fastapi import HTTPException


class QueryMustNotRun:
    def query(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("release capability must deny before any database query")


USER = SimpleNamespace(id=17, lab_id=7, role="lab_admin")


def _assert_release_denial(action: object) -> None:
    with pytest.raises(HTTPException) as exc_info:
        action()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"] == "release_capability_not_available"
    assert exc_info.value.detail["reason"] == "not_enabled_for_release"


def test_specimen_registration_fails_closed_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GULA_RELEASE_ENABLED_CAPABILITIES", raising=False)
    monkeypatch.delenv("GULA_RELEASE_APPROVED_TENANT_IDS", raising=False)

    _assert_release_denial(
        lambda: register_specimen(
            SpecimenRegisterRequest(order_id=1, barcode="SYNTHETIC-001", specimen_type="blood"),
            USER,
            QueryMustNotRun(),
        )
    )


def test_result_entry_fails_closed_before_database_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GULA_RELEASE_ENABLED_CAPABILITIES", raising=False)
    monkeypatch.delenv("GULA_RELEASE_APPROVED_TENANT_IDS", raising=False)

    _assert_release_denial(
        lambda: create_result(
            ResultCreateRequest(specimen_id=1, test_code="SYNTH", test_name="Synthetic Test"),
            USER,
            QueryMustNotRun(),
        )
    )


def test_order_creation_fails_closed_before_database_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GULA_RELEASE_ENABLED_CAPABILITIES", raising=False)
    monkeypatch.delenv("GULA_RELEASE_APPROVED_TENANT_IDS", raising=False)

    _assert_release_denial(
        lambda: create_lims_order(
            OrderCreateRequest(order_id=1, accession_number="SYNTHETIC-001"),
            USER,
            QueryMustNotRun(),
        )
    )


def test_critical_alert_fails_closed_before_workflow_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GULA_RELEASE_ENABLED_CAPABILITIES", raising=False)
    monkeypatch.delenv("GULA_RELEASE_APPROVED_TENANT_IDS", raising=False)

    _assert_release_denial(lambda: process_critical_alert(1, USER, QueryMustNotRun()))
