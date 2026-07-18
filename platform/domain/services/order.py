from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from platform.core.event_bus import EventBus
from platform.domain.events import OrderCreated, OrderStatusChanged


@dataclass
class OrderData:
    patient_id: str = ""
    lab_id: str = ""
    test_type_ids: list[str] = field(default_factory=list)
    doctor_name: str = ""
    notes: str = ""
    priority: str = "routine"
    metadata: dict[str, Any] = field(default_factory=dict)


class OrderService:
    def __init__(self, db_adapter=None, monolith_adapter=None, event_bus: EventBus | None = None):
        self._db = db_adapter
        self._monolith = monolith_adapter
        self._event_bus = event_bus
        self._order_model = None

    def _get_model(self) -> Any:
        if self._order_model is None and self._monolith:
            self._order_model = self._monolith.get_model("LabOrder")
        return self._order_model

    async def create(self, data: OrderData) -> dict[str, Any]:
        model = self._get_model()
        if model is None:
            raise RuntimeError("Order model not available")
        session = self._db.session() if self._db else None
        if session is None:
            raise RuntimeError("Database session not available")
        try:
            order = model(
                patient_id=data.patient_id,
                lab_id=data.lab_id,
                doctor_name=data.doctor_name,
                notes=data.notes,
                priority=data.priority,
                status="pending",
            )
            session.add(order)
            session.commit()
            session.refresh(order)

            order_id = str(getattr(order, "id", ""))
            if self._event_bus:
                event = OrderCreated(
                    data={
                        "order_id": order_id,
                        "patient_id": data.patient_id,
                        "lab_id": data.lab_id,
                        "test_types": data.test_type_ids,
                    }
                )
                await self._event_bus.publish("order.created", event)

            return {"id": order_id, "status": "pending"}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def update_status(self, order_id: str, status: str) -> dict[str, Any] | None:
        model = self._get_model()
        if model is None:
            return None
        session = self._db.session() if self._db else None
        if session is None:
            return None
        try:
            order = session.query(model).filter(model.id == order_id).first()
            if order is None:
                return None
            old_status = getattr(order, "status", "")
            order.status = status  # type: ignore
            session.commit()
            if self._event_bus:
                event = OrderStatusChanged(
                    data={"order_id": order_id, "old_status": old_status, "new_status": status}
                )
                await self._event_bus.publish("order.status_changed", event)
            return {"id": order_id, "status": status}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_by_id(self, order_id: str) -> dict[str, Any] | None:
        model = self._get_model()
        if model is None:
            return None
        session = self._db.session() if self._db else None
        if session is None:
            return None
        try:
            order = session.query(model).filter(model.id == order_id).first()
            if order is None:
                return None
            return {
                "id": str(getattr(order, "id", "")),
                "patient_id": str(getattr(order, "patient_id", "")),
                "lab_id": str(getattr(order, "lab_id", "")),
                "status": getattr(order, "status", ""),
                "priority": getattr(order, "priority", ""),
                "doctor_name": getattr(order, "doctor_name", ""),
                "created_at": str(getattr(order, "created_at", "")),
            }
        finally:
            session.close()
