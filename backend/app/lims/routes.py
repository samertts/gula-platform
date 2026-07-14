"""National LIMS API Routes — complete laboratory management API surface.

All routes are prefixed with /lims and follow existing GULA patterns:
  - JWT auth via get_current_user
  - Tenant isolation via lab_id
  - Audit logging via log_action
  - Optimistic locking via version
"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.database import get_db
from app.models.lab_order import LabOrder
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import models as lims_models
from .exceptions import (
    AccessionNumberConflict,
    DeltaCheckFailed,
    DuplicateSpecimenBarcode,
    InstrumentOffline,
    LIMSError,
)
from .fhir_mappers import (
    instrument_to_fhir_device,
    order_to_fhir_service_request,
    report_to_fhir_diagnostic,
    result_to_fhir,
    specimen_to_fhir,
)
from .integration.astm import parse_astm_message
from .integration.hl7 import parse_oru_message
from .services import (
    InstrumentService,
    OrderService,
    QCService,
    ReportService,
    ResultService,
    SpecimenService,
)

router = APIRouter(prefix="/lims", tags=["lims"])


# ===========================================================================
# Pydantic Schemas (inline for route definitions)
# ===========================================================================


class SpecimenRegisterRequest(BaseModel):
    order_id: int
    barcode: str
    specimen_type: str
    container_type: str | None = None
    volume_ml: float | None = None
    clinical_info: str | None = None


class SpecimenTransitionRequest(BaseModel):
    target_status: str
    notes: str | None = None
    rejection_reason: str | None = None


class OrderCreateRequest(BaseModel):
    order_id: int
    accession_number: str
    priority: str = "routine"
    clinical_note: str | None = None
    diagnosis_code: str | None = None


class ResultCreateRequest(BaseModel):
    specimen_id: int
    test_code: str
    test_name: str
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    instrument_id: int | None = None
    loinc_code: str | None = None


class ResultValidateRequest(BaseModel):
    notes: str | None = None
    signature_hash: str | None = None
    action: str = "validate"   # validate, reject, flag


class IQCRunRequest(BaseModel):
    program_id: int
    test_code: str
    measured_value: float
    expected_value: float
    sd: float
    level: str = "normal"
    lot_number: str | None = None
    instrument_id: int | None = None
    notes: str | None = None


class InstrumentCreateRequest(BaseModel):
    model_id: int
    instrument_code: str
    serial_number: str | None = None
    workstation_id: int | None = None
    ip_address: str | None = None
    port: int | None = None


class MaintenanceRecordRequest(BaseModel):
    maintenance_type: str
    title: str
    description: str | None = None
    performed_at: datetime | None = None
    cost: float | None = None
    notes: str | None = None


class CalibrationRecordRequest(BaseModel):
    calibration_type: str
    calibrator_lot: str | None = None
    passed: bool | None = None
    notes: str | None = None


class InventoryRequest(BaseModel):
    code: str
    name: str
    name_ar: str | None = None
    current_quantity: float
    unit: str
    minimum_quantity: float | None = None
    supplier_id: int | None = None
    storage_location: str | None = None


class ReportGenerateRequest(BaseModel):
    order_id: int
    report_number: str
    locale: str = "ar"
    title: str | None = None
    title_ar: str | None = None


class DeviceMessageRequest(BaseModel):
    instrument_id: int
    raw_message: str


class ASTMResultResponse(BaseModel):
    specimen_id: str
    test_code: str
    value: str
    unit: str
    flag: str


# ===========================================================================
# Helper: extract lab_id from current user
# ===========================================================================


def _lab_id(current_user: LabUser) -> int:
    return current_user.lab_id


def _list_to_dict(qs, exclude: set | None = None) -> list[dict]:
    return [{k: v for k, v in row.__dict__.items() if not k.startswith("_") and (exclude is None or k not in exclude)} for row in qs]


# ===========================================================================
# DEPARTMENTS, SECTIONS, WORKSTATIONS
# ===========================================================================


@router.get("/departments")
def list_departments(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    depts = db.query(lims_models.Department).filter(
        lims_models.Department.lab_id == _lab_id(current_user),
        lims_models.Department.is_deleted == False,
    ).order_by(lims_models.Department.sort_order).all()
    return {"departments": _list_to_dict(depts)}


@router.post("/departments", status_code=201)
def create_department(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    dept = lims_models.Department(
        lab_id=_lab_id(current_user),
        code=data.get("code"),
        name=data.get("name"),
        name_ar=data.get("name_ar"),
        description=data.get("description"),
        created_by=current_user.id,
    )
    db.add(dept)
    db.flush()
    log_action(db, "create", "lims_department", dept.id, current_user.id, current_user.role, f"Department {dept.code} created")
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/sections")
def list_sections(
    department_id: int | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Section).filter(lims_models.Section.is_deleted == False)
    if department_id:
        q = q.filter(lims_models.Section.department_id == department_id)
    return {"sections": _list_to_dict(q.all())}


@router.get("/workstations")
def list_workstations(
    section_id: int | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Workstation).filter(lims_models.Workstation.is_deleted == False)
    if section_id:
        q = q.filter(lims_models.Workstation.section_id == section_id)
    return {"workstations": _list_to_dict(q.all())}


# ===========================================================================
# INSTRUMENTS / ANALYZERS
# ===========================================================================


@router.get("/instruments")
def list_instruments(
    status: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.lab_id == _lab_id(current_user),
        lims_models.Instrument.is_deleted == False,
    )
    if status:
        q = q.filter(lims_models.Instrument.status == status)
    instruments = q.order_by(lims_models.Instrument.instrument_code).all()

    result = []
    for inst in instruments:
        d = {k: v for k, v in inst.__dict__.items() if not k.startswith("_")}
        if inst.model:
            d["model_name"] = inst.model.model_name
            if inst.model.manufacturer:
                d["manufacturer"] = inst.model.manufacturer.name
        result.append(d)
    return {"instruments": result}


@router.post("/instruments", status_code=201)
def create_instrument(
    data: InstrumentCreateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.lab_id == _lab_id(current_user),
        lims_models.Instrument.instrument_code == data.instrument_code,
    ).first()
    if existing:
        raise HTTPException(409, detail="Instrument code already exists")

    inst = lims_models.Instrument(
        lab_id=_lab_id(current_user),
        model_id=data.model_id,
        instrument_code=data.instrument_code,
        serial_number=data.serial_number,
        workstation_id=data.workstation_id,
        ip_address=data.ip_address,
        port=data.port,
        created_by=current_user.id,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


@router.get("/instruments/{instrument_id}")
def get_instrument(
    instrument_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")
    return inst


@router.post("/instruments/{instrument_id}/online")
def instrument_online(
    instrument_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = InstrumentService.mark_online(db, instrument_id)
    if not inst or inst.lab_id != _lab_id(current_user):
        raise HTTPException(404, detail="Instrument not found")
    db.commit()
    return {"status": "online", "instrument_id": instrument_id}


@router.post("/instruments/{instrument_id}/offline")
def instrument_offline(
    instrument_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = InstrumentService.mark_offline(db, instrument_id)
    if not inst or inst.lab_id != _lab_id(current_user):
        raise HTTPException(404, detail="Instrument not found")
    db.commit()
    return {"status": "offline", "instrument_id": instrument_id}


@router.post("/instruments/{instrument_id}/maintenance", status_code=201)
def record_maintenance(
    instrument_id: int,
    data: MaintenanceRecordRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify instrument belongs to lab
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")

    maint = InstrumentService.record_maintenance(
        db, instrument_id, data.maintenance_type, data.title,
        performed_by=current_user.id,
        description=data.description,
        cost=data.cost,
        notes=data.notes,
    )
    db.commit()
    db.refresh(maint)
    return maint


@router.post("/instruments/{instrument_id}/calibrations", status_code=201)
def record_calibration(
    instrument_id: int,
    data: CalibrationRecordRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")

    cal = InstrumentService.record_calibration(
        db, instrument_id, data.calibration_type,
        performed_by=current_user.id,
        passed=data.passed,
        calibrator_lot=data.calibrator_lot,
        notes=data.notes,
    )
    db.commit()
    db.refresh(cal)
    return cal


@router.get("/instruments/{instrument_id}/fhir")
def instrument_fhir(
    instrument_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")
    return instrument_to_fhir_device(inst)


# ===========================================================================
# MANUFACTURERS & MODELS
# ===========================================================================


@router.get("/manufacturers")
def list_manufacturers(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mfrs = db.query(lims_models.Manufacturer).filter(
        lims_models.Manufacturer.is_deleted == False,
    ).order_by(lims_models.Manufacturer.name).all()
    return {"manufacturers": _list_to_dict(mfrs)}


@router.post("/manufacturers", status_code=201)
def create_manufacturer(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mfr = lims_models.Manufacturer(
        code=data.get("code"),
        name=data.get("name"),
        name_ar=data.get("name_ar"),
        created_by=current_user.id,
    )
    db.add(mfr)
    db.commit()
    db.refresh(mfr)
    return mfr


@router.get("/instrument-models")
def list_instrument_models(
    manufacturer_id: int | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.InstrumentModel).filter(
        lims_models.InstrumentModel.is_deleted == False,
    )
    if manufacturer_id:
        q = q.filter(lims_models.InstrumentModel.manufacturer_id == manufacturer_id)
    models = q.all()
    result = []
    for m in models:
        d = {k: v for k, v in m.__dict__.items() if not k.startswith("_")}
        if m.manufacturer:
            d["manufacturer_name"] = m.manufacturer.name
        result.append(d)
    return {"models": result}


# ===========================================================================
# SPECIMENS
# ===========================================================================


@router.post("/specimens", status_code=201)
def register_specimen(
    data: SpecimenRegisterRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        specimen = SpecimenService.register(
            db, data.order_id, _lab_id(current_user),
            data.specimen_type, data.barcode, current_user.id,
            container_type=data.container_type,
            volume_ml=data.volume_ml,
            clinical_info=data.clinical_info,
        )
    except DuplicateSpecimenBarcode as e:
        raise HTTPException(409, detail=str(e))

    db.commit()
    db.refresh(specimen)
    return specimen


@router.get("/specimens")
def list_specimens(
    status: str | None = None,
    order_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.lab_id == _lab_id(current_user),
        lims_models.Specimen.is_deleted == False,
    )
    if status:
        q = q.filter(lims_models.Specimen.status == status)
    if order_id:
        q = q.filter(lims_models.Specimen.order_id == order_id)

    total = q.count()
    specimens = q.order_by(lims_models.Specimen.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "specimens": _list_to_dict(specimens)}


@router.get("/specimens/{barcode}")
def get_specimen_by_barcode(
    barcode: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    specimen = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.barcode == barcode,
        lims_models.Specimen.lab_id == _lab_id(current_user),
    ).first()
    if not specimen:
        raise HTTPException(404, detail="Specimen not found")
    return specimen


@router.put("/specimens/{specimen_id}/status")
def transition_specimen(
    specimen_id: int,
    data: SpecimenTransitionRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    specimen = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.id == specimen_id,
        lims_models.Specimen.lab_id == _lab_id(current_user),
    ).first()
    if not specimen:
        raise HTTPException(404, detail="Specimen not found")

    try:
        if data.rejection_reason:
            specimen = SpecimenService.reject(db, specimen, data.rejection_reason, current_user.id)
        else:
            specimen = SpecimenService.transition(db, specimen, data.target_status, current_user.id, data.notes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

    db.commit()
    db.refresh(specimen)
    return specimen


@router.get("/specimens/{specimen_id}/fhir")
def specimen_fhir(
    specimen_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    specimen = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.id == specimen_id,
        lims_models.Specimen.lab_id == _lab_id(current_user),
    ).first()
    if not specimen:
        raise HTTPException(404, detail="Specimen not found")
    return specimen_to_fhir(specimen)


# ===========================================================================
# ORDERS (LIMS Extension)
# ===========================================================================


@router.post("/orders", status_code=201)
def create_lims_order(
    data: OrderCreateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify base order exists
    base_order = db.query(LabOrder).filter(
        LabOrder.id == data.order_id,
        LabOrder.lab_id == _lab_id(current_user),
    ).first()
    if not base_order:
        raise HTTPException(404, detail="Base order not found")

    try:
        lims_order = OrderService.create_lims_order(
            db, data.order_id, _lab_id(current_user), current_user.id,
            data.accession_number, data.priority,
            clinical_note=data.clinical_note,
            diagnosis_code=data.diagnosis_code,
        )
    except AccessionNumberConflict as e:
        raise HTTPException(409, detail=str(e))

    db.commit()
    db.refresh(lims_order)
    return lims_order


@router.get("/orders")
def list_lims_orders(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Order).filter(
        lims_models.Order.lab_id == _lab_id(current_user),
        lims_models.Order.is_deleted == False,
    )
    if status:
        q = q.filter(lims_models.Order.order_status == status)

    total = q.count()
    orders = q.order_by(lims_models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "orders": _list_to_dict(orders)}


@router.get("/orders/{order_id}")
def get_lims_order(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lims_order = db.query(lims_models.Order).filter(
        lims_models.Order.id == order_id,
        lims_models.Order.lab_id == _lab_id(current_user),
    ).first()
    if not lims_order:
        raise HTTPException(404, detail="LIMS order not found")
    return lims_order


@router.put("/orders/{order_id}/status")
def transition_order(
    order_id: int,
    data: SpecimenTransitionRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lims_order = db.query(lims_models.Order).filter(
        lims_models.Order.id == order_id,
        lims_models.Order.lab_id == _lab_id(current_user),
    ).first()
    if not lims_order:
        raise HTTPException(404, detail="LIMS order not found")

    try:
        lims_order = OrderService.transition(db, lims_order, data.target_status, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

    db.commit()
    db.refresh(lims_order)
    return lims_order


@router.get("/orders/{order_id}/fhir")
def order_fhir(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lims_order = db.query(lims_models.Order).filter(
        lims_models.Order.id == order_id,
        lims_models.Order.lab_id == _lab_id(current_user),
    ).first()
    if not lims_order:
        raise HTTPException(404, detail="LIMS order not found")
    return order_to_fhir_service_request(lims_order)


# ===========================================================================
# PANELS
# ===========================================================================


@router.get("/panels")
def list_panels(
    category: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Panel).filter(
        lims_models.Panel.lab_id == _lab_id(current_user),
        lims_models.Panel.is_deleted == False,
    )
    if category:
        q = q.filter(lims_models.Panel.category == category)

    panels = q.order_by(lims_models.Panel.name).all()
    result = []
    for p in panels:
        d = {k: v for k, v in p.__dict__.items() if not k.startswith("_")}
        tests = db.query(lims_models.PanelTest).filter(
            lims_models.PanelTest.panel_id == p.id,
        ).order_by(lims_models.PanelTest.display_order).all()
        d["tests"] = [{"test_code": t.test_code, "display_order": t.display_order} for t in tests]
        result.append(d)
    return {"panels": result}


@router.post("/panels", status_code=201)
def create_panel(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    panel = lims_models.Panel(
        lab_id=_lab_id(current_user),
        code=data.get("code"),
        name=data.get("name"),
        name_ar=data.get("name_ar"),
        category=data.get("category"),
        description=data.get("description"),
        tat_target_minutes=data.get("tat_target_minutes"),
        created_by=current_user.id,
    )
    db.add(panel)
    db.flush()

    # Add panel tests
    tests = data.get("tests", [])
    for i, tc in enumerate(tests):
        pt = lims_models.PanelTest(
            panel_id=panel.id,
            test_code=tc if isinstance(tc, str) else tc.get("test_code"),
            display_order=i,
        )
        db.add(pt)

    db.commit()
    db.refresh(panel)
    return panel


# ===========================================================================
# RESULTS
# ===========================================================================


@router.post("/results", status_code=201)
def create_result(
    data: ResultCreateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify specimen belongs to lab
    specimen = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.id == data.specimen_id,
        lims_models.Specimen.lab_id == _lab_id(current_user),
    ).first()
    if not specimen:
        raise HTTPException(404, detail="Specimen not found")

    result = ResultService.create_result(
        db, data.specimen_id, specimen.order_id,
        _lab_id(current_user), data.test_code, data.test_name,
        current_user.id,
        value_numeric=data.value_numeric,
        value_text=data.value_text,
        unit=data.unit,
        instrument_id=data.instrument_id,
        loinc_code=data.loinc_code,
    )
    db.commit()
    db.refresh(result)
    return result


@router.get("/results")
def list_results(
    specimen_id: int | None = None,
    order_id: int | None = None,
    test_code: str | None = None,
    validation_status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Result).filter(
        lims_models.Result.lab_id == _lab_id(current_user),
        lims_models.Result.is_deleted == False,
    )
    if specimen_id:
        q = q.filter(lims_models.Result.specimen_id == specimen_id)
    if order_id:
        q = q.filter(lims_models.Result.order_id == order_id)
    if test_code:
        q = q.filter(lims_models.Result.test_code == test_code)
    if validation_status:
        q = q.filter(lims_models.Result.validation_status == validation_status)

    total = q.count()
    results = q.order_by(lims_models.Result.created_at.desc()).offset(skip).limit(limit).all()

    data = []
    for r in results:
        d = {k: v for k, v in r.__dict__.items() if not k.startswith("_")}
        if r.instrument:
            d["instrument_code"] = r.instrument.instrument_code
        data.append(d)
    return {"total": total, "results": data}


@router.get("/results/{result_id}")
def get_result(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.query(lims_models.Result).filter(
        lims_models.Result.id == result_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).first()
    if not result:
        raise HTTPException(404, detail="Result not found")
    return result


@router.post("/results/{result_id}/validate")
def validate_result(
    result_id: int,
    data: ResultValidateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.query(lims_models.Result).filter(
        lims_models.Result.id == result_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).first()
    if not result:
        raise HTTPException(404, detail="Result not found")

    if data.action == "validate":
        result = ResultService.validate_manually(
            db, result, current_user.id, data.notes, data.signature_hash,
        )
    elif data.action == "reject":
        result.validation_status = "rejected"
        result.updated_by = current_user.id
    elif data.action == "flag":
        result.validation_status = "flagged"
        result.updated_by = current_user.id

    db.commit()
    db.refresh(result)
    return result


@router.post("/results/{result_id}/release")
def release_result(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.query(lims_models.Result).filter(
        lims_models.Result.id == result_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).first()
    if not result:
        raise HTTPException(404, detail="Result not found")

    release = ResultService.release(db, result, current_user.id)
    # Update the specimen status to released
    specimen = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.id == result.specimen_id,
    ).first()
    if specimen:
        from .state_machine import enforce_specimen_transition
        try:
            SpecimenService.transition(db, specimen, "released", current_user.id)
        except Exception:
            pass  # Already in released or later state

    db.commit()
    return release


@router.get("/results/{result_id}/fhir")
def result_fhir(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.query(lims_models.Result).filter(
        lims_models.Result.id == result_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).first()
    if not result:
        raise HTTPException(404, detail="Result not found")
    return result_to_fhir(result)


# ===========================================================================
# QUALITY CONTROL
# ===========================================================================


@router.post("/qc/run", status_code=201)
def run_iqc(
    data: IQCRunRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = QCService.run_iqc(
        db, _lab_id(current_user), data.program_id, data.test_code,
        data.measured_value, data.expected_value, data.sd,
        current_user.id, data.level, data.lot_number,
        data.instrument_id, data.notes,
    )
    db.commit()
    return result


@router.get("/qc/results")
def list_qc_results(
    test_code: str | None = None,
    instrument_id: int | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.IQC).filter(
        lims_models.IQC.lab_id == _lab_id(current_user),
    )
    if test_code:
        q = q.filter(lims_models.IQC.test_code == test_code)
    if instrument_id:
        q = q.filter(lims_models.IQC.instrument_id == instrument_id)
    if status:
        q = q.filter(lims_models.IQC.status == status)

    results = q.order_by(lims_models.IQC.performed_at.desc()).limit(limit).all()
    return {"results": _list_to_dict(results)}


@router.get("/qc/programs")
def list_qc_programs(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    programs = db.query(lims_models.QCProgram).filter(
        lims_models.QCProgram.lab_id == _lab_id(current_user),
        lims_models.QCProgram.is_deleted == False,
    ).all()
    return {"programs": _list_to_dict(programs)}


@router.post("/qc/programs", status_code=201)
def create_qc_program(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    program = lims_models.QCProgram(
        lab_id=_lab_id(current_user),
        code=data.get("code"),
        name=data.get("name"),
        program_type=data.get("program_type", "iqc"),
        test_code=data.get("test_code"),
        instrument_id=data.get("instrument_id"),
        frequency=data.get("frequency"),
        created_by=current_user.id,
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


# ===========================================================================
# QC Levey-Jennings Statistics
# ===========================================================================


@router.get("/qc/statistics/{test_code}")
def qc_statistics(
    test_code: str,
    instrument_id: int | None = None,
    days: int = 90,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta
    cutoff = datetime.now(UTC) - timedelta(days=days)

    q = db.query(lims_models.IQC).filter(
        lims_models.IQC.lab_id == _lab_id(current_user),
        lims_models.IQC.test_code == test_code,
        lims_models.IQC.performed_at >= cutoff,
    )
    if instrument_id:
        q = q.filter(lims_models.IQC.instrument_id == instrument_id)

    iqc_results = q.order_by(lims_models.IQC.performed_at.asc()).all()
    values = [r.measured_value for r in iqc_results if r.measured_value is not None]

    from .quality import calculate_lj_statistics, calculate_lj_limits
    stats = calculate_lj_statistics(values)
    limits = calculate_lj_limits(stats["mean"], stats["sd"]) if stats["n"] > 1 else {}

    return {
        "test_code": test_code,
        "statistics": stats,
        "limits": limits,
        "data_points": [
            {"value": r.measured_value, "performed_at": r.performed_at.isoformat(), "status": r.status}
            for r in iqc_results
        ],
    }


# ===========================================================================
# ISO 15189 Quality Indicators
# ===========================================================================


@router.get("/quality/indicators")
def list_quality_indicators():
    from .quality import ISO_15189_INDICATORS, CAP_INDICATORS

    return {
        "iso_15189": [
            {"id": k, **v} for k, v in ISO_15189_INDICATORS.items()
        ],
        "cap": [
            {"id": k, **v} for k, v in CAP_INDICATORS.items()
        ],
    }


@router.post("/quality/indicators/{indicator_id}/evaluate")
def evaluate_indicator(
    indicator_id: str,
    value: float = Query(...),
):
    from .quality import evaluate_iso_15189_indicator
    try:
        return evaluate_iso_15189_indicator(indicator_id, value)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


# ===========================================================================
# INVENTORY
# ===========================================================================


@router.get("/reagents")
def list_reagents(
    low_stock: bool = False,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Reagent).filter(
        lims_models.Reagent.lab_id == _lab_id(current_user),
        lims_models.Reagent.is_deleted == False,
    )
    if low_stock:
        q = q.filter(lims_models.Reagent.current_quantity <= lims_models.Reagent.minimum_quantity)

    reagents = q.order_by(lims_models.Reagent.reagent_name).all()
    return {"reagents": _list_to_dict(reagents)}


@router.post("/reagents", status_code=201)
def create_reagent(
    data: InventoryRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reagent = lims_models.Reagent(
        lab_id=_lab_id(current_user),
        reagent_code=data.code,
        reagent_name=data.name,
        reagent_name_ar=data.name_ar,
        current_quantity=data.current_quantity,
        unit=data.unit,
        minimum_quantity=data.minimum_quantity,
        supplier_id=data.supplier_id,
        storage_location=data.storage_location,
        created_by=current_user.id,
    )
    db.add(reagent)
    db.commit()
    db.refresh(reagent)
    return reagent


@router.put("/reagents/{reagent_id}/stock")
def update_reagent_stock(
    reagent_id: int,
    quantity_change: float = Query(...),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reagent = db.query(lims_models.Reagent).filter(
        lims_models.Reagent.id == reagent_id,
        lims_models.Reagent.lab_id == _lab_id(current_user),
    ).first()
    if not reagent:
        raise HTTPException(404, detail="Reagent not found")

    reagent.current_quantity += quantity_change
    reagent.updated_by = current_user.id
    reagent.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(reagent)
    return reagent


@router.get("/consumables")
def list_consumables(
    low_stock: bool = False,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.Consumable).filter(
        lims_models.Consumable.lab_id == _lab_id(current_user),
        lims_models.Consumable.is_deleted == False,
    )
    if low_stock:
        q = q.filter(lims_models.Consumable.current_quantity <= lims_models.Consumable.minimum_quantity)
    return {"consumables": _list_to_dict(q.all())}


@router.get("/lots")
def list_lots(
    expiring_within_days: int | None = None,
    item_type: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta
    q = db.query(lims_models.Lot).filter(
        lims_models.Lot.lab_id == _lab_id(current_user),
        lims_models.Lot.is_deleted == False,
    )
    if item_type:
        q = q.filter(lims_models.Lot.item_type == item_type)
    if expiring_within_days:
        cutoff = datetime.now(UTC).date() + timedelta(days=expiring_within_days)
        q = q.filter(lims_models.Lot.expiry_at <= cutoff, lims_models.Lot.expiry_at >= datetime.now(UTC).date())

    return {"lots": _list_to_dict(q.all())}


@router.get("/suppliers")
def list_suppliers(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    suppliers = db.query(lims_models.Supplier).filter(
        lims_models.Supplier.lab_id == _lab_id(current_user),
        lims_models.Supplier.is_deleted == False,
    ).all()
    return {"suppliers": _list_to_dict(suppliers)}


@router.get("/storage")
def list_storage(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    storage = db.query(lims_models.Storage).filter(
        lims_models.Storage.lab_id == _lab_id(current_user),
        lims_models.Storage.is_deleted == False,
    ).all()
    return {"storage": _list_to_dict(storage)}


@router.post("/storage/temperature", status_code=201)
def record_temperature(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    temp = lims_models.TemperatureLog(
        lab_id=_lab_id(current_user),
        storage_id=data.get("storage_id"),
        temperature=data.get("temperature"),
        recorded_at=datetime.now(UTC),
        recorded_by=current_user.id,
        is_breach=data.get("is_breach", False),
    )
    db.add(temp)
    db.commit()
    return temp


# ===========================================================================
# REFERENCE RANGES
# ===========================================================================


@router.get("/reference-ranges")
def list_reference_ranges(
    test_code: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.ReferenceRangeDef).filter(
        lims_models.ReferenceRangeDef.is_deleted == False,
    )
    if test_code:
        q = q.filter(lims_models.ReferenceRangeDef.test_code == test_code)
    return {"reference_ranges": _list_to_dict(q.all())}


@router.post("/reference-ranges", status_code=201)
def create_reference_range(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rr = lims_models.ReferenceRangeDef(
        test_code=data.get("test_code"),
        lab_id=_lab_id(current_user),
        gender=data.get("gender"),
        age_min_days=data.get("age_min_days"),
        age_max_days=data.get("age_max_days"),
        ref_range_low=data.get("ref_range_low"),
        ref_range_high=data.get("ref_range_high"),
        critical_low=data.get("critical_low"),
        critical_high=data.get("critical_high"),
        unit=data.get("unit"),
        created_by=current_user.id,
    )
    db.add(rr)
    db.commit()
    db.refresh(rr)
    return rr


# ===========================================================================
# AUTO-VALIDATION & DELTA CHECK RULES
# ===========================================================================


@router.get("/auto-validation-rules")
def list_auto_validation_rules(
    test_code: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.AutoValidationRule).filter(
        lims_models.AutoValidationRule.lab_id == _lab_id(current_user),
        lims_models.AutoValidationRule.is_deleted == False,
    )
    if test_code:
        q = q.filter(lims_models.AutoValidationRule.test_code == test_code)
    return {"rules": _list_to_dict(q.all())}


@router.post("/auto-validation-rules", status_code=201)
def create_auto_validation_rule(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = lims_models.AutoValidationRule(
        lab_id=_lab_id(current_user),
        rule_name=data.get("rule_name"),
        test_code=data.get("test_code"),
        rule_type=data.get("rule_type", "range"),
        conditions=data.get("conditions", {}),
        action=data.get("action", "validate"),
        priority=data.get("priority", 0),
        created_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/delta-check-rules")
def list_delta_check_rules(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rules = db.query(lims_models.DeltaCheckRule).filter(
        lims_models.DeltaCheckRule.lab_id == _lab_id(current_user),
        lims_models.DeltaCheckRule.is_deleted == False,
    ).all()
    return {"rules": _list_to_dict(rules)}


# ===========================================================================
# REPORTS
# ===========================================================================


@router.post("/reports", status_code=201)
def generate_report(
    data: ReportGenerateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = ReportService.generate_report(
        db, data.order_id, _lab_id(current_user), data.report_number,
        current_user.id, data.locale,
        title=data.title, title_ar=data.title_ar,
    )
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports")
def list_reports(
    status: str | None = None,
    order_id: int | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(lims_models.LabReport).filter(
        lims_models.LabReport.lab_id == _lab_id(current_user),
        lims_models.LabReport.is_deleted == False,
    )
    if status:
        q = q.filter(lims_models.LabReport.status == status)
    if order_id:
        q = q.filter(lims_models.LabReport.order_id == order_id)
    return {"reports": _list_to_dict(q.all())}


@router.get("/reports/{report_id}")
def get_report(
    report_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(lims_models.LabReport).filter(
        lims_models.LabReport.id == report_id,
        lims_models.LabReport.lab_id == _lab_id(current_user),
    ).first()
    if not report:
        raise HTTPException(404, detail="Report not found")
    return report


@router.post("/reports/{report_id}/finalize")
def finalize_report(
    report_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(lims_models.LabReport).filter(
        lims_models.LabReport.id == report_id,
        lims_models.LabReport.lab_id == _lab_id(current_user),
    ).first()
    if not report:
        raise HTTPException(404, detail="Report not found")

    report = ReportService.finalize(db, report, current_user.id)
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/correct")
def correct_report(
    report_id: int,
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(lims_models.LabReport).filter(
        lims_models.LabReport.id == report_id,
        lims_models.LabReport.lab_id == _lab_id(current_user),
    ).first()
    if not report:
        raise HTTPException(404, detail="Report not found")

    report = ReportService.correct(db, report, data.get("reason", ""), current_user.id)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/fhir")
def report_fhir(
    report_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(lims_models.LabReport).filter(
        lims_models.LabReport.id == report_id,
        lims_models.LabReport.lab_id == _lab_id(current_user),
    ).first()
    if not report:
        raise HTTPException(404, detail="Report not found")

    # Get associated results
    results = db.query(lims_models.Result).filter(
        lims_models.Result.order_id == report.order_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).all()

    return report_to_fhir_diagnostic(report, results)


# ===========================================================================
# DEVICE INTEGRATION (ASTM/HL7)
# ===========================================================================


@router.post("/integration/astm/receive")
def receive_astm(
    data: DeviceMessageRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive and parse an ASTM E1394 message from an instrument."""
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == data.instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")

    results = parse_astm_message(data.raw_message)
    return {
        "parsed_results": [
            {"specimen_id": r.specimen_id, "test_code": r.test_code,
             "value": r.value, "unit": r.unit, "flag": r.flag}
            for r in results
        ],
        "count": len(results),
    }


