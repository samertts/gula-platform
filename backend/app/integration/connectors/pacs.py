from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.pacs")


class PACSConnector(BaseConnector):
    def __init__(
        self,
        name: str = "pacs",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._ae_title = self.config.get("ae_title", "GULA_PACS")
        self._wado_url = self.config.get("wado_url", "")
        self._qido_url = self.config.get("qido_url", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers={"Accept": "application/dicom+json"},
            )
            self._connected = True
            logger.info("PACS connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("PACS connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("PACS connector disconnected")
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
            resp = await self._client.get(urljoin(self._base_url, "/dicom-web/health"))
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status"] = "healthy" if resp.is_success else "degraded"
            result["status_code"] = resp.status_code
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "query")
        if action == "store":
            return await self._store_dicom(data)
        if action == "query":
            return await self._query_studies(data)
        if action == "retrieve":
            return await self._retrieve_study(data)
        if action == "wado":
            return await self._wado_rs(data)
        if action == "qido":
            return await self._qido_rs(data)
        raise ValueError(f"Unknown PACS action: {action}")

    async def _query_studies(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("PACS connector not connected")
        qido_base = self._qido_url or urljoin(self._base_url, "/dicom-web/studies")
        params: dict[str, str] = {}
        for field in (
            "PatientName",
            "PatientID",
            "StudyDate",
            "StudyDescription",
            "AccessionNumber",
        ):
            if field in data:
                params[field] = str(data[field])
        try:
            resp = await self._client.get(qido_base, params=params)
            if resp.is_success:
                studies = resp.json() if resp.text else []
                return {"success": True, "studies": studies, "count": len(studies)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("PACS query failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _retrieve_study(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("PACS connector not connected")
        study_uid = data.get("study_uid", "")
        if not study_uid:
            return {"success": False, "error": "study_uid required"}
        wado_base = self._wado_url or urljoin(self._base_url, f"/dicom-web/studies/{study_uid}")
        try:
            resp = await self._client.get(wado_base)
            if resp.is_success:
                return {
                    "success": True,
                    "study_uid": study_uid,
                    "content_type": resp.headers.get("content-type", ""),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("PACS retrieve failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _store_dicom(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("PACS connector not connected")
        dicom_data = data.get("dicom_data")
        if not dicom_data:
            return {"success": False, "error": "dicom_data required"}
        stow_url = urljoin(self._base_url, "/dicom-web/studies")
        try:
            resp = await self._client.post(
                stow_url, content=dicom_data, headers={"Content-Type": "application/dicom"}
            )
            return {"success": resp.is_success, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("PACS store failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _wado_rs(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("PACS connector not connected")
        study_uid = data.get("study_uid", "")
        series_uid = data.get("series_uid", "")
        instance_uid = data.get("instance_uid", "")
        path = f"/dicom-web/studies/{study_uid}"
        if series_uid:
            path += f"/series/{series_uid}"
        if instance_uid:
            path += f"/instances/{instance_uid}"
        url = urljoin(self._base_url, path)
        try:
            resp = await self._client.get(url)
            return {
                "success": resp.is_success,
                "content_type": resp.headers.get("content-type", ""),
                "status_code": resp.status_code,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _qido_rs(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._query_studies(data)


ConnectorRegistry.register("pacs", PACSConnector)
