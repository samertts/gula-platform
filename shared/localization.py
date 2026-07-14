from __future__ import annotations

import json
import os
from typing import Any

_LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locales")
_cache: dict[str, dict[str, str]] = {}


class Localization:
    def __init__(self, locale: str = "ar") -> None:
        self._locale = locale
        self._load()

    def _load(self) -> None:
        if self._locale not in _cache:
            path = os.path.join(_LOCALE_DIR, f"{self._locale}.json")
            if os.path.exists(path):
                with open(path) as f:
                    _cache[self._locale] = json.load(f)
            else:
                _cache[self._locale] = {}
        self._strings = _cache[self._locale]

    def get(self, key: str, default: str = "") -> str:
        return self._strings.get(key, default)

    def format(self, key: str, **kwargs: Any) -> str:
        template = self.get(key, key)
        return template.format(**kwargs)

    @property
    def locale(self) -> str:
        return self._locale


_global = Localization()


def t(key: str, default: str = "") -> str:
    return _global.get(key, default)


def set_locale(locale: str) -> None:
    global _global
    _global = Localization(locale)


__all__ = ["Localization", "set_locale", "t"]
