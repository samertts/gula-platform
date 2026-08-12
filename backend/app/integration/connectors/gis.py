from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.gis")


class GISConnector(BaseConnector):
    def __init__(
        self,
        name: str = "gis",
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
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("GIS connector connected")
            return True
        except Exception as exc:
            logger.error("GIS connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("GIS connector disconnected")
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
        if action == "geocode":
            return await self._geocode(data)
        if action == "reverse_geocode":
            return await self._reverse_geocode(data)
        if action == "find_facilities":
            return await self._find_facilities(data)
        if action == "get_boundary":
            return await self._get_boundary(data)
        if action == "map_facility":
            return await self._map_facility(data)
        if action == "nearby_facilities":
            return await self._nearby_facilities(data)
        raise ValueError(f"Unknown GIS action: {action}")

    async def _geocode(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        address = data.get("address", "")
        if not address:
            return {"success": False, "error": "address required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/geocode"),
                params={"address": address, "country": data.get("country", "IQ")},
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "latitude": result.get("latitude", 0),
                    "longitude": result.get("longitude", 0),
                    "formatted_address": result.get("formatted_address", ""),
                    "confidence": result.get("confidence", 0),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Geocode failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _reverse_geocode(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return {"success": False, "error": "latitude and longitude required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/reverse-geocode"),
                params={"latitude": latitude, "longitude": longitude},
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "address": result.get("address", ""),
                    "city": result.get("city", ""),
                    "province": result.get("province", ""),
                    "country": result.get("country", "IQ"),
                    "postal_code": result.get("postal_code", ""),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Reverse geocode failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _find_facilities(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        facility_type = data.get("facility_type", "hospital")
        region = data.get("region", "")
        try:
            params: dict[str, str] = {"type": facility_type}
            if region:
                params["region"] = region
            resp = await self._client.get(
                urljoin(self._base_url, "/api/facilities"),
                params=params,
            )
            if resp.is_success:
                facilities = resp.json()
                return {"success": True, "facilities": facilities, "count": len(facilities)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Find facilities failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_boundary(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        region = data.get("region", "")
        level = data.get("level", "province")
        if not region:
            return {"success": False, "error": "region required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/boundaries/{region}"),
                params={"level": level},
            )
            if resp.is_success:
                return {"success": True, "boundary": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Boundary query failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _map_facility(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        facility = {
            "name": data.get("name", ""),
            "type": data.get("type", "clinic"),
            "latitude": data.get("latitude", 0),
            "longitude": data.get("longitude", 0),
            "address": data.get("address", ""),
            "phone": data.get("phone", ""),
            "services": data.get("services", []),
        }
        if not facility["name"]:
            return {"success": False, "error": "facility name required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/facilities"),
                json=facility,
            )
            if resp.is_success:
                return {"success": True, "facility": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Facility mapping failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _nearby_facilities(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GIS connector not connected")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        radius_km = data.get("radius_km", 10)
        facility_type = data.get("facility_type", "")
        if latitude is None or longitude is None:
            return {"success": False, "error": "latitude and longitude required"}
        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
        }
        if facility_type:
            params["type"] = facility_type
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/facilities/nearby"),
                params=params,
            )
            if resp.is_success:
                facilities = resp.json()
                return {"success": True, "facilities": facilities, "count": len(facilities)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Nearby facilities query failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("gis", GISConnector)
