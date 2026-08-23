import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from .events import EVENT_REGISTRY, get_event_catalog
from .fhir import get_capability_statement, get_fhir_profiles, get_structure_definitions
from .generator import ContractGenerator
from .models import ContractExport
from app.security.dependencies import require_permission

_require_contract_export_admin = require_permission("system:admin")

logger = logging.getLogger("gula.contracts.router")

router = APIRouter(prefix="/contracts", tags=["contracts"])

_generator = ContractGenerator()


@router.get("/openapi.json", summary="Generated OpenAPI 3.1 specification")
async def get_openapi():
    spec = _generator.generate_openapi()
    return JSONResponse(content=spec)


@router.get("/asyncapi.json", summary="Generated AsyncAPI 2.6 event specification")
async def get_asyncapi():
    spec = _generator.generate_asyncapi()
    return JSONResponse(content=spec)


@router.get("/schemas/{module:path}", summary="JSON Schema for a specific module")
async def get_schema(module: str):
    from .events import EVENT_REGISTRY

    module_map = {
        "events": lambda: {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "GULA Platform Events",
            "definitions": {
                name: evt["payload"] for name, evt in EVENT_REGISTRY.items()
            },
        },
        "event-catalog": lambda: get_event_catalog(),
        "fhir-profiles": get_fhir_profiles,
        "fhir-structure-definitions": get_structure_definitions,
        "fhir-capability": get_capability_statement,
    }

    handler = module_map.get(module)
    if handler is None:
        from .models import LabOrder, LabResult, Patient, Sample

        model_map = {
            "patient": Patient,
            "lab-order": LabOrder,
            "lab-result": LabResult,
            "sample": Sample,
        }
        model_cls = model_map.get(module)
        if model_cls is None:
            raise HTTPException(status_code=404, detail=f"Unknown module: {module}")

        schema = _generator.generate_json_schema([model_cls])
        definitions = schema.get("definitions", {})
        model_name = model_cls.__name__
        schema_data = definitions.get(model_name, {})
        return JSONResponse(content=schema_data)

    data = handler()
    return JSONResponse(content=data)


@router.get("/fhir/profiles", summary="All FHIR R4 profiles")
async def get_fhir_profiles_endpoint():
    profiles = get_fhir_profiles()
    return JSONResponse(
        content={"resourceType": "Bundle", "type": "collection", "entry": [{"resource": p} for p in profiles]},
    )


@router.get("/fhir/capability", summary="FHIR capability statement")
async def get_fhir_capability_endpoint():
    return JSONResponse(content=get_capability_statement())


@router.get("/fhir/structure-definitions", summary="FHIR structure definitions summary")
async def get_fhir_structure_definitions():
    return JSONResponse(content=get_structure_definitions())


@router.get("/graphql/schema", summary="GraphQL schema")
async def get_graphql_schema():
    schema_str = _generator.generate_graphql_schema()
    return PlainTextResponse(content=schema_str, media_type="text/plain")


@router.get("/catalog", summary="Contract catalog (all available contracts)")
async def get_contract_catalog():
    catalog = {
        "app_name": _generator._app_name,
        "app_version": _generator._app_version,
        "generated_at": _generator._generated_at,
        "available_contracts": [
            {
                "name": "OpenAPI 3.1",
                "path": "/contracts/openapi.json",
                "format": "openapi",
                "description": "REST API specification for all HTTP endpoints",
            },
            {
                "name": "AsyncAPI 2.6",
                "path": "/contracts/asyncapi.json",
                "format": "asyncapi",
                "description": "Event-driven message bus specification",
            },
            {
                "name": "JSON Schema",
                "path": "/contracts/schemas/{module}",
                "format": "json_schema",
                "description": "JSON Schema definitions per domain module",
                "available_modules": [
                    "events",
                    "event-catalog",
                    "fhir-profiles",
                    "fhir-structure-definitions",
                    "fhir-capability",
                    "patient",
                    "lab-order",
                    "lab-result",
                    "sample",
                ],
            },
            {
                "name": "FHIR R4 Profiles",
                "path": "/contracts/fhir/profiles",
                "format": "fhir_profile",
                "description": "FHIR R4 StructureDefinition profiles for all GULA resources",
            },
            {
                "name": "FHIR Capability Statement",
                "path": "/contracts/fhir/capability",
                "format": "fhir_capability",
                "description": "FHIR R4 CapabilityStatement for the GULA interface",
            },
            {
                "name": "GraphQL Schema",
                "path": "/contracts/graphql/schema",
                "format": "graphql_schema",
                "description": "GraphQL schema (Query, Mutation, Subscription)",
            },
        ],
        "events_count": len(EVENT_REGISTRY),
        "fhir_profiles_count": len(get_fhir_profiles()),
    }
    return JSONResponse(content=catalog)


@router.post("/export", summary="Export all contracts to filesystem")
async def export_contracts(
    export: ContractExport,
    _current_user=Depends(_require_contract_export_admin),
):
    try:
        exported_files = _generator.export_all(export.output_dir)
        return JSONResponse(
            content={
                "success": True,
                "output_dir": export.output_dir,
                "files": [Path(path).name for path in exported_files],
                "count": len(exported_files),
                "generated_at": _generator._generated_at,
            },
        )
    except Exception as exc:
        logger.exception("Contract export failed")
        raise HTTPException(status_code=500, detail="Export failed") from exc
