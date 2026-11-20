"""HTTP wiring for the GULA Universal Language System.

The core implementation lives in ``app.localization`` and is transport-agnostic.
This module only binds it to the existing FastAPI application dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.localization.delivery import _load_pack_store
from app.localization.delivery import create_router as create_delivery_router
from app.localization.language_registry import LanguageRegistry
from app.localization.pack_manager import PackManager
from app.localization.preferences import (
    AccessibilityProfilePreferenceStore,
)
from app.localization.preferences import (
    create_router as create_preference_router,
)
from app.security.dependencies import require_institutional_user

_registry = LanguageRegistry.load()
_dist_value = os.getenv("GULS_PACK_DIST_ROOT")
_pack_manager = PackManager(
    Path(os.getenv("GULS_LOCAL_PACK_ROOT", "/tmp/gula-language-packs")),
    _registry,
    allow_synthetic_packs=os.getenv("GULS_ALLOW_SYNTHETIC_PACKS", "0") == "1",
)


def _preference_store_provider(db: Session = Depends(get_db)) -> AccessibilityProfilePreferenceStore:
    return AccessibilityProfilePreferenceStore(db)


router = APIRouter(tags=["localization"])
router.include_router(
    create_delivery_router(
        registry=_registry,
        pack_manager=_pack_manager,
        pack_store=_load_pack_store(Path(_dist_value) if _dist_value else None),
    )
)
router.include_router(
    create_preference_router(
        registry=_registry,
        pack_manager=_pack_manager,
        preference_store_provider=_preference_store_provider,
        current_user_provider=require_institutional_user,
    )
)
