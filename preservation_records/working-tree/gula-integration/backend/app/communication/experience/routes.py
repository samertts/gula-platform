"""User Communication Experience API (PROGRAM-COMM-003).

Mounted once at the platform factory so every GULA application gains:
preferences, channel catalog, unified inbox (filter/search/paginate),
notification actions, history, mute, and retry — without any per-application
code.

All endpoints are user-scoped (``current_user.id``) and reject any
notification owned by another user (object-level authorization). Critical
categories cannot be muted/disabled anywhere in this API.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.lab_user import LabUser
from ...security.dependencies import get_current_user
from .domain import MANDATORY_CATEGORIES
from .inbox_service import (
    bulk_state,
    get_inbox_item,
    grouped_summary,
    history,
    list_inbox,
    purge,
    retry_delivery,
    set_pinned,
    set_state,
    unread_count,
)
from .preferences_service import (
    categories as preference_categories,
)
from .preferences_service import (
    channel_catalog,
    get_preferences,
    mute_category,
    mute_channel,
    priorities,
    update_preferences,
)

router = APIRouter(prefix="/communication", tags=["communication"])


class _PreferencesPatch(BaseModel):
    locale: str | None = None
    timezone: str | None = None
    channels: dict[str, bool] | None = None
    channel_priority: list[str] | None = None
    categories: dict[str, bool] | None = None
    frequency: str | None = None
    digest_schedule: str | None = None
    quiet_hours: dict[str, Any] | None = None
    weekend_rules: bool | None = None
    holiday_rules: bool | None = None
    emergency_override: bool | None = None


class _MuteRequest(BaseModel):
    muted: bool = True


class _BulkRequest(BaseModel):
    action: str
    ids: list[int] | None = Field(default=None)


# ── Preferences ──────────────────────────────────────────────────────────────


@router.get("/preferences")
def read_preferences(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_preferences(db, current_user.id).to_dict()


@router.put("/preferences")
def write_preferences(
    patch: _PreferencesPatch,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return update_preferences(db, current_user.id, patch.model_dump(exclude_none=True)).to_dict()


@router.get("/preferences/catalog")
def preference_catalog(current_user: LabUser = Depends(get_current_user)) -> dict[str, Any]:
    try:
        from ...communication import get_communication_center

        center = get_communication_center()
        provider_channels = center.providers.channels()
        states = {
            p["channel"]: p["health"] for p in center.providers.describe() if "channel" in p
        }
    except Exception:
        provider_channels = ["inapp"]
        states = {"inapp": "ready"}
    catalog = channel_catalog(
        provider_channels=[*provider_channels, "webhook", "push"],
        provider_states=states,
    )
    return {
        "channels": catalog,
        "categories": preference_categories(),
        "priorities": priorities(),
        "mandatory_categories": sorted(MANDATORY_CATEGORIES),
    }


@router.post("/preferences/mute-category")
def mute_notification_category(
    body: _MuteRequest,
    category: str = Query(...),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if category in MANDATORY_CATEGORIES:
        raise HTTPException(status_code=400, detail="category_is_mandatory")
    return mute_category(db, current_user.id, category, body.muted).to_dict()


@router.post("/preferences/mute-channel")
def mute_notification_channel(
    body: _MuteRequest,
    channel: str = Query(...),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from .domain import MANDATORY_CHANNELS

    if channel in MANDATORY_CHANNELS:
        raise HTTPException(status_code=400, detail="channel_is_mandatory")
    return mute_channel(db, current_user.id, channel, body.muted).to_dict()


# ── Inbox ────────────────────────────────────────────────────────────────────


def _inbox_query(
    state: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    group_key: str | None = None,
    search: str | None = None,
    pinned: bool | None = None,
    cursor: int | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    return {
        "state": state,
        "category": category,
        "priority": priority,
        "group_key": group_key,
        "search": search,
        "pinned": pinned,
        "cursor": cursor,
        "limit": limit,
    }


@router.get("/inbox")
def read_inbox(
    state: str | None = Query(default=None),
    category: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    group_key: str | None = Query(default=None),
    search: str | None = Query(default=None),
    pinned: bool | None = Query(default=None),
    cursor: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    include_deleted: bool = Query(default=False),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return list_inbox(
        db,
        current_user.id,
        **_inbox_query(
            state=state,
            category=category,
            priority=priority,
            group_key=group_key,
            search=search,
            pinned=pinned,
            cursor=cursor,
            limit=limit,
        ),
        include_deleted=include_deleted,
    )


@router.get("/inbox/groups")
def read_inbox_groups(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return {"groups": grouped_summary(db, current_user.id)}


@router.get("/inbox/unread-count")
def read_unread_count(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {"unread": unread_count(db, current_user.id)}


@router.get("/inbox/{notification_id}")
def read_inbox_item(
    notification_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        row = get_inbox_item(db, current_user.id, notification_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="notification_not_found") from None
    return {"item": row.to_dict(), "history": history(db, current_user.id, notification_id)}


@router.patch("/inbox/{notification_id}")
def act_on_inbox_item(
    notification_id: int,
    action: str = Query(...),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if action in ("pin", "unpin"):
        try:
            return set_pinned(db, current_user.id, notification_id, action == "pin")
        except LookupError:
            raise HTTPException(status_code=404, detail="notification_not_found") from None
    if action not in ("read", "unread", "archive", "restore", "delete"):
        raise HTTPException(status_code=400, detail="unknown_action")
    try:
        return set_state(db, current_user.id, notification_id, action)
    except LookupError:
        raise HTTPException(status_code=404, detail="notification_not_found") from None


@router.delete("/inbox/{notification_id}")
def delete_inbox_item(
    notification_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return purge(db, current_user.id, notification_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="notification_not_found") from None


@router.post("/inbox/bulk")
def bulk_inbox_action(
    body: _BulkRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if body.action not in ("read", "unread", "archive", "restore", "delete"):
        raise HTTPException(status_code=400, detail="unknown_action")
    return bulk_state(db, current_user.id, body.action, ids=body.ids)


@router.post("/inbox/{notification_id}/retry")
def retry_inbox_item(
    notification_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        row = get_inbox_item(db, current_user.id, notification_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="notification_not_found") from None
    from .gateway import rebuild_context, send_communication

    _ = rebuild_context(db, row)

    def _dispatch(ctx: dict[str, Any]) -> dict[str, Any]:
        result = send_communication(
            db,
            int(ctx.get("user_id", current_user.id)),
            category=str(ctx.get("category") or "system"),
            priority=str(ctx.get("priority") or "medium"),
            title=str(ctx.get("title") or row.title),
            body=str(ctx.get("body") or row.body),
            template_id=str(ctx.get("template_id") or ""),
            recipient=str(ctx.get("recipient") or None),
            group_key=str(ctx.get("group_key") or ""),
            action=str(ctx.get("action") or ""),
            context={"retry_of": notification_id},
        )
        return {
            "success": bool(result.get("delivered")),
            "error": result.get("error") or result.get("reason"),
        }

    return retry_delivery(db, current_user.id, notification_id, _dispatch)


router.__all__ = [  # type: ignore[attr-defined]
    "read_preferences",
    "write_preferences",
    "preference_catalog",
    "mute_notification_category",
    "mute_notification_channel",
    "read_inbox",
    "read_inbox_groups",
    "read_unread_count",
    "read_inbox_item",
    "act_on_inbox_item",
    "delete_inbox_item",
    "bulk_inbox_action",
    "retry_inbox_item",
]
