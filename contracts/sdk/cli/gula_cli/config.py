from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".gula"
CONFIG_FILE = CONFIG_DIR / "config"


class Config:
    def __init__(self) -> None:
        self._data: dict = {}
        self._load()

    def _ensure_dir(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}

    def _save(self) -> None:
        self._ensure_dir()
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(self._data, f, default_flow_style=False)

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "http://localhost:8000")

    @base_url.setter
    def base_url(self, url: str) -> None:
        self._data["base_url"] = url.rstrip("/")
        self._save()

    @property
    def token(self) -> str | None:
        return self._data.get("token")

    @token.setter
    def token(self, value: str | None) -> None:
        if value is None:
            self._data.pop("token", None)
        else:
            self._data["token"] = value
        self._save()

    @property
    def refresh_token(self) -> str | None:
        return self._data.get("refresh_token")

    @refresh_token.setter
    def refresh_token(self, value: str | None) -> None:
        if value is None:
            self._data.pop("refresh_token", None)
        else:
            self._data["refresh_token"] = value
        self._save()

    def clear_auth(self) -> None:
        self._data.pop("token", None)
        self._data.pop("refresh_token", None)
        self._save()
