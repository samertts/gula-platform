from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from app.services.care_continuum_service import (
    ReferralScopeError,
    _require_referral_lab,
    accept_referral,
    complete_referral,
    create_cross_org_referral,
    create_referral_request,
    create_referral_response,
    get_referral_analytics,
    get_referral_timeline,
    reject_referral,
)


@pytest.mark.parametrize(
    ("operation", "args"),
    [
        (create_referral_request, (Mock(), {}, None)),
        (accept_referral, (Mock(), "referral-1", None)),
        (reject_referral, (Mock(), "referral-1", "reason", None)),
        (complete_referral, (Mock(), "referral-1", None)),
        (get_referral_timeline, (Mock(), "referral-1", None)),
        (create_cross_org_referral, (Mock(), {}, None)),
        (create_referral_response, (Mock(), {}, None)),
        (get_referral_analytics, (Mock(), None, None, None, None, None)),
    ],
)
def test_referral_operations_require_server_derived_lab_scope(operation: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ReferralScopeError, match="institution_scope_required"):
        operation(*args)


def test_referral_scope_rejects_client_tenant_mismatch() -> None:
    with pytest.raises(ReferralScopeError, match="institution_scope_mismatch"):
        create_referral_request(
            Mock(),
            {"lab_id": 99},
            lab_id=7,
        )


def test_referral_scope_accepts_only_positive_server_lab_id() -> None:
    assert _require_referral_lab(7) == 7
    with pytest.raises(ReferralScopeError):
        _require_referral_lab(0)


def test_referral_timeline_is_server_scoped() -> None:
    from app.services.care_continuum_service import _add_referral_timeline

    db = Mock()
    entry = _add_referral_timeline(
        db,
        "referral-1",
        "created",
        "Referral request created",
        lab_id=7,
    )

    assert entry.lab_id == 7
    assert entry.referral_request_id == "referral-1"
    db.add.assert_called_once_with(entry)
