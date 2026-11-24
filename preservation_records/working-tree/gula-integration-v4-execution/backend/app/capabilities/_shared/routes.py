from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import (
    LabUser,
    require_institutional_permission,
)

from . import crud

_read_actor = require_institutional_permission("lab:read")
_write_actor = require_institutional_permission("lab:manage")


def _actor(user: LabUser) -> dict[str, Any]:
    """Build the immutable authorization context passed into persistence."""
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
    }


def build_crud_router(capability: str, prefix: str, tags: list[str]) -> APIRouter:
    """Build real CRUD routes bound to one capability namespace and lab owner."""
    router = APIRouter(prefix=prefix, tags=tags)

    async def list_records(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: LabUser = Depends(_read_actor),
    ) -> dict[str, Any]:
        return crud.list_records(db, capability, _actor(current_user), skip=skip, limit=limit)

    async def get_record(
        id: str,
        db: Session = Depends(get_db),
        current_user: LabUser = Depends(_read_actor),
    ) -> dict[str, Any]:
        return crud.get_record(db, capability, id, _actor(current_user))

    async def create_record(
        payload: dict[str, Any],
        db: Session = Depends(get_db),
        current_user: LabUser = Depends(_write_actor),
    ) -> dict[str, Any]:
        return crud.create_record(db, capability, payload, _actor(current_user))

    async def update_record(
        id: str,
        payload: dict[str, Any],
        db: Session = Depends(get_db),
        current_user: LabUser = Depends(_write_actor),
    ) -> dict[str, Any]:
        return crud.update_record(db, capability, id, payload, _actor(current_user))

    async def delete_record(
        id: str,
        db: Session = Depends(get_db),
        current_user: LabUser = Depends(_write_actor),
    ) -> dict[str, Any]:
        return crud.delete_record(db, capability, id, _actor(current_user))

    # Unique operation IDs prevent OpenAPI collisions across capabilities.
    handlers = (
        ("GET", "/", list_records, f"list_{capability}"),
        ("GET", "/{id}", get_record, f"get_{capability}"),
        ("POST", "/", create_record, f"create_{capability}"),
        ("PUT", "/{id}", update_record, f"update_{capability}"),
        ("DELETE", "/{id}", delete_record, f"delete_{capability}"),
    )
    for method, path, handler, operation_id in handlers:
        handler.__name__ = operation_id
        router.add_api_route(
            path,
            handler,
            methods=[method],
            operation_id=operation_id,
            summary=f"{operation_id.replace('_', ' ').title()}",
        )
    return router
