"""GULA Blood Network (GBN) — Core Models.

Tables:
  donors            — registered blood donors (linked to citizens/users)
  blood_units       — individual units: whole blood + components (RBC/plasma/platelets/cryo)
  plasma_products   — manufactured plasma-derived products (Factor VIII, Albumin, IVIG…)
  blood_requests    — hospital/clinic requests for blood or components
  transfusions      — recorded transfusion events with crossmatch + reaction tracking
  blood_transfers   — inter-lab unit transfers (national coordination)
"""

from datetime import datetime, timezone, date as date_type, timedelta
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Date, Text, ForeignKey, Index, CheckConstraint,
)
from sqlalchemy.orm import relationship
from ..database import Base


# ── Blood type constants (enforced at API layer; stored as VARCHAR) ───────────

BLOOD_TYPES = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")

# Recipient → compatible donor blood types (whole blood / RBC)
BLOOD_COMPATIBILITY: dict[str, tuple[str, ...]] = {
    "O-":  ("O-",),
    "O+":  ("O-", "O+"),
    "A-":  ("O-", "A-"),
    "A+":  ("O-", "O+", "A-", "A+"),
    "B-":  ("O-", "B-"),
    "B+":  ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"),
}

# Component max shelf-life in days (stored at correct temperature)
COMPONENT_EXPIRY_DAYS: dict[str, int] = {
    "whole":       35,
    "RBC":         42,
    "plasma":      365,   # frozen fresh plasma
    "platelets":   5,
    "cryo":        365,   # cryoprecipitate, frozen
}

COMPONENT_TYPES = tuple(COMPONENT_EXPIRY_DAYS.keys())

# Donor eligibility thresholds (WHO / Iraqi MoH standards)
MIN_DONATION_INTERVAL_DAYS = 90     # ≥ 90 days between whole-blood donations
MIN_HB_MALE_G_DL           = 13.0  # Hb ≥ 13 g/dL for males
MIN_HB_FEMALE_G_DL         = 12.5  # Hb ≥ 12.5 g/dL for females


def _default_now():
    return datetime.now(timezone.utc)


# ── 1. Donors ─────────────────────────────────────────────────────────────────

class Donor(Base):
    """Blood donor registry.

    A donor is linked to an existing `users` row (citizen portal account)
    so the platform can reach them via phone/notification.
    """
    __tablename__ = "gbn_donors"
    __table_args__ = (
        Index("ix_gbn_donors_blood_type",   "blood_type"),
        Index("ix_gbn_donors_lab_id",       "lab_id"),
        Index("ix_gbn_donors_user_id",      "user_id"),
        Index("ix_gbn_donors_eligibility",  "eligibility_status"),
        Index("ix_gbn_donors_city",         "city"),
        CheckConstraint("blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')",
                        name="ck_gbn_donors_blood_type"),
    )

    id               = Column(Integer, primary_key=True, autoincrement=True)
    # Optional link to citizen portal user — enables self-registration + notifications
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),  nullable=True)
    # Lab that registered / manages this donor
    lab_id           = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"),   nullable=True)

    # Demographics
    full_name        = Column(String(200), nullable=False)
    national_id_hash = Column(String(255), nullable=True, index=True)  # HMAC-SHA256
    phone            = Column(String(20),  nullable=True, index=True)
    blood_type       = Column(String(5),   nullable=False)
    gender           = Column(String(1),   nullable=True)   # M / F
    birth_date       = Column(Date,        nullable=True)
    city             = Column(String(100), nullable=True)

    # Donation state
    eligibility_status  = Column(String(30), nullable=False, default="eligible")
    # eligible / deferred_temporary / deferred_permanent
    deferral_reason     = Column(Text,       nullable=True)
    deferral_until      = Column(Date,       nullable=True)   # NULL = permanent
    last_donation_date  = Column(Date,       nullable=True)
    total_donations     = Column(Integer,    nullable=False,  default=0)

    # Recorded at most recent pre-donation screening
    last_hb_g_dl        = Column(Float,      nullable=True)   # Haemoglobin g/dL
    last_weight_kg      = Column(Float,      nullable=True)

    is_active           = Column(Boolean,    nullable=False,  default=True)
    notes               = Column(Text,       nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_default_now)
    updated_at          = Column(DateTime(timezone=True), default=_default_now,
                                 onupdate=_default_now)

    # Relationships
    user       = relationship("User",  foreign_keys=[user_id])
    lab        = relationship("Lab",   foreign_keys=[lab_id])
    donations  = relationship("BloodUnit", back_populates="donor",
                              cascade="all, delete-orphan")

    @property
    def is_eligible(self) -> bool:
        """Quick eligibility check (doesn't re-screen — use screening endpoint)."""
        if self.eligibility_status == "deferred_permanent":
            return False
        if self.eligibility_status == "deferred_temporary":
            if self.deferral_until and date_type.today() < self.deferral_until:
                return False
        if self.last_donation_date:
            days_since = (date_type.today() - self.last_donation_date).days
            if days_since < MIN_DONATION_INTERVAL_DAYS:
                return False
        return True

    @property
    def days_until_eligible(self) -> int | None:
        """Days remaining before donor can donate again (None if already eligible)."""
        if not self.last_donation_date:
            return None
        days_since = (date_type.today() - self.last_donation_date).days
        remaining = MIN_DONATION_INTERVAL_DAYS - days_since
        return max(0, remaining) if remaining > 0 else None


