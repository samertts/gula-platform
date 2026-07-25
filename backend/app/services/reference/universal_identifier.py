from __future__ import annotations

import hashlib
import logging
import time
import uuid
from enum import Enum

logger = logging.getLogger("gula.reference.identifier")


class IdentifierType(Enum):
    HEALTH_NUMBER = "health_number"
    LAB_ORDER = "lab_order"
    SPECIMEN = "specimen"
    ACCESSION_NUMBER = "accession_number"
    REPORT = "report"
    VISIT = "visit"
    ENCOUNTER = "encounter"
    APPOINTMENT = "appointment"
    INVOICE = "invoice"
    NOTIFICATION = "notification"
    WORKFLOW = "workflow"
    AUDIT_EVENT = "audit_event"


class UniversalIdentifierService:
    def __init__(self):
        self._sequences: dict[str, int] = {}
        self._generated: set[str] = set()
        self._prefixes: dict[IdentifierType, str] = {
            IdentifierType.HEALTH_NUMBER: "HN",
            IdentifierType.LAB_ORDER: "ORD",
            IdentifierType.SPECIMEN: "SPC",
            IdentifierType.ACCESSION_NUMBER: "ACC",
            IdentifierType.REPORT: "RPT",
            IdentifierType.VISIT: "VIS",
            IdentifierType.ENCOUNTER: "ENC",
            IdentifierType.APPOINTMENT: "APT",
            IdentifierType.INVOICE: "INV",
            IdentifierType.NOTIFICATION: "NTF",
            IdentifierType.WORKFLOW: "WF",
            IdentifierType.AUDIT_EVENT: "AUD",
        }

    def generate(
        self,
        id_type: IdentifierType,
        tenant_id: str = "",
        seed: str = "",
        format: str = "uuid",
    ) -> str:
        if format == "uuid":
            identifier = self._generate_uuid(id_type, tenant_id, seed)
        elif format == "sequential":
            identifier = self._generate_sequential(id_type, tenant_id)
        elif format == "hash":
            identifier = self._generate_hash(id_type, tenant_id, seed)
        else:
            identifier = self._generate_uuid(id_type, tenant_id, seed)

        self._generated.add(identifier)
        logger.debug("Generated %s: %s (format=%s)", id_type.value, identifier, format)
        return identifier

    def _generate_uuid(self, id_type: IdentifierType, tenant_id: str, seed: str) -> str:
        prefix = self._prefixes.get(id_type, "ID")
        raw = (
            str(uuid.uuid4())
            if not seed
            else hashlib.sha256(
                (seed + str(uuid.uuid4())).encode(),
            ).hexdigest()[:16]
        )
        if tenant_id:
            return f"{prefix}-{tenant_id}-{raw[:12].upper()}"
        return f"{prefix}-{raw[:12].upper()}"

    def _generate_sequential(self, id_type: IdentifierType, tenant_id: str) -> str:
        prefix = self._prefixes.get(id_type, "ID")
        key = f"{id_type.value}:{tenant_id or 'default'}"
        self._sequences[key] = self._sequences.get(key, 0) + 1
        seq = self._sequences[key]
        ts = int(time.time()) % 100000
        if tenant_id:
            return f"{prefix}-{tenant_id}-{ts:05d}{seq:06d}"
        return f"{prefix}-{ts:05d}{seq:06d}"

    def _generate_hash(self, id_type: IdentifierType, tenant_id: str, seed: str) -> str:
        prefix = self._prefixes.get(id_type, "ID")
        raw = (
            hashlib.sha256(
                (seed + str(time.time()) + (tenant_id or "")).encode(),
            )
            .hexdigest()[:16]
            .upper()
        )
        return f"{prefix}-{raw[:8]}-{raw[8:16]}"

    def validate(self, identifier: str) -> bool:
        return identifier in self._generated

    def get_prefix(self, id_type: IdentifierType) -> str:
        return self._prefixes.get(id_type, "ID")

    def count_generated(self) -> int:
        return len(self._generated)

    def count_by_type(
        self,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for identifier in self._generated:
            id_type = identifier.split("-")[0] if "-" in identifier else "UNKNOWN"
            counts[id_type] = counts.get(id_type, 0) + 1
        return counts
