from __future__ import annotations

import io
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger("gula.storage")


class StorageBackend(ABC):
    @abstractmethod
    def save(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        ...

    @abstractmethod
    def read(self, path: str) -> bytes | None:
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        ...

    @abstractmethod
    def list(self, prefix: str = "") -> list[str]:
        ...


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str = "/tmp/gula_storage") -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        full = self._base / path
        full.parent.mkdir(parents=True, exist_ok=True)
        return full

    def save(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        full = self._resolve(path)
        full.write_bytes(data)
        return str(full)

    def read(self, path: str) -> bytes | None:
        full = self._resolve(path)
        if not full.exists():
            return None
        return full.read_bytes()

    def delete(self, path: str) -> bool:
        full = self._resolve(path)
        if full.exists():
            full.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def list(self, prefix: str = "") -> list[str]:
        target = self._base / prefix
        if not target.exists():
            return []
        return [str(p.relative_to(self._base)) for p in target.rglob("*") if p.is_file()]


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, access_key: str = "", secret_key: str = "", endpoint: str = "", region: str = "us-east-1") -> None:
        import boto3
        self._bucket = bucket
        kwargs: dict[str, Any] = {"region_name": region}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        self._client = boto3.client("s3", **kwargs)

    def save(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client.put_object(Bucket=self._bucket, Key=path, Body=data, ContentType=content_type)
        return path

    def read(self, path: str) -> bytes | None:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=path)
            return resp["Body"].read()
        except self._client.exceptions.NoSuchKey:
            return None

    def delete(self, path: str) -> bool:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=path)
            return True
        except Exception:
            return False

    def exists(self, path: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=path)
            return True
        except Exception:
            return False

    def list(self, prefix: str = "") -> list[str]:
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    keys.append(obj["Key"])
        return keys


class R2Storage(S3Storage):
    def __init__(self, bucket: str, access_key: str = "", secret_key: str = "", account_id: str = "") -> None:
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        super().__init__(bucket, access_key, secret_key, endpoint=endpoint)


_storage_instance: StorageBackend | None = None


def get_storage(backend: str = "local", **kwargs: Any) -> StorageBackend:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance
    if backend == "s3":
        _storage_instance = S3Storage(**kwargs)
    elif backend == "r2":
        _storage_instance = R2Storage(**kwargs)
    else:
        _storage_instance = LocalStorage(**kwargs)
    return _storage_instance