# ── 2. Blood Units ────────────────────────────────────────────────────────────

class BloodUnit(Base):
    """A single collected and processed blood unit or component.

    Created when a donation is processed.  Status lifecycle:
        quarantine → available → reserved → used / expired / discarded
    """
    __tablename__ = "gbn_blood_units"
    __table_args__ = (
        Index("ix_gbn_blood_units_lab_id",       "lab_id"),
        Index("ix_gbn_blood_units_blood_type",    "blood_type"),
        Index("ix_gbn_blood_units_component",     "component"),
        Index("ix_gbn_blood_units_status",        "status"),
        Index("ix_gbn_blood_units_expiry",        "expiry_date"),
        Index("ix_gbn_blood_units_available",     "lab_id", "blood_type", "component", "status"),
        CheckConstraint("blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')",
                        name="ck_gbn_units_blood_type"),
        CheckConstraint("component IN ('whole','RBC','plasma','platelets','cryo')",
                        name="ck_gbn_units_component"),
        CheckConstraint("status IN ('quarantine','available','reserved','used','expired','discarded')",
                        name="ck_gbn_units_status"),
    )

    id              = Column(Integer, primary_key=True, autoincrement=True)
    lab_id          = Column(Integer, ForeignKey("labs.id",          ondelete="RESTRICT"), nullable=False)
    donor_id        = Column(Integer, ForeignKey("gbn_donors.id",    ondelete="SET NULL"), nullable=True)

    barcode         = Column(String(30),  nullable=False, unique=True, index=True)
    blood_type      = Column(String(5),   nullable=False)
    component       = Column(String(20),  nullable=False)   # whole/RBC/plasma/platelets/cryo
    volume_ml       = Column(Integer,     nullable=True)
    collection_date = Column(Date,        nullable=False, default=date_type.today)
    expiry_date     = Column(Date,        nullable=False)

    status              = Column(String(20), nullable=False, default="quarantine")
    storage_location    = Column(String(100), nullable=True)    # e.g. "Fridge-A-Shelf-3"
    storage_temp_c      = Column(Float,       nullable=True)    # last recorded temperature
    temp_alert_flag     = Column(Boolean,     nullable=False, default=False)  # cold chain breach

    # Infectious disease screening results
    hiv_screened        = Column(Boolean, nullable=True)
    hbsag_screened      = Column(Boolean, nullable=True)
    hcv_screened        = Column(Boolean, nullable=True)
    syphilis_screened   = Column(Boolean, nullable=True)
    screening_passed    = Column(Boolean, nullable=True)   # None = pending

    collected_by        = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    processed_by        = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_default_now)
    updated_at          = Column(DateTime(timezone=True), default=_default_now, onupdate=_default_now)

    lab         = relationship("Lab",    foreign_keys=[lab_id])
    donor       = relationship("Donor",  back_populates="donations", foreign_keys=[donor_id])
    transfusion = relationship("Transfusion", back_populates="unit", uselist=False)

    @property
    def is_expired(self) -> bool:
        return date_type.today() > self.expiry_date

    @property
    def days_remaining(self) -> int:
        return (self.expiry_date - date_type.today()).days

    @classmethod
    def compute_expiry(cls, component: str, collection_date: date_type) -> date_type:
        days = COMPONENT_EXPIRY_DAYS.get(component, 35)
        return collection_date + timedelta(days=days)


# ── 3. Plasma Products ────────────────────────────────────────────────────────

