from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.pharmacy.base import TenantAuditEntity
from app.pharmacy.enums import (
    DispenseStatus,
    DosageForm,
    DrugCategory,
    InteractionSeverity,
    PrescriptionStatus,
    RouteOfAdministration,
    StockMovementType,
    StorageCondition,
)


class DrugCatalog(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_catalog"

    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    generic_name = Column(String(300), nullable=True)
    brand_name = Column(String(300), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    manufacturer_code = Column(String(50), nullable=True)

    form = Column(SAEnum(DosageForm), nullable=True)
    strength_value = Column(String(50), nullable=True)
    strength_unit = Column(String(50), nullable=True)
    route = Column(SAEnum(RouteOfAdministration), nullable=True)

    category = Column(SAEnum(DrugCategory), nullable=True)
    therapeutic_class = Column(String(200), nullable=True)
    atc_code = Column(String(20), nullable=True)
    atc_description = Column(String(300), nullable=True)

    is_controlled = Column(Boolean, default=False)
    is_narcotic = Column(Boolean, default=False)
    requires_prescription = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    max_daily_dose = Column(String(50), nullable=True)
    min_age = Column(Integer, nullable=True)
    pregnancy_category = Column(String(10), nullable=True)
    lactation_category = Column(String(10), nullable=True)

    ingredients = Column(JSON, nullable=True)
    side_effects = Column(JSON, nullable=True)
    drug_images = Column(JSON, nullable=True)
    barcode_gs1 = Column(String(50), nullable=True)
    barcode_type = Column(String(20), nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_drug_catalog_code", "code"),
        Index("ix_pharmacy_drug_catalog_name", "name"),
        Index("ix_pharmacy_drug_catalog_atc", "atc_code"),
        Index("ix_pharmacy_drug_catalog_category", "category"),
        Index("ix_pharmacy_drug_catalog_active", "is_active"),
        Index("ix_pharmacy_drug_catalog_barcode", "barcode_gs1"),
        {"extend_existing": True},
    )


class DrugBatch(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_batches"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_number = Column(String(100), nullable=False)
    manufacturer_batch = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    manufacturing_date = Column(Date, nullable=True)

    quantity_initial = Column(Integer, nullable=False, default=0)
    quantity_remaining = Column(Integer, nullable=False, default=0)

    storage_condition = Column(SAEnum(StorageCondition), nullable=True)
    location = Column(String(200), nullable=True)

    received_date = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(String(26), nullable=True)

    supplier = Column(String(200), nullable=True)
    cost_price = Column(Numeric(12, 2), nullable=True)
    selling_price = Column(Numeric(12, 2), nullable=True)

    is_quarantined = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_drug_batch_catalog", "drug_catalog_id"),
        Index("ix_pharmacy_drug_batch_number", "batch_number"),
        Index("ix_pharmacy_drug_batch_expiry", "expiry_date"),
        Index("ix_pharmacy_drug_batch_quarantine", "is_quarantined"),
        {"extend_existing": True},
    )


class DrugSupplier(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_suppliers"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(50), nullable=False, unique=True)
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    license_number = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    payment_terms = Column(String(500), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_supplier_code", "code"),
        Index("ix_pharmacy_supplier_name", "name"),
        {"extend_existing": True},
    )


class Prescription(TenantAuditEntity):
    __tablename__ = "pharmacy_prescriptions"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    prescriber_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    prescription_number = Column(String(50), nullable=False, unique=True)
    status = Column(SAEnum(PrescriptionStatus), nullable=False, default=PrescriptionStatus.ACTIVE)
    intent = Column(String(50), nullable=False, default="order")
    priority = Column(String(20), default="routine")

    diagnosis = Column(String(500), nullable=True)
    diagnosis_code = Column(String(50), nullable=True)
    diagnosis_system = Column(String(20), nullable=True)

    authored_on = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    dispense_interval = Column(Integer, nullable=True)
    substitution_allowed = Column(Boolean, default=True)

    note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    signed_by = Column(String(26), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_rx_patient", "patient_id", "status"),
        Index("ix_pharmacy_rx_number", "prescription_number"),
        Index("ix_pharmacy_rx_prescriber", "prescriber_id"),
        Index("ix_pharmacy_rx_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class PrescriptionItem(TenantAuditEntity):
    __tablename__ = "pharmacy_prescription_items"

    prescription_id = Column(
        String(26),
        ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    drug_batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    medication_code = Column(String(50), nullable=True)
    medication_name = Column(String(300), nullable=False)
    strength_value = Column(String(50), nullable=True)
    strength_unit = Column(String(50), nullable=True)
    form = Column(String(100), nullable=True)
    route = Column(String(100), nullable=True)

    dose_quantity = Column(String(50), nullable=True)
    dose_unit = Column(String(50), nullable=True)
    frequency = Column(String(200), nullable=True)
    duration = Column(Integer, nullable=True)
    duration_unit = Column(String(50), nullable=True)

    quantity = Column(Integer, nullable=True)
    quantity_unit = Column(String(50), nullable=True)
    refills = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)

    instructions = Column(Text, nullable=True)
    substitution_allowed = Column(Boolean, default=True)
    status = Column(String(50), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_rx_item_prescription", "prescription_id"),
        Index("ix_pharmacy_rx_item_catalog", "drug_catalog_id"),
        Index("ix_pharmacy_rx_item_medication", "medication_code"),
        {"extend_existing": True},
    )


class DispenseRecord(TenantAuditEntity):
    __tablename__ = "pharmacy_dispense_records"

    prescription_id = Column(
        String(26),
        ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prescription_item_id = Column(
        String(26),
        ForeignKey("pharmacy_prescription_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)

    dispensed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)
    verified_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)

    dispensed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)
    status = Column(SAEnum(DispenseStatus), nullable=False, default=DispenseStatus.PENDING)

    quantity_dispensed = Column(Integer, nullable=False)
    quantity_unit = Column(String(50), nullable=True)
    days_supply = Column(Integer, nullable=True)

    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)

    cost_price = Column(Numeric(12, 2), nullable=True)
    selling_price = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)

    patient_signature = Column(Text, nullable=True)
    pharmacist_notes = Column(Text, nullable=True)
    counseling_provided = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_dispense_patient", "patient_id"),
        Index("ix_pharmacy_dispense_prescription", "prescription_id"),
        Index("ix_pharmacy_dispense_dispenser", "dispensed_by"),
        Index("ix_pharmacy_dispense_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class DispenseQueue(TenantAuditEntity):
    __tablename__ = "pharmacy_dispense_queue"

    prescription_id = Column(
        String(26),
        ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    priority = Column(String(20), default="normal")
    queued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    status = Column(SAEnum(DispenseStatus), nullable=False, default=DispenseStatus.PENDING)

    assigned_to = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    pickup_time = Column(DateTime(timezone=True), nullable=True)
    ready_time = Column(DateTime(timezone=True), nullable=True)
    completion_time = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_queue_prescription", "prescription_id"),
        Index("ix_pharmacy_queue_status", "status"),
        Index("ix_pharmacy_queue_priority", "priority"),
        {"extend_existing": True},
    )


class Warehouse(TenantAuditEntity):
    __tablename__ = "pharmacy_warehouses"

    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_warehouse_code", "code"),
        {"extend_existing": True},
    )


class Store(TenantAuditEntity):
    __tablename__ = "pharmacy_stores"

    warehouse_id = Column(
        String(26),
        ForeignKey("pharmacy_warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    store_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_store_warehouse", "warehouse_id"),
        Index("ix_pharmacy_store_code", "code"),
        {"extend_existing": True},
    )


class StockLevel(TenantAuditEntity):
    __tablename__ = "pharmacy_stock_levels"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    warehouse_id = Column(
        String(26),
        ForeignKey("pharmacy_warehouses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    store_id = Column(
        String(26),
        ForeignKey("pharmacy_stores.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)

    reorder_point = Column(Integer, nullable=True)
    reorder_quantity = Column(Integer, nullable=True)
    max_level = Column(Integer, nullable=True)

    storage_condition = Column(SAEnum(StorageCondition), nullable=True)
    last_count_date = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_stock_drug", "drug_catalog_id"),
        Index("ix_pharmacy_stock_batch", "batch_id"),
        Index("ix_pharmacy_stock_warehouse", "warehouse_id"),
        Index("ix_pharmacy_stock_store", "store_id"),
        Index("ix_pharmacy_stock_reorder", "reorder_point", "available_quantity"),
        {"extend_existing": True},
    )


class StockMovement(TenantAuditEntity):
    __tablename__ = "pharmacy_stock_movements"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    warehouse_id = Column(
        String(26),
        ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    store_id = Column(
        String(26),
        ForeignKey("pharmacy_stores.id", ondelete="SET NULL"),
        nullable=True,
    )

    movement_type = Column(SAEnum(StockMovementType), nullable=False)
    quantity = Column(Integer, nullable=False)

    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(26), nullable=True)

    reason = Column(String(500), nullable=True)
    performed_by = Column(String(26), nullable=True)
    movement_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_movement_drug", "drug_catalog_id"),
        Index("ix_pharmacy_movement_batch", "batch_id"),
        Index("ix_pharmacy_movement_type", "movement_type"),
        Index("ix_pharmacy_movement_date", "movement_date"),
        Index("ix_pharmacy_movement_reference", "reference_type", "reference_id"),
        {"extend_existing": True},
    )


class InventoryTransfer(TenantAuditEntity):
    __tablename__ = "pharmacy_inventory_transfers"

    from_warehouse_id = Column(
        String(26),
        ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_warehouse_id = Column(
        String(26),
        ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_store_id = Column(
        String(26),
        ForeignKey("pharmacy_stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_store_id = Column(
        String(26),
        ForeignKey("pharmacy_stores.id", ondelete="SET NULL"),
        nullable=True,
    )

    status = Column(String(50), nullable=False, default="pending")
    initiated_by = Column(String(26), nullable=True)
    approved_by = Column(String(26), nullable=True)
    dispatch_date = Column(DateTime(timezone=True), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_transfer_from_wh", "from_warehouse_id"),
        Index("ix_pharmacy_transfer_to_wh", "to_warehouse_id"),
        Index("ix_pharmacy_transfer_status", "status"),
        {"extend_existing": True},
    )


class InventoryTransferItem(TenantAuditEntity):
    __tablename__ = "pharmacy_inventory_transfer_items"

    transfer_id = Column(
        String(26),
        ForeignKey("pharmacy_inventory_transfers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    quantity_requested = Column(Integer, nullable=False)
    quantity_shipped = Column(Integer, nullable=True)
    quantity_received = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_transfer_item_transfer", "transfer_id"),
        {"extend_existing": True},
    )


class DrugReturn(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_returns"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="SET NULL"), nullable=True, index=True)
    prescription_id = Column(
        String(26),
        ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    return_reason = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False)
    returned_by = Column(String(26), nullable=True)
    returned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    disposition = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_return_patient", "patient_id"),
        Index("ix_pharmacy_return_drug", "drug_catalog_id"),
        {"extend_existing": True},
    )


class WasteRecord(TenantAuditEntity):
    __tablename__ = "pharmacy_waste_records"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    quantity = Column(Integer, nullable=False)
    waste_reason = Column(String(500), nullable=False)
    witness_by = Column(String(26), nullable=True)
    disposal_method = Column(String(100), nullable=True)
    disposal_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_waste_drug", "drug_catalog_id"),
        Index("ix_pharmacy_waste_date", "disposal_date"),
        {"extend_existing": True},
    )


class Recall(TenantAuditEntity):
    __tablename__ = "pharmacy_recalls"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_batches.id", ondelete="CASCADE"),
        nullable=True,
    )

    recall_reason = Column(String(500), nullable=False)
    recall_date = Column(DateTime(timezone=True), nullable=False)
    initiated_by = Column(String(26), nullable=True)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="active")

    affected_patients = Column(JSON, nullable=True)
    actions_taken = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_recall_drug", "drug_catalog_id"),
        Index("ix_pharmacy_recall_status", "status"),
        {"extend_existing": True},
    )


class InventoryForecast(TenantAuditEntity):
    __tablename__ = "pharmacy_inventory_forecasts"

    drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    predicted_consumption = Column(Integer, nullable=True)
    actual_consumption = Column(Integer, nullable=True)

    reorder_recommendation = Column(String(50), nullable=True)
    recommendation_quantity = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_forecast_drug", "drug_catalog_id"),
        Index("ix_pharmacy_forecast_period", "period_start", "period_end"),
        {"extend_existing": True},
    )


class DrugInteractionRule(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_interaction_rules"

    drug_a_code = Column(String(50), nullable=False, index=True)
    drug_b_code = Column(String(50), nullable=False, index=True)
    severity = Column(SAEnum(InteractionSeverity), nullable=False)
    mechanism = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    evidence_level = Column(String(50), nullable=True)
    reference = Column(String(500), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_interaction_drugs", "drug_a_code", "drug_b_code"),
        {"extend_existing": True},
    )


class ContraindicationRule(TenantAuditEntity):
    __tablename__ = "pharmacy_contraindication_rules"

    drug_code = Column(String(50), nullable=False, index=True)
    condition_code = Column(String(50), nullable=False, index=True)
    condition_system = Column(String(20), nullable=True)
    severity = Column(SAEnum(InteractionSeverity), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_contraindication_drug_condition", "drug_code", "condition_code"),
        {"extend_existing": True},
    )


class AllergyRule(TenantAuditEntity):
    __tablename__ = "pharmacy_allergy_rules"

    allergen_code = Column(String(50), nullable=False, index=True)
    allergen_system = Column(String(20), nullable=True)
    drug_code = Column(String(50), nullable=False, index=True)
    severity = Column(SAEnum(InteractionSeverity), nullable=False)
    reaction = Column(String(500), nullable=True)
    recommendation = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_allergy_allergen_drug", "allergen_code", "drug_code"),
        {"extend_existing": True},
    )


class DoseGuideline(TenantAuditEntity):
    __tablename__ = "pharmacy_dose_guidelines"

    drug_code = Column(String(50), nullable=False, index=True)
    indication_code = Column(String(50), nullable=True)

    age_min_months = Column(Integer, nullable=True)
    age_max_months = Column(Integer, nullable=True)
    weight_min_kg = Column(Float, nullable=True)
    weight_max_kg = Column(Float, nullable=True)

    dose_min = Column(String(50), nullable=False)
    dose_max = Column(String(50), nullable=True)
    dose_unit = Column(String(50), nullable=False)
    frequency = Column(String(200), nullable=True)
    max_daily_dose = Column(String(50), nullable=True)
    route = Column(String(100), nullable=True)

    renal_adjustment = Column(JSON, nullable=True)
    hepatic_adjustment = Column(JSON, nullable=True)

    pediatric_note = Column(Text, nullable=True)
    pregnancy_note = Column(Text, nullable=True)
    breastfeeding_note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_dose_guideline_drug", "drug_code"),
        {"extend_existing": True},
    )


class DrugMonitoring(TenantAuditEntity):
    __tablename__ = "pharmacy_drug_monitoring"

    drug_code = Column(String(50), nullable=False, unique=True, index=True)
    required_tests = Column(JSON, nullable=True)
    monitoring_frequency = Column(String(200), nullable=True)
    therapeutic_range = Column(String(200), nullable=True)
    toxic_level = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = {"extend_existing": True}


class ClinicalGuideline(TenantAuditEntity):
    __tablename__ = "pharmacy_clinical_guidelines"

    guideline_code = Column(String(50), nullable=False, unique=True)
    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)
    drug_codes = Column(JSON, nullable=True)
    condition_codes = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    evidence_level = Column(String(50), nullable=True)
    source = Column(String(200), nullable=True)
    version = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_guideline_code", "guideline_code"),
        Index("ix_pharmacy_guideline_active", "is_active"),
        {"extend_existing": True},
    )


