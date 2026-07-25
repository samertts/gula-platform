from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.integration.transformation.schema_mapping")


@dataclass
class FieldMapping:
    source_field: str = ""
    target_field: str = ""
    default_value: Any = None
    required: bool = False
    transform: Callable[[Any], Any] | None = None
    description: str = ""


@dataclass
class SchemaMap:
    source_schema: str = ""
    target_schema: str = ""
    field_mappings: list[FieldMapping] = field(default_factory=list)
    version: str = "1.0"

    def add_mapping(self, mapping: FieldMapping) -> None:
        self.field_mappings.append(mapping)


class SchemaMapper:
    def __init__(self):
        self._maps: dict[str, SchemaMap] = {}

    def register_map(self, schema_map: SchemaMap) -> None:
        key = f"{schema_map.source_schema}:{schema_map.target_schema}"
        self._maps[key] = schema_map
        logger.info(
            "Schema map registered: %s -> %s", schema_map.source_schema, schema_map.target_schema
        )

    def map(self, data: dict[str, Any], source_schema: str, target_schema: str) -> dict[str, Any]:
        key = f"{source_schema}:{target_schema}"
        schema_map = self._maps.get(key)
        if not schema_map:
            raise ValueError(f"No mapping found for {key}")

        result: dict[str, Any] = {}
        for mapping in schema_map.field_mappings:
            value = data.get(mapping.source_field, mapping.default_value)
            if value is None and mapping.required:
                logger.warning("Required field missing: %s", mapping.source_field)
                continue
            if value is not None and mapping.transform:
                try:
                    value = mapping.transform(value)
                except Exception as exc:
                    logger.error("Transform failed for %s: %s", mapping.source_field, exc)
                    value = mapping.default_value
            result[mapping.target_field] = value
        return result

    def create_map(self, source: str, target: str, mappings: list[FieldMapping]) -> SchemaMap:
        schema_map = SchemaMap(source_schema=source, target_schema=target)
        for m in mappings:
            schema_map.add_mapping(m)
        self.register_map(schema_map)
        return schema_map

    def list_maps(self) -> list[str]:
        return list(self._maps.keys())

    def get_map(self, source: str, target: str) -> SchemaMap | None:
        return self._maps.get(f"{source}:{target}")
