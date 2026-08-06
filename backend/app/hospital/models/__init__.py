from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import backref, relationship

from app._compat import UTC

from ..base import HospitalBaseEntity


class HospitalMaster(HospitalBaseEntity):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    hospital_type = Column(String(50), nullable=False, index=True)
    license_number = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    website = Column(String(300), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    country = Column(String(10), default="IQ")

    campuses = relationship("Campus", back_populates="hospital", cascade="all, delete-orphan")
    departments = relationship(
        "HospitalDepartment", back_populates="hospital", cascade="all, delete-orphan"
    )
    units = relationship("Unit", back_populates="hospital", cascade="all, delete-orphan")
    operation_theaters = relationship(
        "OperationTheater", back_populates="hospital", cascade="all, delete-orphan"
    )
    equipment = relationship(
        "MedicalEquipment", back_populates="hospital", cascade="all, delete-orphan"
    )
    cost_centers = relationship(
        "CostCenter", back_populates="hospital", cascade="all, delete-orphan"
    )
    clinics = relationship("Clinic", back_populates="hospital", cascade="all, delete-orphan")


class Campus(HospitalBaseEntity):
    __tablename__ = "hospital_campuses"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    address = Column(String(500), nullable=True)

    hospital = relationship("HospitalMaster", back_populates="campuses")
    buildings = relationship("Building", back_populates="campus", cascade="all, delete-orphan")


class Building(HospitalBaseEntity):
    __tablename__ = "hospital_buildings"

    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(
        Integer, ForeignKey("hospital_campuses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    floors_count = Column(Integer, default=0)

    campus = relationship("Campus", back_populates="buildings")
    floors = relationship("Floor", back_populates="building", cascade="all, delete-orphan")


class Floor(HospitalBaseEntity):
    __tablename__ = "hospital_floors"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(
        Integer, ForeignKey("hospital_buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    floor_number = Column(Integer, nullable=False)

    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")


class HospitalDepartment(HospitalBaseEntity):
    __tablename__ = "hospital_departments"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id = Column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    department_type = Column(String(50), nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    hospital = relationship("HospitalMaster", back_populates="departments")
    children = relationship(
        "HospitalDepartment",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )
    clinics = relationship("Clinic", back_populates="department", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="department", cascade="all, delete-orphan")
    operation_theaters = relationship(
        "OperationTheater", back_populates="department", cascade="all, delete-orphan"
    )
    equipment = relationship(
        "MedicalEquipment", back_populates="department", cascade="all, delete-orphan"
    )


class Clinic(HospitalBaseEntity):
    __tablename__ = "hospital_clinics"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id = Column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    clinic_type = Column(String(50), nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    hospital = relationship("HospitalMaster", back_populates="clinics")
    department = relationship("HospitalDepartment", back_populates="clinics")
    rooms = relationship("Room", back_populates="clinic", cascade="all, delete-orphan")


class Room(HospitalBaseEntity):
    __tablename__ = "hospital_rooms"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id = Column(
        Integer, ForeignKey("hospital_clinics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    floor_id = Column(
        Integer, ForeignKey("hospital_floors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    room_type = Column(String(50), nullable=False, index=True)
    capacity = Column(Integer, default=1)

    department = relationship("HospitalDepartment", back_populates="rooms")
    clinic = relationship("Clinic", back_populates="rooms")
    floor = relationship("Floor", back_populates="rooms")
    beds = relationship("Bed", back_populates="room", cascade="all, delete-orphan")


class Bed(HospitalBaseEntity):
    __tablename__ = "hospital_beds"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(
        Integer, ForeignKey("hospital_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bed_number = Column(String(20), nullable=False)
    bed_type = Column(String(30), nullable=False, default="standard", index=True)
    status = Column(String(20), nullable=False, default="available", index=True)
    current_patient_id = Column(Integer, nullable=True, index=True)

    room = relationship("Room", back_populates="beds")
    current_patient = relationship("Patient", foreign_keys=[current_patient_id])
    assignments = relationship("BedAssignment", back_populates="bed", cascade="all, delete-orphan")


class Unit(HospitalBaseEntity):
    __tablename__ = "hospital_units"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    unit_type = Column(String(50), nullable=False, index=True)

    hospital = relationship("HospitalMaster", back_populates="units")


class OperationTheater(HospitalBaseEntity):
    __tablename__ = "hospital_operation_theaters"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id = Column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    theater_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="available", index=True)
    current_surgery_id = Column(Integer, nullable=True)

    hospital = relationship("HospitalMaster", back_populates="operation_theaters")
    department = relationship("HospitalDepartment", back_populates="operation_theaters")


class MedicalEquipment(HospitalBaseEntity):
    __tablename__ = "hospital_medical_equipment"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id = Column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    equipment_code = Column(String(50), nullable=False, index=True)
    equipment_name = Column(String(300), nullable=False)
    equipment_name_ar = Column(String(300), nullable=True)
    category = Column(String(50), nullable=False, index=True)
    manufacturer = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    serial_number = Column(String(100), nullable=True, unique=True)
    status = Column(String(30), nullable=False, default="operational", index=True)
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)

    hospital = relationship("HospitalMaster", back_populates="equipment")
    department = relationship("HospitalDepartment", back_populates="equipment")


class CostCenter(HospitalBaseEntity):
    __tablename__ = "hospital_cost_centers"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    cost_center_type = Column(String(50), nullable=False, index=True)
    budget_amount = Column(Numeric(15, 2), nullable=True)
    budget_currency = Column(String(3), default="IQD")

    hospital = relationship("HospitalMaster", back_populates="cost_centers")


class BedAssignment(HospitalBaseEntity):
    __tablename__ = "bed_assignments"

    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(
        Integer, ForeignKey("hospital_beds.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(Integer, nullable=False, index=True)
    admission_date = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    discharge_date = Column(DateTime(timezone=True), nullable=True)
    reason = Column(String(500), nullable=True)
    diagnosis = Column(String(500), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    discharge_reason = Column(String(500), nullable=True)
    discharged_by = Column(Integer, nullable=True)

    bed = relationship("Bed", back_populates="assignments")
    patient = relationship("Patient", foreign_keys=[patient_id])


__all__ = [
    "Bed",
    "BedAssignment",
    "Building",
    "Campus",
    "Clinic",
    "CostCenter",
    "Floor",
    "HospitalDepartment",
    "HospitalMaster",
    "MedicalEquipment",
    "OperationTheater",
    "Room",
    "Unit",
]
