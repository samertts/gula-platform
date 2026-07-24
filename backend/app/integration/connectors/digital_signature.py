from __future__ import annotations

import hashlib
import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.digital_signature")


class DigitalSignatureConnector(BaseConnector):
    def __init__(
        self,
        name: str = "digital_signature",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._pki_cert = self.config.get("pki_certificate", "")
        self._pki_key = self.config.get("pki_private_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            if self._pki_cert:
                headers["X-Certificate-Thumbprint"] = hashlib.sha256(
                    self._pki_cert.encode(),
                ).hexdigest()
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("Digital Signature connector connected")
            return True
        except Exception as exc:
            logger.error("Digital Signature connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Digital Signature connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if not self._client:
            result["status"] = "disconnected"
            return result
        try:
            start = time.monotonic()
            resp = await self._client.get(urljoin(self._base_url, "/health"))
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status"] = "healthy" if resp.is_success else "degraded"
            result["status_code"] = resp.status_code
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "")
        if action == "sign":
            return await self._sign_document(data)
        if action == "verify":
            return await self._verify_signature(data)
        if action == "register_certificate":
            return await self._register_certificate(data)
        if action == "revoke_certificate":
            return await self._revoke_certificate(data)
        if action == "list_certificates":
            return await self._list_certificates(data)
        raise ValueError(f"Unknown Digital Signature action: {action}")

    async def _sign_document(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Digital Signature connector not connected")
        payload = {
            "document_id": data.get("document_id", ""),
            "document_hash": data.get("document_hash", ""),
            "document_content": data.get("document_content", ""),
            "signer_id": data.get("signer_id", ""),
            "signer_name": data.get("signer_name", ""),
            "certificate_id": data.get("certificate_id", ""),
            "reason": data.get("reason", "GULA Platform signing"),
            "location": data.get("location", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/sign"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "signature": result.get("signature", ""),
                    "signed_hash": result.get("signed_hash", ""),
                    "certificate_id": result.get("certificate_id", ""),
                    "signing_time": result.get("signing_time", ""),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Document signing failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _verify_signature(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Digital Signature connector not connected")
        payload = {
            "document_id": data.get("document_id", ""),
            "document_hash": data.get("document_hash", ""),
            "document_content": data.get("document_content", ""),
            "signature": data.get("signature", ""),
            "certificate_id": data.get("certificate_id", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/verify"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "valid": result.get("valid", False),
                    "signer": result.get("signer", ""),
                    "verified_at": result.get("verified_at", ""),
                    "details": result,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Signature verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _register_certificate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Digital Signature connector not connected")
        payload = {
            "certificate": data.get("certificate", self._pki_cert),
            "owner_id": data.get("owner_id", ""),
            "owner_name": data.get("owner_name", ""),
            "valid_from": data.get("valid_from", ""),
            "valid_until": data.get("valid_until", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/certificates"),
                json=payload,
            )
            if resp.is_success:
                return {"success": True, "certificate": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Certificate registration failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _revoke_certificate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Digital Signature connector not connected")
        certificate_id = data.get("certificate_id", "")
        if not certificate_id:
            return {"success": False, "error": "certificate_id required"}
        payload = {
            "reason": data.get("reason", "unspecified"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, f"/api/certificates/{certificate_id}/revoke"),
                json=payload,
            )
            return {"success": resp.is_success, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Certificate revocation failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _list_certificates(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Digital Signature connector not connected")
        params = {
            "owner_id": data.get("owner_id", ""),
            "status": data.get("status", "active"),
        }
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/certificates"),
                params=params,
            )
            if resp.is_success:
                certs = resp.json()
                return {"success": True, "certificates": certs, "count": len(certs)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Certificate listing failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("digital_signature", DigitalSignatureConnector)