@router.post("/integration/hl7/receive")
def receive_hl7(
    data: DeviceMessageRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive and parse an HL7 ORU^R01 message from an instrument."""
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == data.instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")

    results = parse_oru_message(data.raw_message)
    return {
        "parsed_results": [
            {"specimen_id": r.specimen_id, "test_code": r.test_code,
             "value": r.value, "unit": r.unit, "abnormal_flag": r.abnormal_flag}
            for r in results
        ],
        "count": len(results),
    }


@router.post("/integration/simulate")
def simulate_device_message(
    instrument_id: int = Query(...),
    protocol: str = Query("astm"),
    test_codes: str | None = Query(None),
    inject_error: bool = False,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simulate a device message for testing."""
    inst = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.id == instrument_id,
        lims_models.Instrument.lab_id == _lab_id(current_user),
    ).first()
    if not inst:
        raise HTTPException(404, detail="Instrument not found")

    codes = test_codes.split(",") if test_codes else None

    from .integration.simulator import generate_astm_message, generate_hl7_message

    if protocol == "astm":
        raw = generate_astm_message(test_codes=codes, inject_error=inject_error)
        parsed = parse_astm_message(raw)
    elif protocol == "hl7":
        raw = generate_hl7_message(test_codes=codes, inject_error=inject_error)
        parsed = parse_oru_message(raw)
    else:
        raise HTTPException(400, detail=f"Unsupported protocol: {protocol}")

    return {
        "protocol": protocol,
        "raw_message": raw,
        "parsed": [
            {"specimen_id": r.specimen_id if hasattr(r, "specimen_id") else getattr(r, "specimen_id", ""),
             "test_code": r.test_code, "value": r.value}
            for r in parsed
        ],
    }


