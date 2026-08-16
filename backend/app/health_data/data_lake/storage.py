from __future__ import annotations

import io
import logging
import os
import tempfile
from abc import ABC, abstractmethod

from app.config import IS_PRODUCTION

logger = logging.getLogger("gula.health_data.data_lake.storage")


class StorageBackend(ABC):
    @abstractmethod
    async def write(self, path: str, data: bytes) -> None: ...

    @abstractmethod
    async def read(self, path: str) -> bytes: ...

    @abstractmethod
    async def exists(self, path: str) -> bool: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def list(self, prefix: str) -> list[str]: ...

    @abstractmethod
    async def size(self, path: str) -> int: ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str | None = None):
        configured_path = (base_path or os.environ.get("GULA_DATA_LAKE_PATH", "")).strip()
        if IS_PRODUCTION and not configured_path:
            raise RuntimeError(
                "GULA_DATA_LAKE_PATH must point to a durable, access-controlled volume "
                "in staging/production; /tmp fallback is forbidden",
            )
        self.base_path = configured_path or os.path.join(
            tempfile.gettempdir(), "gula", "data", "lake",
        )
        os.makedirs(self.base_path, exist_ok=True)

    def _resolve(self, path: str) -> str:
        full = os.path.normpath(os.path.join(self.base_path, path))
        if not full.startswith(self.base_path):
            raise ValueError("Path traversal detected")
        return full

    async def write(self, path: str, data: bytes) -> None:
        full = self._resolve(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)

    async def read(self, path: str) -> bytes:
        full = self._resolve(path)
        with open(full, "rb") as f:
            return f.read()

    async def exists(self, path: str) -> bool:
        return os.path.exists(self._resolve(path))

    async def delete(self, path: str) -> None:
        full = self._resolve(path)
        if os.path.exists(full):
            os.remove(full)

    async def list(self, prefix: str) -> list[str]:
        full = self._resolve(prefix)
        if not os.path.exists(full):
            return []
        results = []
        for root, _dirs, files in os.walk(full):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.base_path)
                results.append(rel)
        return results

    async def size(self, path: str) -> int:
        full = self._resolve(path)
        return os.path.getsize(full) if os.path.exists(full) else 0


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str, prefix: str = "health-data", client=None):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self._client = client

    async def _get_client(self):
        if self._client is None:
            import aiobotocore.session

            session = aiobotocore.session.get_session()
            self._client = session.create_client("s3")
        return self._client

    async def write(self, path: str, data: bytes) -> None:
        client = await self._get_client()
        key = f"{self.prefix}/{path}" if self.prefix else path
        buf = io.BytesIO(data)
        await client.put_object(Bucket=self.bucket, Key=key, Body=buf)

    async def read(self, path: str) -> bytes:
        client = await self._get_client()
        key = f"{self.prefix}/{path}" if self.prefix else path
        resp = await client.get_object(Bucket=self.bucket, Key=key)
        return await resp["Body"].read()

    async def exists(self, path: str) -> bool:
        client = await self._get_client()
        key = f"{self.prefix}/{path}" if self.prefix else path
        try:
            await client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def delete(self, path: str) -> None:
        client = await self._get_client()
        key = f"{self.prefix}/{path}" if self.prefix else path
        await client.delete_object(Bucket=self.bucket, Key=key)

    async def list(self, prefix: str) -> list[str]:
        client = await self._get_client()
        key_prefix = f"{self.prefix}/{prefix}" if self.prefix else prefix
        keys = []
        paginator = client.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=self.bucket, Prefix=key_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if self.prefix:
                    key = key[len(self.prefix) + 1:]
                keys.append(key)
        return keys

    async def size(self, path: str) -> int:
        client = await self._get_client()
        key = f"{self.prefix}/{path}" if self.prefix else path
        resp = await client.head_object(Bucket=self.bucket, Key=key)
        return resp.get("ContentLength", 0)
