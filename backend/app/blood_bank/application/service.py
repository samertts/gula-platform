from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.blood_bank.domain.entities import (
    BloodComponentEntity,
    BloodDonation,
    BloodDonor,
    BloodInventory,
    BloodRequest,
    BloodUnit,
    Crossmatch,
    DonorDeferral,
    Transfusion,
)
from app.blood_bank.domain.enums import (
    ComponentStatus,
    CrossmatchStatus,
    DonationStatus,
    DonorStatus,
    TransfusionStatus,
)
from app.blood_bank.domain.state_machine import transition
from app.blood_bank.exceptions import (
    BloodBankValidationError,
    BloodBankWorkflowError,
    CrossmatchConflictError,
    DonationNotFoundError,
    DonorDeferredError,
    DonorNotFoundError,
    InsufficientStockError,
    TransfusionNotFoundError,
)
from app.blood_bank.infrastructure.models import (
    BloodComponentModel,
    BloodDonationModel,
    BloodDonorModel,
    BloodInventoryModel,
    BloodRequestModel,
    BloodUnitModel,
    CrossmatchModel,
    DonorDeferralModel,
    TransfusionModel,
    InventoryMovementModel,
)
from app.national.events.base import NationalDomainEvent


class BloodBankService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ---- Donor Management ----

    def register_donor(self, data: dict[str, Any]) -> BloodDonor:
        existing = self.db.query(BloodDonorModel).filter(
            BloodDonorModel.citizen_id == data.get("citizen_id", ""),
            BloodDonorModel.is_deleted.isnot(True),
        ).first()
        if existing:
            existing.status = DonorStatus.ACTIVE.value
            return self._update_donor(existing, data)
        model = BloodDonorModel(**{k: v for k, v in data.items() if hasattr(BloodDonorModel, k)})
        if not model.next_eligible_date:
            model.next_eligible_date = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        donor = self._donor_from_model(model)
        self._emit(NationalDomainEvent(
            event_type="bloodbank.donor.registered", aggregate_type="BloodDonor",
            aggregate_id=donor.id, payload={"blood_group": data.get("blood_group", "")},
        ))
        return donor

    def get_donor(self, donor_id: str) -> BloodDonor:
        model = self.db.query(BloodDonorModel).filter_by(id=donor_id).first()
        if not model or model.is_deleted:
            raise DonorNotFoundError()
        return self._donor_from_model(model)

    def find_donors(self, blood_group: str | None = None, status: str | None = None, skip: int = 0, limit: int = 100) -> list[BloodDonor]:
        query = self.db.query(BloodDonorModel).filter(BloodDonorModel.is_deleted.isnot(True))
        if blood_group:
            query = query.filter_by(blood_group=blood_group)
        if status:
            query = query.filter_by(status=status)
        return [self._donor_from_model(m) for m in query.offset(skip).limit(limit).all()]

    def defer_donor(self, donor_id: str, data: dict[str, Any]) -> DonorDeferral:
        donor = self.db.query(BloodDonorModel).filter_by(id=donor_id).first()
        if not donor:
            raise DonorNotFoundError()
        deferral_days = data.get("deferral_days", 0)
        deferred_until = datetime.now(UTC) + timedelta(days=deferral_days) if deferral_days else None
        model = DonorDeferralModel(
            donor_id=donor_id, deferral_type=data.get("deferral_type", "temporary"),
            reason=data.get("reason", "other"), reason_detail=data.get("reason_detail", ""),
            deferral_days=deferral_days, deferred_until=deferred_until,
            deferred_by=data.get("deferred_by", ""), notes=data.get("notes", ""),
        )
        donor.status = DonorStatus.DEFERRED.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DonorDeferral(id=model.id, donor_id=donor_id, deferral_days=deferral_days,
                             deferred_until=deferred_until, reason=data.get("reason", "other"))

    # ---- Donation ----

    def register_donation(self, data: dict[str, Any]) -> BloodDonation:
        donor_id = data.get("donor_id", "")
        donor = self.db.query(BloodDonorModel).filter_by(id=donor_id).first()
        if not donor:
            raise DonorNotFoundError()
        if donor.status == DonorStatus.DEFERRED.value:
            active_deferral = self.db.query(DonorDeferralModel).filter(
                DonorDeferralModel.donor_id == donor_id,
                DonorDeferralModel.is_active,
            ).first()
            if active_deferral:
                raise DonorDeferredError(f"Donor is deferred until {active_deferral.deferred_until}")
        model = BloodDonationModel(**{k: v for k, v in data.items() if hasattr(BloodDonationModel, k)})
        model.status = DonationStatus.REGISTERED.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        donor.last_donation_date = datetime.now(UTC)
        donor.next_eligible_date = datetime.now(UTC) + timedelta(days=56)
        donor.total_donations = (donor.total_donations or 0) + 1
        donor.total_volume_ml = (donor.total_volume_ml or 0) + (data.get("volume_ml", 450))
        self.db.commit()
        return BloodDonation(
            id=model.id, donor_id=donor_id, donation_type=data.get("donation_type", "whole_blood"),
            volume_ml=data.get("volume_ml", 450), status=model.status,
            bag_identifier=model.bag_identifier or "", isbt_128_code=model.isbt_128_code or "",
        )

    def complete_donation(self, donation_id: str) -> BloodDonation:
        model = self.db.query(BloodDonationModel).filter_by(id=donation_id).first()
        if not model:
            raise DonationNotFoundError()
        model.status = DonationStatus.COMPLETED.value
        self.db.commit()
        self.db.refresh(model)
        return BloodDonation(id=model.id, donor_id=model.donor_id, status=model.status, donation_type=model.donation_type,
                             volume_ml=model.volume_ml, bag_identifier=model.bag_identifier or "")

    # ---- Components ----

    def process_component(self, data: dict[str, Any]) -> BloodComponentEntity:
        model = BloodComponentModel(**{k: v for k, v in data.items() if hasattr(BloodComponentModel, k)})
        model.processing_date = datetime.now(UTC)
        model.status = ComponentStatus.AVAILABLE.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return BloodComponentEntity(id=model.id, donation_id=model.donation_id, component=model.component, status=model.status,
                                     bag_identifier=model.bag_identifier or "", isbt_128_code=model.isbt_128_code or "")

    # ---- Inventory ----

    def get_inventory(self, facility_id: str | None = None) -> list[BloodInventory]:
        query = self.db.query(BloodInventoryModel)
        if facility_id:
            query = query.filter_by(facility_id=facility_id)
        results = []
        for m in query.all():
            results.append(BloodInventory(
                id=m.id, facility_id=m.facility_id, blood_group=m.blood_group,
                rh_factor=m.rh_factor, component=m.component,
                quantity=m.quantity or 0, reserved_quantity=m.reserved_quantity or 0,
                minimum_stock=m.minimum_stock or 10, critical_threshold=m.critical_threshold or 5,
            ))
        return results

    def get_critical_inventory(self) -> list[BloodInventory]:
        models = self.db.query(BloodInventoryModel).all()
        critical = []
        for m in models:
            available = (m.quantity or 0) - (m.reserved_quantity or 0)
            if available <= (m.critical_threshold or 5):
                critical.append(BloodInventory(
                    id=m.id, facility_id=m.facility_id, blood_group=m.blood_group,
                    rh_factor=m.rh_factor, component=m.component,
                    quantity=m.quantity or 0, reserved_quantity=m.reserved_quantity or 0,
                    minimum_stock=m.minimum_stock or 10, critical_threshold=m.critical_threshold or 5,
                ))
        return critical

    def issue_units(self, blood_group: str, component: str, quantity: int, facility_id: str) -> list[BloodUnit]:
        available = self.db.query(BloodUnitModel).filter(
            BloodUnitModel.blood_group == blood_group,
            BloodUnitModel.component == component,
            BloodUnitModel.status == "available",
            BloodUnitModel.facility_id == facility_id,
            BloodUnitModel.expiry_date > datetime.now(UTC) if BloodUnitModel.expiry_date else True,
        ).limit(quantity).all()
        if len(available) < quantity:
            raise InsufficientStockError(f"Only {len(available)} units available, {quantity} requested")
        issued = []
        for unit in available:
            unit.status = "issued"
            unit.issued_at = datetime.now(UTC)
            issued.append(BloodUnit(id=unit.id, blood_group=unit.blood_group, component=unit.component,
                                     bag_identifier=unit.bag_identifier or "", status="issued"))
        self.db.commit()
        return issued

    # ---- Crossmatch ----

    def perform_crossmatch(self, data: dict[str, Any]) -> Crossmatch:
        patient_bg = data.get("patient_blood_group", "")
        unit_bg = data.get("blood_group", "")
        from app.blood_bank.compatibility import check_compatibility
        result = check_compatibility(patient_bg, unit_bg)
        model = CrossmatchModel(
            patient_id=data.get("patient_id", ""), patient_name=data.get("patient_name", ""),
            patient_blood_group=patient_bg, patient_rh_factor=data.get("patient_rh_factor", ""),
            unit_id=data.get("unit_id", ""), blood_group=unit_bg,
            abo_compatible=result.get("abo_compatible", False),
            rh_compatible=result.get("rh_compatible", False),
            status=CrossmatchStatus.COMPATIBLE.value if result.get("compatible") else CrossmatchStatus.INCOMPATIBLE.value,
            crossmatch_result=result.get("result", ""),
            performed_by=data.get("performed_by", ""), performed_at=datetime.now(UTC),
            crossmatch_type=data.get("crossmatch_type", "full"),
        )
        if not result.get("compatible"):
            raise CrossmatchConflictError(f"Crossmatch incompatible: {result.get('result', '')}")
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Crossmatch(id=model.id, patient_id=model.patient_id, unit_id=model.unit_id,
                          status=CrossmatchStatus.COMPATIBLE, abo_compatible=True)

    # ---- Transfusion ----

    def record_transfusion(self, data: dict[str, Any]) -> Transfusion:
        model = TransfusionModel(**{k: v for k, v in data.items() if hasattr(TransfusionModel, k)})
        model.status = TransfusionStatus.ORDERED.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Transfusion(id=model.id, patient_id=model.patient_id, unit_id=model.unit_id, status=model.status)

    def start_transfusion(self, transfusion_id: str) -> Transfusion:
        model = self.db.query(TransfusionModel).filter_by(id=transfusion_id).first()
        if not model:
            raise TransfusionNotFoundError()
        model.status = TransfusionStatus.IN_PROGRESS.value
        model.start_time = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return Transfusion(id=model.id, patient_id=model.patient_id, status=TransfusionStatus.IN_PROGRESS)

    def complete_transfusion(self, transfusion_id: str) -> Transfusion:
        model = self.db.query(TransfusionModel).filter_by(id=transfusion_id).first()
        if not model:
            raise TransfusionNotFoundError()
        model.status = TransfusionStatus.COMPLETED.value
        model.end_time = datetime.now(UTC)
        if model.unit_id:
            unit = self.db.query(BloodUnitModel).filter_by(id=model.unit_id).first()
            if unit:
                unit.status = "transfused"
                unit.transfused_at = datetime.now(UTC)
        self.db.commit()
        return Transfusion(id=model.id, patient_id=model.patient_id, status=TransfusionStatus.COMPLETED)

    # ---- Safety-critical blood issue and transfusion commands ----

    @staticmethod
    def _require_lab_id(data: dict[str, Any]) -> int:
        lab_id = data.get("lab_id")
        if not isinstance(lab_id, int) or lab_id <= 0:
            raise BloodBankValidationError("A valid lab_id is required for blood bank commands")
        return lab_id

    def issue_units_safely(
        self, *, request_id: str, lab_id: int, quantity: int, issued_by: str,
    ) -> list[BloodUnitModel]:
        if not request_id or not issued_by.strip() or not isinstance(quantity, int) or quantity <= 0:
            raise BloodBankValidationError("request_id, positive quantity, and issued_by are required")
        request = (
            self.db.query(BloodRequestModel)
            .filter(BloodRequestModel.id == request_id, BloodRequestModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not request or request.is_deleted:
            raise BloodBankValidationError("Active blood request is required")
        if request.status not in {"pending", "approved", "partially_fulfilled"}:
            raise BloodBankWorkflowError("Blood request is not eligible for issuance")
        if not request.patient_id or not request.blood_group or not request.component:
            raise BloodBankValidationError("Blood request must bind patient, blood group, and component")
        remaining = (request.units_requested or 0) - (request.fulfilled_units or 0)
        if quantity > remaining:
            raise BloodBankWorkflowError("Requested issue quantity exceeds the outstanding blood request")
        now = datetime.now(UTC)
        units = cast(
            list[BloodUnitModel],
            self.db.query(BloodUnitModel)
            .filter(
                BloodUnitModel.lab_id == lab_id,
                BloodUnitModel.facility_id == request.facility_id,
                BloodUnitModel.blood_group == request.blood_group,
                BloodUnitModel.component == request.component,
                BloodUnitModel.status == ComponentStatus.AVAILABLE.value,
                BloodUnitModel.screening_complete.is_(True),
                BloodUnitModel.processing_complete.is_(True),
                BloodUnitModel.recalled.isnot(True),
                or_(BloodUnitModel.expiry_date.is_(None), BloodUnitModel.expiry_date > now),
            )
            .order_by(BloodUnitModel.expiry_date.asc(), BloodUnitModel.id.asc())
            .with_for_update()
            .limit(quantity)
            .all(),
        )
        if len(units) != quantity:
            raise InsufficientStockError("Insufficient screened, processed, unexpired units for this request")
        for unit in units:
            transition(unit.status, ComponentStatus.ISSUED.value, entity="blood_unit")
            previous_status = unit.status
            unit.status = ComponentStatus.ISSUED.value
            unit.issued_to = request.patient_id
            unit.issued_at = now
            unit.version += 1
            self.db.add(InventoryMovementModel(
                unit_id=unit.id, facility_id=unit.facility_id or request.facility_id,
                from_location=unit.storage_location, to_location="issued",
                movement_type="issued", performed_by=issued_by, performed_at=now,
                notes=f"{previous_status} -> issued for request {request.id}", lab_id=lab_id,
            ))
        request.fulfilled_units = (request.fulfilled_units or 0) + quantity
        request.status = "fulfilled" if request.fulfilled_units == request.units_requested else "partially_fulfilled"
        request.version += 1
        self.db.flush()
        return units

    def perform_crossmatch_safely(self, data: dict[str, Any]) -> CrossmatchModel:
        lab_id = self._require_lab_id(data)
        patient_id = str(data.get("patient_id", "")).strip()
        unit_id = str(data.get("unit_id", "")).strip()
        performed_by = str(data.get("performed_by", "")).strip()
        if not patient_id or not unit_id or not performed_by:
            raise BloodBankValidationError("patient_id, unit_id, and performed_by are required")
        unit = (
            self.db.query(BloodUnitModel)
            .filter(BloodUnitModel.id == unit_id, BloodUnitModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not unit or unit.is_deleted:
            raise BloodBankValidationError("Blood unit not found in the current institution")
        if unit.status not in {ComponentStatus.AVAILABLE.value, ComponentStatus.ISSUED.value}:
            raise BloodBankWorkflowError("Blood unit is not eligible for crossmatch")
        if not unit.screening_complete or not unit.processing_complete or unit.recalled:
            raise BloodBankWorkflowError("Only screened, processed, non-recalled units can be crossmatched")
        if unit.expiry_date and unit.expiry_date <= datetime.now(UTC):
            raise BloodBankWorkflowError("Expired blood units cannot be crossmatched")
        patient_group = str(data.get("patient_blood_group", "")).strip()
        patient_rh = str(data.get("patient_rh_factor", "")).strip()
        if not patient_group or not patient_rh:
            raise BloodBankValidationError("Patient ABO group and Rh factor are required")
        patient_rh_normalized = "+" if patient_rh.casefold() in {"+", "positive", "pos"} else "-" if patient_rh.casefold() in {"-", "negative", "neg"} else ""
        unit_rh_normalized = "+" if str(unit.rh_factor).casefold() in {"+", "positive", "pos"} else "-" if str(unit.rh_factor).casefold() in {"-", "negative", "neg"} else ""
        if not patient_rh_normalized or not unit_rh_normalized:
            raise BloodBankValidationError("Valid patient and unit Rh factors are required")
        from app.blood_bank.compatibility import check_compatibility
        compatibility = check_compatibility(
            f"{patient_group}{patient_rh_normalized}",
            f"{unit.blood_group}{unit_rh_normalized}",
        )
        if not compatibility.get("compatible"):
            raise CrossmatchConflictError("ABO/Rh incompatibility prevents crossmatch")
        duplicate = (
            self.db.query(CrossmatchModel)
            .filter(
                CrossmatchModel.lab_id == lab_id,
                CrossmatchModel.patient_id == patient_id,
                CrossmatchModel.unit_id == unit.id,
                CrossmatchModel.status == CrossmatchStatus.COMPATIBLE.value,
                CrossmatchModel.expires_at > datetime.now(UTC),
            )
            .with_for_update()
            .first()
        )
        if duplicate:
            raise BloodBankWorkflowError("A current compatible crossmatch already exists for this patient and unit")
        model = CrossmatchModel(
            lab_id=lab_id, patient_id=patient_id, patient_name=data.get("patient_name", ""),
            patient_blood_group=patient_group, patient_rh_factor=patient_rh,
            unit_id=unit.id, unit_identifier=unit.bag_identifier or unit.isbt_128_code,
            blood_group=unit.blood_group, abo_compatible=True,
            rh_compatible=bool(compatibility.get("rh_compatible")),
            status=CrossmatchStatus.COMPATIBLE.value,
            crossmatch_result=str(compatibility.get("result", "compatible")),
            performed_by=performed_by, performed_at=datetime.now(UTC),
            crossmatch_type=data.get("crossmatch_type", "full"),
            expires_at=data.get("expires_at"), notes=data.get("notes"),
        )
        if not model.expires_at or model.expires_at <= datetime.now(UTC):
            raise BloodBankValidationError("A future crossmatch expiry is required")
        self.db.add(model)
        self.db.flush()
        return model

    def verify_crossmatch_safely(self, crossmatch_id: str, lab_id: int, verified_by: str) -> CrossmatchModel:
        model = (
            self.db.query(CrossmatchModel)
            .filter(CrossmatchModel.id == crossmatch_id, CrossmatchModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not model:
            raise BloodBankValidationError("Crossmatch not found")
        if model.status != CrossmatchStatus.COMPATIBLE.value or not model.abo_compatible or not model.rh_compatible:
            raise BloodBankWorkflowError("Only compatible crossmatches can be independently verified")
        if not model.expires_at or model.expires_at <= datetime.now(UTC):
            raise BloodBankWorkflowError("Expired crossmatches cannot be verified")
        if not verified_by.strip() or verified_by == model.performed_by:
            raise BloodBankValidationError("Crossmatch verification requires an independent verifier")
        if model.verified_at:
            raise BloodBankWorkflowError("Crossmatch is already verified")
        model.verified_by = verified_by
        model.verified_at = datetime.now(UTC)
        model.version += 1
        self.db.flush()
        return model

    def record_transfusion_safely(self, data: dict[str, Any]) -> TransfusionModel:
        lab_id = self._require_lab_id(data)
        patient_id = str(data.get("patient_id", "")).strip()
        unit_id = str(data.get("unit_id", "")).strip()
        crossmatch_id = str(data.get("crossmatch_id", "")).strip()
        ordered_by = str(data.get("ordered_by", "")).strip()
        if not patient_id or not unit_id or not crossmatch_id or not ordered_by:
            raise BloodBankValidationError("patient_id, unit_id, crossmatch_id, and ordered_by are required")
        unit = (
            self.db.query(BloodUnitModel)
            .filter(BloodUnitModel.id == unit_id, BloodUnitModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        crossmatch = (
            self.db.query(CrossmatchModel)
            .filter(CrossmatchModel.id == crossmatch_id, CrossmatchModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not unit or not crossmatch:
            raise BloodBankValidationError("Blood unit and crossmatch must exist in the current institution")
        if unit.status != ComponentStatus.ISSUED.value or unit.issued_to != patient_id:
            raise BloodBankWorkflowError("Only a unit issued to this patient can be transfused")
        if unit.expiry_date and unit.expiry_date <= datetime.now(UTC):
            raise BloodBankWorkflowError("Expired blood units cannot be transfused")
        if (
            crossmatch.patient_id != patient_id or crossmatch.unit_id != unit_id
            or crossmatch.status != CrossmatchStatus.COMPATIBLE.value
            or not crossmatch.verified_at or not crossmatch.expires_at
            or crossmatch.expires_at <= datetime.now(UTC)
        ):
            raise BloodBankWorkflowError("A current independently verified compatible crossmatch is required")
        active = (
            self.db.query(TransfusionModel)
            .filter(
                TransfusionModel.lab_id == lab_id,
                TransfusionModel.unit_id == unit_id,
                TransfusionModel.status.in_([TransfusionStatus.ORDERED.value, TransfusionStatus.VERIFIED.value, TransfusionStatus.IN_PROGRESS.value]),
            )
            .with_for_update()
            .first()
        )
        if active:
            raise BloodBankWorkflowError("An unfinished transfusion already exists for this blood unit")
        model = TransfusionModel(**{k: v for k, v in data.items() if hasattr(TransfusionModel, k)})
        model.status = TransfusionStatus.ORDERED.value
        model.order_datetime = data.get("order_datetime") or datetime.now(UTC)
        model.unit_identifier = unit.bag_identifier or unit.isbt_128_code
        model.blood_group = unit.blood_group
        model.component = unit.component
        self.db.add(model)
        self.db.flush()
        return model

    def verify_transfusion_safely(self, transfusion_id: str, lab_id: int, data: dict[str, Any]) -> TransfusionModel:
        model = (
            self.db.query(TransfusionModel)
            .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not model:
            raise TransfusionNotFoundError()
        if model.status != TransfusionStatus.ORDERED.value:
            raise BloodBankWorkflowError("Only ordered transfusions can be verified")
        verifier = str(data.get("verified_by", "")).strip()
        if not verifier or verifier == model.ordered_by:
            raise BloodBankValidationError("Bedside transfusion verification requires an independent verifier")
        if not all(bool(data.get(field)) for field in ("patient_verified", "unit_verified", "consent_verified", "bedside_verification_complete")):
            raise BloodBankValidationError("Patient, unit, consent, and bedside checks must all be confirmed")
        if not data.get("pre_vitals"):
            raise BloodBankValidationError("Pre-transfusion vital signs are required")
        model.verified_by = verifier
        model.verified_at = datetime.now(UTC)
        model.patient_verified = True
        model.unit_verified = True
        model.consent_verified = True
        model.bedside_verification_complete = True
        model.pre_vitals = data["pre_vitals"]
        model.status = TransfusionStatus.VERIFIED.value
        model.version += 1
        self.db.flush()
        return model

    def start_transfusion_safely(self, transfusion_id: str, lab_id: int, administered_by: str) -> TransfusionModel:
        model = (
            self.db.query(TransfusionModel)
            .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not model:
            raise TransfusionNotFoundError()
        if model.status != TransfusionStatus.VERIFIED.value:
            raise BloodBankWorkflowError("Only bedside-verified transfusions can be started")
        transition(model.status, TransfusionStatus.IN_PROGRESS.value, entity="transfusion")
        if not administered_by.strip() or administered_by == model.verified_by:
            raise BloodBankValidationError("Transfusion administration requires a second clinical actor")
        unit = (
            self.db.query(BloodUnitModel)
            .filter(BloodUnitModel.id == model.unit_id, BloodUnitModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not unit or unit.status != ComponentStatus.ISSUED.value or unit.issued_to != model.patient_id:
            raise BloodBankWorkflowError("Issued blood unit no longer matches the verified transfusion")
        model.administered_by = administered_by
        model.status = TransfusionStatus.IN_PROGRESS.value
        model.start_time = datetime.now(UTC)
        model.version += 1
        self.db.flush()
        return model

    def complete_transfusion_safely(self, transfusion_id: str, lab_id: int, data: dict[str, Any]) -> TransfusionModel:
        model = (
            self.db.query(TransfusionModel)
            .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not model:
            raise TransfusionNotFoundError()
        if model.status != TransfusionStatus.IN_PROGRESS.value:
            raise BloodBankWorkflowError("Only in-progress transfusions can be completed")
        if model.reaction_occurred:
            raise BloodBankWorkflowError("A transfusion with a recorded reaction cannot be completed")
        if not data.get("post_vitals"):
            raise BloodBankValidationError("Post-transfusion vital signs are required")
        unit = (
            self.db.query(BloodUnitModel)
            .filter(BloodUnitModel.id == model.unit_id, BloodUnitModel.lab_id == lab_id)
            .with_for_update()
            .first()
        )
        if not unit or unit.status != ComponentStatus.ISSUED.value:
            raise BloodBankWorkflowError("Issued unit is not available for completion")
        transition(model.status, TransfusionStatus.COMPLETED.value, entity="transfusion")
        model.post_vitals = data["post_vitals"]
        model.status = TransfusionStatus.COMPLETED.value
        model.end_time = datetime.now(UTC)
        model.outcome = data.get("outcome") or "completed"
        model.version += 1
        transition(unit.status, ComponentStatus.TRANSFUSED.value, entity="blood_unit")
        unit.status = ComponentStatus.TRANSFUSED.value
        unit.transfused_at = model.end_time
        unit.version += 1
        self.db.add(InventoryMovementModel(
            unit_id=unit.id, facility_id=unit.facility_id, from_location="issued",
            to_location="transfused", movement_type="transferred",
            performed_by=str(data.get("completed_by") or model.administered_by or "system"),
            performed_at=model.end_time, notes=f"issued -> transfused for transfusion {model.id}", lab_id=lab_id,
        ))
        self.db.flush()
        return model

    # ---- Blood Requests ----

    def create_blood_request(self, data: dict[str, Any]) -> BloodRequest:
        model = BloodRequestModel(**{k: v for k, v in data.items() if hasattr(BloodRequestModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return BloodRequest(id=model.id, patient_id=model.patient_id, blood_group=model.blood_group,
                            units_requested=model.units_requested, status=model.status)

    # ---- Dashboard ----

    def get_dashboard(self) -> dict[str, Any]:
        total_donors = self.db.query(BloodDonorModel).filter(BloodDonorModel.is_deleted.isnot(True)).count()
        active_donors = self.db.query(BloodDonorModel).filter_by(status="active").count()
        donations_today = self.db.query(BloodDonationModel).filter(
            BloodDonationModel.created_at >= datetime.now(UTC).replace(hour=0, minute=0, second=0),
        ).count()
        total_donations = self.db.query(BloodDonationModel).count()
        total_units = self.db.query(BloodUnitModel).filter_by(status="available").count()
        critical = self.get_critical_inventory()
        pending_requests = self.db.query(BloodRequestModel).filter_by(status="pending").count()
        total_transfusions = self.db.query(TransfusionModel).count()
        return {
            "total_donors": total_donors, "active_donors": active_donors,
            "donations_today": donations_today, "total_donations": total_donations,
            "available_units": total_units, "critical_items": len(critical),
            "pending_requests": pending_requests, "total_transfusions": total_transfusions,
        }

    def _donor_from_model(self, m: BloodDonorModel) -> BloodDonor:
        return BloodDonor(
            id=m.id, citizen_id=m.citizen_id or "", full_name=m.full_name,
            phone=m.phone or "", blood_group=m.blood_group or "unknown",
            rh_factor=m.rh_factor or "unknown", status=m.status or "active",
            total_donations=m.total_donations or 0, total_volume_ml=m.total_volume_ml or 0.0,
            last_donation_date=m.last_donation_date, next_eligible_date=m.next_eligible_date,
            consent_signed=m.consent_signed or False,
        )

    def _update_donor(self, model: BloodDonorModel, data: dict[str, Any]) -> BloodDonor:
        for k, v in data.items():
            if hasattr(model, k) and k not in ("id", "created_at"):
                setattr(model, k, v)
        self.db.commit()
        self.db.refresh(model)
        return self._donor_from_model(model)
