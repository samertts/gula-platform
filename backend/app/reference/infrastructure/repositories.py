from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.reference.domain.interfaces import (
    OrderRepository,
    PatientRepository,
    ResultRepository,
)
from app.reference.domain.models import (
    LabOrderDomain,
    LabResultDomain,
    OrderStatus,
    PatientDomain,
    ReferenceRange,
)


class SQLPatientRepository(PatientRepository):
    """SQLAlchemy implementation of PatientRepository.

    This is the ONLY place patient persistence logic lives.
    """

    # Mapping of domain field → DB column for search
    _SEARCHABLE_COLUMNS = {
        "name": "name",
        "phone": "phone",
        "lab_id": "lab_id",
        "national_id": "national_id",
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, patient: PatientDomain) -> PatientDomain:
        stmt = text("""
            INSERT INTO patients (name, date_of_birth, gender, phone,
                                  lab_id, national_id, address,
                                  created_at, updated_at)
            VALUES (:name, :date_of_birth, :gender, :phone,
                    :lab_id, :national_id, :address, :created_at, :updated_at)
            RETURNING
                id AS patient_id,
                name,
                date_of_birth,
                gender,
                phone,
                lab_id,
                national_id,
                address,
                created_at,
                updated_at
        """)
        now = datetime.now(UTC)
        row = (
            (
                await self._session.execute(
                    stmt,
                    {
                        "name": patient.name,
                        "date_of_birth": patient.date_of_birth,
                        "gender": patient.gender.value if patient.gender else None,
                        "phone": patient.phone,
                        "lab_id": patient.lab_id,
                        "national_id": patient.national_id,
                        "address": patient.address,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            )
            .mappings()
            .one()
        )

        return self._row_to_domain(row)

    async def get_by_id(self, patient_id: str) -> PatientDomain | None:
        stmt = text("""
            SELECT id AS patient_id, name, date_of_birth, gender, phone,
                   lab_id, national_id, address, created_at, updated_at
            FROM patients
            WHERE id = :patient_id
        """)
        row = (
            (await self._session.execute(stmt, {"patient_id": patient_id})).mappings().one_or_none()
        )
        return self._row_to_domain(row) if row else None

    async def search(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        lab_id: str | None = None,
        national_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PatientDomain], int]:
        conditions: list = []
        if name:
            conditions.append(text("name ILIKE :name"))
        if phone:
            conditions.append(text("phone = :phone"))
        if lab_id:
            conditions.append(text("lab_id = :lab_id"))
        if national_id:
            conditions.append(text("national_id = :national_id"))

        where_clause = and_(*conditions) if conditions else text("TRUE")
        base_sql = f"""
            FROM patients
            WHERE {where_clause.compile(compile_kwargs={"literal_binds": False})}
        """

        params: dict = {}
        if name:
            params["name"] = f"%{name}%"
        if phone:
            params["phone"] = phone
        if lab_id:
            params["lab_id"] = lab_id
        if national_id:
            params["national_id"] = national_id

        count_stmt = text(f"SELECT COUNT(*) AS total {base_sql}")
        total_row = (await self._session.execute(count_stmt, params)).mappings().one()
        total = total_row["total"]

        data_stmt = text(f"""
            SELECT id AS patient_id, name, date_of_birth, gender, phone,
                   lab_id, national_id, address, created_at, updated_at
            {base_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        params["limit"] = limit
        params["offset"] = offset
        rows = (await self._session.execute(data_stmt, params)).mappings().all()

        patients = [self._row_to_domain(r) for r in rows]
        return patients, total

    async def find_duplicate(
        self,
        name: str,
        phone: str,
        lab_id: str,
    ) -> PatientDomain | None:
        stmt = text("""
            SELECT id AS patient_id, name, date_of_birth, gender, phone,
                   lab_id, national_id, address, created_at, updated_at
            FROM patients
            WHERE name = :name AND phone = :phone AND lab_id = :lab_id
            LIMIT 1
        """)
        row = (
            (
                await self._session.execute(
                    stmt,
                    {
                        "name": name,
                        "phone": phone,
                        "lab_id": lab_id,
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._row_to_domain(row) if row else None

    @staticmethod
    def _row_to_domain(row) -> PatientDomain:
        return PatientDomain(
            patient_id=str(row["patient_id"]),
            name=row["name"],
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            phone=row["phone"],
            lab_id=row["lab_id"],
            national_id=row["national_id"],
            address=row["address"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SQLOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: LabOrderDomain) -> LabOrderDomain:
        stmt = text("""
            INSERT INTO lab_orders
                (patient_id, lab_id, test_type, status, priority,
                 notes, created_at, updated_at, performed_by)
            VALUES
                (:patient_id, :lab_id, :test_type, :status, :priority,
                 :notes, :created_at, :updated_at, :performed_by)
            RETURNING
                id AS order_id, patient_id, lab_id, test_type, status,
                priority, notes, created_at, updated_at, performed_by
        """)
        now = datetime.now(UTC)
        row = (
            (
                await self._session.execute(
                    stmt,
                    {
                        "patient_id": order.patient_id,
                        "lab_id": order.lab_id,
                        "test_type": order.test_type,
                        "status": order.status.value,
                        "priority": order.priority.value,
                        "notes": order.notes,
                        "created_at": now,
                        "updated_at": now,
                        "performed_by": order.performed_by,
                    },
                )
            )
            .mappings()
            .one()
        )
        return self._row_to_domain(row)

    async def get_by_id(self, order_id: str) -> LabOrderDomain | None:
        stmt = text("""
            SELECT id AS order_id, patient_id, lab_id, test_type, status,
                   priority, notes, created_at, updated_at, performed_by
            FROM lab_orders
            WHERE id = :order_id
        """)
        row = (await self._session.execute(stmt, {"order_id": order_id})).mappings().one_or_none()
        return self._row_to_domain(row) if row else None

    async def list_by_patient(
        self,
        patient_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[LabOrderDomain], int]:
        count_stmt = text("""
            SELECT COUNT(*) AS total
            FROM lab_orders
            WHERE patient_id = :patient_id
        """)
        total_row = (
            (
                await self._session.execute(
                    count_stmt,
                    {"patient_id": patient_id},
                )
            )
            .mappings()
            .one()
        )
        total = total_row["total"]

        data_stmt = text("""
            SELECT id AS order_id, patient_id, lab_id, test_type, status,
                   priority, notes, created_at, updated_at, performed_by
            FROM lab_orders
            WHERE patient_id = :patient_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        rows = (
            (
                await self._session.execute(
                    data_stmt,
                    {
                        "patient_id": patient_id,
                        "limit": limit,
                        "offset": offset,
                    },
                )
            )
            .mappings()
            .all()
        )
        return [self._row_to_domain(r) for r in rows], total

    @staticmethod
    def _row_to_domain(row) -> LabOrderDomain:
        return LabOrderDomain(
            order_id=str(row["order_id"]),
            patient_id=row["patient_id"],
            lab_id=row["lab_id"],
            test_type=row["test_type"],
            status=OrderStatus(row["status"]),
            priority=row["priority"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            performed_by=row["performed_by"],
        )


class SQLResultRepository(ResultRepository):
    """SQLAlchemy implementation of ResultRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: LabResultDomain) -> LabResultDomain:
        stmt = text("""
            INSERT INTO lab_results
                (order_id, analyte, value, unit,
                 min_value, max_value, min_critical, max_critical,
                 is_critical, flagged, notes, created_at, performed_by)
            VALUES
                (:order_id, :analyte, :value, :unit,
                 :min_value, :max_value, :min_critical, :max_critical,
                 :is_critical, :flagged, :notes, :created_at, :performed_by)
            RETURNING
                id AS result_id, order_id, analyte, value, unit,
                min_value, max_value, min_critical, max_critical,
                is_critical, flagged, notes, created_at, performed_by
        """)
        now = datetime.now(UTC)
        rr = result.reference_range
        row = (
            (
                await self._session.execute(
                    stmt,
                    {
                        "order_id": result.order_id,
                        "analyte": result.analyte,
                        "value": str(result.value),
                        "unit": result.unit,
                        "min_value": str(rr.min_value) if rr and rr.min_value is not None else None,
                        "max_value": str(rr.max_value) if rr and rr.max_value is not None else None,
                        "min_critical": str(rr.min_critical)
                        if rr and rr.min_critical is not None
                        else None,
                        "max_critical": str(rr.max_critical)
                        if rr and rr.max_critical is not None
                        else None,
                        "is_critical": result.is_critical,
                        "flagged": result.flagged,
                        "notes": result.notes,
                        "created_at": now,
                        "performed_by": result.performed_by,
                    },
                )
            )
            .mappings()
            .one()
        )
        return self._row_to_domain(row)

    async def get_by_id(self, result_id: str) -> LabResultDomain | None:
        stmt = text("""
            SELECT id AS result_id, order_id, analyte, value, unit,
                   min_value, max_value, min_critical, max_critical,
                   is_critical, flagged, notes, created_at, performed_by
            FROM lab_results
            WHERE id = :result_id
        """)
        row = (await self._session.execute(stmt, {"result_id": result_id})).mappings().one_or_none()
        return self._row_to_domain(row) if row else None

    async def list_by_order(
        self,
        order_id: str,
    ) -> Sequence[LabResultDomain]:
        stmt = text("""
            SELECT id AS result_id, order_id, analyte, value, unit,
                   min_value, max_value, min_critical, max_critical,
                   is_critical, flagged, notes, created_at, performed_by
            FROM lab_results
            WHERE order_id = :order_id
            ORDER BY created_at ASC
        """)
        rows = (await self._session.execute(stmt, {"order_id": order_id})).mappings().all()
        return [self._row_to_domain(r) for r in rows]

    async def list_critical(
        self,
        lab_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[LabResultDomain], int]:
        count_stmt = text("""
            SELECT COUNT(*) AS total
            FROM lab_results lr
            JOIN lab_orders lo ON lo.id = lr.order_id
            WHERE lr.is_critical = TRUE
              AND lo.lab_id = :lab_id
        """)
        total_row = (
            (
                await self._session.execute(
                    count_stmt,
                    {"lab_id": lab_id},
                )
            )
            .mappings()
            .one()
        )
        total = total_row["total"]

        data_stmt = text("""
            SELECT lr.id AS result_id, lr.order_id, lr.analyte,
                   lr.value, lr.unit,
                   lr.min_value, lr.max_value,
                   lr.min_critical, lr.max_critical,
                   lr.is_critical, lr.flagged, lr.notes,
                   lr.created_at, lr.performed_by
            FROM lab_results lr
            JOIN lab_orders lo ON lo.id = lr.order_id
            WHERE lr.is_critical = TRUE
              AND lo.lab_id = :lab_id
            ORDER BY lr.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        rows = (
            (
                await self._session.execute(
                    data_stmt,
                    {
                        "lab_id": lab_id,
                        "limit": limit,
                        "offset": offset,
                    },
                )
            )
            .mappings()
            .all()
        )
        return [self._row_to_domain(r) for r in rows], total

    @staticmethod
    def _row_to_domain(row) -> LabResultDomain:
        rr: ReferenceRange | None = None
        if any(
            row.get(c) is not None
            for c in ("min_value", "max_value", "min_critical", "max_critical")
        ):
            rr = ReferenceRange(
                analyte=row["analyte"],
                unit=row["unit"],
                min_value=(row["min_value"] if row["min_value"] is not None else None),
                max_value=(row["max_value"] if row["max_value"] is not None else None),
                min_critical=(row["min_critical"] if row["min_critical"] is not None else None),
                max_critical=(row["max_critical"] if row["max_critical"] is not None else None),
            )

        return LabResultDomain(
            result_id=str(row["result_id"]),
            order_id=row["order_id"],
            analyte=row["analyte"],
            value=row["value"],
            unit=row["unit"],
            reference_range=rr,
            is_critical=row["is_critical"],
            flagged=row["flagged"],
            notes=row["notes"],
            created_at=row["created_at"],
            performed_by=row["performed_by"],
        )