class PharmacySale(TenantAuditEntity):  # type: ignore[misc]
    """Institution-scoped pharmacy POS sale.

    A sale is the commercial envelope around stock movements, billing, and the
    citizen medication record. It never stores payment credentials.
    """

    __tablename__ = "pharmacy_sales"

    patient_id = Column(String(26), nullable=True, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)
    # Integer bridge to the legacy billing patient table. The database migration
    # owns the FK because PharmacyBase and the core Base are separate metadata.
    billing_patient_id = Column(Integer, nullable=True, index=True)
    encounter_id = Column(String(26), nullable=True, index=True)
    # Integer bridge to billing projection; see the migration for the DB FK.
    billing_invoice_id = Column(Integer, nullable=True, index=True)

    sale_number = Column(String(50), nullable=False)
    status = Column(String(24), nullable=False, default="completed")
    currency = Column(String(3), nullable=False, default="IQD")
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    cost_amount = Column(Numeric(12, 2), nullable=False, default=0)
    gross_profit = Column(Numeric(12, 2), nullable=False, default=0)
    payment_status = Column(String(24), nullable=False, default="paid")
    payment_method = Column(String(40), nullable=False, default="synthetic_settlement")
    idempotency_key = Column(String(128), nullable=True)
    sold_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    lines = relationship("PharmacySaleLine", back_populates="sale", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("lab_id", "sale_number", name="uq_pharmacy_sale_lab_number"),
        UniqueConstraint("lab_id", "idempotency_key", name="uq_pharmacy_sale_lab_idempotency"),
        CheckConstraint("subtotal >= 0", name="ck_pharmacy_sale_subtotal_non_negative"),
        CheckConstraint("discount >= 0", name="ck_pharmacy_sale_discount_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_pharmacy_sale_total_non_negative"),
        CheckConstraint("cost_amount >= 0", name="ck_pharmacy_sale_cost_non_negative"),
        Index("ix_pharmacy_sales_lab_status", "lab_id", "status"),
        Index("ix_pharmacy_sales_lab_citizen", "lab_id", "citizen_id"),
        Index("ix_pharmacy_sales_lab_sold_at", "lab_id", "sold_at"),
        {"extend_existing": True},
    )


