from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.models.base import AuditMixin, SoftDeleteMixin
from app.pharmacy.base import (
    CanonicalEntity,
    GlobalCatalogEntity,
    PharmacyBase,
    TenantScopedEntity,
)
from app.pharmacy.enums import (
    DispenseStatus,
    PrescriptionStatus,
)


class DrugCatalog(GlobalCatalogEntity):
    """The National Drug Catalog (CANONICAL_DRUG_CONTRACT §1).

    Every column below exists in the migration-built PostgreSQL schema with
    the type declared here; the physical schema is authoritative and this
    model follows it, not the other way round.

    Identity (contract §2, §3):

    * ``id`` — ``INTEGER``, database-assigned, internal only, the target of
      every relational foreign key. Never exposed as the public identity.
    * ``drug_id`` — ``UUID4``, server-generated, ``NOT NULL``, ``UNIQUE``,
      immutable. The only identifier that may appear in a public API path,
      payload, export or report as *the* identity of a drug. It is a GULA
      platform identity, **not** a Ministry of Health national registration
      number.
    * ``drug_code`` — mutable business/catalog code (contract §4). Unique and
      searchable, but never a key of any kind.

    Tenancy (contract §6): the catalog is global national reference data and
    has no tenant column. There is none physically, so a ``lab_id`` filter
    here would match nothing and must never be added.
    """

    __tablename__ = "pharmacy_drug_catalog"

    # -- identity -----------------------------------------------------------
    # Generated in Python rather than by a column default: the physical column
    # is NOT NULL with no server default, so a write that fails to supply an
    # identity is rejected by the database instead of silently receiving one.
    drug_id = Column(
        # sqlalchemy.Uuid renders as PostgreSQL UUID on the real schema while
        # staying portable, so tests that still build from ORM metadata on
        # another dialect keep working during M2-M4.
        Uuid(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        default=uuid.uuid4,
    )
    drug_code = Column(String(50), nullable=False, unique=True, index=True)

    # -- naming and classification -----------------------------------------
    drug_name = Column(String(300), nullable=False)
    drug_name_ar = Column(String(300), nullable=True)
    generic_name = Column(String(300), nullable=True, index=True)
    drug_class = Column(String(100), nullable=True)
    therapeutic_category = Column(String(100), nullable=True)
    atc_code = Column(String(20), nullable=True, index=True)

    # -- presentation -------------------------------------------------------
    # dosage_form and route_of_administration are VARCHAR physically, not
    # PostgreSQL enums. The DosageForm / RouteOfAdministration enums remain the
    # vocabulary for request validation at the schema layer; they are not the
    # storage type.
    dosage_form = Column(String(50), nullable=False)
    strength = Column(String(50), nullable=True)
    unit = Column(String(20), nullable=True)
    route_of_administration = Column(String(50), nullable=True)
    package_description = Column(String(200), nullable=True)

    # -- regulatory ---------------------------------------------------------
    is_controlled_substance = Column(Boolean, nullable=True, default=False)
    controlled_substance_schedule = Column(String(10), nullable=True)
    requires_prescription = Column(Boolean, nullable=True, default=True)
    is_antibiotic = Column(Boolean, nullable=True, default=False)
    is_refrigerated = Column(Boolean, nullable=True, default=False)

    # -- dosing -------------------------------------------------------------
    max_daily_dosage = Column(String(100), nullable=True)
    max_daily_dosage_mg = Column(Double, nullable=True)

    # -- provenance ---------------------------------------------------------
    manufacturer = Column(String(200), nullable=True)
    country_of_origin = Column(String(100), nullable=True)

    is_active = Column(Boolean, nullable=True, default=True)

    # -- external identifiers (contract §11: each in its own column) --------
    sync_id = Column(String(26), nullable=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    __table_args__ = ({"extend_existing": True},)

    def __repr__(self) -> str:
        return f"<DrugCatalog id={self.id} drug_id={self.drug_id} code={self.drug_code}>"

class DrugSupplier(TenantScopedEntity):  # type: ignore[misc]
    """A laboratory's pharmaceutical supplier.

    Tenant-scoped: ``supplier_code`` is unique per lab, not nationally.
    """

    __tablename__ = "pharmacy_drug_suppliers"

    lab_id = Column(Integer, nullable=False, index=True)
    supplier_code = Column(String(50), nullable=False)
    supplier_name = Column(String(200), nullable=False)
    supplier_name_ar = Column(String(200), nullable=True)
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    license_number = Column(String(100), nullable=True)
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    payment_terms = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = (
        UniqueConstraint("lab_id", "supplier_code", name="uq_pharmacy_supplier_lab_code"),
        {"extend_existing": True},
    )


class Warehouse(TenantScopedEntity):  # type: ignore[misc]
    """A physical storage facility owned by one laboratory."""

    __tablename__ = "pharmacy_warehouses"

    lab_id = Column(Integer, nullable=False, index=True)
    warehouse_code = Column(String(30), nullable=False)
    warehouse_name = Column(String(200), nullable=False)
    warehouse_name_ar = Column(String(200), nullable=True)
    warehouse_type = Column(String(30), nullable=True)
    location = Column(String(300), nullable=True)
    capacity = Column(Double, nullable=True)
    capacity_unit = Column(String(20), nullable=True)
    temperature_min = Column(Double, nullable=True)
    temperature_max = Column(Double, nullable=True)
    humidity_min = Column(Double, nullable=True)
    humidity_max = Column(Double, nullable=True)
    is_active = Column(Boolean, nullable=True)
    is_refrigerated = Column(Boolean, nullable=True)
    is_controlled_substance_storage = Column(Boolean, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = (
        UniqueConstraint("lab_id", "warehouse_code", name="uq_pharmacy_warehouse_lab_code"),
        {"extend_existing": True},
    )


class Store(TenantScopedEntity):  # type: ignore[misc]
    """A dispensing point inside a warehouse."""

    __tablename__ = "pharmacy_stores"

    lab_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(
        Integer, ForeignKey("pharmacy_warehouses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    store_code = Column(String(30), nullable=False)
    store_name = Column(String(200), nullable=False)
    store_name_ar = Column(String(200), nullable=True)
    store_type = Column(String(30), nullable=True)
    location = Column(String(300), nullable=True)
    is_active = Column(Boolean, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = (
        UniqueConstraint("lab_id", "store_code", name="uq_pharmacy_store_lab_code"),
        {"extend_existing": True},
    )


class DrugBatch(TenantScopedEntity):  # type: ignore[misc]
    """A received lot of one catalog drug held by one laboratory.

    Identity (P0-2 M4). Internal key ``id`` (Integer); public identity
    ``batch_id`` (UUID4) because the internal key is never published
    (CANONICAL_DRUG_CONTRACT §3). ``batch_number`` is the mutable business
    lot code and is unique only within ``(lab_id, drug_id)`` — never a key.

    The catalog reference is ``drug_id``, not ``drug_catalog_id``. That is not
    a naming preference: ``pharmacy_drug_batches_drug_id_fkey`` is an enforced
    constraint onto ``pharmacy_drug_catalog(id)``, while ``drug_catalog_id``
    has never existed as a physical column. The previous ORM mapped the name
    that does not exist, which is why every batch INSERT failed.
    """

    __tablename__ = "pharmacy_drug_batches"

    batch_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    supplier_id = Column(
        Integer, ForeignKey("pharmacy_drug_suppliers.id", ondelete="SET NULL"), nullable=True
    )
    batch_number = Column(String(100), nullable=False)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    # Quantities are DOUBLE PRECISION physically: a dispensed amount can be
    # fractional (half a tablet, millilitres), so an Integer would silently
    # truncate stock.
    quantity_received = Column(Double, nullable=False)
    quantity_remaining = Column(Double, nullable=False)
    unit_cost = Column(Numeric(12, 4), nullable=True)
    selling_price = Column(Numeric(12, 4), nullable=True)
    # VARCHAR physically, not a PostgreSQL enum type. The StorageCondition
    # enum remains the source of valid values for application code.
    storage_condition = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    received_by = Column(Integer, nullable=True)
    is_quarantined = Column(Boolean, nullable=True, default=False)
    quarantine_reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    sync_id = Column(String(26), nullable=True, index=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    # selectin, not joined: a joined eager load emits a LEFT OUTER JOIN and
    # PostgreSQL cannot apply FOR UPDATE to the nullable side of one, which
    # would break every locked read of a batch during a stock change.
    drug = relationship("DrugCatalog", lazy="selectin")
    supplier = relationship("DrugSupplier", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("lab_id", "batch_number", "drug_id", name="uq_pharmacy_batch_lab_number_drug"),
        Index("ix_pharmacy_drug_batches_expiry_status", "expiry_date", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<DrugBatch id={self.id} batch_id={self.batch_id} number={self.batch_number}>"


class Prescription(TenantScopedEntity):  # type: ignore[misc]
    """A prescription written for one patient at one laboratory.

    Identity (P0-2 M4): internal ``id`` (Integer), public ``prescription_id``
    (UUID4), business code ``prescription_number`` (unique per lab).

    ``prescribed_by`` is the prescriber's NAME as free text and
    ``prescriber_license`` their licence number — the physical schema has no
    practitioner foreign key. The previous ORM declared ``prescriber_id``,
    which does not exist; M4 does not invent a practitioner relationship the
    schema does not define.
    """

    __tablename__ = "pharmacy_prescriptions"

    prescription_id = Column(
        Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )

    lab_id = Column(Integer, nullable=False, index=True)
    # Integer foreign key to the core `patients` table, which belongs to a
    # different declarative base; the constraint is enforced physically.
    patient_id = Column(Integer, nullable=True, index=True)
    prescription_number = Column(String(30), nullable=False)
    prescribed_by = Column(String(200), nullable=False)
    prescriber_license = Column(String(100), nullable=True)
    prescribed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    prescription_type = Column(String(30), nullable=True)
    status = Column(String(20), nullable=False, default=PrescriptionStatus.ACTIVE.value)
    diagnosis_code = Column(String(20), nullable=True)
    diagnosis_description = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    is_stat = Column(Boolean, nullable=True, default=False)
    is_verbal = Column(Boolean, nullable=True, default=False)
    is_emergency = Column(Boolean, nullable=True, default=False)
    refills_allowed = Column(Integer, nullable=True, default=0)
    refills_used = Column(Integer, nullable=True, default=0)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("lab_id", "prescription_number", name="uq_pharmacy_rx_lab_number"),
        Index("ix_pharmacy_prescriptions_lab_status", "lab_id", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Prescription id={self.id} prescription_id={self.prescription_id}>"


class PrescriptionItem(CanonicalEntity):  # type: ignore[misc]
    """One prescribed medication line.

    Deliberately NOT tenant-scoped: the physical table has no ``lab_id``.
    Tenancy is inherited from the parent prescription, so a query must reach
    an item through its prescription rather than filtering the item directly.
    """

    __tablename__ = "pharmacy_prescription_items"

    prescription_item_id = Column(
        Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )

    prescription_id = Column(
        Integer, ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True)
    # Denormalised display copy of the drug's name. The authoritative
    # relationship is drug_id (contract §7).
    drug_name = Column(String(300), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50), nullable=True)
    duration = Column(String(100), nullable=True)
    quantity = Column(Double, nullable=False)
    quantity_unit = Column(String(20), nullable=True)
    refill_quantity = Column(Double, nullable=True)
    instructions = Column(Text, nullable=True)
    patient_education = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    is_substitution_allowed = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    prescription = relationship("Prescription", back_populates="items")
    drug = relationship("DrugCatalog", lazy="selectin")

    __table_args__ = (
        Index("ix_pharmacy_prescription_items_rx_status", "prescription_id", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<PrescriptionItem id={self.id} prescription_item_id={self.prescription_item_id}>"


class DispenseRecord(TenantScopedEntity):  # type: ignore[misc]
    """An immutable record that a quantity of a drug was handed to a patient."""

    __tablename__ = "pharmacy_dispense_records"

    lab_id = Column(Integer, nullable=False, index=True)
    prescription_id = Column(
        Integer, ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prescription_item_id = Column(
        Integer, ForeignKey("pharmacy_prescription_items.id", ondelete="SET NULL"), nullable=True
    )
    patient_id = Column(Integer, nullable=True, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True)
    dispense_number = Column(String(30), nullable=False)
    dispensed_by = Column(Integer, nullable=False)
    dispensed_at = Column(
        DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(UTC)
    )
    quantity_dispensed = Column(Double, nullable=False)
    quantity_unit = Column(String(20), nullable=True)
    days_supply = Column(Integer, nullable=True)
    dosage_dispensed = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)
    label_notes = Column(Text, nullable=True)
    is_verified = Column(Boolean, nullable=True, default=False)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    is_counselled = Column(Boolean, nullable=True, default=False)
    counselled_by = Column(Integer, nullable=True)
    counselled_at = Column(DateTime(timezone=True), nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    __table_args__ = (
        UniqueConstraint("lab_id", "dispense_number", name="uq_pharmacy_dispense_lab_number"),
        {"extend_existing": True},
    )


class DispenseQueue(TenantScopedEntity):  # type: ignore[misc]
    """A prescription waiting to be prepared, verified and handed over."""

    __tablename__ = "pharmacy_dispense_queue"

    queue_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)

    lab_id = Column(Integer, nullable=False, index=True)
    prescription_id = Column(
        Integer, ForeignKey("pharmacy_prescriptions.id", ondelete="CASCADE"), nullable=False
    )
    prescription_item_id = Column(
        Integer, ForeignKey("pharmacy_prescription_items.id", ondelete="SET NULL"), nullable=True
    )
    patient_id = Column(Integer, nullable=True)
    queue_number = Column(String(20), nullable=False)
    priority = Column(Integer, nullable=True, default=0)
    status = Column(String(20), nullable=False, default=DispenseStatus.PENDING.value)
    entered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    assigned_to = Column(Integer, nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_wait_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    prescription = relationship("Prescription", lazy="selectin")

    __table_args__ = (
        Index("ix_pharmacy_dispense_queue_lab_status", "lab_id", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<DispenseQueue id={self.id} queue_id={self.queue_id}>"


class StockLevel(TenantScopedEntity):  # type: ignore[misc]
    """Quantity of one drug batch held at one store, for one laboratory.

    Inventory is tenant-scoped and references the GLOBAL catalog by internal
    foreign key (contract §9). It never duplicates catalog identity: there is
    one national drug record, and many per-facility stock rows pointing at it.
    """

    __tablename__ = "pharmacy_stock_levels"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(
        Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    store_id = Column(
        Integer, ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    warehouse_id = Column(
        Integer, ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True
    )
    quantity_on_hand = Column(Double, nullable=False, default=0)
    quantity_reserved = Column(Double, nullable=True, default=0)
    quantity_available = Column(Double, nullable=False, default=0)
    quantity_on_order = Column(Double, nullable=True, default=0)
    reorder_point = Column(Double, nullable=True)
    reorder_quantity = Column(Double, nullable=True)
    maximum_level = Column(Double, nullable=True)
    unit = Column(String(20), nullable=False, default="unit")
    location = Column(String(100), nullable=True)
    last_counted_at = Column(DateTime(timezone=True), nullable=True)
    last_counted_by = Column(Integer, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    # selectin: this row is locked with FOR UPDATE during every stock change.
    batch = relationship("DrugBatch", lazy="selectin")

    __table_args__ = (
        # The name is the one the schema already carries, not a new one: M4
        # declared `uq_pharmacy_stock_lab_drug_batch_store`, which never existed
        # physically.
        #
        # NULLS NOT DISTINCT because `batch_id` and `store_id` are legitimately
        # NULL — receiving a batch opens a stock row before any dispensing point
        # is assigned — and SQL's default treats each NULL as unique, so the
        # constraint silently guaranteed nothing for exactly those rows.
        UniqueConstraint(
            "lab_id",
            "drug_id",
            "batch_id",
            "store_id",
            name="uq_pharmacy_stock",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_pharmacy_stock_levels_lab_available", "lab_id", "quantity_available"),
        {"extend_existing": True},
    )


class StockMovement(TenantScopedEntity):  # type: ignore[misc]
    """An append-only record of one stock quantity change.

    ``reference_type`` / ``reference_id`` are a polymorphic pointer at whatever
    caused the movement. ``reference_id`` is INTEGER physically, so it holds
    the referring row's internal key; it carries no foreign key because the
    target table varies by ``reference_type``.
    """

    __tablename__ = "pharmacy_stock_movements"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(
        Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    movement_type = Column(String(30), nullable=False)
    quantity = Column(Double, nullable=False)
    unit = Column(String(20), nullable=False, default="unit")
    from_location = Column(String(100), nullable=True)
    to_location = Column(String(100), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    reason = Column(String(200), nullable=True)
    performed_by = Column(Integer, nullable=False)
    performed_at = Column(
        DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(UTC)
    )
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = ({"extend_existing": True},)


class InventoryTransfer(TenantScopedEntity):  # type: ignore[misc]
    """A movement of stock between two stores or warehouses."""

    __tablename__ = "pharmacy_inventory_transfers"

    transfer_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)

    lab_id = Column(Integer, nullable=False, index=True)
    from_store_id = Column(
        Integer, ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    to_store_id = Column(
        Integer, ForeignKey("pharmacy_stores.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_warehouse_id = Column(
        Integer, ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True
    )
    to_warehouse_id = Column(
        Integer, ForeignKey("pharmacy_warehouses.id", ondelete="SET NULL"), nullable=True
    )
    transfer_number = Column(String(30), nullable=False)
    transfer_type = Column(String(30), nullable=False, default="internal")
    status = Column(String(20), nullable=False, default="pending")
    requested_by = Column(Integer, nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(UTC))
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_by = Column(Integer, nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(Integer, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    # There is no general `reason` column: the schema records only why a
    # transfer was cancelled. Free-text context goes in `notes`.
    cancelled_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    items = relationship(
        "InventoryTransferItem", back_populates="transfer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("lab_id", "transfer_number", name="uq_pharmacy_transfer_lab_number"),
        Index("ix_pharmacy_inventory_transfers_lab_status", "lab_id", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<InventoryTransfer id={self.id} transfer_id={self.transfer_id}>"


class InventoryTransferItem(PharmacyBase):  # type: ignore[misc]
    """One drug line within a transfer. Tenancy comes from the parent transfer.

    Declared directly on the base rather than on :class:`CanonicalEntity`,
    because the physical table deliberately carries neither soft-delete
    columns nor ``updated_by``: a transfer line is a record of what was moved,
    and a transfer is withdrawn at the header through ``cancelled_reason``
    rather than by deleting its lines. The columns below are exactly the
    physical ones.
    """

    __tablename__ = "pharmacy_inventory_transfer_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    transfer_id = Column(
        Integer, ForeignKey("pharmacy_inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Double, nullable=False)
    unit = Column(String(20), nullable=False, default="unit")
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    created_by = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    transfer = relationship("InventoryTransfer", back_populates="items")

    __table_args__ = ({"extend_existing": True},)


class DrugReturn(TenantScopedEntity):  # type: ignore[misc]
    """Stock returned by a patient or to a supplier."""

    __tablename__ = "pharmacy_drug_returns"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True)
    return_type = Column(String(30), nullable=False)
    return_reason = Column(Text, nullable=False)
    quantity = Column(Double, nullable=False)
    unit = Column(String(20), nullable=False, default="unit")
    patient_id = Column(Integer, nullable=True)
    returned_by = Column(Integer, nullable=True)
    returned_at = Column(
        DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(UTC)
    )
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    disposition = Column(String(30), nullable=True)
    disposition_notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = ({"extend_existing": True},)


class WasteRecord(TenantScopedEntity):  # type: ignore[misc]
    """Stock destroyed or disposed of, with the required witness."""

    __tablename__ = "pharmacy_waste_records"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(
        Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    waste_type = Column(String(30), nullable=False)
    waste_reason = Column(Text, nullable=False)
    quantity = Column(Double, nullable=False)
    unit = Column(String(20), nullable=False, default="unit")
    witnessed_by = Column(Integer, nullable=True)
    wasted_by = Column(Integer, nullable=False)
    wasted_at = Column(
        DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(UTC)
    )
    disposal_method = Column(String(100), nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = ({"extend_existing": True},)


class Recall(TenantScopedEntity):  # type: ignore[misc]
    """A drug or batch recall being tracked to completion."""

    __tablename__ = "pharmacy_recalls"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id = Column(
        Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recall_number = Column(String(50), nullable=False)
    recall_reason = Column(Text, nullable=False)
    recall_source = Column(String(200), nullable=True)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    initiated_by = Column(Integer, nullable=True)
    initiated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    affected_quantity = Column(Double, nullable=True)
    recovered_quantity = Column(Double, nullable=True)
    patient_notification_required = Column(Boolean, nullable=True, default=False)
    notified_patients_count = Column(Integer, nullable=True, default=0)
    actions_taken = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    __table_args__ = (
        Index("ix_pharmacy_recalls_lab_status", "lab_id", "status"),
        {"extend_existing": True},
    )


class InventoryForecast(TenantScopedEntity):  # type: ignore[misc]
    """A predicted consumption window for one drug at one laboratory."""

    __tablename__ = "pharmacy_inventory_forecasts"

    lab_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer, ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False, index=True
    )
    forecast_date = Column(Date, nullable=False)
    forecast_period_start = Column(Date, nullable=False)
    forecast_period_end = Column(Date, nullable=False)
    predicted_consumption = Column(Double, nullable=False)
    predicted_consumption_unit = Column(String(20), nullable=False, default="unit")
    confidence_lower = Column(Double, nullable=True)
    confidence_upper = Column(Double, nullable=True)
    recommended_reorder_quantity = Column(Double, nullable=True)
    current_stock = Column(Double, nullable=True)
    days_until_stockout = Column(Integer, nullable=True)
    seasonal_factor = Column(Double, nullable=True)
    trend_factor = Column(Double, nullable=True)
    model_used = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)

    __table_args__ = (
        Index(
            "ix_pharmacy_inventory_forecasts_lab_drug_period",
            "lab_id",
            "drug_id",
            "forecast_period_start",
        ),
        {"extend_existing": True},
    )


class DrugInteractionRule(CanonicalEntity):
    """Drug-drug interaction, keyed on two catalog foreign keys.

    Global national reference data: no tenant column exists physically.
    ``severity`` is VARCHAR in the schema, not a PostgreSQL enum; the
    InteractionSeverity vocabulary validates input at the schema layer.
    """

    __tablename__ = "pharmacy_drug_interaction_rules"

    drug_id_a = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drug_id_b = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=True)
    clinical_consequence = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    evidence_level = Column(String(20), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, unique=True)

    __table_args__ = (
        UniqueConstraint("drug_id_a", "drug_id_b", name="uq_pharmacy_interaction_pair"),
        {"extend_existing": True},
    )


class ContraindicationRule(CanonicalEntity):
    """Contraindication for one drug. Global reference data.

    The authoritative link is ``drug_id`` -> ``pharmacy_drug_catalog.id``.
    There is no ``drug_code`` column here, so editing a business code cannot
    detach this rule (contract §7).
    """

    __tablename__ = "pharmacy_contraindication_rules"

    drug_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contraindication_type = Column(String(50), nullable=False, index=True)
    contraindication_value = Column(String(300), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    clinical_consequence = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    evidence_level = Column(String(20), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, unique=True)

    __table_args__ = ({"extend_existing": True},)


class AllergyRule(CanonicalEntity):
    """Drug-allergen rule. Global reference data.

    ``allergen_code`` is a coding-system code for the allergen, not a drug
    identity; the drug relationship is ``drug_id``.
    """

    __tablename__ = "pharmacy_allergy_rules"

    drug_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allergen = Column(String(200), nullable=False, index=True)
    allergen_code = Column(String(50), nullable=True)
    reaction_type = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    evidence_level = Column(String(20), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, unique=True)

    __table_args__ = ({"extend_existing": True},)


class DoseGuideline(CanonicalEntity):
    """Dosing guidance for one drug. Global reference data.

    Doses are numeric in the schema (double precision), not strings, and the
    age bounds are in years rather than months.
    """

    __tablename__ = "pharmacy_dose_guidelines"

    drug_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    route = Column(String(50), nullable=True)
    indication = Column(String(300), nullable=True)

    age_min_years = Column(Double, nullable=True)
    age_max_years = Column(Double, nullable=True)
    weight_min_kg = Column(Double, nullable=True)
    weight_max_kg = Column(Double, nullable=True)

    dose_min = Column(Double, nullable=False)
    dose_max = Column(Double, nullable=True)
    dose_unit = Column(String(30), nullable=False)
    frequency = Column(String(100), nullable=False)
    max_daily_dose = Column(Double, nullable=True)
    duration = Column(String(100), nullable=True)

    renal_adjustment = Column(Text, nullable=True)
    hepatic_adjustment = Column(Text, nullable=True)
    pediatric_note = Column(Text, nullable=True)
    geriatric_note = Column(Text, nullable=True)
    pregnancy_category = Column(String(10), nullable=True)

    evidence_level = Column(String(20), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, unique=True)

    __table_args__ = (
        Index("ix_pharmacy_dose_guidelines_indication", "drug_id", "indication"),
        {"extend_existing": True},
    )


class DrugMonitoring(TenantScopedEntity):
    """A therapeutic-monitoring OBSERVATION for one patient on one drug.

    Note the semantics: the physical table records a monitoring *event*
    (a patient, a date, a measured value), not a drug-level monitoring rule.
    The previous ORM modelled it as a per-drug rule keyed on ``drug_code``
    with ``required_tests`` / ``therapeutic_range`` — none of which exists in
    the schema. This model follows the schema.

    Unlike the other rule tables this one IS tenant-scoped: ``lab_id`` is
    NOT NULL with a foreign key to ``labs``, because a monitoring result is
    patient data belonging to one laboratory.

    ``patient_id``, ``prescription_id`` and ``performed_by`` carry no ORM
    foreign key: ``patients`` and ``lab_users`` belong to a different
    declarative base, and ``pharmacy_prescriptions`` still has a String(26)
    key until M4. All four constraints exist and are enforced physically.
    """

    __tablename__ = "pharmacy_drug_monitoring"

    lab_id = Column(Integer, nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    drug_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prescription_id = Column(Integer, nullable=True)

    monitoring_type = Column(String(50), nullable=False)
    monitoring_date = Column(DateTime(timezone=True), nullable=False)

    value = Column(String(200), nullable=True)
    value_numeric = Column(Double, nullable=True)
    unit = Column(String(20), nullable=True)
    therapeutic_range_low = Column(Double, nullable=True)
    therapeutic_range_high = Column(Double, nullable=True)
    is_within_range = Column(Boolean, nullable=True)

    adverse_reaction = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)
    action_taken = Column(Text, nullable=True)
    performed_by = Column(Integer, nullable=True)
    next_monitoring_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    sync_id = Column(String(26), nullable=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    __table_args__ = (
        Index(
            "ix_pharmacy_drug_monitoring_patient_drug",
            "patient_id",
            "drug_id",
            "monitoring_date",
        ),
        {"extend_existing": True},
    )


class ClinicalGuideline(SoftDeleteMixin, AuditMixin, PharmacyBase):  # type: ignore[misc]
    """A national clinical guideline. Global reference data, not tenant-scoped.

    The physical table has no ``lab_id``: a guideline is curated nationally and
    read by every laboratory, exactly like the drug catalog (contract §6). The
    previous ORM inherited a tenant column that does not exist.

    This is the one Pharmacy entity that carries no optimistic-lock counter:
    its ``version`` column is ``VARCHAR(20) NOT NULL`` and holds the
    *guideline's own document version* ("2024.1"), which is why it is declared
    below rather than inherited. Inheriting :class:`CanonicalEntity` here would
    silently redefine that column as the ``Integer`` lock counter.
    """

    __tablename__ = "pharmacy_clinical_guidelines"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # The guideline's published document version, not a concurrency counter.
    version = Column(String(20), nullable=False, default="1")

    guideline_code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)
    guideline_type = Column(String(50), nullable=False, index=True)
    condition = Column(String(200), nullable=True)
    icd_code = Column(String(20), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    drug_recommendations = Column(JSON, nullable=True)
    algorithms = Column(JSON, nullable=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    sync_id = Column(String(26), nullable=True, index=True, unique=True)
    fhir_id = Column(String(64), nullable=True)
    fhir_resource_type = Column(String(32), nullable=True)

    __table_args__ = ({"extend_existing": True},)

class PharmacySale(TenantScopedEntity):  # type: ignore[misc]
    """Institution-scoped pharmacy POS sale.

    A sale is the commercial envelope around stock movements, billing, and the
    citizen medication record. It never stores payment credentials.

    Identity (P0-2 M3). The primary key is the internal Integer key every
    physical Pharmacy table uses; the public identity is ``sale_id`` (UUID4),
    because the internal key must never be exposed as an entity's public
    identity (CANONICAL_DRUG_CONTRACT §3). ``sale_number`` stays a mutable
    business code (§4) and is never a key. The previous ``String(26)``
    ``_ulid()`` key was a Generation B assumption and is gone.
    """

    __tablename__ = "pharmacy_sales"

    # PUBLIC_ID (contract §11). Named `<noun>_id` after the platform's existing
    # public UUID identifiers — pharmacy_drug_catalog.drug_id, and the
    # provider_id/campaign_id/interaction_id family — rather than a new suffix.
    sale_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)

    # TENANT_ID. Declared here, not inherited: the physical foreign key to
    # `labs` lives in the migration because `labs` is on a different
    # declarative base (same reasoning as DrugMonitoring).
    lab_id = Column(Integer, nullable=False, index=True)

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

    def __repr__(self) -> str:
        return f"<PharmacySale id={self.id} sale_id={self.sale_id} number={self.sale_number}>"


class PharmacySaleLine(TenantScopedEntity):  # type: ignore[misc]
    """One stockable medication line within a POS sale.

    Identity (P0-2 M3): internal Integer key, public ``sale_line_id`` (UUID4).

    ``drug_catalog_id`` is an INTERNAL_FK (contract §11) onto the catalog's
    Integer key — this is P0-2-SUBBLOCKER-A Group A, resolved here.

    ``batch_id`` and ``prescription_id`` are Group B and remain
    ``String(26)``: ``pharmacy_drug_batches`` and ``pharmacy_prescriptions``
    are integer-keyed physically, but their application models are still
    Generation B, so no canonical batch/prescription identity exists to point
    at yet. They deliberately carry no ORM ``ForeignKey``: the previous
    declarations named a constraint PostgreSQL cannot create (varchar → integer)
    and that the database therefore never had. Reconciled by M4.
    """

    __tablename__ = "pharmacy_sale_lines"

    sale_line_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4)

    lab_id = Column(Integer, nullable=False, index=True)

    sale_id = Column(Integer, ForeignKey("pharmacy_sales.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_catalog_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # P0-2-SUBBLOCKER-A Group B, resolved by M4: both targets now have a
    # canonical integer-keyed application model to point at.
    batch_id = Column(
        Integer, ForeignKey("pharmacy_drug_batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    prescription_id = Column(
        Integer, ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
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
    drug = relationship("DrugCatalog", lazy="joined")

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

    def __repr__(self) -> str:
        return f"<PharmacySaleLine id={self.id} sale_line_id={self.sale_line_id}>"


class DrugSubstitutionRule(TenantScopedEntity):  # type: ignore[misc]
    """Institution-approved mapping between a requested drug and an equivalent.

    The catalog references were already canonical Integer foreign keys from the
    NR-003 correction; M3 reconciles the entity's own identity to match.
    """

    __tablename__ = "pharmacy_drug_substitution_rules"

    substitution_rule_id = Column(
        Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )

    lab_id = Column(Integer, nullable=False, index=True)

    # Foreign keys to the catalog's internal Integer primary key (NR-003 / ADR-006).
    # These are relational references, not the public drug identity: the public
    # identity is DrugCatalog.drug_id (UUID4) and is never used as a foreign key.
    original_drug_catalog_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alternative_drug_catalog_id = Column(
        Integer,
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

    def __repr__(self) -> str:
        return f"<DrugSubstitutionRule id={self.id} substitution_rule_id={self.substitution_rule_id}>"


class DrugSubstitutionRequest(TenantScopedEntity):  # type: ignore[misc]
    """Auditable approval record consumed by a pharmacy POS sale.

    Identity (P0-2 M3): internal Integer key, public
    ``substitution_request_id`` (UUID4).

    ``original_drug_catalog_id`` and ``alternative_drug_catalog_id`` are
    P0-2-SUBBLOCKER-A Group A: INTERNAL_FKs onto the catalog's Integer key,
    now with the foreign keys the database could never hold while they were
    ``String(26)``.

    ``prescription_id`` is Group B and stays ``String(26)`` without a foreign
    key until M4 reconciles prescription identity.
    """

    __tablename__ = "pharmacy_drug_substitution_requests"

    substitution_request_id = Column(
        Uuid(as_uuid=True), nullable=False, unique=True, index=True, default=uuid.uuid4
    )

    lab_id = Column(Integer, nullable=False, index=True)

    rule_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_substitution_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    original_drug_catalog_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    alternative_drug_catalog_id = Column(
        Integer,
        ForeignKey("pharmacy_drug_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # P0-2-SUBBLOCKER-A Group B, resolved by M4.
    prescription_id = Column(
        Integer, ForeignKey("pharmacy_prescriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    patient_id = Column(String(26), nullable=True, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="pending")
    reason = Column(String(500), nullable=False)
    approval_level = Column(String(32), nullable=False, default="pharmacist")
    approved_by = Column(String(26), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    patient_consent = Column(Boolean, nullable=False, default=False)
    patient_notified_at = Column(DateTime(timezone=True), nullable=True)
    consumed_sale_id = Column(
        Integer,
        ForeignKey("pharmacy_sales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_ = Column("metadata", JSON, nullable=True)

    rule = relationship("DrugSubstitutionRule", lazy="joined")
    consumed_sale = relationship("PharmacySale", lazy="joined")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_pharmacy_substitution_request_quantity_positive"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'consumed')", name="ck_pharmacy_substitution_request_status"),
        Index("ix_pharmacy_substitution_request_status", "lab_id", "status"),
        Index("ix_pharmacy_substitution_request_patient", "lab_id", "patient_id"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<DrugSubstitutionRequest id={self.id} substitution_request_id={self.substitution_request_id}>"
