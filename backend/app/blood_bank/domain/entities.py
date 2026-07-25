from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.blood_bank.domain.enums import (
    ABOGroup,
    BloodComponent,
    CollectionMethod,
    ComponentStatus,
    CrossmatchStatus,
    CrossmatchType,
    DeferralReason,
    DeferralType,
    DonationStatus,
    DonationType,
    DonorStatus,
    InventoryMovementType,
    RhFactor,
    ScreeningResult,
    ScreeningTest,
    StorageCondition,
    TransfusionReactionSeverity,
    TransfusionReactionType,
    TransfusionStatus,
)


@dataclass
class BloodDonor:
    id: str
    citizen_id: str = ""
    national_id: str = ""
    full_name: str = ""
    phone: str = ""
    email: str = ""
    date_of_birth: str = ""
    gender: str = ""
    blood_group: ABOGroup = ABOGroup.UNKNOWN
    rh_factor: RhFactor = RhFactor.UNKNOWN
    weight_kg: float | None = None
    height_cm: float | None = None
    hemoglobin_g_dl: float | None = None
    status: DonorStatus = DonorStatus.ACTIVE
    total_donations: int = 0
    total_volume_ml: float = 0.0
    last_donation_date: datetime | None = None
    next_eligible_date: datetime | None = None
    is_regular_donor: bool = False
    consent_signed: bool = False
    consent_date: datetime | None = None
    emergency_contact: str = ""
    emergency_phone: str = ""
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_eligible(self) -> bool:
        return (
            self.status == DonorStatus.ACTIVE
            and self.next_eligible_date
            and datetime.now(UTC) >= self.next_eligible_date
        )


@dataclass
class DonorDeferral:
    id: str
    donor_id: str
    deferral_type: DeferralType = DeferralType.TEMPORARY
    reason: DeferralReason = DeferralReason.OTHER
    reason_detail: str = ""
    deferral_days: int = 0
    deferred_from: datetime = field(default_factory=lambda: datetime.now(UTC))
    deferred_until: datetime | None = None
    deferred_by: str = ""
    is_active: bool = True
    notes: str = ""

    @property
    def is_expired(self) -> bool:
        if self.deferred_until:
            return datetime.now(UTC) >= self.deferred_until
        return False


@dataclass
class BloodDonation:
    id: str
    donor_id: str
    donation_type: DonationType = DonationType.WHOLE_BLOOD
    collection_method: CollectionMethod = CollectionMethod.MANUAL
    status: DonationStatus = DonationStatus.REGISTERED
    volume_ml: float = 450.0
    collection_site: str = ""
    collection_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    phlebotomist_id: str = ""
    pulse_before: int | None = None
    bp_systolic_before: int | None = None
    bp_diastolic_before: int | None = None
    temperature_before: float | None = None
    hemoglobin_pre: float | None = None
    pulse_after: int | None = None
    bp_systolic_after: int | None = None
    bp_diastolic_after: int | None = None
    adverse_event: str = ""
    bag_identifier: str = ""
    isbt_128_code: str = ""
    barcode: str = ""
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def isbt_label(self) -> str:
        if self.isbt_128_code:
            return self.isbt_128_code
        return self.bag_identifier or self.id


@dataclass
class ScreeningResultData:
    id: str
    donation_id: str
    test: ScreeningTest = ScreeningTest.HIV
    result: ScreeningResult = ScreeningResult.PENDING
    result_value: str = ""
    analyzer_id: str = ""
    operator_id: str = ""
    test_date: datetime | None = None
    verified_by: str = ""
    verified_at: datetime | None = None
    kit_lot_number: str = ""
    kit_expiry: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BloodComponentEntity:
    id: str
    donation_id: str
    component: BloodComponent = BloodComponent.PACKED_RBC
    status: ComponentStatus = ComponentStatus.PENDING_PROCESSING
    volume_ml: float | None = None
    parent_component_id: str = ""
    bag_identifier: str = ""
    isbt_128_code: str = ""
    barcode: str = ""
    storage_condition: StorageCondition = StorageCondition.REFRIGERATED
    expiry_date: datetime | None = None
    processing_date: datetime | None = None
    processed_by: str = ""
    leukocyte_reduced: bool = False
    irradiated: bool = False
    washed: bool = False
    pathogen_reduced: bool = False
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        if self.expiry_date:
            return datetime.now(UTC) >= self.expiry_date
        return False


