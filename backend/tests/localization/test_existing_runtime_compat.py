from __future__ import annotations

from app.platform.i18n import TranslationService


def test_backend_i18n_uses_english_fallback_for_unknown_locale():
    service = TranslationService()
    assert service.translate("save", locale="xx") == "Save"
    assert service.translate("missing_key", locale="xx") == ""


def test_backend_i18n_supported_locales_use_approved_identifiers():
    service = TranslationService()
    assert set(service.get_supported_locales()) == {"ar", "en", "ckb"}
    assert service.get_locale() == "en"
