from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("gula.integration.transformation.data_transform")


class DataTransformer:
    def __init__(self):
        self._transforms: dict[str, Any] = {}

    def register_transform(self, name: str, transform_fn: Any) -> None:
        self._transforms[name] = transform_fn
        logger.info("Transform registered: %s", name)

    def transform(self, data: Any, transform_name: str, **kwargs: Any) -> Any:
        transform_fn = self._transforms.get(transform_name)
        if not transform_fn:
            raise ValueError(f"Transform not found: {transform_name}")
        return transform_fn(data, **kwargs)

    @staticmethod
    def json_to_dict(data: str | bytes) -> dict[str, Any]:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        return json.loads(data)

    @staticmethod
    def dict_to_json(data: dict[str, Any], pretty: bool = False) -> str:
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def flatten(data: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
        items: dict[str, Any] = {}
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(DataTransformer.flatten(v, new_key, sep=sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.update(DataTransformer.flatten(item, f"{new_key}[{i}]", sep=sep))
                    else:
                        items[f"{new_key}[{i}]"] = item
            else:
                items[new_key] = v
        return items

    @staticmethod
    def unflatten(data: dict[str, Any], sep: str = ".") -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in data.items():
            parts = key.split(sep)
            current = result
            for i, part in enumerate(parts):
                if "[" in part and "]" in part:
                    base = part.split("[")[0]
                    idx = int(part.split("[")[1].split("]")[0])
                    if base not in current:
                        current[base] = []
                    while len(current[base]) <= idx:
                        current[base].append({} if i < len(parts) - 1 else None)
                    if i < len(parts) - 1:
                        current = current[base][idx]
                    else:
                        current[base][idx] = value
                elif i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        return result

    @staticmethod
    def rename_keys(data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in data.items():
            new_key = mapping.get(key, key)
            if isinstance(value, dict):
                result[new_key] = DataTransformer.rename_keys(value, mapping)
            elif isinstance(value, list):
                result[new_key] = [
                    DataTransformer.rename_keys(item, mapping) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[new_key] = value
        return result

    @staticmethod
    def filter_fields(data: dict[str, Any], include: list[str] | None = None, exclude: list[str] | None = None) -> dict[str, Any]:
        if include:
            return {k: v for k, v in data.items() if k in include}
        if exclude:
            return {k: v for k, v in data.items() if k not in exclude}
        return dict(data)

    @staticmethod
    def to_lowercase(data: dict[str, Any]) -> dict[str, Any]:
        return {k.lower(): v.lower() if isinstance(v, str) else v for k, v in data.items()}

    @staticmethod
    def to_uppercase(data: dict[str, Any]) -> dict[str, Any]:
        return {k.upper(): v.upper() if isinstance(v, str) else v for k, v in data.items()}
