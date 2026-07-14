from app.hospital.base import HospitalAuditEntity, HospitalTenantAuditEntity, _ulid
from app.hospital.enums import BedStatus, RoomType
from sqlalchemy import Boolean, Column, Enum as SAEnum, Float, ForeignKey, Index, Integer, SmallInteger, String, Text


class Building(HospitalAuditEntity):
    __tablename__ = "hospital_buildings"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)

    total_floors = Column(SmallInteger, default=1)
    building_type = Column(String(50), nullable=True)
    address_line = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_hospital_buildings_hospital", "hospital_id"),
        Index("ix_hospital_buildings_facility", "facility_id"),
        {"extend_existing": True},
    )


class Campus(HospitalAuditEntity):
    __tablename__ = "hospital_campuses"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_hospital_campuses_hospital", "hospital_id"),
        Index("ix_hospital_campuses_facility", "facility_id"),
        {"extend_existing": True},
    )


class Floor(HospitalAuditEntity):
    __tablename__ = "hospital_floors"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    number = Column(Integer, nullable=False)
    code = Column(String(20), nullable=True, index=True)

    building_id = Column(String(26), ForeignKey("hospital_buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    total_rooms = Column(SmallInteger, default=0)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_hospital_floors_building", "building_id"),
        Index("ix_hospital_floors_number_building", "building_id", "number", unique=True),
        {"extend_existing": True},
    )


class HospitalUnit(HospitalAuditEntity):
    __tablename__ = "hospital_units"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)
    floor_id = Column(String(26), ForeignKey("hospital_floors.id", ondelete="SET NULL"), nullable=True, index=True)

    unit_type = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    extension = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hospital_units_hospital", "hospital_id"),
        Index("ix_hospital_units_facility", "facility_id"),
        Index("ix_hospital_units_department", "department_id"),
        Index("ix_hospital_units_floor", "floor_id"),
        {"extend_existing": True},
    )


class Room(HospitalAuditEntity):
    __tablename__ = "hospital_rooms"

    room_number = Column(String(20), nullable=False)
    room_type = Column(SAEnum(RoomType), nullable=False)
    code = Column(String(30), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    building_id = Column(String(26), ForeignKey("hospital_buildings.id", ondelete="SET NULL"), nullable=True, index=True)
    floor_id = Column(String(26), ForeignKey("hospital_floors.id", ondelete="SET NULL"), nullable=True, index=True)
    ward_id = Column(String(26), ForeignKey("hospital_wards.id", ondelete="SET NULL"), nullable=True, index=True)
    unit_id = Column(String(26), ForeignKey("hospital_units.id", ondelete="SET NULL"), nullable=True, index=True)

    total_beds = Column(SmallInteger, default=1)
    max_occupancy = Column(SmallInteger, nullable=True)
    square_meters = Column(Float, nullable=True)
    is_private = Column(Boolean, default=False)
    is_negative_pressure = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hospital_rooms_hospital", "hospital_id"),
        Index("ix_hospital_rooms_facility", "facility_id"),
        Index("ix_hospital_rooms_building", "building_id"),
        Index("ix_hospital_rooms_floor", "floor_id"),
        Index("ix_hospital_rooms_ward", "ward_id"),
        Index("ix_hospital_rooms_number_hospital", "hospital_id", "room_number", unique=True),
        {"extend_existing": True},
    )


class Bed(HospitalTenantAuditEntity):
    __tablename__ = "hospital_beds"

    bed_label = Column(String(20), nullable=False)
    status = Column(SAEnum(BedStatus), nullable=False, default=BedStatus.AVAILABLE)
    code = Column(String(30), nullable=True, index=True)

    room_id = Column(String(26), ForeignKey("hospital_rooms.id", ondelete="RESTRICT"), nullable=False, index=True)
    ward_id = Column(String(26), ForeignKey("hospital_wards.id", ondelete="SET NULL"), nullable=True, index=True)
    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    is_isolated = Column(Boolean, default=False)
    isolation_type = Column(String(30), nullable=True)
    is_icu_bed = Column(Boolean, default=False)
    is_emergency_bed = Column(Boolean, default=False)
    is_ventilator_capable = Column(Boolean, default=False)
    is_monitored = Column(Boolean, default=False)
    max_weight_kg = Column(Integer, nullable=True)
    features = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hospital_beds_room", "room_id"),
        Index("ix_hospital_beds_ward", "ward_id"),
        Index("ix_hospital_beds_hospital", "hospital_id"),
        Index("ix_hospital_beds_status", "status"),
        Index("ix_hospital_beds_label_room", "room_id", "bed_label", unique=True),
        {"extend_existing": True},
    )