@dataclass
class BloodInventory:
    id: str
    facility_id: str = ""
    blood_group: ABOGroup = ABOGroup.UNKNOWN
    rh_factor: RhFactor = RhFactor.UNKNOWN
    component: BloodComponent = BloodComponent.PACKED_RBC
    quantity: int = 0
    reserved_quantity: int = 0
    minimum_stock: int = 10
    critical_threshold: int = 5
    storage_location: str = ""
    storage_condition: StorageCondition = StorageCondition.REFRIGERATED
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity

    @property
    def is_critical(self) -> bool:
        return self.available_quantity <= self.critical_threshold

    @property
    def is_below_minimum(self) -> bool:
        return self.available_quantity <= self.minimum_stock


@dataclass
class BloodUnit:
    id: str
    component_id: str = ""
    facility_id: str = ""
    blood_group: str = ""
    rh_factor: str = ""
    component: str = ""
    bag_identifier: str = ""
    isbt_128_code: str = ""
    barcode: str = ""
    volume_ml: float | None = None
    collection_date: datetime | None = None
    expiry_date: datetime | None = None
    donor_id: str = ""
    donor_name: str = ""
    status: str = "available"
    storage_location: str = ""
    location_facility_id: str = ""
    screening_complete: bool = False
    processing_complete: bool = False
    crossmatch_compatible: str = ""
    issued_to: str = ""
    issued_at: datetime | None = None
    transfused_at: datetime | None = None
    discarded_at: datetime | None = None
    discard_reason: str = ""
    recalled: bool = False
    recall_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        if self.expiry_date:
            return datetime.now(UTC) >= self.expiry_date
        return False

    @property
    def days_until_expiry(self) -> int | None:
        if self.expiry_date:
            return (self.expiry_date - datetime.now(UTC)).days
        return None


@dataclass
class Crossmatch:
    id: str
    patient_id: str = ""
    patient_name: str = ""
    patient_blood_group: str = ""
    patient_rh_factor: str = ""
    unit_id: str = ""
    unit_identifier: str = ""
    blood_group: str = ""
    crossmatch_type: CrossmatchType = CrossmatchType.FULL
    status: CrossmatchStatus = CrossmatchStatus.PENDING
    abo_compatible: bool = False
    rh_compatible: bool = False
    crossmatch_result: str = ""
    performed_by: str = ""
    performed_at: datetime | None = None
    verified_by: str = ""
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_compatible(self) -> bool:
        return self.status == CrossmatchStatus.COMPATIBLE


@dataclass
class Transfusion:
    id: str
    patient_id: str = ""
    patient_name: str = ""
    patient_blood_group: str = ""
    patient_rh_factor: str = ""
    medical_record_number: str = ""
    unit_id: str = ""
    unit_identifier: str = ""
    blood_group: str = ""
    component: str = ""
    volume_ml: float | None = None
    crossmatch_id: str = ""
    ordered_by: str = ""
    order_datetime: datetime | None = None
    administered_by: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    pre_vitals: dict[str, Any] = field(default_factory=dict)
    post_vitals: dict[str, Any] = field(default_factory=dict)
    status: TransfusionStatus = TransfusionStatus.ORDERED
    verification_method: str = "manual"
    verified_by: str = ""
    verified_at: datetime | None = None
    patient_verified: bool = False
    unit_verified: bool = False
    consent_verified: bool = False
    rate_ml_per_hour: float | None = None
    infusion_pump_id: str = ""
    bedside_verification_complete: bool = False
    reaction_occurred: bool = False
    reaction_type: TransfusionReactionType | None = None
    reaction_severity: TransfusionReactionSeverity | None = None
    reaction_time: datetime | None = None
    reaction_description: str = ""
    reaction_intervention: str = ""
    outcome: str = ""
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BloodRequest:
    id: str
    patient_id: str = ""
    patient_name: str = ""
    medical_record_number: str = ""
    facility_id: str = ""
    department: str = ""
    requested_by: str = ""
    physician_name: str = ""
    blood_group: str = ""
    rh_factor: str = ""
    component: str = ""
    units_requested: int = 1
    urgency: str = "routine"
    indication: str = ""
    crossmatch_required: bool = True
    status: str = "pending"
    approved_by: str = ""
    approved_at: datetime | None = None
    fulfilled_units: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InventoryMovement:
    id: str
    unit_id: str = ""
    facility_id: str = ""
    from_location: str = ""
    to_location: str = ""
    movement_type: InventoryMovementType = InventoryMovementType.RECEIVED
    performed_by: str = ""
    performed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str = ""
