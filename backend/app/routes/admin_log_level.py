"""Runtime log level management — change log levels without restart."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import IS_PRODUCTION
from app.security.dependencies import require_permission

router = APIRouter(prefix="/admin/log-level", tags=["admin"])


class LogLevelRequest(BaseModel):
    logger_name: str = Field(default="gula", min_length=4, max_length=120)
    level: str = Field(default="INFO", min_length=4, max_length=10)


VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_PRODUCTION_LEVELS = VALID_LEVELS - {"DEBUG"}
_ALLOWED_LOGGER_PREFIX = "gula"


@router.get("")
async def get_log_level(
    _current_user=Depends(require_permission("system:admin")),
):
    logger = logging.getLogger("gula")
    return {
        "root_level": logging.getLevelName(logger.level),
        "effective_level": logging.getLevelName(logger.getEffectiveLevel()),
    }


@router.post("")
async def set_log_level(
    req: LogLevelRequest,
    current_user=Depends(require_permission("system:admin")),
):
    level_upper = req.level.upper()
    valid_levels = _PRODUCTION_LEVELS if IS_PRODUCTION else VALID_LEVELS
    if level_upper not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level. Choose from: {', '.join(sorted(valid_levels))}",
        )
    if req.logger_name != _ALLOWED_LOGGER_PREFIX and not req.logger_name.startswith(f"{_ALLOWED_LOGGER_PREFIX}."):
        raise HTTPException(status_code=400, detail="Only GULA logger namespaces may be changed")
    target = logging.getLogger(req.logger_name)
    previous_level = logging.getLevelName(target.level)
    target.setLevel(level_upper)
    logging.getLogger("gula.security").warning(
        "Runtime log level changed actor_id=%s logger=%s level=%s",
        getattr(current_user, "id", "unknown"),
        req.logger_name,
        level_upper,
    )
    return {
        "logger": req.logger_name,
        "previous_level": previous_level,
        "new_level": level_upper,
    }
