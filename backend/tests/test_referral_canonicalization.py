from __future__ import annotations

from unittest.mock import Mock

import pytest
from app.insurance.api.referrals import router as insurance_referral_router
from app.nursing.routes import router as nursing_router
from app.security.legacy_referral import block_legacy_referral_write
from app.services.care_continuum_service import ReferralScopeError, create_referral_request
from app.services.referral_canonical_mapping import (
    CanonicalReferralMappingError,
    CanonicalReferralMappingService,
)
from fastapi import HTTPException


def test_legacy_referral_write_blocker_returns_gone_successor() -> None:
    request = Mock()
    request.url.path = "/referrals"
    request.method = "POST"
    user = Mock(id=7, lab_id=11)

    with pytest.raises(HTTPException) as exc_info:
        block_legacy_referral_write(request, user)

    assert exc_info.value.status_code == 410
    assert exc_info.value.headers is not None
    assert exc_info.value.headers["Deprecation"] == "true"
    assert exc_info.value.headers["Cache-Control"] == "no-store"
    assert "/care-continuum/referrals" in exc_info.value.headers["Link"]


def test_care_referral_create_rejects_client_practitioner_and_facility_authority() -> None:
    with pytest.raises(ReferralScopeError, match="client_authority_forbidden"):
        create_referral_request(
            Mock(),
            {
                "patient_id": "national-patient-1",
                "referral_reason": "specialist review",
                "referring_practitioner_id": "client-practitioner",
                "referring_facility_id": "client-facility",
            },
            lab_id=11,
            server_practitioner_id=7,
        )


def test_care_referral_create_requires_server_practitioner_proof() -> None:
    with pytest.raises(ReferralScopeError, match="server_practitioner_mapping_required"):
        create_referral_request(
            Mock(),
            {"patient_id": "national-patient-1", "referral_reason": "specialist review"},
            lab_id=11,
        )


def test_insurance_facility_mapping_fails_closed_without_reviewed_bridge() -> None:
    with pytest.raises(CanonicalReferralMappingError, match="server_facility_mapping_required"):
        CanonicalReferralMappingService._require_facility_mapping(42)

    CanonicalReferralMappingService._require_facility_mapping(None)


def test_legacy_insurance_writes_are_contained_by_router_dependency() -> None:
    write_routes = {
        (route.path, method)
        for route in insurance_referral_router.routes
        if hasattr(route, "methods")
        for method in route.methods
        if method in {"POST", "PUT", "PATCH", "DELETE"}
    }
    assert ("/referrals", "POST") in write_routes
    assert all(
        any(getattr(getattr(dependency, "dependency", None), "__name__", "") == "block_legacy_referral_write" for dependency in route.dependencies)
        for route in insurance_referral_router.routes
        if hasattr(route, "methods")
        and any(method in {"POST", "PUT", "PATCH", "DELETE"} for method in route.methods)
    )


def test_legacy_nursing_referral_write_is_contained_by_router_dependency() -> None:
    route = next(
        route
        for route in nursing_router.routes
        if getattr(route, "path", "") == "/nursing/coordination/referral"
    )
    assert any(
        getattr(getattr(dependency, "dependency", None), "__name__", "") == "block_legacy_referral_write"
        for dependency in route.dependencies
    )