class PharmacySaleLine(TenantAuditEntity):  # type: ignore[misc]
    """One stockable medication line within a POS sale."""

    __tablename__ = "pharmacy_sale_lines"

    sale_id = Column(String(26), ForeignKey("pharmacy_sales.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_catalog_id = Column(String(26), ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(String(26), ForeignKey("pharmacy_drug_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    prescription_id = Column(String(26), ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    medication_dispense_id = Column(String(26), nullable=True, index=True)

    line_number = Column(Integer, nullable=False)
    barcode = Column(String(64), nullable=True)
    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)
    quantity = Column(Integer, nullable=False)
    quantity_unit = Column(String(50), nullable=True, default="unit")
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    unit_price = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=False, default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    line_cost = Column(Numeric(12, 2), nullable=False, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)

    sale = relationship("PharmacySale", back_populates="lines")

    __table_args__ = (
        UniqueConstraint("sale_id", "line_number", name="uq_pharmacy_sale_line_number"),
        CheckConstraint("quantity > 0", name="ck_pharmacy_sale_line_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_pharmacy_sale_line_unit_price_non_negative"),
        CheckConstraint("unit_cost >= 0", name="ck_pharmacy_sale_line_unit_cost_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_pharmacy_sale_line_total_non_negative"),
        CheckConstraint("line_cost >= 0", name="ck_pharmacy_sale_line_cost_non_negative"),
        Index("ix_pharmacy_sale_lines_sale_drug", "sale_id", "drug_catalog_id"),
        {"extend_existing": True},
    )


class DrugSubstitutionRule(TenantAuditEntity):  # type: ignore[misc]
    """Institution-approved mapping between a requested drug and an equivalent."""

    __tablename__ = "pharmacy_drug_substitution_rules"

    original_drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alternative_drug_catalog_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    equivalence_type = Column(String(32), nullable=False, default="generic")
    approval_level = Column(String(32), nullable=False, default="pharmacist")
    requires_patient_consent = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "lab_id",
            "original_drug_catalog_id",
            "alternative_drug_catalog_id",
            name="uq_pharmacy_substitution_rule_pair",
        ),
        CheckConstraint(
            "original_drug_catalog_id <> alternative_drug_catalog_id",
            name="ck_pharmacy_substitution_rule_distinct_drugs",
        ),
        Index("ix_pharmacy_substitution_rule_active", "lab_id", "is_active"),
        {"extend_existing": True},
    )


class DrugSubstitutionRequest(TenantAuditEntity):  # type: ignore[misc]
    """Auditable approval record consumed by a pharmacy POS sale."""

    __tablename__ = "pharmacy_drug_substitution_requests"

    rule_id = Column(
        String(26),
        ForeignKey("pharmacy_drug_substitution_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    original_drug_catalog_id = Column(String(26), nullable=False, index=True)
    alternative_drug_catalog_id = Column(String(26), nullable=False, index=True)
    prescription_id = Column(String(26), nullable=True, index=True)
    patient_id = Column(String(26), nullable=True, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="pending")
    reason = Column(String(500), nullable=False)
    approval_level = Column(String(32), nullable=False, default="pharmacist")
    approved_by = Column(String(26), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    patient_consent = Column(Boolean, nullable=False, default=False)
    patient_notified_at = Column(DateTime(timezone=True), nullable=True)
    consumed_sale_id = Column(String(26), nullable=True, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_substitution_request_status", "lab_id", "status"),
        Index("ix_pharmacy_substitution_request_patient", "lab_id", "patient_id"),
        {"extend_existing": True},
    )
