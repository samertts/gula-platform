from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.cloud_storage")

SUPPORTED_PROVIDERS = frozenset({"s3", "minio", "azure_blob", "gcs"})


class CloudStorageConnector(BaseConnector):
    def __init__(
        self,
        name: str = "cloud_storage",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._provider = self.config.get("provider", "s3")
        if self._provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported cloud storage provider: {self._provider}. "
                f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}",
            )
        self._endpoint = self.config.get("endpoint", "")
        self._region = self.config.get("region", "us-east-1")
        self._bucket = self.config.get("bucket", "")
        self._access_key = self.config.get("access_key", "")
        self._secret_key = self.config.get("secret_key", "")
        self._container = self.config.get("container", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 60.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers: dict[str, str] = {}
            if self._access_key and self._secret_key:
                headers["Authorization"] = self._build_auth_header()
            if self._provider in ("azure_blob",):
                headers["x-ms-version"] = "2021-08-06"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("Cloud storage connector connected: provider=%s bucket=%s", self._provider, self._bucket)
            return True
        except Exception as exc:
            logger.error("Cloud storage connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Cloud storage connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "provider": self._provider,
            "bucket": self._bucket,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if not self._client:
            result["status"] = "disconnected"
            return result
        try:
            start = time.monotonic()
            url = self._build_url()
            resp = await self._client.head(url)
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status"] = "healthy" if resp.is_success else "degraded"
            result["status_code"] = resp.status_code
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "")
        if action == "upload":
            return await self._upload_file(data)
        if action == "download":
            return await self._download_file(data)
        if action == "delete":
            return await self._delete_file(data)
        if action == "list":
            return await self._list_files(data)
        if action == "exists":
            return await self._file_exists(data)
        if action == "copy":
            return await self._copy_file(data)
        raise ValueError(f"Unknown cloud storage action: {action}")

    def _build_auth_header(self) -> str:
        return f"Bearer {self._access_key}:{self._secret_key}"

    def _build_url(self, key: str = "") -> str:
        if self._provider in ("s3", "minio"):
            if self._endpoint:
                base = self._endpoint.rstrip("/")
                return f"{base}/{self._bucket}/{key}" if key else f"{base}/{self._bucket}"
            return f"https://{self._bucket}.s3.{self._region}.amazonaws.com/{key}" if key else f"https://{self._bucket}.s3.{self._region}.amazonaws.com"
        if self._provider == "azure_blob":
            base = self._endpoint.rstrip("/") if self._endpoint else f"https://{self._container}.blob.core.windows.net"
            return f"{base}/{self._bucket}/{key}" if key else f"{base}/{self._bucket}"
        if self._provider == "gcs":
            return f"https://storage.googleapis.com/{self._bucket}/{key}" if key else f"https://storage.googleapis.com/storage/v1/b/{self._bucket}"
        return ""

    async def _upload_file(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        key = data.get("key", "")
        content = data.get("content", "")
        content_type = data.get("content_type", "application/octet-stream")
        if not key or not content:
            return {"success": False, "error": "key and content required"}
        url = self._build_url(key)
        headers = {"Content-Type": content_type}
        try:
            content_bytes = content.encode() if isinstance(content, str) else content
            resp = await self._client.put(url, content=content_bytes, headers=headers)
            if resp.is_success:
                return {"success": True, "key": key, "size": len(content_bytes)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Cloud storage upload failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _download_file(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        key = data.get("key", "")
        if not key:
            return {"success": False, "error": "key required"}
        url = self._build_url(key)
        try:
            resp = await self._client.get(url)
            if resp.is_success:
                return {"success": True, "key": key, "content": resp.text, "size": len(resp.content)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Cloud storage download failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _delete_file(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        key = data.get("key", "")
        if not key:
            return {"success": False, "error": "key required"}
        url = self._build_url(key)
        try:
            resp = await self._client.delete(url)
            if resp.is_success:
                return {"success": True, "key": key}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Cloud storage delete failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _list_files(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        prefix = data.get("prefix", "")
        url = self._build_url()
        params: dict[str, Any] = {}
        if prefix:
            params["prefix"] = prefix
        if self._provider == "gcs":
            params["projection"] = "noAcl"
        try:
            resp = await self._client.get(url, params=params)
            if resp.is_success:
                body = resp.json()
                keys = []
                if self._provider in ("s3", "minio"):
                    contents = body.get("Contents", [])
                    keys = [c.get("Key", "") for c in contents]
                elif self._provider == "azure_blob":
                    blobs = body.get("Blobs", body.get("blobs", []))
                    keys = [b.get("Name", "") for b in blobs]
                elif self._provider == "gcs":
                    items = body.get("items", [])
                    keys = [i.get("name", "") for i in items]
                return {"success": True, "keys": keys, "count": len(keys)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Cloud storage list failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _file_exists(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        key = data.get("key", "")
        if not key:
            return {"success": False, "error": "key required"}
        url = self._build_url(key)
        try:
            resp = await self._client.head(url)
            return {"success": True, "key": key, "exists": resp.is_success}
        except Exception as exc:
            logger.error("Cloud storage exists check failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _copy_file(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Cloud storage connector not connected")
        source_key = data.get("source_key", "")
        dest_key = data.get("dest_key", "")
        if not source_key or not dest_key:
            return {"success": False, "error": "source_key and dest_key required"}
        self._build_url(source_key)
        dest_url = self._build_url(dest_key)
        try:
            headers = {"X-Amz-Copy-Source": f"/{self._bucket}/{source_key}"}
            resp = await self._client.put(dest_url, headers=headers)
            if resp.is_success:
                return {"success": True, "source_key": source_key, "dest_key": dest_key}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Cloud storage copy failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("cloud_storage", CloudStorageConnector)