# ===========================================================================
# WORKFLOW-LEVEL OPERATIONS
# ===========================================================================


@router.post("/workflows/auto-validate")
def run_auto_validation(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger auto-validation workflow for a result."""
    result = db.query(lims_models.Result).filter(
        lims_models.Result.id == result_id,
        lims_models.Result.lab_id == _lab_id(current_user),
    ).first()
    if not result:
        raise HTTPException(404, detail="Result not found")

    from .workflows import auto_validate_result
    validation = auto_validate_result(
        db, result.value_numeric, result.test_code,
        lab_id=result.lab_id,
        instrument_id=result.instrument_id,
    )

    if validation["auto_validated"]:
        result.validation_status = "auto_validated"
        result.auto_validated = True
        result.auto_validated_at = datetime.now(UTC)
        db.commit()

    return validation


@router.post("/workflows/critical-result/{result_id}")
def process_critical_alert(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process a critical result alert."""
    from .workflows import process_critical_result
    result = process_critical_result(db, result_id, _lab_id(current_user), current_user.id)
    return result


# ===========================================================================
# ELECTRONIC SIGNATURES
# ===========================================================================


@router.post("/electronic-signatures", status_code=201)
def create_electronic_signature(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sig = lims_models.ElectronicSignature(
        lab_id=_lab_id(current_user),
        user_id=current_user.id,
        signature_type=data.get("signature_type", "validation"),
        resource_type=data.get("resource_type"),
        resource_id=data.get("resource_id"),
        signature_hash=data.get("signature_hash"),
        signed_at=datetime.now(UTC),
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


# ===========================================================================
# CHAIN OF CUSTODY
# ===========================================================================


@router.post("/chain-of-custody", status_code=201)
def record_chain_of_custody(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coc = lims_models.ChainOfCustody(
        specimen_id=data.get("specimen_id"),
        event_type=data.get("event_type"),
        from_person=data.get("from_person"),
        to_person=data.get("to_person"),
        timestamp=datetime.now(UTC),
        reason=data.get("reason"),
        signature=data.get("signature"),
        created_by=current_user.id,
    )
    db.add(coc)
    db.commit()
    db.refresh(coc)
    return coc


# ===========================================================================
# DASHBOARD / OVERVIEW
# ===========================================================================


@router.get("/dashboard")
def lims_dashboard(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab_id = _lab_id(current_user)

    specimens_total = db.query(lims_models.Specimen).filter(
        lims_models.Specimen.lab_id == lab_id,
        lims_models.Specimen.is_deleted == False,
    ).count()

    specimens_by_status = {}
    for status_val in ["collected", "received", "processing", "analyzing", "analyzed", "released"]:
        specimens_by_status[status_val] = db.query(lims_models.Specimen).filter(
            lims_models.Specimen.lab_id == lab_id,
            lims_models.Specimen.status == status_val,
        ).count()

    results_pending_validation = db.query(lims_models.Result).filter(
        lims_models.Result.lab_id == lab_id,
        lims_models.Result.validation_status == "pending",
    ).count()

    results_critical = db.query(lims_models.Result).filter(
        lims_models.Result.lab_id == lab_id,
        lims_models.Result.is_critical == True,
    ).count()

    instruments_online = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.lab_id == lab_id,
        lims_models.Instrument.status == "online",
    ).count()

    instruments_total = db.query(lims_models.Instrument).filter(
        lims_models.Instrument.lab_id == lab_id,
        lims_models.Instrument.is_deleted == False,
    ).count()

    qc_warnings = db.query(lims_models.IQC).filter(
        lims_models.IQC.lab_id == lab_id,
        lims_models.IQC.status.in_(["warning", "out_of_control"]),
    ).count()

    low_stock = db.query(lims_models.Reagent).filter(
        lims_models.Reagent.lab_id == lab_id,
        lims_models.Reagent.current_quantity <= lims_models.Reagent.minimum_quantity,
    ).count()

    return {
        "specimens": {
            "total": specimens_total,
            "by_status": specimens_by_status,
        },
        "results": {
            "pending_validation": results_pending_validation,
            "critical": results_critical,
        },
        "instruments": {
            "total": instruments_total,
            "online": instruments_online,
        },
        "quality": {
            "qc_warnings": qc_warnings,
        },
        "inventory": {
            "low_stock_items": low_stock,
        },
    }
