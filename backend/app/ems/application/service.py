from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.ems.domain.entities import (
    Ambulance,
    AmbulanceCrew,
    CrewShift,
    DisasterEvent,
    DispatchAssignment,
    EmergencyIncident,
    HospitalStatus,
    IncidentCommandSystem,
    Shelter,
    TriageAssessment,
    ePCR,
)
from app.ems.domain.enums import (
    AmbulanceStatus,
    DispatchStatus,
    IncidentStatus,
    TriageCategory,
)
from app.ems.exceptions import (
    AmbulanceNotAvailableError,
    AmbulanceNotFoundError,
    IncidentNotFoundError,
    InvalidIncidentStateError,
    ePCRNotFoundError,
)
from app.ems.infrastructure.models import (
    AmbulanceCrewModel,
    AmbulanceModel,
    CrewShiftModel,
    DisasterEventModel,
    DispatchAssignmentModel,
    EmergencyIncidentModel,
    HospitalStatusModel,
    IncidentCommandModel,
    ShelterModel,
    TriageAssessmentModel,
    ePCRModel,
)
from app.national.events.base import NationalDomainEvent


class EMSService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ---- Incident Management ----

    def create_incident(self, data: dict[str, Any]) -> EmergencyIncident:
        model = EmergencyIncidentModel(**{k: v for k, v in data.items() if hasattr(EmergencyIncidentModel, k)})
        model.created_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        incident = self._incident_from_model(model)
        self._emit(create_incident_event(incident))
        return incident

    def get_incident(self, incident_id: str) -> EmergencyIncident:
        model = self.db.query(EmergencyIncidentModel).filter_by(id=incident_id).first()
        if not model or model.is_deleted:
            raise IncidentNotFoundError(f"Incident {incident_id} not found")
        return self._incident_from_model(model)

    def list_incidents(
        self, status: str | None = None, category: str | None = None, skip: int = 0, limit: int = 100,
    ) -> list[EmergencyIncident]:
        query = self.db.query(EmergencyIncidentModel).filter(EmergencyIncidentModel.is_deleted.isnot(True))
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        query = query.order_by(EmergencyIncidentModel.created_at.desc()).offset(skip).limit(limit)
        return [self._incident_from_model(m) for m in query.all()]

    def update_incident_status(self, incident_id: str, new_status: str) -> EmergencyIncident:
        model = self.db.query(EmergencyIncidentModel).filter_by(id=incident_id).first()
        if not model or model.is_deleted:
            raise IncidentNotFoundError(f"Incident {incident_id} not found")
        valid_transitions = {
            "pending": ["dispatched", "cancelled"],
            "dispatched": ["en_route", "cancelled"],
            "en_route": ["on_scene", "cancelled"],
            "on_scene": ["transporting", "completed"],
            "transporting": ["at_destination"],
            "at_destination": ["completed"],
        }
        if new_status not in valid_transitions.get(model.status, []):
            raise InvalidIncidentStateError(f"Cannot transition from {model.status} to {new_status}")
        setattr(model, f"{new_status}_time", datetime.now(UTC))
        model.status = new_status
        model.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return self._incident_from_model(model)

    def dispatch_incident(self, incident_id: str, ambulance_id: str, crew_ids: list[str] | None = None) -> DispatchAssignment:
        incident = self.db.query(EmergencyIncidentModel).filter_by(id=incident_id).first()
        if not incident:
            raise IncidentNotFoundError()
        ambulance = self.db.query(AmbulanceModel).filter_by(id=ambulance_id).first()
        if not ambulance:
            raise AmbulanceNotFoundError()
        if ambulance.status != AmbulanceStatus.AVAILABLE.value:
            raise AmbulanceNotAvailableError(f"Ambulance {ambulance_id} is currently {ambulance.status}")
        ambulance.status = AmbulanceStatus.EN_ROUTE.value
        incident.status = IncidentStatus.DISPATCHED.value
        incident.dispatch_time = datetime.now(UTC)
        incident.updated_at = datetime.now(UTC)
        dispatch = DispatchAssignmentModel(
            incident_id=incident_id,
            ambulance_id=ambulance_id,
            status=DispatchStatus.ASSIGNED.value,
            assigned_at=datetime.now(UTC),
            created_by="",
        )
        self.db.add(dispatch)
        self.db.commit()
        self.db.refresh(dispatch)
        return self._dispatch_from_model(dispatch)

    # ---- Ambulance Management ----

    def register_ambulance(self, data: dict[str, Any]) -> Ambulance:
        model = AmbulanceModel(**{k: v for k, v in data.items() if hasattr(AmbulanceModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._ambulance_from_model(model)

    def get_ambulance(self, ambulance_id: str) -> Ambulance:
        model = self.db.query(AmbulanceModel).filter_by(id=ambulance_id).first()
        if not model or model.is_deleted:
            raise AmbulanceNotFoundError()
        return self._ambulance_from_model(model)

    def list_ambulances(self, status: str | None = None, skip: int = 0, limit: int = 100) -> list[Ambulance]:
        query = self.db.query(AmbulanceModel).filter(AmbulanceModel.is_deleted.isnot(True))
        if status:
            query = query.filter_by(status=status)
        query = query.offset(skip).limit(limit)
        return [self._ambulance_from_model(m) for m in query.all()]

    def update_ambulance_location(self, ambulance_id: str, lat: float, lng: float) -> Ambulance:
        model = self.db.query(AmbulanceModel).filter_by(id=ambulance_id).first()
        if not model:
            raise AmbulanceNotFoundError()
        model.current_location_lat = lat
        model.current_location_lng = lng
        model.current_location_updated = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return self._ambulance_from_model(model)

    def update_ambulance_status(self, ambulance_id: str, status: str, reason: str = "") -> Ambulance:
        model = self.db.query(AmbulanceModel).filter_by(id=ambulance_id).first()
        if not model:
            raise AmbulanceNotFoundError()
        model.status = status
        model.status_reason = reason
        self.db.commit()
        self.db.refresh(model)
        return self._ambulance_from_model(model)

    # ---- Crew Management ----

    def register_crew_member(self, data: dict[str, Any]) -> AmbulanceCrew:
        model = AmbulanceCrewModel(**{k: v for k, v in data.items() if hasattr(AmbulanceCrewModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._crew_from_model(model)

    def list_crew(self, station_id: str | None = None, skip: int = 0, limit: int = 100) -> list[AmbulanceCrew]:
        query = self.db.query(AmbulanceCrewModel).filter(AmbulanceCrewModel.is_deleted.isnot(True))
        if station_id:
            query = query.filter_by(station_id=station_id)
        query = query.offset(skip).limit(limit)
        return [self._crew_from_model(m) for m in query.all()]

    # ---- Shift Management ----

    def create_shift(self, data: dict[str, Any]) -> CrewShift:
        model = CrewShiftModel(**{k: v for k, v in data.items() if hasattr(CrewShiftModel, k)})
        model.created_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._shift_from_model(model)

    # ---- Triage ----

    def record_triage(self, data: dict[str, Any]) -> TriageAssessment:
        if data.get("ambulatory") and data.get("respiratory_rate", 30) < 30:
            category = TriageCategory.MINOR.value
        elif data.get("respiratory_rate", 0) > 30:
            category = TriageCategory.IMMEDIATE.value
        elif not data.get("ambulatory"):
            category = TriageCategory.DELAYED.value
        else:
            category = TriageCategory.MINOR.value
        data["category"] = category
        model = TriageAssessmentModel(**{k: v for k, v in data.items() if hasattr(TriageAssessmentModel, k)})
        model.assessed_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        triage = self._triage_from_model(model)
        self._emit(create_triage_event(triage))
        return triage

    # ---- ePCR ----

    def create_epcr(self, data: dict[str, Any]) -> ePCR:
        model = ePCRModel(**{k: v for k, v in data.items() if hasattr(ePCRModel, k)})
        model.created_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._epcr_from_model(model)

    def get_epcr(self, epcr_id: str) -> ePCR:
        model = self.db.query(ePCRModel).filter_by(id=epcr_id).first()
        if not model or model.is_deleted:
            raise ePCRNotFoundError()
        return self._epcr_from_model(model)

    def list_epcrs(self, incident_id: str | None = None, skip: int = 0, limit: int = 100) -> list[ePCR]:
        query = self.db.query(ePCRModel).filter(ePCRModel.is_deleted.isnot(True))
        if incident_id:
            query = query.filter_by(incident_id=incident_id)
        query = query.offset(skip).limit(limit)
        return [self._epcr_from_model(m) for m in query.all()]

    def submit_epcr(self, epcr_id: str) -> ePCR:
        model = self.db.query(ePCRModel).filter_by(id=epcr_id).first()
        if not model:
            raise ePCRNotFoundError()
        model.status = "completed"
        model.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return self._epcr_from_model(model)

    # ---- Hospital Status ----

    def update_hospital_status(self, data: dict[str, Any]) -> HospitalStatus:
        facility_id = data.get("facility_id", "")
        existing = self.db.query(HospitalStatusModel).filter_by(facility_id=facility_id).first()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and k not in ("id", "created_at"):
                    setattr(existing, k, v)
            existing.last_updated = datetime.now(UTC)
            model = existing
        else:
            data["last_updated"] = datetime.now(UTC)
            model = HospitalStatusModel(**{k: v for k, v in data.items() if hasattr(HospitalStatusModel, k)})
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._hospital_status_from_model(model)

    def get_nearest_hospitals(self, lat: float, lng: float, limit: int = 10) -> list[dict[str, Any]]:
        hospitals = self.db.query(HospitalStatusModel).filter(
            HospitalStatusModel.diversion_status.isnot(True),
            HospitalStatusModel.available_beds > 0,
        ).limit(limit).all()
        return [self._hospital_status_from_model(h).__dict__ for h in hospitals]

    # ---- Disaster Management ----

    def declare_disaster(self, data: dict[str, Any]) -> DisasterEvent:
        model = DisasterEventModel(**{k: v for k, v in data.items() if hasattr(DisasterEventModel, k)})
        model.declared_at = datetime.now(UTC)
        model.created_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        disaster = self._disaster_from_model(model)
        self._emit(create_disaster_event(disaster))
        return disaster

    def list_disasters(self, phase: str | None = None, skip: int = 0, limit: int = 100) -> list[DisasterEvent]:
        query = self.db.query(DisasterEventModel).filter(DisasterEventModel.is_deleted.isnot(True))
        if phase:
            query = query.filter_by(phase=phase)
        query = query.order_by(DisasterEventModel.severity_level.desc()).offset(skip).limit(limit)
        return [self._disaster_from_model(m) for m in query.all()]

    def create_incident_command(self, data: dict[str, Any]) -> IncidentCommandSystem:
        model = IncidentCommandModel(**{k: v for k, v in data.items() if hasattr(IncidentCommandModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._ics_from_model(model)

    def create_shelter(self, data: dict[str, Any]) -> Shelter:
        model = ShelterModel(**{k: v for k, v in data.items() if hasattr(ShelterModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._shelter_from_model(model)

    # ---- Dashboard ----

    def get_dashboard_stats(self) -> dict[str, Any]:
        active_incidents = self.db.query(EmergencyIncidentModel).filter(
            EmergencyIncidentModel.status.in_(["pending", "dispatched", "en_route", "on_scene", "transporting"]),
        ).count()
        available_ambulances = self.db.query(AmbulanceModel).filter_by(status="available", vehicle_status="active").count()
        on_duty_crew = self.db.query(AmbulanceCrewModel).filter_by(is_available=True, is_active=True).count()
        total_disasters = self.db.query(DisasterEventModel).filter(
            DisasterEventModel.phase.in_(["response", "recovery"]),
        ).count()
        total_today = self.db.query(EmergencyIncidentModel).filter(
            EmergencyIncidentModel.created_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0),
        ).count()
        return {
            "active_incidents": active_incidents,
            "available_ambulances": available_ambulances,
            "on_duty_crew": on_duty_crew,
            "total_disasters": total_disasters,
            "total_today": total_today,
        }

    # ---- Model Mappers ----

    def _incident_from_model(self, model: EmergencyIncidentModel) -> EmergencyIncident:
        return EmergencyIncident(
            id=model.id,
            caller_name=model.caller_name or "",
            caller_phone=model.caller_phone or "",
            caller_relationship=model.caller_relationship or "",
            location_lat=model.location_lat,
            location_lng=model.location_lng,
            location_address=model.location_address or "",
            location_description=model.location_description or "",
            category=model.category or "medical",
            priority=model.priority or "bravo",
            status=model.status or "pending",
            description=model.description or "",
            symptoms=model.symptoms or "",
            patient_count=model.patient_count or 1,
            patient_age=model.patient_age,
            patient_gender=model.patient_gender or "",
            patient_name=model.patient_name or "",
            patient_phone=model.patient_phone or "",
            patient_condition=model.patient_condition or "",
            is_conscious=model.is_conscious if model.is_conscious is not None else True,
            is_breathing=model.is_breathing if model.is_breathing is not None else True,
            has_pulse=model.has_pulse if model.has_pulse is not None else True,
            has_allergies=model.has_allergies or False,
            has_bleeding=model.has_bleeding or False,
            has_chest_pain=model.has_chest_pain or False,
            has_difficulty_breathing=model.has_difficulty_breathing or False,
            is_pregnant=model.is_pregnant or False,
            is_diabetic=model.is_diabetic or False,
            has_seizure=model.has_seizure or False,
            dispatcher_notes=model.dispatcher_notes or "",
            dispatch_time=model.dispatch_time,
            scene_arrival_time=model.scene_arrival_time,
            scene_departure_time=model.scene_departure_time,
            destination_arrival_time=model.destination_arrival_time,
            completion_time=model.completion_time,
            destination_facility_id=model.destination_facility_id or "",
            destination_facility_name=model.destination_facility_name or "",
            destination_type=model.destination_type or "emergency_department",
            incident_command_id=model.incident_command_id or "",
            disaster_event_id=model.disaster_event_id or "",
            mass_casualty_id=model.mass_casualty_id or "",
            created_by=model.created_by or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _dispatch_from_model(self, model: DispatchAssignmentModel) -> DispatchAssignment:
        return DispatchAssignment(id=model.id, incident_id=model.incident_id, ambulance_id=model.ambulance_id or "")

    def _ambulance_from_model(self, model: AmbulanceModel) -> Ambulance:
        return Ambulance(
            id=model.id,
            vehicle_id=model.vehicle_id or "",
            registration_number=model.registration_number or "",
            call_sign=model.call_sign or "",
            type=model.type or "bls",
            status=model.status or "available",
            status_reason=model.status_reason or "",
            current_location_lat=model.current_location_lat,
            current_location_lng=model.current_location_lng,
            current_location_updated=model.current_location_updated,
            station_id=model.station_id or "",
            station_name=model.station_name or "",
            facility_id=model.facility_id or "",
            is_gps_enabled=model.is_gps_enabled if model.is_gps_enabled is not None else True,
            fuel_level=model.fuel_level or 100.0,
            mileage_km=model.mileage_km or 0.0,
            last_maintenance_date=model.last_maintenance_date,
            next_maintenance_due=model.next_maintenance_due,
            vehicle_status=model.vehicle_status or "active",
            equipment_inventory=model.equipment_inventory or {},
        )

    def _crew_from_model(self, model: AmbulanceCrewModel) -> AmbulanceCrew:
        return AmbulanceCrew(
            id=model.id, user_id=model.user_id or "", full_name=model.full_name, role=model.role or "emt",
            is_available=model.is_available if model.is_available is not None else True,
            station_id=model.station_id or "", facility_id=model.facility_id or "",
            certifications=model.certifications or [], phone=model.phone or "",
            is_active=model.is_active if model.is_active is not None else True,
        )

    def _shift_from_model(self, model: CrewShiftModel) -> CrewShift:
        return CrewShift(id=model.id, crew_id=model.crew_id, start_time=model.start_time, end_time=model.end_time)

    def _triage_from_model(self, model: TriageAssessmentModel) -> TriageAssessment:
        return TriageAssessment(
            id=model.id, incident_id=model.incident_id or "", patient_name=model.patient_name or "",
            category=model.category or "minor", system=model.system or "start",
            respiratory_rate=model.respiratory_rate, heart_rate=model.heart_rate,
            systolic_bp=model.systolic_bp, ambulatory=model.ambulatory if model.ambulatory is not None else True,
        )

    def _epcr_from_model(self, model: ePCRModel) -> ePCR:
        return ePCR(
            id=model.id, incident_id=model.incident_id, patient_name=model.patient_name or "",
            status=model.status or "draft", chief_complaint=model.chief_complaint or "",
            narrative=model.narrative or "",
        )

    def _disaster_from_model(self, model: DisasterEventModel) -> DisasterEvent:
        return DisasterEvent(
            id=model.id, event_name=model.event_name, disaster_type=model.disaster_type or "other",
            phase=model.phase or "response", severity_level=model.severity_level or 3,
            location_address=model.location_address or "", region=model.region or "",
            governorate=model.governorate or "", description=model.description or "",
            casualties_count=model.casualties_count or 0, fatalities_count=model.fatalities_count or 0,
            missing_count=model.missing_count or 0, displaced_count=model.displaced_count or 0,
        )

    def _ics_from_model(self, model: IncidentCommandModel) -> IncidentCommandSystem:
        return IncidentCommandSystem(
            id=model.id, disaster_event_id=model.disaster_event_id or "",
            incident_name=model.incident_name or "", command_staff=model.command_staff or {},
            status=model.status or "active",
        )

    def _shelter_from_model(self, model: ShelterModel) -> Shelter:
        return Shelter(
            id=model.id, name=model.name, disaster_event_id=model.disaster_event_id or "",
            capacity=model.capacity or 0, current_occupants=model.current_occupants or 0,
            status=model.status or "active",
        )

    def _hospital_status_from_model(self, model: HospitalStatusModel) -> HospitalStatus:
        return HospitalStatus(
            id=model.id, facility_id=model.facility_id, facility_name=model.facility_name or "",
            total_beds=model.total_beds or 0, available_beds=model.available_beds or 0,
            icu_beds=model.icu_beds or 0, available_icu_beds=model.available_icu_beds or 0,
            ventilators_total=model.ventilators_total or 0, ventilators_available=model.ventilators_available or 0,
            emergency_room_status=model.emergency_room_status or "normal",
            diversion_status=model.diversion_status or False,
        )


def create_incident_event(incident: EmergencyIncident) -> NationalDomainEvent:
    return NationalDomainEvent(
        event_type="ems.incident.created",
        aggregate_type="EmergencyIncident",
        aggregate_id=incident.id,
        payload={"category": incident.category, "priority": incident.priority},
    )


def create_triage_event(triage: TriageAssessment) -> NationalDomainEvent:
    return NationalDomainEvent(
        event_type="ems.triage.performed",
        aggregate_type="TriageAssessment",
        aggregate_id=triage.id,
        payload={"category": triage.category, "incident_id": triage.incident_id},
    )


def create_disaster_event(disaster: DisasterEvent) -> NationalDomainEvent:
    return NationalDomainEvent(
        event_type="ems.disaster.declared",
        aggregate_type="DisasterEvent",
        aggregate_id=disaster.id,
        payload={"disaster_type": disaster.disaster_type, "severity_level": disaster.severity_level},
    )
