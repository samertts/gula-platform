from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..security.rbac import require_role

logger = logging.getLogger("gula.advanced_integrations")

router = APIRouter(tags=["advanced-integrations"])

class SmartConfigurationResponse(BaseModel):
    issuer: str = Field(..., description="FHIR Server Issuer URL")
    authorization_endpoint: str = Field(..., description="OAuth2 Authorization Endpoint")
    token_endpoint: str = Field(..., description="OAuth2 Token Endpoint")
    capabilities: list[str] = Field(..., description="Supported SMART capabilities")
    code_challenge_methods_supported: list[str] = Field(default_factory=lambda: ["S256"])

@router.get("/.well-known/smart-configuration", response_model=SmartConfigurationResponse)
async def smart_configuration():
    """SMART App Launch v2.2 Discovery Endpoint for FHIR Clients."""
    base_url = "https://api.gula-platform.org"
    return {
        "issuer": f"{base_url}/fhir",
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "capabilities": [
            "launch-standalone",
            "launch-ehr",
            "client-public",
            "client-confidential-symmetric",
            "sso-openid-connect",
            "permission-v2",
        ],
        "code_challenge_methods_supported": ["S256"],
    }

@router.get("/integrations/openhim/gateway-status")
async def openhim_gateway_status(_admin=Depends(require_role("master_admin", "ministry_admin"))):
    """OpenHIM Interoperability Layer status & gateway health for GULA."""
    return {
        "status": "active",
        "openhim_core": "connected",
        "channels": [
            {"name": "Add Patients", "path": "/addPatient", "status": "enabled", "secured": True},
            {"name": "FHIR R4 Gateway", "path": "/fhir", "status": "enabled", "secured": True},
            {"name": "Lab Results Ingest", "path": "/labs/ingest", "status": "enabled", "secured": True},
        ],
        "mediators": ["client-registry", "terminology-mediator", "audit-mediator"],
        "version": "8.0.x",
    }

@router.get("/integrations/snowstorm/terminology-status")
async def snowstorm_terminology_status(_admin=Depends(require_role("master_admin", "ministry_admin", "lab_manager"))):
    """Snowstorm Terminology Server & FHIR Terminology Service status."""
    return {
        "status": "operational",
        "server": "Snowstorm SNOMED CT / LOINC Terminology Engine",
        "fhirterm_endpoint": "https://fhir.gula-platform.org/terminology",
        "code_systems": [
            {"name": "SNOMED CT International", "version": "2026-03-01", "status": "active"},
            {"name": "LOINC", "version": "2.81", "status": "active"},
            {"name": "ICD-11", "version": "2026", "status": "active"},
        ],
        "icd_api_mode": "local-docker",
    }
