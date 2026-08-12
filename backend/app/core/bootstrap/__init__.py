from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class BootstrapContext:
    db: Any = None
    config: dict[str, str] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)

    def get_db(self) -> Any:
        return self.db

    def set_db(self, db: Any) -> None:
        self.db = db

    def get_config(self, key: str, default: str = "") -> str:
        return self.config.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)


BootstrapPhase = Callable[[BootstrapContext], None]

BOOTSTRAP_SEQUENCE: list[str] = [
    "master_admin",
    "tenants",
    "organizations",
    "ministry",
    "directorates",
    "facilities",
    "laboratories",
    "departments",
    "roles",
    "permissions",
    "users",
    "subscriptions",
    "demo_data",
]

from .bootstrap import run_bootstrap
from .master_admin import ensure_master_admin
from .subscriptions import seed_subscriptions
from .validation import validate_bootstrap

__all__ = [
    "BOOTSTRAP_SEQUENCE",
    "BootstrapContext",
    "BootstrapPhase",
    "ensure_master_admin",
    "run_bootstrap",
    "seed_subscriptions",
    "validate_bootstrap",
]
