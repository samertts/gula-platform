from __future__ import annotations

import base64
import binascii
import logging
from datetime import datetime, timedelta

from defusedxml import ElementTree as ET  # noqa: N817
from signxml import InvalidInput, InvalidSignature, SignatureConfiguration, XMLVerifier
from signxml.algorithms import DigestAlgorithm, SignatureMethod

from app._compat import UTC

logger = logging.getLogger("gula.saml")

SAML_NS = {
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
    "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


def parse_saml_response(raw_base64: str) -> ET.Element | None:
    try:
        decoded = base64.b64decode(raw_base64, validate=True)
        return ET.fromstring(decoded)
    except (binascii.Error, ValueError, ET.ParseError) as exc:
        logger.error("SAML response parse failed: %s", exc)
        return None


def extract_assertion(saml_response: ET.Element) -> ET.Element | None:
    return saml_response.find(".//saml:Assertion", SAML_NS)


_SAFE_SIGNATURE_METHODS = frozenset({
    SignatureMethod.RSA_SHA256,
    SignatureMethod.RSA_SHA384,
    SignatureMethod.RSA_SHA512,
    SignatureMethod.ECDSA_SHA256,
    SignatureMethod.ECDSA_SHA384,
    SignatureMethod.ECDSA_SHA512,
})
_SAFE_DIGEST_ALGORITHMS = frozenset({
    DigestAlgorithm.SHA256,
    DigestAlgorithm.SHA384,
    DigestAlgorithm.SHA512,
})


def verify_saml_signature(saml_response: ET.Element, signing_cert_pem: str) -> bool:
    """Verify the SAML XML signature against the pinned IdP certificate."""
    if not signing_cert_pem.strip():
        logger.error("SAML signing certificate is not configured")
        return False
    try:
        XMLVerifier().verify(
            ET.tostring(saml_response, encoding="utf-8"),
            x509_cert=signing_cert_pem,
            expect_config=SignatureConfiguration(
                require_x509=True,
                expect_references=1,
                signature_methods=_SAFE_SIGNATURE_METHODS,
                digest_algorithms=_SAFE_DIGEST_ALGORITHMS,
            ),
        )
        return True
    except (InvalidInput, InvalidSignature, ValueError, TypeError) as exc:
        logger.warning("SAML signature verification failed: %s", type(exc).__name__)
        return False


def validate_assertion(
    assertion: ET.Element,
    expected_issuer: str,
    expected_audience: str,
    allowed_clock_skew_s: int = 300,
) -> bool:
    issuer_el = assertion.find("./saml:Issuer", SAML_NS)
    if issuer_el is None or issuer_el.text != expected_issuer:
        logger.warning("SAML issuer mismatch: %s", issuer_el.text if issuer_el is not None else None)
        return False

    conditions = assertion.find("./saml:Conditions", SAML_NS)
    if conditions is not None:
        not_before = conditions.get("NotBefore")
        not_on_or_after = conditions.get("NotOnOrAfter")
        now = datetime.now(UTC)
        if not_before:
            nb = datetime.fromisoformat(not_before.replace("Z", "+00:00"))
            if now < nb - timedelta(seconds=allowed_clock_skew_s):
                logger.warning("SAML assertion not yet valid (NotBefore)")
                return False
        if not_on_or_after:
            noa = datetime.fromisoformat(not_on_or_after.replace("Z", "+00:00"))
            if now > noa + timedelta(seconds=allowed_clock_skew_s):
                logger.warning("SAML assertion expired (NotOnOrAfter)")
                return False

    audience_el = assertion.find(".//saml:Audience", SAML_NS)
    if audience_el is not None and audience_el.text != expected_audience:
        logger.warning("SAML audience mismatch: %s", audience_el.text)
        return False

    subject_el = assertion.find("./saml:Subject", SAML_NS)
    if subject_el is None:
        logger.warning("SAML assertion missing Subject")
        return False

    return True


def extract_attributes(assertion: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}

    subject_el = assertion.find("./saml:Subject/saml:NameID", SAML_NS)
    if subject_el is not None:
        result["name_id"] = subject_el.text or ""

    attr_stmts = assertion.findall(".//saml:AttributeStatement", SAML_NS)
    for stmt in attr_stmts:
        for attr in stmt.findall("saml:Attribute", SAML_NS):
            name = attr.get("Name", "")
            values = [v.text or "" for v in attr.findall("saml:AttributeValue", SAML_NS)]
            if values:
                result[name] = values[0]

    return result


def generate_sp_metadata(entity_id: str, acs_url: str, org_name: str = "GULA Platform") -> str:
    metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{entity_id}">
  <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{acs_url}"
        index="1"/>
  </md:SPSSODescriptor>
  <md:Organization>
    <md:OrganizationName xml:lang="en">{org_name}</md:OrganizationName>
    <md:OrganizationDisplayName xml:lang="en">{org_name}</md:OrganizationDisplayName>
  </md:Organization>
</md:EntityDescriptor>"""
    return metadata.strip()
