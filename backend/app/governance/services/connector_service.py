from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

from ..enums import ConnectorMode, ConnectorType


@dataclass
class ConnectorResponse:
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    source: str | None = None
    trust_level: str = "non_critical"
    is_stale: bool = False
    requires_verification: bool = False
    timestamp: str = ""


class ConnectorAdapter(ABC):
    def __init__(self, connector_type: ConnectorType, mode: ConnectorMode = ConnectorMode.STUB):
        self.connector_type = connector_type
        self.mode = mode

    @abstractmethod
    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        ...

    @abstractmethod
    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        ...


class StubNationalIDAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.NATIONAL_ID, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "national_id": query.get("national_id", ""),
                "full_name": "محمد أحمد علي",
                "father_name": "أحمد",
                "mother_name": "فاطمة",
                "birth_date": "1990-01-15",
                "gender": "male",
                "governorate": "بغداد",
                "is_verified": True,
            },
            source="stub_nid",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_nid",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubBirthRegistryAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.BIRTH_REGISTRY, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "birth_certificate_number": query.get("certificate_number", ""),
                "full_name": "مولود جديد",
                "father_name": "الأب",
                "mother_name": "الأم",
                "birth_date": query.get("birth_date", "2025-01-01"),
                "birth_place": "مستشفى بغداد",
                "is_registered": True,
            },
            source="stub_birth_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_birth_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubDeathRegistryAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.DEATH_REGISTRY, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "death_certificate_number": query.get("certificate_number", ""),
                "deceased_name": "متوفي",
                "date_of_death": "2025-06-01",
                "cause_of_death": "Natural causes",
                "icd10_code": "R99",
                "is_registered": True,
            },
            source="stub_death_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_death_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubCivilStatusAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.CIVIL_STATUS, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "national_id": query.get("national_id", ""),
                "marital_status": "married",
                "spouse_name": "زوجة",
                "marriage_date": "2015-03-20",
                "divorce_date": None,
                "is_verified": True,
            },
            source="stub_civil_status",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_civil_status",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubPassportAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.PASSPORT, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "passport_number": query.get("passport_number", ""),
                "full_name": "مسافر عراقي",
                "nationality": "Iraqi",
                "date_of_birth": "1985-07-10",
                "issue_date": "2023-01-01",
                "expiry_date": "2028-01-01",
                "is_valid": True,
            },
            source="stub_passport",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_passport",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubResidenceAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.RESIDENCE, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "residence_number": query.get("residence_number", ""),
                "full_name": "مقيم أجنبي",
                "nationality": "Syrian",
                "residence_type": "temporary",
                "issue_date": "2024-01-01",
                "expiry_date": "2025-01-01",
                "sponsor": "كفيل عراقي",
                "is_valid": True,
            },
            source="stub_residence",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_residence",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubVisaAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.VISA, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "visa_number": query.get("visa_number", ""),
                "visa_type": "tourist",
                "nationality": "Turkish",
                "issue_date": "2024-06-01",
                "expiry_date": "2024-09-01",
                "entries_allowed": 1,
                "is_valid": True,
            },
            source="stub_visa",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_visa",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubFamilyRegistryAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.FAMILY_REGISTRY, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "family_id": query.get("family_id", ""),
                "family_name": "عائلة عراقية",
                "head_of_family": "رب الأسرة",
                "members": [
                    {"name": "فرد 1", "relation": "head", "national_id": "..."},
                    {"name": "فرد 2", "relation": "spouse", "national_id": "..."},
                ],
                "governorate": "بغداد",
                "is_registered": True,
            },
            source="stub_family_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_family_registry",
            timestamp=datetime.now(UTC).isoformat(),
        )


class StubRationCardAdapter(ConnectorAdapter):
    def __init__(self):
        super().__init__(ConnectorType.RATION_CARD, ConnectorMode.STUB)

    def lookup(self, query: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={
                "ration_card_number": query.get("ration_card_number", ""),
                "head_of_family": "رب الأسرة",
                "family_members_count": 5,
                "governorate": "بغداد",
                "distribution_point": "نقطة توزيع الكرخ",
                "is_active": True,
            },
            source="stub_ration_card",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def verify(self, identity: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(
            success=True,
            data={"match": True, "confidence": 1.0},
            source="stub_ration_card",
            timestamp=datetime.now(UTC).isoformat(),
        )


_ADAPTER_REGISTRY: dict[ConnectorType, type[ConnectorAdapter]] = {
    ConnectorType.NATIONAL_ID: StubNationalIDAdapter,
    ConnectorType.BIRTH_REGISTRY: StubBirthRegistryAdapter,
    ConnectorType.DEATH_REGISTRY: StubDeathRegistryAdapter,
    ConnectorType.CIVIL_STATUS: StubCivilStatusAdapter,
    ConnectorType.PASSPORT: StubPassportAdapter,
    ConnectorType.RESIDENCE: StubResidenceAdapter,
    ConnectorType.VISA: StubVisaAdapter,
    ConnectorType.FAMILY_REGISTRY: StubFamilyRegistryAdapter,
    ConnectorType.RATION_CARD: StubRationCardAdapter,
}


class CitizenRegistryConnectorService:
    def __init__(self, db: Session):
        self.db = db
        self._adapters: dict[ConnectorType, ConnectorAdapter] = {}

    def get_adapter(self, connector_type: ConnectorType) -> ConnectorAdapter:
        if connector_type not in self._adapters:
            adapter_cls = _ADAPTER_REGISTRY.get(connector_type)
            if not adapter_cls:
                raise ValueError(f"No adapter registered for connector type: {connector_type}")
            self._adapters[connector_type] = adapter_cls()
        return self._adapters[connector_type]

    def lookup(self, connector_type: ConnectorType, query: dict[str, Any]) -> ConnectorResponse:
        adapter = self.get_adapter(connector_type)
        return adapter.lookup(query)

    def verify(self, connector_type: ConnectorType, identity: dict[str, Any]) -> ConnectorResponse:
        adapter = self.get_adapter(connector_type)
        return adapter.verify(identity)

    def register_adapter(
        self, connector_type: ConnectorType, adapter: ConnectorAdapter,
    ) -> None:
        self._adapters[connector_type] = adapter
