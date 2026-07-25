from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..enums import AnalyticsScope, ProductivityPeriod
from ..models.hierarchy import GovernanceNode
from ..models.laboratory import (
    EQARecord,
    EquipmentRegistry,
    LaboratoryRegistry,
    QCModRecord,
)
from ..models.workforce import HealthcareWorker, ProductivityRecord


class NationalAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def citizen_statistics(
        self,
        governorate: str | None = None,
        node_id: int | None = None,
    ) -> dict[str, Any]:
        return {
            "scope": "citizen_statistics",
            "note": "Delegates to national domain citizen service for actual counts",
            "governorate": governorate,
            "node_id": node_id,
            "requires_integration": True,
        }

    def disease_statistics(
        self,
        icd10_code: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict[str, Any]:
        return {
            "scope": "disease_statistics",
            "note": "Delegates to national domain encounter service for actual counts",
            "icd10_code": icd10_code,
            "requires_integration": True,
        }

    def lab_statistics(self, lab_type: str | None = None) -> dict[str, Any]:
        q = self.db.query(
            func.count(LaboratoryRegistry.id).label("total"),
            LaboratoryRegistry.lab_type,
        )
        if lab_type:
            q = q.filter(LaboratoryRegistry.lab_type == lab_type)
        q = q.group_by(LaboratoryRegistry.lab_type)
        results = q.all()

        total_labs = self.db.query(LaboratoryRegistry).count()
        active_labs = (
            self.db.query(LaboratoryRegistry)
            .filter(
                LaboratoryRegistry.is_active.is_(True),
            )
            .count()
        )

        return {
            "total_labs": total_labs,
            "active_labs": active_labs,
            "by_type": {str(r.lab_type): r.total for r in results},
        }

    def equipment_utilization(self, lab_id: int | None = None) -> dict[str, Any]:
        q = self.db.query(
            EquipmentRegistry.status,
            func.count(EquipmentRegistry.id).label("count"),
        )
        if lab_id:
            q = q.filter(EquipmentRegistry.lab_id == lab_id)
        q = q.group_by(EquipmentRegistry.status)
        results = q.all()
        return {
            "by_status": {str(r.status): r.count for r in results},
            "total": sum(r.count for r in results),
        }

    def workforce_statistics(self, node_id: int | None = None) -> dict[str, Any]:
        q = self.db.query(
            HealthcareWorker.profession,
            func.count(HealthcareWorker.id).label("count"),
        )
        if node_id:
            q = q.filter(HealthcareWorker.organization_node_id == node_id)
        q = q.group_by(HealthcareWorker.profession)
        results = q.all()

        total = sum(r.count for r in results)
        return {
            "total_workers": total,
            "by_profession": {str(r.profession): r.count for r in results},
        }

    def turnaround_time_statistics(
        self,
        lab_id: int | None = None,
        period: ProductivityPeriod = ProductivityPeriod.DAILY,
    ) -> dict[str, Any]:
        q = self.db.query(
            func.avg(ProductivityRecord.tat_average_minutes).label("avg_tat"),
            func.min(ProductivityRecord.tat_average_minutes).label("min_tat"),
            func.max(ProductivityRecord.tat_average_minutes).label("max_tat"),
        ).filter(ProductivityRecord.period == period)
        if lab_id:
            q = q.join(HealthcareWorker).filter(
                HealthcareWorker.organization_node_id == lab_id,
            )
        result = q.first()
        return {
            "average_tat_minutes": round(float(result.avg_tat), 2)
            if result and result.avg_tat
            else None,
            "min_tat_minutes": round(float(result.min_tat), 2)
            if result and result.min_tat
            else None,
            "max_tat_minutes": round(float(result.max_tat), 2)
            if result and result.max_tat
            else None,
        }

    def quality_indicators(self, lab_id: int | None = None) -> dict[str, Any]:
        q = self.db.query(QCModRecord.id, QCModRecord.status)
        if lab_id:
            q = q.filter(QCModRecord.lab_id == lab_id)
        qc_rows = q.all()
        total_qc = len(qc_rows)
        in_control_qc = sum(1 for r in qc_rows if str(r.status) == "in_control")

        eq = self.db.query(EQARecord.id, EQARecord.result)
        if lab_id:
            eq = eq.filter(EQARecord.lab_id == lab_id)
        eqa_rows = eq.all()
        total_eqa = len(eqa_rows)
        acceptable_eqa = sum(1 for r in eqa_rows if str(r.result) == "acceptable")

        return {
            "qc_in_control_rate": round((in_control_qc / total_qc * 100), 2) if total_qc > 0 else 0,
            "eqa_acceptable_rate": round((acceptable_eqa / total_eqa * 100), 2)
            if total_eqa > 0
            else 0,
        }

    def national_dashboard(self) -> dict[str, Any]:
        return {
            "laboratories": self.lab_statistics(),
            "workforce": self.workforce_statistics(),
            "quality": self.quality_indicators(),
            "equipment": self.equipment_utilization(),
            "scope": AnalyticsScope.NATIONAL.value,
        }

    def governorate_dashboard(self, governorate: str) -> dict[str, Any]:
        labs = (
            self.db.query(LaboratoryRegistry)
            .filter(
                LaboratoryRegistry.governorate == governorate,
            )
            .count()
        )
        workers = (
            self.db.query(HealthcareWorker)
            .join(
                GovernanceNode,
                HealthcareWorker.organization_node_id == GovernanceNode.id,
            )
            .filter(
                GovernanceNode.governorate == governorate,
            )
            .count()
        )
        return {
            "governorate": governorate,
            "laboratories": labs,
            "workforce": workers,
            "scope": AnalyticsScope.GOVERNORATE.value,
        }

    def lab_dashboard(self, lab_id: int) -> dict[str, Any]:
        lab = self.db.query(LaboratoryRegistry).filter(LaboratoryRegistry.id == lab_id).first()
        if not lab:
            return {"error": "lab not found"}
        return {
            "lab": {"id": lab.id, "name_ar": lab.name_ar, "lab_type": lab.lab_type.value},
            "stats": self.lab_statistics(),
            "quality": self.quality_indicators(lab_id),
            "equipment": self.equipment_utilization(lab_id),
            "workforce": self.workforce_statistics(),
        }
