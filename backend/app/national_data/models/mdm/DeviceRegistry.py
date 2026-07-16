from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.national_data.base import BaseEntity


class DeviceRegistry(BaseEntity):
    __tablename__ = "dp_device_registry"

    device_bridge_id = Column(Integer, ForeignKey("edge_devices.id", ondelete="SET NULL"), nullable=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)

    device_name = Column(String(200), nullable=False)
    device_model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True)
    manufacturer = Column(String(100), nullable=True)

    device_type = Column(String(50), nullable=False)
    device_class = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_calibrated = Column(Boolean, default=False, nullable=False)
    last_calibration_date = Column(String(50), nullable=True)
    next_calibration_date = Column(String(50), nullable=True)

    firmware_version = Column(String(50), nullable=True)
    software_version = Column(String(50), nullable=True)
    connectivity_protocol = Column(String(50), nullable=True)

    location = Column(String(200), nullable=True)
    facility_id = Column(String(26), nullable=True)

    __table_args__ = (
        Index("ix_dp_device_lab", "lab_id"),
        Index("ix_dp_device_type", "device_type"),
        {"extend_existing": True},
    )
