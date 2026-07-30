from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.ris")


class RISConnector(BaseConnector):
    def __init__(
        self,
        name: str = "ris",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("RIS connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("RIS connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("RIS connector disconnected")
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
        if action == "send_orm":
            return await self._send_orm(data)
        if action == "send_oru":
            return await self._send_oru(data)
        if action == "get_worklist":
            return await self._get_worklist(data)
        if action == "schedule":
            return await self._schedule_exam(data)
        if action == "get_report":
            return await self._get_report(data)
        if action == "submit_report":
            return await self._submit_report(data)
        if action == "cancel_order":
            return await self._cancel_order(data)
        raise ValueError(f"Unknown RIS action: {action}")

    async def _send_orm(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        hl7_message = data.get("hl7_message", "")
        order_payload = {
            "message_type": "ORM",
            "message": hl7_message,
            "sending_app": data.get("sending_app", "GULA_RIS"),
            "order_control": data.get("order_control", "NW"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/hl7/orm"),
                json=order_payload,
            )
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "response": resp.text,
            }
        except Exception as exc:
            logger.error("RIS ORM failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_oru(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        hl7_message = data.get("hl7_message", "")
        result_payload = {
            "message_type": "ORU",
            "message": hl7_message,
            "sending_app": data.get("sending_app", "GULA_RIS"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/hl7/oru"),
                json=result_payload,
            )
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "response": resp.text,
            }
        except Exception as exc:
            logger.error("RIS ORU failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_worklist(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        modality = data.get("modality", "")
        date = data.get("date", "")
        params: dict[str, str] = {}
        if modality:
            params["modality"] = modality
        if date:
            params["date"] = date
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/worklist"),
                params=params,
            )
            if resp.is_success:
                items = resp.json()
                return {"success": True, "worklist": items, "count": len(items)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("RIS worklist failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _schedule_exam(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        exam_payload = {
            "patient_id": data.get("patient_id", ""),
            "accession_number": data.get("accession_number", ""),
            "modality": data.get("modality", ""),
            "procedure_code": data.get("procedure_code", ""),
            "scheduled_date": data.get("scheduled_date", ""),
            "referring_physician": data.get("referring_physician", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/schedule"),
                json=exam_payload,
            )
            if resp.is_success:
                return {"success": True, "schedule": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("RIS schedule failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        accession_number = data.get("accession_number", "")
        study_uid = data.get("study_uid", "")
        if not accession_number and not study_uid:
            return {"success": False, "error": "accession_number or study_uid required"}
        params = {}
        if accession_number:
            params["accession_number"] = accession_number
        if study_uid:
            params["study_uid"] = study_uid
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/reports"),
                params=params,
            )
            if resp.is_success:
                return {"success": True, "report": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("RIS get_report failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _submit_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        report_payload = {
            "accession_number": data.get("accession_number", ""),
            "study_uid": data.get("study_uid", ""),
            "report_text": data.get("report_text", ""),
            "radiologist": data.get("radiologist", ""),
            "status": data.get("status", "final"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/reports"),
                json=report_payload,
            )
            return {"success": resp.is_success, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("RIS submit_report failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _cancel_order(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("RIS connector not connected")
        order_id = data.get("order_id", "")
        if not order_id:
            return {"success": False, "error": "order_id required"}
        cancel_payload = {
            "order_id": order_id,
            "reason": data.get("reason", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, f"/api/orders/{order_id}/cancel"),
                json=cancel_payload,
            )
            return {"success": resp.is_success, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("RIS cancel_order failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("ris", RISConnector)
