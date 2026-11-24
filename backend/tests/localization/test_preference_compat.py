from __future__ import annotations

from app.routes.user_preferences import AccessibilityPreferences, AccessibilityResponse


def test_legacy_accessibility_response_accepts_guls_keys():
    payload = AccessibilityPreferences().model_dump()
    payload.update({"fallback_language": "en", "auto_download": True})
    response = AccessibilityResponse(**payload, version=3, status="saved")
    assert response.language == "en"
    assert response.version == 3


def test_retired_language_identifiers_are_normalized_instead_of_failing():
    payload = AccessibilityPreferences().model_dump()
    payload["language"] = "ku"
    assert AccessibilityPreferences(**payload).language == "ckb"
    payload["language"] = "tk"
    assert AccessibilityPreferences(**payload).language == "en"
    payload["language"] = "syr"
    assert AccessibilityPreferences(**payload).language == "en"