class PlasmaProduct(Base):
    """Manufactured plasma-derived product (Factor VIII, Albumin, IVIG, etc.).

    These are processed industrial products — different from raw blood units.
    Managed at the lab / blood bank level.
    """
    __tablename__ = "gbn_plasma_products"
    __table_args__ = (
        Index("ix_gbn_plasma_lab_id",   "lab_id"),
        Index("ix_gbn_plasma_type",     "product_type"),
        Index("ix_gbn_plasma_expiry",   "expiry_date"),
        Index("ix_gbn_plasma_status",   "status"),
        CheckConstraint(
            "product_type IN ('factor_viii','factor_ix','albumin','ivig','anti_d','fibrinogen','prothrombin_complex','other')",
            name="ck_gbn_plasma_type",
        ),
        CheckConstraint("status IN ('available','reserved','used','expired','recalled')",
                        name="ck_gbn_plasma_status"),
    )

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    lab_id              = Column(Integer, ForeignKey("labs.id", ondelete="RESTRICT"), nullable=False)

    product_type        = Column(String(50),  nullable=False)
    brand_name          = Column(String(200), nullable=True)
    batch_number        = Column(String(100), nullable=False, index=True)
    lot_number          = Column(String(100), nullable=True)

    quantity_units      = Column(Integer, nullable=False)      # vials / bottles
    unit_volume_ml      = Column(Float,   nullable=True)       # volume per vial
    concentration       = Column(String(50), nullable=True)    # e.g. "250 IU/vial"

    manufacturer        = Column(String(200), nullable=True)
    country_of_origin   = Column(String(100), nullable=True)
    storage_condition   = Column(String(100), nullable=True)   # e.g. "2-8°C"
    expiry_date         = Column(Date,        nullable=False)
    status              = Column(String(20),  nullable=False, default="available")
    recall_reason       = Column(Text,        nullable=True)

    received_date       = Column(Date,        nullable=False, default=date_type.today)
    received_by         = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    notes               = Column(Text,        nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_default_now)

    lab = relationship("Lab", foreign_keys=[lab_id])


# ── 4. Blood Requests ─────────────────────────────────────────────────────────

class BloodRequest(Base):
    """A hospital / clinic request for blood units or plasma products.

    Lifecycle:
        pending → matching → matched → in_transit → fulfilled
        pending → cancelled
    """
    __tablename__ = "gbn_blood_requests"
    __table_args__ = (
        Index("ix_gbn_requests_lab_id",     "requesting_lab_id"),
        Index("ix_gbn_requests_status",     "status"),
        Index("ix_gbn_requests_urgency",    "urgency"),
        Index("ix_gbn_requests_blood_type", "blood_type"),
        Index("ix_gbn_requests_created",    "created_at"),
        CheckConstraint("blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-','any')",
                        name="ck_gbn_req_blood_type"),
        CheckConstraint("component IN ('whole','RBC','plasma','platelets','cryo','plasma_product')",
                        name="ck_gbn_req_component"),
        CheckConstraint("urgency IN ('routine','urgent','critical','massive_transfusion')",
                        name="ck_gbn_req_urgency"),
        CheckConstraint("status IN ('pending','matching','matched','in_transit','fulfilled','cancelled')",
                        name="ck_gbn_req_status"),
    )

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    requesting_lab_id   = Column(Integer, ForeignKey("labs.id", ondelete="RESTRICT"), nullable=False)
    patient_id          = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    requested_by        = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)

    blood_type          = Column(String(5),  nullable=False)     # "any" = accept any compatible
    component           = Column(String(30), nullable=False)
    units_required      = Column(Integer,    nullable=False, default=1)
    units_fulfilled     = Column(Integer,    nullable=False, default=0)

    urgency             = Column(String(30), nullable=False, default="routine")
    clinical_indication = Column(Text,       nullable=True)      # e.g. "post-op hemorrhage"
    status              = Column(String(30), nullable=False, default="pending")

    # Fulfilling lab (may differ if cross-lab transfer was needed)
    fulfilling_lab_id   = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)
    matched_at          = Column(DateTime(timezone=True), nullable=True)
    fulfilled_at        = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason    = Column(Text,       nullable=True)

    notes               = Column(Text,       nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_default_now, index=True)
    updated_at          = Column(DateTime(timezone=True), default=_default_now, onupdate=_default_now)

    requesting_lab  = relationship("Lab",       foreign_keys=[requesting_lab_id])
    fulfilling_lab  = relationship("Lab",       foreign_keys=[fulfilling_lab_id])
    patient         = relationship("Patient",   foreign_keys=[patient_id])
    transfusions    = relationship("Transfusion", back_populates="request",
                                   cascade="all, delete-orphan")


# ── 5. Transfusions ───────────────────────────────────────────────────────────

