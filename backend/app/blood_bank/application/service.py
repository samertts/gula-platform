from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

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
from app.blood_bank.exceptions import (
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
        existing = (
            self.db.query(BloodDonorModel)
            .filter(
                BloodDonorModel.citizen_id == data.get("citizen_id", ""),
                BloodDonorModel.is_deleted.isnot(True),
            )
            .first()
        )
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
        self._emit(
            NationalDomainEvent(
                event_type="bloodbank.donor.registered",
                aggregate_type="BloodDonor",
                aggregate_id=donor.id,
                payload={"blood_group": data.get("blood_group", "")},
            ),
        )
        return donor

    def get_donor(self, donor_id: str) -> BloodDonor:
        model = self.db.query(BloodDonorModel).filter_by(id=donor_id).first()
        if not model or model.is_deleted:
            raise DonorNotFoundError()
        return self._donor_from_model(model)

    def find_donors(
        self,
        blood_group: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BloodDonor]:
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
        deferred_until = (
            datetime.now(UTC) + timedelta(days=deferral_days) if deferral_days else None
        )
        model = DonorDeferralModel(
            donor_id=donor_id,
            deferral_type=data.get("deferral_type", "temporary"),
            reason=data.get("reason", "other"),
            reason_detail=data.get("reason_detail", ""),
            deferral_days=deferral_days,
            deferred_until=deferred_until,
            deferred_by=data.get("deferred_by", ""),
            notes=data.get("notes", ""),
        )
        donor.status = DonorStatus.DEFERRED.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DonorDeferral(
            id=model.id,
            donor_id=donor_id,
            deferral_days=deferral_days,
            deferred_until=deferred_until,
            reason=data.get("reason", "other"),
        )

    # ---- Donation ----

    def register_donation(self, data: dict[str, Any]) -> BloodDonation:
        donor_id = data.get("donor_id", "")
        donor = self.db.query(BloodDonorModel).filter_by(id=donor_id).first()
        if not donor:
            raise DonorNotFoundError()
        if donor.status == DonorStatus.DEFERRED.value:
            active_deferral = (
                self.db.query(DonorDeferralModel)
                .filter(
                    DonorDeferralModel.donor_id == donor_id,
                    DonorDeferralModel.is_active,
                )
                .first()
            )
            if active_deferral:
                raise DonorDeferredError(
                    f"Donor is deferred until {active_deferral.deferred_until}",
                )
        model = BloodDonationModel(
            **{k: v for k, v in data.items() if hasattr(BloodDonationModel, k)},
        )
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
            id=model.id,
            donor_id=donor_id,
            donation_type=data.get("donation_type", "whole_blood"),
            volume_ml=data.get("volume_ml", 450),
            status=model.status,
            bag_identifier=model.bag_identifier or "",
            isbt_128_code=model.isbt_128_code or "",
        )

    def complete_donation(self, donation_id: str) -> BloodDonation:
        model = self.db.query(BloodDonationModel).filter_by(id=donation_id).first()
        if not model:
            raise DonationNotFoundError()
        model.status = DonationStatus.COMPLETED.value
        self.db.commit()
        self.db.refresh(model)
        return BloodDonation(
            id=model.id,
            donor_id=model.donor_id,
            status=model.status,
            donation_type=model.donation_type,
            volume_ml=model.volume_ml,
            bag_identifier=model.bag_identifier or "",
        )

    # ---- Components ----

    def process_component(self, data: dict[str, Any]) -> BloodComponentEntity:
        model = BloodComponentModel(
            **{k: v for k, v in data.items() if hasattr(BloodComponentModel, k)},
        )
        model.processing_date = datetime.now(UTC)
        model.status = ComponentStatus.AVAILABLE.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return BloodComponentEntity(
            id=model.id,
            donation_id=model.donation_id,
            component=model.component,
            status=model.status,
            bag_identifier=model.bag_identifier or "",
            isbt_128_code=model.isbt_128_code or "",
        )

    # ---- Inventory ----

    def get_inventory(self, facility_id: str | None = None) -> list[BloodInventory]:
        query = self.db.query(BloodInventoryModel)
        if facility_id:
            query = query.filter_by(facility_id=facility_id)
        results = []
        for m in query.all():
            results.append(
                BloodInventory(
                    id=m.id,
                    facility_id=m.facility_id,
                    blood_group=m.blood_group,
                    rh_factor=m.rh_factor,
                    component=m.component,
                    quantity=m.quantity or 0,
                    reserved_quantity=m.reserved_quantity or 0,
                    minimum_stock=m.minimum_stock or 10,
                    critical_threshold=m.critical_threshold or 5,
                ),
            )
        return results

    def get_critical_inventory(self) -> list[BloodInventory]:
        models = self.db.query(BloodInventoryModel).all()
        critical = []
        for m in models:
            available = (m.quantity or 0) - (m.reserved_quantity or 0)
            if available <= (m.critical_threshold or 5):
                critical.append(
                    BloodInventory(
                        id=m.id,
                        facility_id=m.facility_id,
                        blood_group=m.blood_group,
                        rh_factor=m.rh_factor,
                        component=m.component,
                        quantity=m.quantity or 0,
                        reserved_quantity=m.reserved_quantity or 0,
                        minimum_stock=m.minimum_stock or 10,
                        critical_threshold=m.critical_threshold or 5,
                    ),
                )
        return critical

    def issue_units(
        self, blood_group: str, component: str, quantity: int, facility_id: str,
    ) -> list[BloodUnit]:
        available = (
            self.db.query(BloodUnitModel)
            .filter(
                BloodUnitModel.blood_group == blood_group,
                BloodUnitModel.component == component,
                BloodUnitModel.status == "available",
                BloodUnitModel.facility_id == facility_id,
                BloodUnitModel.expiry_date > datetime.now(UTC)
                if BloodUnitModel.expiry_date
                else True,
            )
            .limit(quantity)
            .all()
        )
        if len(available) < quantity:
            raise InsufficientStockError(
                f"Only {len(available)} units available, {quantity} requested",
            )
        issued = []
        for unit in available:
            unit.status = "issued"
            unit.issued_at = datetime.now(UTC)
            issued.append(
                BloodUnit(
                    id=unit.id,
                    blood_group=unit.blood_group,
                    component=unit.component,
                    bag_identifier=unit.bag_identifier or "",
                    status="issued",
                ),
            )
        self.db.commit()
        return issued

    # ---- Crossmatch ----

    def perform_crossmatch(self, data: dict[str, Any]) -> Crossmatch:
        patient_bg = data.get("patient_blood_group", "")
        unit_bg = data.get("blood_group", "")
        from app.blood_bank.compatibility import check_compatibility

        result = check_compatibility(patient_bg, unit_bg)
        model = CrossmatchModel(
            patient_id=data.get("patient_id", ""),
            patient_name=data.get("patient_name", ""),
            patient_blood_group=patient_bg,
            patient_rh_factor=data.get("patient_rh_factor", ""),
            unit_id=data.get("unit_id", ""),
            blood_group=unit_bg,
            abo_compatible=result.get("abo_compatible", False),
            rh_compatible=result.get("rh_compatible", False),
            status=CrossmatchStatus.COMPATIBLE.value
            if result.get("compatible")
            else CrossmatchStatus.INCOMPATIBLE.value,
            crossmatch_result=result.get("result", ""),
            performed_by=data.get("performed_by", ""),
            performed_at=datetime.now(UTC),
            crossmatch_type=data.get("crossmatch_type", "full"),
        )
        if not result.get("compatible"):
            raise CrossmatchConflictError(f"Crossmatch incompatible: {result.get('result', '')}")
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Crossmatch(
            id=model.id,
            patient_id=model.patient_id,
            unit_id=model.unit_id,
            status=CrossmatchStatus.COMPATIBLE,
            abo_compatible=True,
        )

    # ---- Transfusion ----

    def record_transfusion(self, data: dict[str, Any]) -> Transfusion:
        model = TransfusionModel(**{k: v for k, v in data.items() if hasattr(TransfusionModel, k)})
        model.status = TransfusionStatus.ORDERED.value
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Transfusion(
            id=model.id, patient_id=model.patient_id, unit_id=model.unit_id, status=model.status,
        )

    def start_transfusion(self, transfusion_id: str) -> Transfusion:
        model = self.db.query(TransfusionModel).filter_by(id=transfusion_id).first()
        if not model:
            raise TransfusionNotFoundError()
        model.status = TransfusionStatus.IN_PROGRESS.value
        model.start_time = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return Transfusion(
            id=model.id, patient_id=model.patient_id, status=TransfusionStatus.IN_PROGRESS,
        )

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
        return Transfusion(
            id=model.id, patient_id=model.patient_id, status=TransfusionStatus.COMPLETED,
        )

    # ---- Blood Requests ----

    def create_blood_request(self, data: dict[str, Any]) -> BloodRequest:
        model = BloodRequestModel(
            **{k: v for k, v in data.items() if hasattr(BloodRequestModel, k)},
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return BloodRequest(
            id=model.id,
            patient_id=model.patient_id,
            blood_group=model.blood_group,
            units_requested=model.units_requested,
            status=model.status,
        )

    # ---- Dashboard ----

    def get_dashboard(self) -> dict[str, Any]:
        total_donors = (
            self.db.query(BloodDonorModel).filter(BloodDonorModel.is_deleted.isnot(True)).count()
        )
        active_donors = self.db.query(BloodDonorModel).filter_by(status="active").count()
        donations_today = (
            self.db.query(BloodDonationModel)
            .filter(
                BloodDonationModel.created_at
                >= datetime.now(UTC).replace(hour=0, minute=0, second=0),
            )
            .count()
        )
        total_donations = self.db.query(BloodDonationModel).count()
        total_units = self.db.query(BloodUnitModel).filter_by(status="available").count()
        critical = self.get_critical_inventory()
        pending_requests = self.db.query(BloodRequestModel).filter_by(status="pending").count()
        total_transfusions = self.db.query(TransfusionModel).count()
        return {
            "total_donors": total_donors,
            "active_donors": active_donors,
            "donations_today": donations_today,
            "total_donations": total_donations,
            "available_units": total_units,
            "critical_items": len(critical),
            "pending_requests": pending_requests,
            "total_transfusions": total_transfusions,
        }

    def _donor_from_model(self, m: BloodDonorModel) -> BloodDonor:
        return BloodDonor(
            id=m.id,
            citizen_id=m.citizen_id or "",
            full_name=m.full_name,
            phone=m.phone or "",
            blood_group=m.blood_group or "unknown",
            rh_factor=m.rh_factor or "unknown",
            status=m.status or "active",
            total_donations=m.total_donations or 0,
            total_volume_ml=m.total_volume_ml or 0.0,
            last_donation_date=m.last_donation_date,
            next_eligible_date=m.next_eligible_date,
            consent_signed=m.consent_signed or False,
        )

    def _update_donor(self, model: BloodDonorModel, data: dict[str, Any]) -> BloodDonor:
        for k, v in data.items():
            if hasattr(model, k) and k not in ("id", "created_at"):
                setattr(model, k, v)
        self.db.commit()
        self.db.refresh(model)
        return self._donor_from_model(model)
