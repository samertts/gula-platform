from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("gula.knowledge_graph.data_dictionary")

_PII_PATTERNS = re.compile(
    r"name|phone|email|address|birth|national_id|ssn|passport|health_id|"
    r"patient_id|guardian|phone_number|mobile|telephone|contact",
    re.IGNORECASE,
)

_PHI_PATTERNS = re.compile(
    r"diagnosis|condition|result|test_value|prescription|medication|"
    r"clinical|lab_result|finding|symptoms|treatment|allergy|immunization",
    re.IGNORECASE,
)

_FHIR_MAP: dict[str, str] = {
    "patient": "Patient",
    "lab_order": "ServiceRequest",
    "lab_result": "Observation",
    "lab_sample": "Specimen",
    "lab_user": "Practitioner",
    "lab": "Organization",
    "visit": "Encounter",
    "diagnosis": "Condition",
    "medication": "MedicationRequest",
    "allergy": "AllergyIntolerance",
    "immunization": "Immunization",
    "care_plan": "CarePlan",
    "clinical_note": "ClinicalNote",
    "device": "Device",
    "location": "Location",
}


@dataclass
class FieldEntry:
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: str | None = None
    default: Any = None
    description: str = ""
    classification: str = "public"
    is_pii: bool = False
    is_phi: bool = False
    fhir_mapping: str | None = None
    enum_values: list[str] | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "foreign_key": self.foreign_key,
            "default": str(self.default) if self.default is not None else None,
            "description": self.description,
            "classification": self.classification,
            "is_pii": self.is_pii,
            "is_phi": self.is_phi,
            "fhir_mapping": self.fhir_mapping,
            "enum_values": self.enum_values,
        }


@dataclass
class DataEntityEntry:
    name: str
    table_name: str
    module: str = ""
    description: str = ""
    fields: list[FieldEntry] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    fhir_resource: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "table_name": self.table_name,
            "module": self.module,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "tags": self.tags,
            "fhir_resource": self.fhir_resource,
        }


@dataclass
class DataLineageEntry:
    source_entity: str
    source_field: str
    target_entity: str
    target_field: str
    transformation: str = "direct"
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "source_entity": self.source_entity,
            "source_field": self.source_field,
            "target_entity": self.target_entity,
            "target_field": self.target_field,
            "transformation": self.transformation,
            "description": self.description,
        }


