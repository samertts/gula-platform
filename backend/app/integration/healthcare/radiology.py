from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.radiology")


class RadiologyIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "radiology_integration",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._ae_title = self.config.get("ae_title", "GULA")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 60.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            headers["X-AE-Title"] = self._ae_title
            self._client = httpx.AsyncClient(
                timeout=self._timeout, verify=self._verify_ssl, headers=headers
            )
            self._connected = True
            logger.info("Radiology integration connected")
            return True
        except Exception as exc:
            logger.error("Radiology integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Radiology integration disconnected")
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
        if action == "order_study":
            return await self._order_study(data)
        if action == "upload_dicom":
            return await self._upload_dicom(data)
        if action == "get_report":
            return await self._get_radiology_report(data)
        if action == "query_studies":
            return await self._query_studies(data)
        if action == "schedule_imaging":
            return await self._schedule_imaging(data)
        raise ValueError(f"Unknown radiology action: {action}")

    async def _order_study(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Radiology connector not connected")
        order = {
            "patient_id": data.get("patient_id", ""),
            "accession_number": data.get("accession_number", ""),
            "study_type": data.get("study_type", ""),
            "body_part": data.get("body_part", ""),
            "modality": data.get("modality", "DX"),
            "ordering_physician": data.get("ordering_physician", ""),
            "clinical_indication": data.get("clinical_indication", ""),
            "priority": data.get("priority", "routine"),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/orders"), json=order)
            if resp.is_success:
                return {"success": True, "study_uid": resp.json().get("study_instance_uid", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Radiology order failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _upload_dicom(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Radiology connector not connected")
        files = data.get("files", [])
        if not files:
            return {"success": False, "error": "no dicom files provided"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/dicom/upload"),
                json={"study_uid": data.get("study_uid", ""), "files": files},
            )
            if resp.is_success:
                return {"success": True, "upload": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("DICOM upload failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_radiology_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Radiology connector not connected")
        study_uid = data.get("study_uid", "")
        if not study_uid:
            return {"success": False, "error": "study_uid required"}
        try:
            resp = await self._client.get(urljoin(self._base_url, f"/api/reports/{study_uid}"))
            if resp.is_success:
                return {"success": True, "report": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Radiology report fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _query_studies(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Radiology connector not connected")
        params = {
            "patient_id": data.get("patient_id", ""),
            "modality": data.get("modality", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/studies"), params=params)
            if resp.is_success:
                studies = resp.json()
                return {
                    "success": True,
                    "studies": studies,
                    "count": len(studies) if isinstance(studies, list) else 0,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Study query failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _schedule_imaging(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Radiology connector not connected")
        appointment = {
            "patient_id": data.get("patient_id", ""),
            "study_type": data.get("study_type", ""),
            "modality": data.get("modality", "DX"),
            "scheduled_date": data.get("scheduled_date", ""),
            "scheduled_time": data.get("scheduled_time", ""),
            "referring_physician": data.get("referring_physician", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/schedule"), json=appointment
            )
            if resp.is_success:
                return {"success": True, "appointment": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Imaging schedule failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("radiology_integration", RadiologyIntegration)
