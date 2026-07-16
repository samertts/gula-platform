from __future__ import annotations

import json
import time
from typing import Any

import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus


class FHIRConnector(BaseConnector):
    FHIR_R4 = "R4"
    FHIR_STU3 = "STU3"

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._fhir_version = (config.options or {}).get("fhir_version", self.FHIR_R4)
        self._base_path = (config.options or {}).get("base_path", "")

    async def connect(self) -> bool:
        try:
            headers = self._build_headers()
            timeout = httpx.Timeout(self._config.timeout_seconds)
            self._client = httpx.AsyncClient(
                base_url=self._config.endpoint,
                headers=headers,
                timeout=timeout,
            )
            capability = await self._capability_statement()
            if capability.success:
                self._connected = True
                self._status = ConnectorStatus.ACTIVE
                return True
            self._status = ConnectorStatus.ERROR
            return False
        except Exception as exc:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = str(exc)
            return False

    async def disconnect(self) -> bool:
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
            self._connected = False
            self._status = ConnectorStatus.INACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            return False

    async def send(self, data: Any) -> ConnectorResult:
        if not isinstance(data, dict):
            return self._build_result(False, error="data must be a dict", status_code=400)
        action = data.get("action", "create")
        resource_type = data.get("resource_type")
        resource_id = data.get("resource_id")
        resource = data.get("resource")
        search_params = data.get("search_params")

        if action == "read":
            if not resource_type or not resource_id:
                return self._build_result(False, error="read requires resource_type and resource_id", status_code=400)
            return await self._read(resource_type, resource_id)
        if action == "search":
            if not resource_type:
                return self._build_result(False, error="search requires resource_type", status_code=400)
            return await self._search(resource_type, search_params)
        if action == "create":
            if not resource_type or not resource:
                return self._build_result(False, error="create requires resource_type and resource", status_code=400)
            return await self._create(resource_type, resource)
        if action == "update":
            if not resource_type or not resource_id or not resource:
                return self._build_result(False, error="update requires resource_type, resource_id, and resource", status_code=400)
            return await self._update(resource_type, resource_id, resource)
        if action == "delete":
            if not resource_type or not resource_id:
                return self._build_result(False, error="delete requires resource_type and resource_id", status_code=400)
            return await self._delete(resource_type, resource_id)
        if action == "patch":
            if not resource_type or not resource_id or not resource:
                return self._build_result(False, error="patch requires resource_type, resource_id, and resource", status_code=400)
            return await self._patch(resource_type, resource_id, resource)
        if action == "transaction":
            bundle = data.get("bundle")
            if not bundle:
                return self._build_result(False, error="transaction requires bundle", status_code=400)
            return await self._transaction(bundle)
        if action == "batch":
            bundle = data.get("bundle")
            if not bundle:
                return self._build_result(False, error="batch requires bundle", status_code=400)
            return await self._batch(bundle)
        return self._build_result(False, error=f"unsupported action {action}", status_code=400)

    async def receive(self) -> ConnectorResult:
        pass

    async def _read(self, resource_type: str, resource_id: str) -> ConnectorResult:
        return await self._fhir_request("GET", f"/{resource_type}/{resource_id}")

    async def _search(self, resource_type: str, params: dict | None = None) -> ConnectorResult:
        return await self._fhir_request("GET", f"/{resource_type}", params=params)

    async def _create(self, resource_type: str, resource: dict) -> ConnectorResult:
        return await self._fhir_request("POST", f"/{resource_type}", json=resource)

    async def _update(self, resource_type: str, resource_id: str, resource: dict) -> ConnectorResult:
        return await self._fhir_request("PUT", f"/{resource_type}/{resource_id}", json=resource)

    async def _delete(self, resource_type: str, resource_id: str) -> ConnectorResult:
        return await self._fhir_request("DELETE", f"/{resource_type}/{resource_id}")

    async def _patch(self, resource_type: str, resource_id: str, resource: list | dict) -> ConnectorResult:
        return await self._fhir_request("PATCH", f"/{resource_type}/{resource_id}", json=resource)

    async def _transaction(self, bundle: dict) -> ConnectorResult:
        bundle["type"] = "transaction"
        return await self._fhir_request("POST", "/", json=bundle)

    async def _batch(self, bundle: dict) -> ConnectorResult:
        bundle["type"] = "batch"
        return await self._fhir_request("POST", "/", json=bundle)

    async def _capability_statement(self) -> ConnectorResult:
        return await self._fhir_request("GET", "/metadata")

    async def _fhir_request(
        self,
        method: str,
        path: str,
        json: Any = None,
        params: dict | None = None,
    ) -> ConnectorResult:
        if not self._client or not self._connected:
            connected = await self.connect()
            if not connected:
                return self._build_result(False, error="not connected", status_code=503)

        start = time.monotonic()
        try:
            response = await self._client.request(method=method, url=path, json=json, params=params)
            duration_ms = int((time.monotonic() - start) * 1000)

            body = self._parse_fhir_response(response)

            if response.is_success:
                self._record_success(duration_ms)
                return self._build_result(True, data=body, duration_ms=duration_ms, status_code=response.status_code)

            error_msg = body.get("issue", [{}])[0].get("diagnostics", str(body)) if isinstance(body, dict) else str(body)
            self._record_failure(error_msg, duration_ms)
            return self._build_result(False, data=body, error=error_msg, duration_ms=duration_ms, status_code=response.status_code)

        except httpx.TimeoutException as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(f"timeout: {exc}", duration_ms)
            return self._build_result(False, error=f"timeout: {exc}", duration_ms=duration_ms)
        except httpx.RequestError as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(f"request error: {exc}", duration_ms)
            return self._build_result(False, error=f"request error: {exc}", duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        if self._fhir_version == self.FHIR_R4:
            headers["X-FHIR-Version"] = "4.0"
        elif self._fhir_version == self.FHIR_STU3:
            headers["X-FHIR-Version"] = "3.0"
        creds = self._config.credentials or {}
        auth_type = self._config.auth_type
        if auth_type == "oauth2" and creds.get("access_token"):
            headers["Authorization"] = f"Bearer {creds['access_token']}"
        elif auth_type == "api_key" and creds.get("api_key"):
            header_name = creds.get("header_name", "X-API-Key")
            headers[header_name] = creds["api_key"]
        elif auth_type == "basic" and creds.get("username") and creds.get("password"):
            import base64
            encoded = base64.b64encode(f"{creds['username']}:{creds['password']}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        return headers

    def _parse_fhir_response(self, response: httpx.Response) -> Any:
        content_type = response.headers.get("content-type", "")
        if "application/fhir+json" in content_type or "application/json" in content_type:
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError):
                return {"resourceType": "OperationOutcome", "issue": [{"diagnostics": response.text}]}
        if "application/fhir+xml" in content_type or "application/xml" in content_type:
            return {"resourceType": "Binary", "data": response.text}
        return response.text
