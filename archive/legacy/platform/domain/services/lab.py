from typing import Any


class LabService:
    def __init__(self, db_adapter=None, monolith_adapter=None):
        self._db = db_adapter
        self._monolith = monolith_adapter
        self._lab_model = None

    def _get_model(self) -> Any:
        if self._lab_model is None and self._monolith:
            self._lab_model = self._monolith.get_model("Lab")
        return self._lab_model

    async def get_by_id(self, lab_id: str) -> dict[str, Any] | None:
        model = self._get_model()
        if model is None:
            return None
        session = self._db.session() if self._db else None
        if session is None:
            return None
        try:
            lab = session.query(model).filter(model.id == lab_id).first()
            if lab is None:
                return None
            return {
                "id": str(getattr(lab, "id", "")),
                "name": getattr(lab, "name", ""),
                "code": getattr(lab, "code", ""),
                "is_active": getattr(lab, "is_active", False),
            }
        finally:
            session.close()

    async def list_active(self) -> list[dict[str, Any]]:
        model = self._get_model()
        if model is None:
            return []
        session = self._db.session() if self._db else None
        if session is None:
            return []
        try:
            labs = session.query(model).filter(model.is_active == True).all()
            return [
                {
                    "id": str(getattr(l, "id", "")),
                    "name": getattr(l, "name", ""),
                    "code": getattr(l, "code", ""),
                }
                for l in labs
            ]
        finally:
            session.close()
