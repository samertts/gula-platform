from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.platform.i18n import TranslationService

logger = logging.getLogger("gula.citizen.accessibility")


@dataclass
class AccessibilityPreference:
    citizen_id: str = ""
    language: str = "ar"
    font_size: str = "medium"
    high_contrast: bool = False
    screen_reader_optimized: bool = False
    reduced_motion: bool = False
    text_to_speech: bool = False
    color_blind_mode: str = "none"
    input_assistance: bool = False
    sign_language_videos: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class AccessibilityService:
    def __init__(self) -> None:
        self._preferences: dict[str, AccessibilityPreference] = {}

    def set_preferences(
        self, citizen_id: str, prefs: AccessibilityPreference
    ) -> AccessibilityPreference:
        self._preferences[citizen_id] = prefs
        return prefs

    def get_preferences(self, citizen_id: str) -> AccessibilityPreference:
        return self._preferences.get(
            citizen_id,
            AccessibilityPreference(citizen_id=citizen_id),
        )

    def update_preference(
        self, citizen_id: str, key: str, value: Any
    ) -> AccessibilityPreference | None:
        prefs = self._preferences.get(citizen_id)
        if not prefs:
            return None
        if hasattr(prefs, key):
            setattr(prefs, key, value)
        return prefs

    def apply_accessibility_transform(
        self, citizen_id: str, content: dict[str, Any]
    ) -> dict[str, Any]:
        prefs = self.get_preferences(citizen_id)
        transformed = dict(content)

        if prefs.high_contrast:
            transformed["theme"] = "high_contrast"

        if prefs.font_size != "medium":
            transformed["font_size"] = prefs.font_size

        if prefs.screen_reader_optimized:
            transformed["aria_labels"] = True
            transformed["semantic_html"] = True

        if prefs.reduced_motion:
            transformed["animations"] = False

        return transformed

    def get_supported_languages(self) -> list[str]:
        return ["ar", "en", "ku", "ckb"]

    def is_rtl_language(self, language: str) -> bool:
        return language in ("ar", "ku", "ckb")


class LocalizationService:
    def __init__(self, translation_service: TranslationService | None = None) -> None:
        self._translator = translation_service or TranslationService()

    def translate(self, key: str, locale: str | None = None, **kwargs: Any) -> str:
        return self._translator.translate(key, locale=locale, **kwargs)

    def get_locale(self) -> str:
        return self._translator.get_locale()

    def set_locale(self, locale: str) -> None:
        self._translator.set_locale(locale)

    def get_supported_locales(self) -> list[str]:
        return self._translator.get_supported_locales()

    def get_direction(self, locale: str | None = None) -> str:
        locale = locale or self.get_locale()
        return "rtl" if locale in ("ar", "ku", "ckb") else "ltr"

    def format_date(
        self,
        date_str: str,
        locale: str | None = None,
        format_str: str = "%Y-%m-%d",
    ) -> str:
        locale = locale or self.get_locale()
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            months_ar = [
                "كانون الثاني", "شباط", "آذار", "نيسان",
                "أيار", "حزيران", "تموز", "آب",
                "أيلول", "تشرين الأول", "تشرين الثاني", "كانون الأول",
            ]
            if locale == "ar":
                return f"{dt.day} {months_ar[dt.month - 1]} {dt.year}"
            return dt.strftime(format_str)
        except (ValueError, IndexError):
            return date_str

    def format_number(self, number: float, locale: str | None = None) -> str:
        locale = locale or self.get_locale()
        if locale == "ar":
            return str(int(number)).translate(
                str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
            )
        return str(number)
