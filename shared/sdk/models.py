from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Patient:
    id: int = 0
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    national_id: str = ""
    date_of_birth: str = ""
    gender: str = ""
    lab_id: int = 0
    created_at: str = ""


@dataclass
class Order:
    id: int = 0
    patient_id: int = 0
    lab_id: int = 0
    test_types: list[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = ""


@dataclass
class Result:
    id: int = 0
    order_id: int = 0
    test_name: str = ""
    value: float = 0.0
    unit: str = ""
    reference_low: float = 0.0
    reference_high: float = 0.0
    flag: str = ""
    is_critical: bool = False
    created_at: str = ""


@dataclass
class Sample:
    id: int = 0
    order_id: int = 0
    sample_type: str = ""
    status: str = "collected"
    collected_at: str = ""


@dataclass
class Lab:
    id: int = 0
    lab_name: str = ""
    city: str = ""
    region: str = ""
    status: str = "active"


__all__ = ["Lab", "Order", "Patient", "Result", "Sample"]
