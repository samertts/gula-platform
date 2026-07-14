from app.hospital.base import HospitalAuditEntity, HospitalTenantAuditEntity, _ulid
from app.hospital.enums import BedStatus, WardType
from sqlalchemy import Boolean, Column, Enum as SAEnum, ForeignKey, Index, Integer, SmallInteger, String, Text


class Ward(HospitalAuditEntity):
    __tablename__ = "hospital_wards"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)
    ward_type = Column(SAEnum(WardType), nullable=False)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)
    building_id = Column(String(26), ForeignKey("hospital_buildings.id", ondelete="SET NULL"), nullable=True, index=True)
    floor_id = Column(String(26), ForeignKey("hospital_floors.id", ondelete="SET NULL"), nullable=True, index=True)
    national_ward_id = Column(String(26), ForeignKey("national_wards.id", ondelete="SET NULL"), nullable=True, index=True)

    total_beds = Column(SmallInteger, default=0)
    available_beds = Column(SmallInteger, default=0)
    occupied_beds = Column(SmallInteger, default=0)
    reserved_beds = Column(SmallInteger, default=0)
    out_of_service_beds = Column(SmallInteger, default=0)

    phone = Column(String(20), nullable=True)
    extension = Column(String(10), nullable=True)
    nurse_station_phone = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True)
    is_emergency_ward = Column(Boolean, default=False)
    is_icu = Column(Boolean, default=False)
    isolation_capable = Column(Boolean, default=False)
    visitation_hours = Column(String(500), nullable=True)
    specialization = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hospital_wards_hospital", "hospital_id"),
        Index("ix_hospital_wards_facility", "facility_id"),
        Index("ix_hospital_wards_department", "department_id"),
        Index("ix_hospital_wards_building", "building_id"),
        Index("ix_hospital_wards_floor", "floor_id"),
        Index("ix_hospital_wards_national", "national_ward_id"),
        Index("ix_hospital_wards_type", "ward_type"),
        Index("ix_hospital_wards_code_hospital", "hospital_id", "code", unique=True),
        {"extend_existing": True},
    )


class WardBed(HospitalTenantAuditEntity):
    __tablename__ = "hospital_ward_beds"

    bed_label = Column(String(20), nullable=False)
    status = Column(SAEnum(BedStatus), nullable=False, default=BedStatus.AVAILABLE)

    ward_id = Column(String(26), ForeignKey("hospital_wards.id", ondelete="RESTRICT"), nullable=False, index=True)
    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    room_id = Column(String(26), ForeignKey("hospital_rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    bed_id = Column(String(26), ForeignKey("hospital_beds.id", ondelete="SET NULL"), nullable=True, index=True)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(String(30), nullable=True)
    assigned_until = Column(String(30), nullable=True)
    last_cleaned_at = Column(String(30), nullable=True)
    is_isolated = Column(Boolean, default=False)
    isolation_type = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hospital_ward_beds_ward", "ward_id"),
        Index("ix_hospital_ward_beds_patient", "patient_id"),
        Index("ix_hospital_ward_beds_hospital", "hospital_id"),
        Index("ix_hospital_ward_beds_room", "room_id"),
        Index("ix_hospital_ward_beds_status", "status"),
        Index("ix_hospital_ward_beds_label_ward", "ward_id", "bed_label", unique=True),
        {"extend_existing": True},
    )
