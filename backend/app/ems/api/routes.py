from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.ems.application.service import EMSService
from app.ems.exceptions import (
    AmbulanceNotAvailableError,
    AmbulanceNotFoundError,
    IncidentNotFoundError,
    InvalidIncidentStateError,
    ePCRNotFoundError,
)

router = APIRouter(prefix="/ems", tags=["National EMS Platform"])


def _get_service(db: Session = Depends(get_db)) -> EMSService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return EMSService(db=db, event_bus=event_bus)


# ---- Emergency Call Intake / Incidents ----

@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def create_incident(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    incident = service.create_incident(body)
    return _incident_to_dict(incident)


@router.get("/incidents")
async def list_incidents(
    status: str | None = Query(None),
    category: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_incident_to_dict(i) for i in service.list_incidents(status, category, skip, limit)]


@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _incident_to_dict(service.get_incident(incident_id))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _incident_to_dict(service.update_incident_status(incident_id, body.get("status", "")))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidIncidentStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# ---- Dispatch ----

@router.post("/dispatch", status_code=status.HTTP_201_CREATED)
async def dispatch_incident(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        dispatch = service.dispatch_incident(
            incident_id=body.get("incident_id", ""),
            ambulance_id=body.get("ambulance_id", ""),
            crew_ids=body.get("crew_ids"),
        )
        return _dispatch_to_dict(dispatch)
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AmbulanceNotAvailableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# ---- Ambulances ----

@router.post("/ambulances", status_code=status.HTTP_201_CREATED)
async def register_ambulance(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    ambulance = service.register_ambulance(body)
    return _ambulance_to_dict(ambulance)


@router.get("/ambulances")
async def list_ambulances(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_ambulance_to_dict(a) for a in service.list_ambulances(status, skip, limit)]


@router.get("/ambulances/{ambulance_id}")
async def get_ambulance(
    ambulance_id: str,
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _ambulance_to_dict(service.get_ambulance(ambulance_id))
    except AmbulanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/ambulances/{ambulance_id}/location")
async def update_ambulance_location(
    ambulance_id: str,
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _ambulance_to_dict(service.update_ambulance_location(
            ambulance_id, body.get("lat", 0.0), body.get("lng", 0.0),
        ))
    except AmbulanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/ambulances/{ambulance_id}/status")
async def update_ambulance_status(
    ambulance_id: str,
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _ambulance_to_dict(service.update_ambulance_status(
            ambulance_id, body.get("status", ""), body.get("reason", ""),
        ))
    except AmbulanceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# ---- Crew ----

@router.post("/crew", status_code=status.HTTP_201_CREATED)
async def register_crew(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _crew_to_dict(service.register_crew_member(body))


@router.get("/crew")
async def list_crew(
    station_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_crew_to_dict(c) for c in service.list_crew(station_id, skip, limit)]


# ---- Triage ----

@router.post("/triage", status_code=status.HTTP_201_CREATED)
async def record_triage(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _triage_to_dict(service.record_triage(body))


@router.get("/triage/{incident_id}")
async def get_triage(
    incident_id: str,
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_triage_to_dict(t) for t in service.list_triage_by_incident(incident_id)]


# ---- ePCR ----

@router.post("/epcr", status_code=status.HTTP_201_CREATED)
async def create_epcr(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _epcr_to_dict(service.create_epcr(body))


@router.get("/epcr")
async def list_epcrs(
    incident_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_epcr_to_dict(e) for e in service.list_epcrs(incident_id, skip, limit)]


@router.get("/epcr/{epcr_id}")
async def get_epcr(
    epcr_id: str,
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _epcr_to_dict(service.get_epcr(epcr_id))
    except ePCRNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/epcr/{epcr_id}/submit")
async def submit_epcr(
    epcr_id: str,
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _epcr_to_dict(service.submit_epcr(epcr_id))
    except ePCRNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# ---- Hospital Status ----

@router.post("/hospitals/status", status_code=status.HTTP_201_CREATED)
async def update_hospital_status(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _hospital_status_to_dict(service.update_hospital_status(body))


@router.get("/hospitals/nearby")
async def get_nearest_hospitals(
    lat: float = Query(...),
    lng: float = Query(...),
    limit: int = Query(10, ge=1, le=50),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.get_nearest_hospitals(lat, lng, limit)


# ---- Disaster Management ----

@router.post("/disasters", status_code=status.HTTP_201_CREATED)
async def declare_disaster(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _disaster_to_dict(service.declare_disaster(body))


@router.get("/disasters")
async def list_disasters(
    phase: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: EMSService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_disaster_to_dict(d) for d in service.list_disasters(phase, skip, limit)]


# ---- ICS ----

@router.post("/incident-command", status_code=status.HTTP_201_CREATED)
async def create_incident_command(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _ics_to_dict(service.create_incident_command(body))


# ---- Shelters ----

@router.post("/shelters", status_code=status.HTTP_201_CREATED)
async def create_shelter(
    body: dict[str, Any],
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return _shelter_to_dict(service.create_shelter(body))


# ---- Dashboard ----

@router.get("/dashboard")
async def get_dashboard(
    service: EMSService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard_stats()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_ems_platform", "version": "1.0.0"}


# ---- Response Serializers ----

def _incident_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id,
        "caller_name": i.caller_name,
        "caller_phone": i.caller_phone,
        "location_lat": i.location_lat,
        "location_lng": i.location_lng,
        "location_address": i.location_address,
        "location_description": i.location_description,
        "category": i.category,
        "priority": i.priority,
        "status": i.status,
        "description": i.description,
        "symptoms": i.symptoms,
        "patient_count": i.patient_count,
        "patient_age": i.patient_age,
        "patient_gender": i.patient_gender,
        "patient_name": i.patient_name,
        "patient_condition": i.patient_condition,
        "is_conscious": i.is_conscious,
        "is_breathing": i.is_breathing,
        "has_pulse": i.has_pulse,
        "dispatcher_notes": i.dispatcher_notes,
        "dispatch_time": i.dispatch_time.isoformat() if i.dispatch_time else None,
        "scene_arrival_time": i.scene_arrival_time.isoformat() if i.scene_arrival_time else None,
        "destination_arrival_time": i.destination_arrival_time.isoformat() if i.destination_arrival_time else None,
        "destination_facility_id": i.destination_facility_id,
        "destination_facility_name": i.destination_facility_name,
        "destination_type": i.destination_type,
        "disaster_event_id": i.disaster_event_id,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "updated_at": i.updated_at.isoformat() if i.updated_at else None,
    }


def _dispatch_to_dict(d: Any) -> dict[str, Any]:
    return {"id": d.id, "incident_id": d.incident_id, "ambulance_id": d.ambulance_id, "status": d.status.value if hasattr(d.status, "value") else d.status}


def _ambulance_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id, "vehicle_id": a.vehicle_id, "registration_number": a.registration_number,
        "call_sign": a.call_sign, "type": a.type, "status": a.status,
        "current_location_lat": a.current_location_lat, "current_location_lng": a.current_location_lng,
        "station_id": a.station_id, "station_name": a.station_name, "facility_id": a.facility_id,
        "fuel_level": a.fuel_level, "mileage_km": a.mileage_km, "vehicle_status": a.vehicle_status,
        "last_maintenance_date": a.last_maintenance_date.isoformat() if a.last_maintenance_date else None,
        "next_maintenance_due": a.next_maintenance_due.isoformat() if a.next_maintenance_due else None,
    }


def _crew_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id, "user_id": c.user_id, "full_name": c.full_name, "role": c.role,
        "is_available": c.is_available, "station_id": c.station_id, "phone": c.phone,
        "certifications": c.certifications,
    }


def _triage_to_dict(t: Any) -> dict[str, Any]:
    return {
        "id": t.id, "incident_id": t.incident_id, "patient_name": t.patient_name,
        "category": t.category, "system": t.system,
        "respiratory_rate": t.respiratory_rate, "heart_rate": t.heart_rate,
        "systolic_bp": t.systolic_bp, "ambulatory": t.ambulatory,
        "glasgow_coma_scale": t.glasgow_coma_scale, "priority_score": t.priority_score,
        "assessed_at": t.assessed_at.isoformat() if t.assessed_at else None,
    }


def _epcr_to_dict(e: Any) -> dict[str, Any]:
    return {
        "id": e.id, "incident_id": e.incident_id, "patient_name": e.patient_name,
        "chief_complaint": e.chief_complaint, "status": e.status,
        "narrative": e.narrative, "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _disaster_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id, "event_name": d.event_name, "disaster_type": d.disaster_type,
        "phase": d.phase, "severity_level": d.severity_level,
        "location_address": d.location_address, "region": d.region, "governorate": d.governorate,
        "description": d.description, "casualties_count": d.casualties_count,
        "fatalities_count": d.fatalities_count, "missing_count": d.missing_count,
        "displaced_count": d.displaced_count, "declared_state_of_emergency": d.declared_state_of_emergency,
        "declared_at": d.declared_at.isoformat() if d.declared_at else None,
    }


def _ics_to_dict(ics: Any) -> dict[str, Any]:
    return {"id": ics.id, "incident_name": ics.incident_name, "status": ics.status, "command_staff": ics.command_staff}


def _shelter_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id, "name": s.name, "capacity": s.capacity,
        "current_occupants": s.current_occupants, "status": s.status,
    }


def _hospital_status_to_dict(h: Any) -> dict[str, Any]:
    return {
        "id": h.id, "facility_id": h.facility_id, "facility_name": h.facility_name,
        "total_beds": h.total_beds, "available_beds": h.available_beds,
        "icu_beds": h.icu_beds, "available_icu_beds": h.available_icu_beds,
        "ventilators_total": h.ventilators_total, "ventilators_available": h.ventilators_available,
        "emergency_room_status": h.emergency_room_status,
        "trauma_bays_available": h.trauma_bays_available,
        "operating_rooms_available": h.operating_rooms_available,
        "diversion_status": h.diversion_status, "diversion_reason": h.diversion_reason,
        "last_updated": h.last_updated.isoformat() if h.last_updated else None,
    }
