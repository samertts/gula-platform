from typing import Any


class ResultService:
    def __init__(self, db_adapter=None, monolith_adapter=None):
        self._db = db_adapter
        self._monolith = monolith_adapter
        self._result_model = None

    def _get_model(self) -> Any:
        if self._result_model is None and self._monolith:
            self._result_model = self._monolith.get_model("LabResult")
        return self._result_model

    async def create(self, order_id: str, test_type_id: str, value: str, lab_id: str, performed_by: str = "") -> dict[str, Any]:
        model = self._get_model()
        if model is None:
            raise RuntimeError("Result model not available")
        session = self._db.session() if self._db else None
        if session is None:
            raise RuntimeError("Database session not available")
        try:
            result = model(
                order_id=order_id,
                test_type_id=test_type_id,
                value=value,
                lab_id=lab_id,
                performed_by=performed_by or "",
                status="completed",
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            return {"id": str(getattr(result, "id", "")), "status": "completed"}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_by_order(self, order_id: str) -> list[dict[str, Any]]:
        model = self._get_model()
        if model is None:
            return []
        session = self._db.session() if self._db else None
        if session is None:
            return []
        try:
            results = session.query(model).filter(model.order_id == order_id).all()
            return [
                {
                    "id": str(getattr(r, "id", "")),
                    "test_type_id": str(getattr(r, "test_type_id", "")),
                    "value": getattr(r, "value", ""),
                    "status": getattr(r, "status", ""),
                }
                for r in results
            ]
        finally:
            session.close()
