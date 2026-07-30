from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class OpenAPISpec:
    title: str
    version: str = "0.1.0"
    description: str = ""
    base_path: str = "/api/v1"
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    schemas: list[dict[str, Any]] = field(default_factory=list)


class OpenAPIGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("openapi"))
        if isinstance(spec, dict):
            spec = OpenAPISpec(**spec)
        if spec is None:
            spec = OpenAPISpec(title=kwargs.get("title", "API"))

        paths: dict[str, Any] = {}
        for ep in spec.endpoints:
            path = ep.get("path", "/")
            method = ep.get("method", "get").lower()
            summary = ep.get("summary", "")
            tags = ep.get("tags", [])
            params = ep.get("parameters", [])
            responses = ep.get("responses", {"200": {"description": "Success"}})
            request_body = ep.get("requestBody", None)

            path_item = paths.setdefault(path, {})
            op: dict[str, Any] = {
                "summary": summary,
                "tags": tags,
                "parameters": params,
                "responses": responses,
            }
            if request_body:
                op["requestBody"] = request_body
            path_item[method] = op

        schemas: dict[str, Any] = {}
        for schema in spec.schemas:
            name = schema.get("name", "Model")
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            schemas[name] = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

        openapi = {
            "openapi": "3.0.3",
            "info": {
                "title": spec.title,
                "version": spec.version,
                "description": spec.description,
            },
            "servers": [{"url": spec.base_path}],
            "paths": paths,
            "components": {"schemas": schemas},
        }

        self._write(
            "openapi.json",
            json.dumps(openapi, indent=2),
        )

        return self._result
