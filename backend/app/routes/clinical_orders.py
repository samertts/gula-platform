from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.routes.clinical_orders")

router = APIRouter(prefix="/clinical/orders", tags=["clinical orders"])


_ORDER_TYPES = frozenset(
    {
        "lab",
        "radiology",
        "medication",
        "procedure",
        "consultation",
        "referral",
        "nutrition",
        "nursing",
    }
)
_ORDER_STATUSES = frozenset(
    {
        "draft",
        "pending",
        "active",
        "completed",
        "cancelled",
        "on_hold",
    }
)


class ClinicalOrderCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    order_type: str = Field(
        ...,
        description="lab/radiology/medication/procedure/consultation/referral/nutrition/nursing",
    )
    order_code: str | None = None
    order_name: str = Field(..., max_length=512)
    description: str | None = None
    priority: str = "routine"
    status: str = "pending"
    ordering_provider_id: str | None = None
    department: str | None = None
    diagnosis_code: str | None = None
    diagnosis_system: str | None = None
    diagnosis_display: str | None = None
    instructions: str | None = None
    notes: str | None = None
    is_stat: bool = False
    is_standing: bool = False
    frequency: str | None = None
    duration: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    source: str = "manual"
    metadata: dict[str, Any] = {}


class ClinicalOrderUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    instructions: str | None = None
    notes: str | None = None


class RecurringOrderCreate(BaseModel):
    patient_id: str
    order_type: str
    order_code: str | None = None
    order_name: str = Field(..., max_length=512)
    description: str | None = None
    frequency: str
    interval_days: int
    start_date: str
    end_date: str | None = None
    max_occurrences: int | None = None
    department: str | None = None
    instructions: str | None = None
    ordering_provider_id: str | None = None


_FAKE_ORDERS: dict[str, dict[str, Any]] = {}
_FAKE_COUNTER: int = 0


def _next_id() -> str:
    global _FAKE_COUNTER
    _FAKE_COUNTER += 1
    return f"CLN-ORD-{_FAKE_COUNTER:06d}"


# ==============================================================================
# Order Management
# ==============================================================================


@router.post("", status_code=201)
def create_order(
    data: ClinicalOrderCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.order_type not in _ORDER_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid order_type. Must be one of: {', '.join(sorted(_ORDER_TYPES))}",
        )
    if data.status not in _ORDER_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(_ORDER_STATUSES))}",
        )

    order_id = _next_id()
    now = datetime.now(UTC).isoformat()
    order = {
        "id": order_id,
        **data.model_dump(exclude_none=True),
        "lab_id": current_user.lab_id,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    _FAKE_ORDERS[order_id] = order
    return order


@router.get("")
def list_orders(
    patient_id: str | None = None,
    encounter_id: str | None = None,
    order_type: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = list(_FAKE_ORDERS.values())
    if patient_id:
        items = [o for o in items if o.get("patient_id") == patient_id]
    if encounter_id:
        items = [o for o in items if o.get("encounter_id") == encounter_id]
    if order_type:
        items = [o for o in items if o.get("order_type") == order_type]
    if status:
        items = [o for o in items if o.get("status") == status]

    total = len(items)
    items.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    paged = items[skip : skip + limit]

    return {"items": paged, "total": total, "skip": skip, "limit": limit}


@router.get("/{order_id}")
def get_order(
    order_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _FAKE_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _FAKE_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] in ("completed", "cancelled"):
        raise HTTPException(
            status_code=422,
            detail=f"Cannot cancel order in status '{order['status']}'",
        )
    order["status"] = "cancelled"
    order["updated_at"] = datetime.now(UTC).isoformat()
    order["cancelled_by"] = current_user.id
    return order


@router.put("/{order_id}/complete")
def complete_order(
    order_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _FAKE_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] == "cancelled":
        raise HTTPException(
            status_code=422,
            detail="Cannot complete a cancelled order",
        )
    order["status"] = "completed"
    order["updated_at"] = datetime.now(UTC).isoformat()
    order["completed_by"] = current_user.id
    order["completed_at"] = datetime.now(UTC).isoformat()
    return order


# ==============================================================================
# Order Templates
# ==============================================================================

_ORDER_TEMPLATES: dict[str, dict[str, Any]] = {}


class OrderTemplateCreate(BaseModel):
    name: str = Field(..., max_length=256)
    order_type: str
    order_code: str | None = None
    order_name: str
    description: str | None = None
    department: str | None = None
    priority: str = "routine"
    instructions: str | None = None
    is_stat: bool = False
    metadata: dict[str, Any] = {}


@router.get("/templates")
def list_order_templates(
    order_type: str | None = None,
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = list(_ORDER_TEMPLATES.values())
    if order_type:
        items = [t for t in items if t.get("order_type") == order_type]
    if department:
        items = [t for t in items if t.get("department") == department]
    return {"items": items, "total": len(items)}


@router.post("/templates", status_code=201)
def create_order_template(
    data: OrderTemplateCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template_id = _next_id()
    template = {
        "id": template_id,
        **data.model_dump(exclude_none=True),
        "lab_id": current_user.lab_id,
        "created_by": current_user.id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _ORDER_TEMPLATES[template_id] = template
    return template


# ==============================================================================
# Recurring Orders
# ==============================================================================

_RECURRING_ORDERS: dict[str, dict[str, Any]] = {}


@router.post("/recurring", status_code=201)
def create_recurring_order(
    data: RecurringOrderCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.order_type not in _ORDER_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid order_type. Must be one of: {', '.join(sorted(_ORDER_TYPES))}",
        )
    rec_id = _next_id()
    now = datetime.now(UTC).isoformat()
    rec = {
        "id": rec_id,
        **data.model_dump(exclude_none=True),
        "lab_id": current_user.lab_id,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }
    _RECURRING_ORDERS[rec_id] = rec
    return rec


@router.get("/recurring")
def list_recurring_orders(
    patient_id: str | None = None,
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = list(_RECURRING_ORDERS.values())
    if patient_id:
        items = [r for r in items if r.get("patient_id") == patient_id]
    if department:
        items = [r for r in items if r.get("department") == department]
    return {"items": items, "total": len(items)}


# ==============================================================================
# Standing Orders for Patient
# ==============================================================================


_STANDING_ORDER_ASSIGNMENTS: dict[str, dict[str, Any]] = {}


@router.get("/standing")
def get_standing_orders_for_patient(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = [
        a
        for a in _STANDING_ORDER_ASSIGNMENTS.values()
        if a.get("patient_id") == patient_id and a.get("is_active", True)
    ]
    return {"items": items, "total": len(items)}
