from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import BASE_URL
from ..database import get_db
from ..security.saml_service import (
    extract_assertion,
    extract_attributes,
    generate_sp_metadata,
    parse_saml_response,
    validate_assertion,
)

logger = logging.getLogger("gula.routes.saml")

router = APIRouter(prefix="/auth/saml", tags=["saml"])

SAML_ENTITY_ID = f"{BASE_URL}/auth/saml/metadata"
SAML_ACS_URL = f"{BASE_URL}/auth/saml/acs"
SAML_EXPECTED_ISSUER = None
SAML_EXPECTED_AUDIENCE = SAML_ENTITY_ID


class SAMLResponseModel(BaseModel):
    SAMLResponse: str
    RelayState: str | None = None


@router.get("/metadata")
def metadata():
    xml = generate_sp_metadata(
        entity_id=SAML_ENTITY_ID,
        acs_url=SAML_ACS_URL,
    )
    return PlainTextResponse(content=xml, media_type="application/xml")


@router.post("/acs")
def acs(
    data: SAMLResponseModel,
    db: Session = Depends(get_db),
):

    saml_response = parse_saml_response(data.SAMLResponse)
    if saml_response is None:
        raise HTTPException(status_code=400, detail="Invalid SAML response")

    assertion = extract_assertion(saml_response)
    if assertion is None:
        raise HTTPException(status_code=400, detail="No SAML assertion found")

    if not validate_assertion(assertion, SAML_EXPECTED_ISSUER or "", SAML_ENTITY_ID):
        raise HTTPException(status_code=400, detail="SAML assertion validation failed")

    attributes = extract_attributes(assertion)
    name_id = attributes.get("name_id", "")
    email = attributes.get("email", "") or attributes.get("Email", "")
    roles_str = attributes.get("roles", "") or attributes.get("Roles", "")

    if not email and not name_id:
        raise HTTPException(status_code=400, detail="No user identifier in SAML assertion")

    return {
        "name_id": name_id,
        "email": email,
        "roles": roles_str.split(",") if roles_str else [],
        "attributes": attributes,
    }
