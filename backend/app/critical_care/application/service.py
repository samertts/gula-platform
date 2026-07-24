from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.critical_care.domain.entities import (
    ContinuousInfusion,
    CriticalAlert,
    DailyChecklist,
    EarlyWarningScore,
    FluidBalance,
    ICUAdmission,
    ICUBed,
    ICUScore,
    RoundRecord,
    VentilatorSetting,
    VitalSignsRecord,
)
from app.critical_care.domain.enums import (
    ICUStatus,
)
from app.critical_care.exceptions import (
    BedNotAvailableError,
    ICUAdmissionNotFoundError,
    ICUAssessmentNotFoundError,
    InfusionNotFoundError,
    MonitoringRecordNotFoundError,
)
from app.critical_care.infrastructure.models import (
    ContinuousInfusionModel,
    CriticalAlertModel,
    DailyChecklistModel,
    EarlyWarningScoreModel,
    FluidBalanceModel,
    ICUAdmissionModel,
    ICUBedModel,
    ICUScoreModel,
    RoundRecordModel,
    VentilatorSettingModel,
    VitalSignsRecordModel,
)
from app.national.events.base import NationalDomainEvent


def _calc_ews(hr: int | None, rr: int | None, sbp: int | None, temp: float | None, o2: float | None, conscious: bool) -> dict:
    score = 0
    scores = {}

    if hr is not None:
        if hr <= 40:
            s = 3
        elif hr <= 50:
            s = 1
        elif hr <= 90:
            s = 0
        elif hr <= 110:
            s = 1
        elif hr <= 130:
            s = 2
        else:
            s = 3
        scores["heart_rate"] = s
        score += s

    if rr is not None:
        if rr <= 8:
            s = 3
        elif rr <= 11:
            s = 1
        elif rr <= 20:
            s = 0
        elif rr <= 24:
            s = 2
        else:
            s = 3
        scores["respiratory_rate"] = s
        score += s

    if sbp is not None:
        if sbp <= 90:
            s = 3
        elif sbp <= 100:
            s = 2
        elif sbp <= 110:
            s = 1
        elif sbp <= 219:
            s = 0
        else:
            s = 3
        scores["systolic_bp"] = s
        score += s

    if temp is not None:
        if temp <= 35.0:
            s = 3
        elif temp <= 36.0:
            s = 1
        elif temp <= 38.0:
            s = 0
        elif temp <= 39.0:
            s = 1
        else:
            s = 2
        scores["temperature"] = s
        score += s

    scores["consciousness"] = 3 if not conscious else 0
    score += scores["consciousness"]

    scores["oxygen"] = 2 if (o2 is not None and o2 < 92) else 0
    score += scores["oxygen"]

    if score >= 7:
        category = "high"
        freq = "q1h"
        escalate = True
    elif score >= 5:
        category = "medium"
        freq = "q2h"
        escalate = True
    else:
        category = "low"
        freq = "q4h"
        escalate = False

    return {
        "score_value": score,
        "risk_category": category,
        "recommended_frequency": freq,
        "triggers_escalation": escalate,
        **{f"{k}_score": v for k, v in scores.items()},
    }


def _calc_sofa(pao2: float | None, fi_o2: float | None, plt: int | None, bili: float | None,
               map: float | None, gcs: int | None, cr: float | None) -> dict:
    resp = 0
    if pao2 is not None and fi_o2 is not None:
        ratio = pao2 / fi_o2 if fi_o2 > 0 else 400
        if ratio < 100:
            resp = 4
        elif ratio < 200:
            resp = 3
        elif ratio < 300:
            resp = 2
        elif ratio < 400:
            resp = 1
    coag = 0
    if plt is not None:
        if plt < 20:
            coag = 4
        elif plt < 50:
            coag = 3
        elif plt < 100:
            coag = 2
        elif plt < 150:
            coag = 1
    liver = 0
    if bili is not None:
        if bili > 12.0:
            liver = 4
        elif bili > 6.0:
            liver = 3
        elif bili > 2.0:
            liver = 2
        elif bili > 1.2:
            liver = 1
    cv = 0
    if map is not None and map < 70:
        cv = 1
    neuro = 0
    if gcs is not None:
        if gcs < 6:
            neuro = 4
        elif gcs < 10:
            neuro = 3
        elif gcs < 13:
            neuro = 2
        elif gcs < 15:
            neuro = 1
    renal = 0
    if cr is not None:
        if cr > 5.0:
            renal = 4
        elif cr > 3.5:
            renal = 3
        elif cr > 2.0:
            renal = 2
        elif cr > 1.2:
            renal = 1
    total = resp + coag + liver + cv + neuro + renal
    mortality = min(100, (total * 5) + 10) if total < 12 else 80
    return {
        "score_value": total,
        "respiratory": resp, "coagulation": coag, "liver": liver,
        "cardiovascular": cv, "neurological": neuro, "renal": renal,
        "mortality_prediction": mortality,
    }


