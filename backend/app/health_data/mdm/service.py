from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.enums import DataQuality
from app.health_data.mdm.matching import MatchingEngine
from app.services.mpi.matcher import build_profile as mpi_build_profile

logger = logging.getLogger("gula.health_data.mdm.service")


class MDMService:
    def __init__(self, engine: MatchingEngine):
        self.engine = engine

    async def create_golden_record(
        self,
        entity_type: str,
        attributes: dict[str, Any],
        source_system: str = "",
        source_id: str = "",
    ) -> dict[str, Any]:
        record = {
            "id": self._generate_id(),
            "entity_type": entity_type,
            **attributes,
            "confidence_score": 1.0,
            "quality": DataQuality.MASTER.value,
            "is_golden": True,
            "is_active": True,
            "source_systems": [source_system] if source_system else [],
            "source_id": source_id,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "version": 1,
        }
        logger.info("Golden record created: %s/%s", entity_type, record["id"])
        return record

    async def merge(
        self,
        survivor: dict[str, Any],
        duplicate: dict[str, Any],
        reason: str = "",
        method: str = "auto",
    ) -> dict[str, Any]:
        for key in duplicate:
            if key in ("id", "created_at", "version", "merged_into_id", "is_active"):
                continue
            if key not in survivor or not survivor[key]:
                survivor[key] = duplicate[key]

        survivor["merged_into_id"] = None
        survivor["version"] = (survivor.get("version") or 1) + 1
        survivor["updated_at"] = datetime.now(UTC).isoformat()

        sources = set(survivor.get("source_systems", []) + duplicate.get("source_systems", []))
        survivor["source_systems"] = list(sources)

        logger.info(
            "Merged %s into %s (method=%s, reason=%s)",
            duplicate.get("id"),
            survivor.get("id"),
            method,
            reason,
        )
        return survivor

    async def split(
        self,
        record: dict[str, Any],
        attributes_to_keep: dict[str, Any],
        new_record_attrs: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        for k, v in attributes_to_keep.items():
            if k in record:
                record[k] = v

        new_record = {
            "id": self._generate_id(),
            "entity_type": record.get("entity_type", ""),
            **new_record_attrs,
            "source_systems": list(record.get("source_systems", [])),
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "version": 1,
            "is_golden": True,
            "is_active": True,
        }

        record["version"] = (record.get("version") or 1) + 1
        record["updated_at"] = datetime.now(UTC).isoformat()

        logger.info("Split record %s into two golden records", record.get("id"))
        return record, new_record

    async def find_duplicates(
        self,
        entity_type: str,
        records: list[dict[str, Any]],
        threshold: float = 0.85,
    ) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
        pairs = []
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                result = self.engine.match(records[i], records[j])
                if result.score >= threshold:
                    pairs.append((records[i], records[j], result.score))
        return pairs

    async def match_against_mpi(
        self,
        patient_data: dict[str, Any],
    ) -> dict[str, Any]:
        profile = mpi_build_profile(
            name=patient_data.get("full_name", ""),
            phone_last10=patient_data.get("phone", ""),
            birth_year=patient_data.get("birth_year"),
            birth_month=patient_data.get("birth_month"),
            birth_day=patient_data.get("birth_day"),
            gender=patient_data.get("gender", ""),
            nid_hash=patient_data.get("national_id_hash"),
        )

        return {
            "profile": {
                "name_canonical": profile.name_canonical,
                "phone_last10": profile.phone_last10,
                "nid_hash": profile.nid_hash,
            },
        }

    def _generate_id(self) -> str:
        import uuid

        return str(uuid.uuid4()).replace("-", "").upper()[:26]