class DataDictionary:
    def __init__(self):
        self._entities: dict[str, DataEntityEntry] = {}
        self._lineage: list[DataLineageEntry] = []

    def discover_entities(self, base: type[DeclarativeBase] | None = None) -> list[DataEntityEntry]:
        if base is None:
            return list(self._entities.values())
        try:
            mapper = inspect(base)
            tables = mapper.get_tables() if hasattr(mapper, "get_tables") else []
            if not tables:
                tables = list(base.metadata.tables.keys())
            for table_name in base.metadata.tables:
                table = base.metadata.tables[table_name]
                if table_name.startswith(("alembic", "knowledge")):
                    continue
                model_class = None
                for mapper_ in base.registry.mappers:
                    if mapper_.persist_selectable and mapper_.persist_selectable.name == table_name:
                        model_class = mapper_.class_
                        break
                class_name = model_class.__name__ if model_class else table_name.title().replace("_", "")
                module = getattr(model_class, "__module__", "") if model_class else ""
                doc = getattr(model_class, "__doc__", "") if model_class else ""
                entity = DataEntityEntry(
                    name=class_name,
                    table_name=table_name,
                    module=module,
                    description=doc.strip() if doc else "",
                )
                for col in table.columns:
                    col_type = str(col.type)
                    fk = None
                    if col.foreign_keys:
                        fk = next(iter(col.foreign_keys)).column.fullname if col.foreign_keys else None
                    is_pii = bool(_PII_PATTERNS.search(col.name))
                    is_phi = bool(_PHI_PATTERNS.search(col.name))
                    classification = "phi" if is_phi else ("pii" if is_pii else "public")
                    if col.primary_key:
                        classification = "identifier"
                    fhir_map = self._resolve_fhir_mapping(table_name, col.name)
                    enum_vals = None
                    if hasattr(col.type, "enums"):
                        enum_vals = list(col.type.enums)
                    entity.fields.append(FieldEntry(
                        name=col.name,
                        type=col_type,
                        nullable=col.nullable,
                        primary_key=col.primary_key,
                        foreign_key=fk,
                        default=col.default.arg if col.default and hasattr(col.default, "arg") else None,
                        classification=classification,
                        is_pii=is_pii,
                        is_phi=is_phi,
                        fhir_mapping=fhir_map,
                        enum_values=enum_vals,
                    ))
                entity.fhir_resource = _FHIR_MAP.get(table_name)
                self._entities[table_name] = entity
            fk_lineage: list[DataLineageEntry] = []
            for entity in self._entities.values():
                for f in entity.fields:
                    if f.foreign_key:
                        parts = f.foreign_key.split(".")
                        if len(parts) == 2:
                            target_entity = parts[0]
                            target_field = parts[1]
                            fk_lineage.append(DataLineageEntry(
                                source_entity=entity.table_name,
                                source_field=f.name,
                                target_entity=target_entity,
                                target_field=target_field,
                                transformation="foreign_key",
                                description=f"FK from {entity.table_name}.{f.name} to {target_entity}.{target_field}",
                            ))
            self._lineage = fk_lineage
            logger.info("Discovered %d data entities with %d fields", len(self._entities), sum(len(e.fields) for e in self._entities.values()))
        except Exception as exc:
            logger.warning("Failed to discover entities: %s", exc)
        return list(self._entities.values())

    def search_entities(self, query: str) -> list[DataEntityEntry]:
        q = query.lower()
        results = []
        for entity in self._entities.values():
            if (
                q in entity.name.lower()
                or q in entity.table_name.lower()
                or any(q in f.name.lower() for f in entity.fields)
                or any(q in f.classification.lower() for f in entity.fields)
            ):
                results.append(entity)
        return results

    def get_entity(self, table_name: str) -> DataEntityEntry | None:
        return self._entities.get(table_name)

    def get_all_entities(self) -> list[DataEntityEntry]:
        return list(self._entities.values())

    def get_pii_inventory(self) -> list[dict]:
        inventory = []
        for entity in self._entities.values():
            for f in entity.fields:
                if f.is_pii or f.is_phi:
                    inventory.append({
                        "table": entity.table_name,
                        "entity": entity.name,
                        "field": f.name,
                        "type": f.type,
                        "classification": f.classification,
                        "nullable": f.nullable,
                        "encrypted": "encrypted" in f.type.lower() if f.type else False,
                    })
        return inventory

    def get_data_lineage(self) -> list[dict]:
        return [entry.to_dict() for entry in self._lineage]

    def get_summary(self) -> dict:
        total_fields = sum(len(e.fields) for e in self._entities.values())
        pii_count = len(self.get_pii_inventory())
        return {
            "total_entities": len(self._entities),
            "total_fields": total_fields,
            "pii_phi_fields": pii_count,
            "lineage_entries": len(self._lineage),
            "entities": sorted(e.table_name for e in self._entities.values()),
        }

    def _resolve_fhir_mapping(self, table_name: str, column_name: str) -> str | None:
        resource = _FHIR_MAP.get(table_name)
        if not resource:
            return None
        fhir_field_map: dict[str, dict[str, str]] = {
            "patient": {
                "id": "Patient.id",
                "full_name": "Patient.name[0].text",
                "phone": "Patient.telecom[0].value",
                "birth_date": "Patient.birthDate",
                "gender": "Patient.gender",
                "national_id": "Patient.identifier[0].value",
                "email": "Patient.telecom[1].value",
                "address": "Patient.address[0].text",
            },
            "lab_order": {
                "id": "ServiceRequest.id",
                "patient_id": "ServiceRequest.subject.reference",
                "status": "ServiceRequest.status",
                "test_type": "ServiceRequest.code.text",
            },
            "lab_result": {
                "id": "Observation.id",
                "order_id": "Observation.basedOn[0].reference",
                "test_name": "Observation.code.text",
                "result_value": "Observation.valueQuantity.value",
                "unit": "Observation.valueQuantity.unit",
                "reference_range": "Observation.referenceRange[0].text",
                "status": "Observation.status",
            },
        }
        return fhir_field_map.get(table_name, {}).get(column_name)


data_dictionary = DataDictionary()
