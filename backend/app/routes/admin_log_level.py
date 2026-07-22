"""Runtime log level management — change log levels without restart."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/admin/log-level", tags=["admin"])


class LogLevelRequest(BaseModel):
    logger_name: str = "gula"
    level: str = "INFO"


VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@router.get("")
async def get_log_level(
    current_user: LabUser = Depends(get_current_user),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    logger = logging.getLogger("gula")
    return {
        "root_level": logging.getLevelName(logger.level),
        "effective_level": logging.getLevelName(logger.getEffectiveLevel()),
    }


@router.post("")
async def set_log_level(
    req: LogLevelRequest,
    current_user: LabUser = Depends(get_current_user),
):
    if current_user.role not in ("master_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    level_upper = req.level.upper()
    if level_upper not in VALID_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level. Choose from: {', '.join(sorted(VALID_LEVELS))}",
        )
    target = logging.getLogger(req.logger_name)
    target.setLevel(level_upper)
    return {
        "logger": req.logger_name,
        "previous_level": logging.getLevelName(target.level),
        "new_level": level_upper,
    }
