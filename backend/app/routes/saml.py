from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import BASE_URL
from ..database import get_db
from ..security.saml_service import (
    extract_assertion,
    extract_attributes,
    generate_sp_metadata,
    parse_saml_response,
    validate_assertion,
    verify_saml_signature,
)

logger = logging.getLogger("gula.routes.saml")

router = APIRouter(prefix="/auth/saml", tags=["saml"])

SAML_ENTITY_ID = f"{BASE_URL}/auth/saml/metadata"
SAML_ACS_URL = f"{BASE_URL}/auth/saml/acs"
SAML_EXPECTED_ISSUER = os.getenv("SAML_IDP_ISSUER", "").strip()
SAML_IDP_SIGNING_CERT_PEM = os.getenv("SAML_IDP_SIGNING_CERT_PEM", "").strip()
SAML_EXPECTED_AUDIENCE = SAML_ENTITY_ID


class SAMLResponseModel(BaseModel):
    SAMLResponse: str = Field(..., min_length=1, max_length=250_000)
    RelayState: str | None = Field(default=None, max_length=2048)


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

    if not SAML_EXPECTED_ISSUER or not SAML_IDP_SIGNING_CERT_PEM:
        raise HTTPException(status_code=503, detail="SAML SSO is not configured")

    saml_response = parse_saml_response(data.SAMLResponse)
    if saml_response is None:
        raise HTTPException(status_code=400, detail="Invalid SAML response")

    if not verify_saml_signature(saml_response, SAML_IDP_SIGNING_CERT_PEM):
        raise HTTPException(status_code=400, detail="SAML signature validation failed")

    assertion = extract_assertion(saml_response)
    if assertion is None:
        raise HTTPException(status_code=400, detail="No SAML assertion found")

    if not validate_assertion(assertion, SAML_EXPECTED_ISSUER, SAML_ENTITY_ID):
        raise HTTPException(status_code=400, detail="SAML assertion validation failed")

    attributes = extract_attributes(assertion)
    name_id = attributes.get("name_id", "")
    email = attributes.get("email", "") or attributes.get("Email", "")
    if not email and not name_id:
        raise HTTPException(status_code=400, detail="No user identifier in SAML assertion")

    logger.info("SAML assertion validated name_id_present=%s email_present=%s", bool(name_id), bool(email))
    return {
        "validated": True,
        "name_id_present": bool(name_id),
        "email_present": bool(email),
        "relay_state_present": bool(data.RelayState),
    }
