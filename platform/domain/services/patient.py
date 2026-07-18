from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any


@dataclass
class PatientData:
    external_id: str = ""
    national_id: str | None = None
    sndhs_health_id: str | None = None
    first_name: str = ""
    father_name: str = ""
    last_name: str = ""
    date_of_birth: date | None = None
    gender: str = ""
    phone: str = ""
    address: str = ""
    lab_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class PatientService:
    def __init__(self, db_adapter=None, monolith_adapter=None):
        self._db = db_adapter
        self._monolith = monolith_adapter
        self._patient_model = None

    def _get_model(self) -> Any:
        if self._patient_model is None and self._monolith:
            self._patient_model = self._monolith.get_model("Patient")
        return self._patient_model

    async def create(self, data: PatientData) -> dict[str, Any]:
        model = self._get_model()
        if model is None:
            raise RuntimeError("Patient model not available")
        session = self._db.session() if self._db else None
        if session is None:
            raise RuntimeError("Database session not available")
        try:
            patient = model(
                lab_id=data.lab_id,
                first_name=data.first_name,
                father_name=data.father_name,
                last_name=data.last_name,
                date_of_birth=data.date_of_birth,
                gender=data.gender,
                phone=data.phone,
                address=data.address,
            )
            if data.national_id:
                patient.national_id = data.national_id
            if data.sndhs_health_id:
                patient.sndhs_health_id = data.sndhs_health_id
            session.add(patient)
            session.commit()
            session.refresh(patient)
            return {"id": str(getattr(patient, "id", "")), "status": "created"}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_by_id(self, patient_id: str) -> dict[str, Any] | None:
        model = self._get_model()
        if model is None:
            return None
        session = self._db.session() if self._db else None
        if session is None:
            return None
        try:
            patient = session.query(model).filter(model.id == patient_id).first()
            if patient is None:
                return None
            return self._to_dict(patient)
        finally:
            session.close()

    async def search(self, query: str, lab_id: str, limit: int = 20) -> list[dict[str, Any]]:
        model = self._get_model()
        if model is None:
            return []
        session = self._db.session() if self._db else None
        if session is None:
            return []
        try:
            from sqlalchemy import or_
            like_pattern = f"%{query}%"
            results = (
                session.query(model)
                .filter(
                    model.lab_id == lab_id,
                    or_(
                        model.first_name.ilike(like_pattern),
                        model.last_name.ilike(like_pattern),
                        model.phone.ilike(like_pattern),
                    ),
                )
                .limit(limit)
                .all()
            )
            return [self._to_dict(p) for p in results]
        finally:
            session.close()

    def _to_dict(self, patient: Any) -> dict[str, Any]:
        return {
            "id": str(getattr(patient, "id", "")),
            "lab_id": str(getattr(patient, "lab_id", "")),
            "first_name": getattr(patient, "first_name", ""),
            "father_name": getattr(patient, "father_name", ""),
            "last_name": getattr(patient, "last_name", ""),
            "date_of_birth": str(getattr(patient, "date_of_birth", "")),
            "gender": getattr(patient, "gender", ""),
            "phone": getattr(patient, "phone", ""),
        }