class Transfusion(Base):
    """A single unit transfused to a patient.

    One BloodRequest can result in multiple Transfusion rows (one per unit).
    Crossmatch MUST be performed and recorded before transfusion.
    """
    __tablename__ = "gbn_transfusions"
    __table_args__ = (
        Index("ix_gbn_transfusions_patient",  "patient_id"),
        Index("ix_gbn_transfusions_unit",     "unit_id"),
        Index("ix_gbn_transfusions_request",  "request_id"),
        Index("ix_gbn_transfusions_date",     "transfusion_time"),
        CheckConstraint("crossmatch_result IN ('compatible','incompatible','not_done')",
                        name="ck_gbn_xmatch"),
        CheckConstraint(
            "reaction_type IN ('none','febrile','allergic','hemolytic_acute','hemolytic_delayed','taco','trali','other') OR reaction_type IS NULL",
            name="ck_gbn_reaction",
        ),
    )

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    patient_id          = Column(Integer, ForeignKey("patients.id",        ondelete="RESTRICT"), nullable=False)
    unit_id             = Column(Integer, ForeignKey("gbn_blood_units.id", ondelete="RESTRICT"), nullable=False, unique=True)
    request_id          = Column(Integer, ForeignKey("gbn_blood_requests.id", ondelete="SET NULL"), nullable=True)
    administered_by     = Column(Integer, ForeignKey("lab_users.id",       ondelete="SET NULL"), nullable=True)

    crossmatch_result   = Column(String(30), nullable=False)    # compatible / incompatible / not_done
    crossmatch_notes    = Column(Text,       nullable=True)

    transfusion_time    = Column(DateTime(timezone=True), nullable=False, default=_default_now)
    volume_transfused_ml= Column(Integer,    nullable=True)
    duration_minutes    = Column(Integer,    nullable=True)

    # Post-transfusion monitoring
    reaction_flag       = Column(Boolean,    nullable=False, default=False)
    reaction_type       = Column(String(30), nullable=True)
    reaction_notes      = Column(Text,       nullable=True)
    reaction_time       = Column(DateTime(timezone=True), nullable=True)

    pre_transfusion_hb  = Column(Float, nullable=True)   # g/dL
    post_transfusion_hb = Column(Float, nullable=True)   # g/dL measured ~1h after

    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_default_now)

    patient    = relationship("Patient",      foreign_keys=[patient_id])
    unit       = relationship("BloodUnit",    back_populates="transfusion", foreign_keys=[unit_id])
    request    = relationship("BloodRequest", back_populates="transfusions", foreign_keys=[request_id])


# ── 6. Blood Transfers (Inter-Lab) ────────────────────────────────────────────

class BloodTransfer(Base):
    """Records movement of blood units between labs (national coordination).

    Used when a requesting lab doesn't have adequate stock and units must
    be sourced from another lab in the network.
    """
    __tablename__ = "gbn_blood_transfers"
    __table_args__ = (
        Index("ix_gbn_transfers_from", "from_lab_id"),
        Index("ix_gbn_transfers_to",   "to_lab_id"),
        Index("ix_gbn_transfers_status","status"),
        CheckConstraint("status IN ('requested','approved','dispatched','received','cancelled')",
                        name="ck_gbn_transfer_status"),
    )

    id              = Column(Integer, primary_key=True, autoincrement=True)
    from_lab_id     = Column(Integer, ForeignKey("labs.id", ondelete="RESTRICT"), nullable=False)
    to_lab_id       = Column(Integer, ForeignKey("labs.id", ondelete="RESTRICT"), nullable=False)
    unit_id         = Column(Integer, ForeignKey("gbn_blood_units.id", ondelete="RESTRICT"), nullable=False)
    request_id      = Column(Integer, ForeignKey("gbn_blood_requests.id", ondelete="SET NULL"), nullable=True)

    status          = Column(String(20), nullable=False, default="requested")
    approved_by     = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    approved_at     = Column(DateTime(timezone=True), nullable=True)
    dispatched_at   = Column(DateTime(timezone=True), nullable=True)
    received_at     = Column(DateTime(timezone=True), nullable=True)

    transport_temp_c= Column(Float,  nullable=True)   # recorded during transport
    transport_notes = Column(Text,   nullable=True)
    tracking_id     = Column(String(100), nullable=True)

    created_at      = Column(DateTime(timezone=True), default=_default_now)
    updated_at      = Column(DateTime(timezone=True), default=_default_now, onupdate=_default_now)

    from_lab = relationship("Lab", foreign_keys=[from_lab_id])
    to_lab   = relationship("Lab", foreign_keys=[to_lab_id])
    unit     = relationship("BloodUnit", foreign_keys=[unit_id])
