"""Standardized localization/internationalization module — English-first fallback."""

from __future__ import annotations

import logging

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.i18n")

_SUPPORTED_LOCALES = {"ar", "en", "ckb"}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ar": {
        "welcome": "أهلاً بك",
        "error": "خطأ",
        "success": "نجاح",
        "save": "حفظ",
        "cancel": "إلغاء",
        "delete": "حذف",
        "search": "بحث",
        "loading": "جارٍ التحميل...",
        "no_results": "لا توجد نتائج",
        "confirm": "تأكيد",
        "back": "رجوع",
        "next": "التالي",
    },
    "en": {
        "welcome": "Welcome",
        "error": "Error",
        "success": "Success",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "search": "Search",
        "loading": "Loading...",
        "no_results": "No results found",
        "confirm": "Confirm",
        "back": "Back",
        "next": "Next",
    },
    "ckb": {
        "welcome": "بەخێربێی",
        "error": "هەڵە",
        "success": "سەرکەوتن",
        "save": "پاشەکەوت",
        "cancel": "ڕەتکردن",
        "delete": "سڕینەوە",
        "search": "گەڕان",
    },
}


class TranslationService:
    def __init__(self) -> None:
        self._locale = "en"

    def translate(self, key: str, locale: str | None = None, **kwargs) -> str:
        locale = locale or self._locale
        # English is the mandatory fallback for every locale. Raw keys are never
        # returned to callers because the UI owns user-facing presentation.
        translations = _TRANSLATIONS.get(locale, {})
        template = translations.get(key, _TRANSLATIONS.get("en", {}).get(key, ""))
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return template

    def get_locale(self) -> str:
        return self._locale

    def set_locale(self, locale: str) -> None:
        if locale in _SUPPORTED_LOCALES:
            self._locale = locale

    def get_supported_locales(self) -> list[str]:
        return list(_SUPPORTED_LOCALES)


PlatformRegistry.register("i18n", TranslationService(), capabilities=[
    {"name": "translate", "description": "Translate a key to the current or specified locale"},
    {"name": "get_locale", "description": "Get the current locale"},
    {"name": "get_supported_locales", "description": "Get all supported locales"},
])
