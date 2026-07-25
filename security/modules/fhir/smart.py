from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlparse
from uuid import uuid4

from security.modules.identity.jwt import JWTManager
from security.modules.identity.oidc import OIDCProvider

logger = logging.getLogger("gula.security.modules.fhir.smart")

_SMART_SCOPES_PATTERN = re.compile(
    r"^(patient|user|system)/"
    r"((\*|(?:\w+(?:-\w+)*|\*))\.(\*|read|write|\*))"
    r"(\?(\w+(?:,\w+)*))?$"
)

_CLINICAL_RESOURCE_TYPES = {
    "Patient", "Observation", "DiagnosticReport", "MedicationRequest",
    "Condition", "Procedure", "Immunization", "AllergyIntolerance",
    "DocumentReference", "Encounter", "Practitioner", "Organization",
    "Location", "HealthcareService", "Bundle", "QuestionnaireResponse",
}


class SMARTOnFHIRManager:
    def __init__(
        self,
        jwt_manager: JWTManager | None = None,
        oidc_provider: OIDCProvider | None = None,
        fhir_base_url: str = "https://fhir.gula-platform.org",
    ) -> None:
        self._jwt = jwt_manager or JWTManager()
        self._oidc = oidc_provider or OIDCProvider()
        self._fhir_base_url = fhir_base_url
        self._launches: dict[str, dict[str, Any]] = {}
        self._clients: dict[str, dict[str, Any]] = {}

    def get_conformance_statement(self, base_url: str = "") -> dict[str, Any]:
        url = base_url or self._fhir_base_url
        return {
            "resourceType": "CapabilityStatement",
            "rest": [{
                "security": {
                    "extension": [{
                        "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
                        "extension": [
                            {"url": "token", "valueUri": f"{url}/token"},
                            {"url": "authorize", "valueUri": f"{url}/authorize"},
                            {"url": "manage", "valueUri": f"{url}/manage"},
                        ],
                    }],
                    "cors": True,
                    "service": [{
                        "coding": [{
                            "system": "http://hl7.org/fhir/restful-security-service",
                            "code": "SMART-on-FHIR",
                        }],
                    }],
                },
            }],
            "smartCapabilities": [
                "launch-ehr",
                "launch-standalone",
                "client-public",
                "client-confidential-symmetric",
                "sso-openid-connect",
                "context-passthrough-banner",
                "context-passthrough-style",
                "openid-connection",
                "permission-offline",
                "permission-patient",
                "permission-user",
                "permission-v2",
            ],
        }

    def register_client(
        self,
        client_name: str,
        redirect_uris: list[str],
        launch_type: str = "ehr",
        software_id: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        client_id = f"smart_{uuid4().hex[:16]}"
        client_secret = uuid4().hex

        self._clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "launch_type": launch_type,
            "software_id": software_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "software_id": software_id,
            "smart_launch_type": launch_type,
        }

    def ehr_launch(
        self,
        client_id: str,
        launch_context: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        client = self._clients.get(client_id)
        if not client:
            return {"error": "invalid_client"}

        launch_id = str(uuid4())
        self._launches[launch_id] = {
            "client_id": client_id,
            "launch_context": launch_context,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "type": "ehr",
        }

        authz_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": client.get("redirect_uris", [""])[0],
            "scope": launch_context.get("scope", "openid fhirUser"),
            "state": str(uuid4()),
            "aud": self._fhir_base_url,
            "launch": launch_id,
        }

        return {
            "launch_id": launch_id,
            "authorization_url": f"{self._fhir_base_url}/authorize?{urlencode(authz_params)}",
            "launch_context": launch_context,
        }

    def standalone_launch(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str,
        state: str = "",
        aud: str = "",
    ) -> dict[str, Any]:
        client = self._clients.get(client_id)
        if not client:
            return {"error": "invalid_client"}

        aud_url = aud or self._fhir_base_url
        authz_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state or str(uuid4()),
            "aud": aud_url,
        }

        return {
            "authorization_url": f"{self._fhir_base_url}/authorize?{urlencode(authz_params)}",
            "state": authz_params["state"],
        }

    def backend_services_authorize(self, client_id: str, scope: str = "system/*.read") -> dict[str, Any]:
        client = self._clients.get(client_id)
        if not client:
            return {"error": "invalid_client"}

        token = self._jwt.create_access_token(
            subject=client_id,
            extra_claims={
                "client_id": client_id,
                "scope": scope,
                "token_type": "bearer",
            },
        )

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope,
        }

    def exchange_token(
        self,
        code: str,
        client_id: str,
        client_secret: str = "",
        redirect_uri: str = "",
    ) -> dict[str, Any]:
        token_response = self._oidc.exchange_code(code, client_id, client_secret, redirect_uri)
        if not token_response.access_token:
            return {"error": "invalid_grant"}

        return {
            "access_token": token_response.access_token,
            "token_type": "Bearer",
            "expires_in": token_response.expires_in,
            "scope": token_response.scope,
            "id_token": token_response.id_token,
            "refresh_token": token_response.refresh_token,
            "patient": "",
            "encounter": "",
        }

    def validate_scope(self, scope: str) -> dict[str, Any]:
        scopes = scope.split()
        validated: list[str] = []
        errors: list[str] = []

        for s in scopes:
            if s in {"openid", "fhirUser", "offline_access", "online_access", "launch"}:
                validated.append(s)
                continue

            match = _SMART_SCOPES_PATTERN.match(s)
            if match:
                entity = match.group(1)
                resource_type = match.group(3)
                access = match.group(4)

                if resource_type != "*" and resource_type not in _CLINICAL_RESOURCE_TYPES:
                    errors.append(f"Unknown resource type: {resource_type}")
                    continue

                validated.append(s)
            else:
                errors.append(f"Invalid scope format: {s}")

        if "openid" not in validated:
            errors.append("openid scope is required")

        return {"valid": len(errors) == 0, "scopes": validated, "errors": errors}

    def get_patient_context(self, access_token: str) -> str:
        payload = self._jwt.verify_access_token(access_token)
        if payload is None:
            return ""
        return payload.get("patient", "")

    def get_encounter_context(self, access_token: str) -> str:
        payload = self._jwt.verify_access_token(access_token)
        if payload is None:
            return ""
        return payload.get("encounter", "")

    def create_launch_context(self, patient_id: str = "", encounter_id: str = "", **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = {
            "patient": patient_id,
            "encounter": encounter_id,
            **kwargs,
        }
        return context

    def get_well_known_smart_configuration(self, base_url: str = "") -> dict[str, Any]:
        url = base_url or self._fhir_base_url
        return {
            "authorization_endpoint": f"{url}/authorize",
            "token_endpoint": f"{url}/token",
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
                "private_key_jwt",
            ],
            "scopes_supported": [
                "openid", "fhirUser", "launch",
                "patient/*.read", "patient/*.write", "patient/*.*",
                "user/*.read", "user/*.write", "user/*.*",
                "system/*.read", "system/*.write", "system/*.*",
            ],
            "response_types_supported": ["code", "id_token", "code id_token"],
            "capabilities": [
                "launch-ehr", "launch-standalone",
                "client-public", "client-confidential-symmetric",
                "sso-openid-connect", "context-passthrough-banner",
                "context-passthrough-style", "openid-connection",
                "permission-offline", "permission-patient",
                "permission-user", "permission-v2",
            ],
        }
