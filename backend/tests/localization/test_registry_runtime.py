from __future__ import annotations

import json

import pytest
from app.localization.language_registry import LanguageRegistry, RegistryError, is_valid_locale_tag
from app.localization.runtime import (
    InvalidTranslationKeyError,
    LanguageRuntime,
    MissingTranslationError,
    StableMessage,
    is_valid_translation_key,
)

CORE = {"ar", "en", "ckb", "PENDING_TURKMEN_IQ", "PENDING_SYRIAC"}


def test_registry_contains_five_core_entries(registry):
    assert {language.language_id for language in registry.core()} >= CORE


def test_registry_load_rejects_malformed_entries(tmp_path):
    path = tmp_path / "registry.json"
    payload = {
        "fallback_language": "en",
        "languages": [
            {
                "language_id": "en",
                "locale_tag": "en",
                "english_name": "English",
                "language": "English",
                "classification": "core",
                "is_active": "yes",
                "is_publishable": True,
                "approval_status": "approved",
                "linguistic_approval_status": "approved",
                "clinical_approval_status": "approved_source",
                "pack_version": "1.0.0",
                "minimum_engine_version": "1.0.0",
                "translation_coverage": 1.0,
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RegistryError, match="boolean"):
        LanguageRegistry.load(path)


def test_registry_requires_english_fallback(registry):
    assert registry.fallback_language == "en"
    assert registry.fallback().direction == "ltr"
    assert registry.fallback().is_active


def test_registry_separates_language_script_region_and_direction(registry):
    sorani = registry.require("ckb")
    assert (sorani.language, sorani.dialect, sorani.region, sorani.script, sorani.direction) == (
        "Kurdish",
        "Sorani",
        "IQ",
        "Arab",
        "rtl",
    )


def test_pending_standards_are_not_publishable(registry):
    for language_id in ("PENDING_TURKMEN_IQ", "PENDING_SYRIAC"):
        language = registry.require(language_id)
        assert language.locale_tag is None
        assert language.direction is None
        assert language.script is None
        assert not language.is_active
        assert not language.is_publishable
        assert language.approval_status == "blocked"


def test_locale_tag_resolution_is_distinct_from_internal_id(registry):
    assert registry.resolve("fa-IR").language_id == "fa"
    assert registry.resolve("ckb").language_id == "ckb"
    assert registry.resolve("ku") is None


@pytest.mark.parametrize(
    ("value", "valid"),
    [("ar", True), ("fa-IR", True), ("zh-CN", True), ("ckb", True), ("en_US", False), ("", False)],
)
def test_bcp47_subset_validation(value, valid):
    assert is_valid_locale_tag(value) is valid


def test_resolution_uses_mandatory_fallback(runtime_factory, registry):
    runtime = runtime_factory(registry)
    result = runtime.resolve("fa", available_language_ids={"en"}, preferred="ar")
    assert result.selected == "en"
    assert result.fallback_used is True
    assert result.reason == "mandatory_fallback"


def test_resolution_prefers_ready_preferred_language(runtime_factory, registry):
    runtime = runtime_factory(registry)
    result = runtime.resolve("ckb", available_language_ids={"en", "ar"}, preferred="ar")
    assert result.selected == "ar"
    assert result.reason == "preferred_ready"


def test_resolution_uses_requested_ready_language(runtime_factory, registry):
    runtime = runtime_factory(registry)
    result = runtime.resolve("ar", available_language_ids={"en", "ar"}, preferred="en")
    assert result.selected == "ar"
    assert result.fallback_used is False


def test_direction_contract(runtime_factory, registry):
    runtime = runtime_factory(registry)
    assert runtime.direction("ar") == "rtl"
    assert runtime.direction("ckb") == "rtl"
    assert runtime.direction("en") == "ltr"
    assert runtime.direction("PENDING_SYRIAC") == "ltr"


def test_missing_key_never_leaks_raw_key(runtime_factory, registry):
    runtime = runtime_factory(registry)
    output = runtime.translate({"ui.save": "Save"}, "ui.delete")
    assert output == ""
    assert "ui.delete" not in output


def test_strict_missing_key_raises(runtime_factory, registry):
    runtime = runtime_factory(registry)
    with pytest.raises(MissingTranslationError):
        runtime.translate({}, "ui.save", strict=True)


def test_fallback_catalog_used_for_missing_key(runtime_factory, registry):
    runtime = runtime_factory(registry)
    assert runtime.translate({"ui.save": ""}, "ui.save", fallback_catalog={"ui.save": "Save"}) == "Save"


def test_invalid_key_is_rejected(runtime_factory, registry):
    runtime = runtime_factory(registry)
    assert is_valid_translation_key("error.patient_not_found") is True
    with pytest.raises(InvalidTranslationKeyError):
        runtime.translate({}, "PATIENT_NOT_FOUND")


def test_number_and_identifier_formatting_preserve_source(runtime_factory, registry):
    runtime = runtime_factory(registry)
    source = "1234567.25"
    display = runtime.format_number(source, "ar")
    assert display != source
    assert runtime.format_identifier(source) == source
    assert runtime.format_number(source, "en", group=False).startswith("1234567")


def test_date_formatting_preserves_iso_source(runtime_factory, registry):
    runtime = runtime_factory(registry)
    assert runtime.format_date("2026-11-20", "en", style="iso") == "2026-11-20"
    assert runtime.format_date("2026-11-20", "ar").startswith("٢٠٢٦")


def test_rtl_display_shaping_does_not_mutate_source(runtime_factory, registry):
    runtime = runtime_factory(registry)
    source = "المريض ١٢٣"
    shaped = runtime.shape_for_display(source)
    assert isinstance(shaped, str)
    assert source == "المريض ١٢٣"


def test_plural_categories(runtime_factory, registry):
    runtime = runtime_factory(registry)
    assert [runtime.plural_category(n, "ar") for n in (0, 1, 2, 5, 20)] == [
        "zero", "one", "two", "few", "many"
    ]
    assert runtime.plural_category(2, "en") == "other"


def test_stable_message_has_no_translated_prose(runtime_factory, registry):
    runtime = runtime_factory(registry)
    message = runtime.stable_message("PATIENT_NOT_FOUND", {"id": "SYNTHETIC-1"}, "req-1")
    payload = message.to_dict()
    assert payload["code"] == "PATIENT_NOT_FOUND"
    assert payload["parameters"] == {"id": "SYNTHETIC-1"}
    assert payload["correlation_id"] == "req-1"
    assert "text" not in payload


@pytest.fixture()
def runtime_factory():
    def build(registry):
        return LanguageRuntime(registry)

    return build
