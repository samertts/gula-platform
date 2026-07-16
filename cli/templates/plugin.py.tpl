import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger("gula.plugins.{{ module_name }}")

PLUGIN_NAME = "{{ name }}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "{{ description }}"


def register(app: Any) -> None:
    logger.info("Registering plugin: %s v%s", PLUGIN_NAME, PLUGIN_VERSION)
    app.include_router(router, prefix="/plugins/{{ prefix }}", tags=["plugins"])


router = APIRouter()


@router.get("/health")
def plugin_health():
    return {"status": "ok", "plugin": PLUGIN_NAME, "version": PLUGIN_VERSION}
