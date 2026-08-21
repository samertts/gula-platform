import json
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.contracts")


class ContractGenerator:
    """Generates platform contracts in multiple formats.

    Produces OpenAPI 3.1, AsyncAPI 2.6, JSON Schema, FHIR R4 profiles,
    and GraphQL schemas from the platform's domain model.
    """

    def __init__(self, app_name: str = "GULA Platform", app_version: str = "2.1.0"):
        self._app_name = app_name
        self._app_version = app_version
        self._generated_at = datetime.now(UTC).isoformat()

    def generate_openapi(self, app=None) -> dict:
        from fastapi import FastAPI
        from fastapi.routing import APIRoute

        paths: dict[str, Any] = {}
        components: dict[str, Any] = {"schemas": {}}

        if app is not None and isinstance(app, FastAPI):
            for route in app.routes:
                if isinstance(route, APIRoute):
                    path = route.path
                    methods = {}
                    for method in route.methods:
                        method_lower = method.lower()
                        if method_lower == "head":
                            continue
                        signature = {
                            "summary": (
                                route.summary
                                or route.description[:60] if route.description else ""
                            ),
                            "description": route.description or "",
                            "operationId": route.name or f"{method_lower}_{path.replace('/', '_')}",
                            "tags": list(route.tags) if route.tags else [],
                            "responses": self._default_responses(),
                        }
                        doc = route.endpoint.__doc__
                        if doc:
                            signature["description"] = doc.strip()
                        methods[method_lower] = signature
                    if methods:
                        paths[path] = methods

        return {
            "openapi": "3.1.0",
            "info": {
                "title": self._app_name,
                "version": self._app_version,
                "description": (
                    "**GULA** - منصة غولا الصحية الذكية للمختبرات\n\n"
                    "Smart Health Platform for Medical Laboratories in Iraq."
                ),
                "contact": {
                    "name": "GULA Platform Support",
                    "url": "https://gula-platform.org",
                    "email": "support@gula-platform.org",
                },
                "license": {
                    "name": "Proprietary - Ministry of Health Iraq Compliant",
                },
            },
            "servers": [
                {
                    "url": "https://api.gula-platform.org",
                    "description": "Production server",
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Local development",
                },
            ],
            "paths": paths or self._default_paths(),
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Obtain token from POST /login",
                    },
                },
                "schemas": components["schemas"],
            },
            "tags": [
                {"name": "patients", "description": "Patient management"},
                {"name": "orders", "description": "Lab order management"},
                {"name": "results", "description": "Test results"},
                {"name": "samples", "description": "Sample management"},
                {"name": "labs", "description": "Laboratory administration"},
                {"name": "auth", "description": "Authentication & authorization"},
                {"name": "system", "description": "Health & system endpoints"},
            ],
        }

    def generate_asyncapi(self, events: list[dict] | None = None) -> dict:
        from .events import get_asyncapi_spec

        if events:
            channels = {}
            for evt in events:
                name = evt.get("name", "UnknownEvent")
                topic_name = name[0].lower() + name[1:]
                topic_name = "".join(
                    [f"-{c.lower()}" if c.isupper() else c for c in topic_name],
                ).lstrip("-")
                channels[f"gula.{topic_name}"] = {
                    "description": evt.get("description", ""),
                    "subscribe": {
                        "message": {
                            "name": name,
                            "contentType": "application/json",
                            "payload": evt.get("payload", {"type": "object"}),
                        },
                    },
                }
            return {
                "asyncapi": "2.6.0",
                "info": {
                    "title": "GULA Platform Events",
                    "version": self._app_version,
                    "description": "Event-driven message bus",
                },
                "channels": channels,
            }
        return get_asyncapi_spec()

    def generate_json_schema(self, models: list[type] | None = None) -> dict:
        if models is None:
            models = []


        definitions: dict[str, Any] = {}
        for model in models:
            name = getattr(model, "__name__", str(model))
            try:
                columns = {}
                if hasattr(model, "__table__"):
                    for col in model.__table__.columns:
                        col_type = self._map_sa_type(col.type)
                        prop: dict[str, Any] = {"type": col_type}
                        if col.nullable:
                            prop["type"] = [col_type, "null"]
                        if col.doc:
                            prop["description"] = col.doc
                        columns[col.name] = prop
                definitions[name] = {
                    "type": "object",
                    "properties": columns,
                }
            except Exception as exc:
                logger.debug("Skipping model %s: %s", name, exc)

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "GULA Platform Data Models",
            "description": "JSON Schema definitions for all GULA domain models",
            "type": "object",
            "definitions": definitions,
            "properties": {},
        }

    def generate_fhir_profiles(self, models: list[type] | None = None) -> dict:
        from .fhir import FHIR_PROFILES, get_capability_statement

        return {
            "profiles": list(FHIR_PROFILES.values()),
            "capabilityStatement": get_capability_statement(),
        }

    def generate_graphql_schema(self, models: list[type] | None = None) -> str:
        if models is None:
            models = []

        type_defs = [
            "type Query {",
            "  health: HealthStatus!",
            "  patient(id: ID!): Patient",
            "  patients(labId: ID!, limit: Int, offset: Int): PatientConnection!",
            "  order(id: ID!): LabOrder",
            "  orders(patientId: ID!, labId: ID!): [LabOrder!]!",
            "  result(id: ID!): LabResult",
            "  results(orderId: ID!): [LabResult!]!",
            "  sample(id: ID!): Sample",
            "  samples(orderId: ID!): [Sample!]!",
            "}",
            "",
            "type Mutation {",
            "  createPatient(input: PatientInput!): Patient!",
            "  updatePatient(id: ID!, input: PatientInput!): Patient!",
            "  createOrder(input: OrderInput!): LabOrder!",
            "  publishResult(input: ResultInput!): LabResult!",
            "  validateOrder(id: ID!): LabOrder!",
            "  cancelOrder(id: ID!): LabOrder!",
            "}",
            "",
            "type Subscription {",
            "  patientCreated: Patient!",
            "  orderCreated: LabOrder!",
            "  resultPublished: LabResult!",
            "  criticalAlert: CriticalAlert!",
            "  systemHealthChanged: HealthStatus!",
            "}",
            "",
            "type HealthStatus {",
            "  status: String!",
            "  version: String!",
            "  database: String!",
            "  degradedMode: Boolean!",
            "}",
            "",
        ]

        scalar_types = [
            "scalar DateTime",
            "scalar JSON",
            "scalar Date",
            "",
        ]

        model_types = [
            "type Patient {",
            "  id: ID!",
            "  labId: ID!",
            "  healthId: String",
            "  fullName: String!",
            "  phone: String!",
            "  birthDate: Date",
            "  gender: String",
            "  email: String",
            "  orders: [LabOrder!]!",
            "  createdAt: DateTime!",
            "}",
            "",
            "type LabOrder {",
            "  id: ID!",
            "  patientId: ID!",
            "  labId: ID!",
            "  doctorName: String",
            "  status: OrderStatus!",
            "  results: [LabResult!]!",
            "  samples: [Sample!]!",
            "  createdAt: DateTime!",
            "  validatedAt: DateTime",
            "  version: Int!",
            "}",
            "",
            "enum OrderStatus {",
            "  pending",
            "  completed",
            "  validated",
            "  cancelled",
            "}",
            "",
            "type LabResult {",
            "  id: ID!",
            "  orderId: ID!",
            "  testName: String!",
            "  value: Float",
            "  valueText: String",
            "  unit: String",
            "  normalRangeLow: Float",
            "  normalRangeHigh: Float",
            "  flag: String",
            "  createdAt: DateTime!",
            "  version: Int!",
            "}",
            "",
            "type Sample {",
            "  id: ID!",
            "  orderId: ID!",
            "  barcode: String!",
            "  sampleType: String!",
            "  status: SampleStatus!",
            "  collectionTime: DateTime!",
            "  collectedBy: String",
            "  rejectionReason: String",
            "  notes: String",
            "}",
            "",
            "enum SampleStatus {",
            "  collected",
            "  received",
            "  processing",
            "  analyzed",
            "  rejected",
            "}",
            "",
            "type CriticalAlert {",
            "  alertId: String!",
            "  resultId: ID!",
            "  orderId: ID!",
            "  patientId: ID!",
            "  testName: String!",
            "  value: Float!",
            "  unit: String",
            "  flag: String!",
            "  message: String!",
            "  notifiedAt: DateTime!",
            "}",
            "",
            "type PatientConnection {",
            "  edges: [Patient!]!",
            "  totalCount: Int!",
            "  hasNextPage: Boolean!",
            "}",
            "",
            "input PatientInput {",
            "  fullName: String!",
            "  phone: String!",
            "  birthDate: Date",
            "  gender: String",
            "  email: String",
            "  nationalId: String",
            "  familyId: String",
            "}",
            "",
            "input OrderInput {",
            "  patientId: ID!",
            "  labId: ID!",
            "  doctorName: String",
            "  testNames: [String!]!",
            "}",
            "",
            "input ResultInput {",
            "  orderId: ID!",
            "  testName: String!",
            "  value: Float",
            "  valueText: String",
            "  unit: String",
            "  normalRangeLow: Float",
            "  normalRangeHigh: Float",
            "}",
            "",
        ]

        return "\n".join(scalar_types + type_defs + model_types)

    def _new_export_directory(self, requested_name: str) -> Path:
        """Create a server-owned export directory; the request value is only a label."""
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", requested_name) is None:
            raise ValueError("Contract export directory name is invalid")
        safe_root = Path(os.environ.get("GULA_EXPORT_ROOT", tempfile.gettempdir())).resolve()
        safe_root.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="gula_contract_export_", dir=safe_root))

    def _new_export_file(self, suffix: str) -> Path:
        safe_root = Path(os.environ.get("GULA_EXPORT_ROOT", tempfile.gettempdir())).resolve()
        safe_root.mkdir(parents=True, exist_ok=True)
        descriptor, raw_path = tempfile.mkstemp(
            prefix="gula_contract_",
            suffix=suffix,
            dir=safe_root,
        )
        os.close(descriptor)
        return Path(raw_path)

    def export_all(self, output_dir: str) -> list[str]:
        destination = self._new_export_directory(output_dir)
        exported: list[str] = []

        openapi_path = destination / "openapi.json"
        self._write_json(self.generate_openapi(), openapi_path)
        exported.append(str(openapi_path))

        asyncapi_path = destination / "asyncapi.json"
        self._write_json(self.generate_asyncapi(), asyncapi_path)
        exported.append(str(asyncapi_path))

        jsonschema_path = destination / "json-schema.json"
        self._write_json(self.generate_json_schema(), jsonschema_path)
        exported.append(str(jsonschema_path))

        fhir_path = destination / "fhir-profiles.json"
        self._write_json(self.generate_fhir_profiles(), fhir_path)
        exported.append(str(fhir_path))

        graphql_path = destination / "graphql-schema.graphql"
        self._write_text(self.generate_graphql_schema(), graphql_path)
        exported.append(str(graphql_path))

        event_catalog_path = destination / "event-catalog.json"
        from .events import get_event_catalog
        self._write_json(get_event_catalog(), event_catalog_path)
        exported.append(str(event_catalog_path))

        manifest_path = destination / "manifest.json"
        manifest = {
            "generated_at": self._generated_at,
            "app_name": self._app_name,
            "app_version": self._app_version,
            "contracts": exported,
        }
        self._write_json(manifest, manifest_path)
        exported.append(str(manifest_path))

        logger.info("Exported %d contract files", len(exported))
        return exported

    def export_openapi(self) -> str:
        output_path = self._new_export_file(".json")
        self._write_json(self.generate_openapi(), output_path)
        logger.info("OpenAPI spec generated")
        return str(output_path)

    def export_asyncapi(self) -> str:
        output_path = self._new_export_file(".json")
        self._write_json(self.generate_asyncapi(), output_path)
        logger.info("AsyncAPI spec generated")
        return str(output_path)

    def _write_json(self, data: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.debug("Contract artifact written (%d bytes)", path.stat().st_size)

    def _write_text(self, text: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        logger.debug("Contract artifact written (%d bytes)", path.stat().st_size)

    def _default_responses(self) -> dict:
        return {
            "200": {"description": "Successful response"},
            "400": {"description": "Bad request"},
            "401": {"description": "Unauthorized"},
            "403": {"description": "Forbidden"},
            "404": {"description": "Not found"},
            "500": {"description": "Internal server error"},
        }

    def _default_paths(self) -> dict:
        return {
            "/health": {
                "get": {
                    "summary": "Liveness probe",
                    "tags": ["system"],
                    "responses": {"200": {"description": "Process is alive"}},
                },
            },
            "/health/ready": {
                "get": {
                    "summary": "Readiness probe",
                    "tags": ["system"],
                    "responses": {"200": {"description": "System is ready"}},
                },
            },
            "/login": {
                "post": {
                    "summary": "Obtain JWT access token",
                    "tags": ["auth"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "password": {"type": "string"},
                                    },
                                    "required": ["email", "password"],
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {"description": "Login successful"},
                        "401": {"description": "Invalid credentials"},
                    },
                },
            },
        }

    def _map_sa_type(self, sa_type) -> str:
        type_str = str(sa_type).lower()
        if "integer" in type_str:
            return "integer"
        if "float" in type_str or "numeric" in type_str or "double" in type_str:
            return "number"
        if "boolean" in type_str or "bool" in type_str:
            return "boolean"
        if "date" in type_str:
            return "string"
        if "json" in type_str:
            return "object"
        return "string"