class CriticalCareService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ---- Admissions ----

    def admit_patient(self, data: dict[str, Any]) -> ICUAdmission:
        model = ICUAdmissionModel(**{k: v for k, v in data.items() if hasattr(ICUAdmissionModel, k)})
        self.db.add(model)
        if data.get("bed_id"):
            bed = self.db.query(ICUBedModel).filter_by(id=data["bed_id"]).first()
            if bed:
                if bed.is_occupied:
                    raise BedNotAvailableError(f"Bed {bed.bed_label} is already occupied")
                bed.is_occupied = True
                bed.current_patient_id = data.get("patient_id", "")
                bed.current_admission_id = ""
        self.db.commit()
        self.db.refresh(model)
        return ICUAdmission(id=model.id, patient_id=model.patient_id, icu_type=model.icu_type,
                            admission_type=model.admission_type, status=model.status,
                            bed_id=model.bed_id or "", facility_id=model.facility_id or "")

    def get_admission(self, admission_id: str) -> ICUAdmission:
        model = self.db.query(ICUAdmissionModel).filter_by(id=admission_id).first()
        if not model or model.is_deleted:
            raise ICUAdmissionNotFoundError()
        return ICUAdmission(id=model.id, patient_id=model.patient_id, patient_name=model.patient_name or "",
                            icu_type=model.icu_type, status=model.status or "stable",
                            admission_diagnosis=model.admission_diagnosis or "")

    def list_admissions(self, icu_type: str | None = None, status: str | None = None, skip: int = 0, limit: int = 100) -> list[ICUAdmission]:
        query = self.db.query(ICUAdmissionModel).filter(ICUAdmissionModel.is_deleted.isnot(True))
        if icu_type:
            query = query.filter_by(icu_type=icu_type)
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(ICUAdmissionModel.created_at.desc()).offset(skip).limit(limit)
        return [ICUAdmission(id=m.id, patient_id=m.patient_id, patient_name=m.patient_name or "",
                              icu_type=m.icu_type, status=m.status or "stable",
                              admission_diagnosis=m.admission_diagnosis or "") for m in query.all()]

    def discharge_patient(self, admission_id: str, data: dict[str, Any]) -> ICUAdmission:
        model = self.db.query(ICUAdmissionModel).filter_by(id=admission_id).first()
        if not model:
            raise ICUAdmissionNotFoundError()
        model.status = ICUStatus.DISCHARGED.value
        model.discharged_at = datetime.now(UTC)
        model.discharge_summary = data.get("discharge_summary", "")
        model.discharge_destination = data.get("destination", "")
        model.discharge_reason = data.get("reason", "")
        if model.bed_id:
            bed = self.db.query(ICUBedModel).filter_by(id=model.bed_id).first()
            if bed:
                bed.is_occupied = False
                bed.current_patient_id = None
        self.db.commit()
        return ICUAdmission(id=model.id, patient_id=model.patient_id, status=ICUStatus.DISCHARGED)

    # ---- Beds ----

    def register_bed(self, data: dict[str, Any]) -> ICUBed:
        model = ICUBedModel(**{k: v for k, v in data.items() if hasattr(ICUBedModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return ICUBed(id=model.id, bed_label=model.bed_label, icu_type=model.icu_type)

    def get_bed_availability(self, icu_type: str | None = None) -> list[dict]:
        query = self.db.query(ICUBedModel).filter(ICUBedModel.is_active.is_(True))
        if icu_type:
            query = query.filter_by(icu_type=icu_type)
        beds = query.all()
        total = len(beds)
        occupied = sum(1 for b in beds if b.is_occupied)
        return [{"total": total, "occupied": occupied, "available": total - occupied, "icu_type": icu_type or "all"}]

    # ---- Vital Signs ----

    def record_vitals(self, data: dict[str, Any]) -> VitalSignsRecord:
        model = VitalSignsRecordModel(**{k: v for k, v in data.items() if hasattr(VitalSignsRecordModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return VitalSignsRecord(id=model.id, patient_id=model.patient_id,
                                 heart_rate=model.heart_rate, respiratory_rate=model.respiratory_rate,
                                 systolic_bp=model.systolic_bp, diastolic_bp=model.diastolic_bp,
                                 temperature=model.temperature, oxygen_saturation=model.oxygen_saturation,
                                 gcs_total=model.gcs_total, recorded_at=model.recorded_at)

    def get_vitals(self, patient_id: str, limit: int = 100) -> list[VitalSignsRecord]:
        models = self.db.query(VitalSignsRecordModel).filter_by(patient_id=patient_id)\
            .order_by(VitalSignsRecordModel.recorded_at.desc()).limit(limit).all()
        return [VitalSignsRecord(id=m.id, patient_id=m.patient_id, heart_rate=m.heart_rate,
                                 respiratory_rate=m.respiratory_rate, systolic_bp=m.systolic_bp,
                                 temperature=m.temperature, oxygen_saturation=m.oxygen_saturation,
                                 recorded_at=m.recorded_at) for m in models]

    # ---- Ventilator ----

    def set_ventilator(self, data: dict[str, Any]) -> VentilatorSetting:
        model = VentilatorSettingModel(**{k: v for k, v in data.items() if hasattr(VentilatorSettingModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return VentilatorSetting(id=model.id, patient_id=model.patient_id, mode=model.mode,
                                  tidal_volume_ml=model.tidal_volume_ml, peep_cmh2o=model.peep_cmh2o,
                                  fi_o2=model.fi_o2, respiratory_rate_set=model.respiratory_rate_set)

    def get_ventilator_settings(self, patient_id: str, limit: int = 50) -> list[VentilatorSetting]:
        models = self.db.query(VentilatorSettingModel).filter_by(patient_id=patient_id)\
            .order_by(VentilatorSettingModel.setting_time.desc()).limit(limit).all()
        return [VentilatorSetting(id=m.id, patient_id=m.patient_id, mode=m.mode) for m in models]

    # ---- Early Warning Scores ----

    def calculate_ews(self, patient_id: str, admission_id: str, vitals_id: str | None = None) -> EarlyWarningScore:
        vitals = self.db.query(VitalSignsRecordModel).filter_by(patient_id=patient_id)\
            .order_by(VitalSignsRecordModel.recorded_at.desc()).first()
        if not vitals:
            raise MonitoringRecordNotFoundError()
        result = _calc_ews(vitals.heart_rate, vitals.respiratory_rate, vitals.systolic_bp,
                           vitals.temperature, vitals.oxygen_saturation, (vitals.gcs_total or 15) >= 13)
        model = EarlyWarningScoreModel(
            patient_id=patient_id, admission_id=admission_id,
            score_time=datetime.now(UTC), score_system="news2",
            score_value=result["score_value"],
            heart_rate_score=result.get("heart_rate_score", 0),
            respiratory_rate_score=result.get("respiratory_rate_score", 0),
            systolic_bp_score=result.get("systolic_bp_score", 0),
            temperature_score=result.get("temperature_score", 0),
            consciousness_score=result.get("consciousness_score", 0),
            oxygen_score=result.get("oxygen_score", 0),
            risk_category=result["risk_category"],
            recommended_frequency=result["recommended_frequency"],
            triggers_escalation=result["triggers_escalation"],
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return EarlyWarningScore(id=model.id, patient_id=patient_id, score_value=model.score_value,
                                  risk_category=model.risk_category, triggers_escalation=model.triggers_escalation,
                                  score_system="news2", recommended_frequency=model.recommended_frequency,
                                  calculated_by=model.calculated_by or "")

    def calculate_sofa(self, patient_id: str, admission_id: str, data: dict[str, Any]) -> ICUScore:
        result = _calc_sofa(
            data.get("pao2"), data.get("fi_o2"), data.get("platelets"),
            data.get("bilirubin"), data.get("map"), data.get("gcs"), data.get("creatinine"),
        )
        model = ICUScoreModel(
            patient_id=patient_id, admission_id=admission_id,
            score_time=datetime.now(UTC), score_type="sofa",
            score_value=result["score_value"],
            score_components={k: v for k, v in result.items() if k in ("respiratory", "coagulation", "liver", "cardiovascular", "neurological", "renal")},
            mortality_prediction=result.get("mortality_prediction"),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return ICUScore(id=model.id, patient_id=patient_id, score_type="sofa",
                         score_value=model.score_value, mortality_prediction=model.mortality_prediction)

    # ---- Infusions ----

    def start_infusion(self, data: dict[str, Any]) -> ContinuousInfusion:
        model = ContinuousInfusionModel(**{k: v for k, v in data.items() if hasattr(ContinuousInfusionModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return ContinuousInfusion(id=model.id, patient_id=model.patient_id, medication=model.medication,
                                   rate=model.rate or "", status=model.status or "active")

    def stop_infusion(self, infusion_id: str) -> ContinuousInfusion:
        model = self.db.query(ContinuousInfusionModel).filter_by(id=infusion_id).first()
        if not model:
            raise InfusionNotFoundError()
        model.status = "stopped"
        model.end_time = datetime.now(UTC)
        self.db.commit()
        return ContinuousInfusion(id=model.id, patient_id=model.patient_id, medication=model.medication, status="stopped")

    # ---- Fluid Balance ----

    def record_fluid_balance(self, data: dict[str, Any]) -> FluidBalance:
        intake = (data.get("iv_fluids_ml", 0) + data.get("enteral_feeding_ml", 0) +
                  data.get("oral_intake_ml", 0) + data.get("blood_products_ml", 0))
        output = (data.get("urine_output_ml", 0) + data.get("stool_output_ml", 0) +
                  data.get("ng_output_ml", 0) + data.get("drain_output_ml", 0) +
                  data.get("estimated_blood_loss_ml", 0) + data.get("insensible_losses_ml", 200))
        data["total_intake_ml"] = intake
        data["total_output_ml"] = output
        data["net_balance_ml"] = intake - output
        model = FluidBalanceModel(**{k: v for k, v in data.items() if hasattr(FluidBalanceModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return FluidBalance(id=model.id, patient_id=model.patient_id, total_intake_ml=intake,
                             total_output_ml=output, net_balance_ml=intake - output)

    # ---- Alerts ----

    def raise_alert(self, data: dict[str, Any]) -> CriticalAlert:
        model = CriticalAlertModel(**{k: v for k, v in data.items() if hasattr(CriticalAlertModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return CriticalAlert(id=model.id, patient_id=model.patient_id, alert_type=model.alert_type,
                              severity=model.severity, alert_message=model.alert_message or "")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> CriticalAlert:
        model = self.db.query(CriticalAlertModel).filter_by(id=alert_id).first()
        if not model:
            raise ICUAssessmentNotFoundError()
        model.acknowledged_by = acknowledged_by
        model.acknowledged_at = datetime.now(UTC)
        self.db.commit()
        return CriticalAlert(id=model.id, patient_id=model.patient_id, alert_type=model.alert_type,
                              severity=model.severity, is_active=model.is_active)

    # ---- Rounds ----

    def record_round(self, data: dict[str, Any]) -> RoundRecord:
        model = RoundRecordModel(**{k: v for k, v in data.items() if hasattr(RoundRecordModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return RoundRecord(id=model.id, patient_id=model.patient_id, attending_physician=model.attending_physician or "")

    # ---- Daily Checklist ----

    def complete_checklist(self, data: dict[str, Any]) -> DailyChecklist:
        model = DailyChecklistModel(**{k: v for k, v in data.items() if hasattr(DailyChecklistModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DailyChecklist(id=model.id, patient_id=model.patient_id, checklist_date=model.checklist_date)

    # ---- Dashboard ----

    def get_dashboard_stats(self) -> dict[str, Any]:
        total_beds = self.db.query(ICUBedModel).filter(ICUBedModel.is_active.is_(True)).count()
        occupied_beds = self.db.query(ICUBedModel).filter(ICUBedModel.is_active.is_(True), ICUBedModel.is_occupied.is_(True)).count()
        active_patients = self.db.query(ICUAdmissionModel).filter(
            ICUAdmissionModel.status.in_(["stable", "improving", "deteriorating", "critical"]),
        ).count()
        ventilated = self.db.query(VentilatorSettingModel).count()
        active_alerts = self.db.query(CriticalAlertModel).filter(CriticalAlertModel.is_active.is_(True)).count()
        high_ews = self.db.query(EarlyWarningScoreModel).filter(
            EarlyWarningScoreModel.risk_category.in_(["high", "medium"]),
            EarlyWarningScoreModel.triggers_escalation.is_(True),
        ).count()
        return {
            "total_beds": total_beds, "occupied_beds": occupied_beds, "available_beds": total_beds - occupied_beds,
            "bed_occupancy_pct": round((occupied_beds / total_beds * 100), 1) if total_beds else 0,
            "active_patients": active_patients, "ventilator_settings": ventilated,
            "active_alerts": active_alerts, "high_ews_alerts": high_ews,
        }
