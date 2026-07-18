from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from xml.etree import ElementTree
from defusedxml.ElementTree import fromstring as safe_xml_parse, ParseError as SafeXMLParseError

import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus


class RESTConnector(BaseConnector):
    SUPPORTED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._headers: dict[str, str] = {}

    async def connect(self) -> bool:
        try:
            headers = self._build_auth_headers()
            timeout = httpx.Timeout(self._config.timeout_seconds)
            self._client = httpx.AsyncClient(
                base_url=self._config.endpoint,
                headers=headers,
                timeout=timeout,
            )
            self._connected = True
            self._status = ConnectorStatus.ACTIVE
            return True
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
        if not isinstance(data, dict) or "method" not in data or "path" not in data:
            return self._build_result(False, error="send requires dict with 'method' and 'path'", status_code=400)
        method = data["method"].upper()
        if method not in self.SUPPORTED_METHODS:
            return self._build_result(False, error=f"unsupported method {method}", status_code=400)
        path = data["path"]
        body = data.get("body")
        params = data.get("params")
        headers = data.get("headers", {})
        return await self._request(method, path, body=body, params=params, headers=headers)

    async def receive(self) -> ConnectorResult:
        return await self._request("GET", "")

    async def _request(
        self,
        method: str,
        path: str,
        body: Any = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> ConnectorResult:
        if not self._check_circuit():
            return self._build_result(False, error="circuit breaker open", status_code=503)

        if not self._client or not self._connected:
            connected = await self.connect()
            if not connected:
                return self._build_result(False, error="not connected", status_code=503)

        start = time.monotonic()
        last_error: str | None = None

        for attempt in range(self._config.retry_count + 1):
            try:
                request_headers = {**self._headers, **(headers or {})}
                content_type = self._detect_content_type(request_headers, body)
                if content_type and content_type != "application/json":
                    request_headers["Content-Type"] = content_type

                response = await self._client.request(
                    method=method,
                    url=path,
                    json=body if content_type == "application/json" else None,
                    content=self._serialize_body(body, content_type) if content_type != "application/json" else None,
                    params=params,
                    headers=request_headers,
                )

                duration_ms = int((time.monotonic() - start) * 1000)
                response_data = self._parse_response(response)

                if response.is_success:
                    self._record_success(duration_ms)
                    return self._build_result(True, data=response_data, duration_ms=duration_ms, status_code=response.status_code)

                error_msg = f"HTTP {response.status_code}: {response_data}"
                self._record_failure(error_msg, duration_ms)
                return self._build_result(False, error=error_msg, duration_ms=duration_ms, status_code=response.status_code)

            except httpx.TimeoutException as exc:
                last_error = f"timeout: {exc}"
                if attempt < self._config.retry_count:
                    await asyncio.sleep(self._config.retry_delay_seconds * (2 ** attempt))
            except httpx.RequestError as exc:
                last_error = f"request error: {exc}"
                if attempt < self._config.retry_count:
                    await asyncio.sleep(self._config.retry_delay_seconds * (2 ** attempt))
            except Exception as exc:
                last_error = str(exc)
                break

        duration_ms = int((time.monotonic() - start) * 1000)
        self._record_failure(last_error or "unknown error", duration_ms)
        return self._build_result(False, error=last_error, duration_ms=duration_ms)

    def _build_auth_headers(self) -> dict[str, str]:
        auth_type = self._config.auth_type
        creds = self._config.credentials or {}
        if auth_type == "oauth2":
            token = creds.get("access_token", "")
            if token:
                self._headers = {"Authorization": f"Bearer {token}"}
        elif auth_type == "api_key":
            key = creds.get("api_key", "")
            header_name = creds.get("header_name", "X-API-Key")
            if key:
                self._headers = {header_name: key}
        elif auth_type == "basic":
            user = creds.get("username", "")
            password = creds.get("password", "")
            if user and password:
                import base64
                encoded = base64.b64encode(f"{user}:{password}".encode()).decode()
                self._headers = {"Authorization": f"Basic {encoded}"}
        return dict(self._headers)

    def _detect_content_type(self, headers: dict[str, str], body: Any) -> str:
        if "Content-Type" in headers:
            return headers["Content-Type"]
        if isinstance(body, (dict, list)):
            return "application/json"
        if isinstance(body, str):
            if body.strip().startswith("<"):
                return "application/xml"
            return "text/plain"
        return "application/json"

    def _serialize_body(self, body: Any, content_type: str) -> str | None:
        if body is None:
            return None
        if content_type == "application/json":
            return json.dumps(body)
        if content_type in ("application/xml", "text/xml"):
            if isinstance(body, str):
                return body
            if isinstance(body, dict):
                root_name = body.get("_root", "root")
                return self._dict_to_xml(root_name, body)
            return str(body)
        if content_type == "application/x-www-form-urlencoded" and isinstance(body, dict):
            from urllib.parse import urlencode
            return urlencode(body)
        return str(body) if body else None

    def _dict_to_xml(self, root_name: str, data: dict) -> str:
        root = ElementTree.Element(root_name)
        for key, value in data.items():
            if key.startswith("_"):
                continue
            child = ElementTree.SubElement(root, key)
            if isinstance(value, dict):
                for k, v in value.items():
                    grandchild = ElementTree.SubElement(child, k)
                    grandchild.text = str(v)
            else:
                child.text = str(value)
        return ElementTree.tostring(root, encoding="unicode")

    def _parse_response(self, response: httpx.Response) -> Any:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError):
                return response.text
        if "application/xml" in content_type or "text/xml" in content_type:
            try:
                root = safe_xml_parse(response.content)
                return self._xml_to_dict(root)
            except SafeXMLParseError:
                return response.text
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return response.text

    def _xml_to_dict(self, element) -> dict:
        result: dict = {}
        for child in element:
            if len(child):
                sub = self._xml_to_dict(child)
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(sub)
                else:
                    result[child.tag] = sub
            else:
                text = child.text or ""
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(text)
                else:
                    result[child.tag] = text
        return result

    def _check_circuit(self) -> bool:
        if self._metrics["circuit_breaker_open"]:
            recovery_window = self._config.retry_delay_seconds * self._config.retry_count
            last_call = self._metrics.get("last_call_at") or 0
            if time.time() - last_call >= recovery_window:
                self._metrics["circuit_breaker_open"] = False
                self._metrics["consecutive_failures"] = 0
                self._status = ConnectorStatus.DEGRADED
                return True
            return False
        return True
