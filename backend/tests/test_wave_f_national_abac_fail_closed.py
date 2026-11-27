from __future__ import annotations

from app.national.security.abac import ABACEngine, AccessRequest


def _request(**overrides: object) -> AccessRequest:
    values: dict[str, object] = {
        "subject_id": "account-1",
        "subject_roles": ["doctor"],
        "action": "read",
        "resource_type": "observation",
        "resource_id": "obs-1",
    }
    values.update(overrides)
    return AccessRequest(**values)  # type: ignore[arg-type]


def test_national_abac_denies_when_no_purpose_matches() -> None:
    decision = ABACEngine().evaluate(_request())

    assert decision.granted is False
    assert decision.reason == "Purpose of use required"


def test_national_abac_denies_unknown_purpose() -> None:
    decision = ABACEngine().evaluate(_request(purpose_of_use="marketing"))

    assert decision.granted is False
    assert decision.reason == "Purpose 'marketing' not authorized"


def test_national_abac_allows_approved_purpose() -> None:
    decision = ABACEngine().evaluate(_request(purpose_of_use="treatment"))

    assert decision.granted is True
    assert decision.reason == "Purpose 'treatment' authorized"


def test_emergency_flag_alone_does_not_grant_access() -> None:
    decision = ABACEngine().evaluate(_request(environment_is_emergency=True))

    assert decision.granted is False
    assert decision.reason == "Emergency purpose of use required"


def test_emergency_with_approved_purpose_keeps_break_glass_obligations() -> None:
    decision = ABACEngine().evaluate(
        _request(environment_is_emergency=True, purpose_of_use="emergency"),
    )

    assert decision.granted is True
    assert decision.obligations == [
        "log_break_glass",
        "notify_administrator",
        "require_review_within_24h",
    ]


def test_sensitive_clearance_is_checked_before_emergency() -> None:
    decision = ABACEngine().evaluate(
        _request(
            resource_is_sensitive=True,
            environment_is_emergency=True,
            purpose_of_use="emergency",
        ),
    )

    assert decision.granted is False
    assert decision.reason == "Insufficient clearance for sensitive record"
