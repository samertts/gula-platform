from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class AuditService:
    def __init__(self, db_adapter=None, monolith_adapter=None):
        self._db = db_adapter
        self._monolith = monolith_adapter
        self._audit_model = None

    def _get_model(self) -> Any:
        if self._audit_model is None and self._monolith:
            self._audit_model = self._monolith.get_model("AuditLog")
        return self._audit_model

    async def log(self, action: str, entity_type: str, entity_id: str, performed_by: str, lab_id: str, details: dict[str, Any] | None = None) -> str:
        model = self._get_model()
        if model is None:
            return ""
        session = self._db.session() if self._db else None
        if session is None:
            return ""
        entry_id = str(uuid4())
        try:
            entry = model(
                id=entry_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                performed_by=performed_by,
                lab_id=lab_id,
                details=details or {},
                timestamp=datetime.now(UTC),
            )
            session.add(entry)
            session.commit()
            return entry_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_by_entity(self, entity_type: str, entity_id: str, limit: int = 50) -> list[dict[str, Any]]:
        model = self._get_model()
        if model is None:
            return []
        session = self._db.session() if self._db else None
        if session is None:
            return []
        try:
            entries = (
                session.query(model)
                .filter(model.entity_type == entity_type, model.entity_id == entity_id)
                .order_by(model.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": getattr(e, "id", ""),
                    "action": getattr(e, "action", ""),
                    "entity_type": getattr(e, "entity_type", ""),
                    "entity_id": getattr(e, "entity_id", ""),
                    "performed_by": getattr(e, "performed_by", ""),
                    "timestamp": str(getattr(e, "timestamp", "")),
                }
                for e in entries
            ]
        finally:
            session.close()
