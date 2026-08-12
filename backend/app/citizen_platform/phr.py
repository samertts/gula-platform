from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.platform.documents import DocumentService as PlatformDocumentService

logger = logging.getLogger("gula.citizen.phr")


@dataclass
class PHRDocument:
    id: str = ""
    citizen_id: str = ""
    document_type: str = ""
    filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    storage_path: str = ""
    uploaded_at: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    is_encrypted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthMetric:
    id: str = ""
    citizen_id: str = ""
    metric_type: str = ""
    value: float = 0.0
    unit: str = ""
    recorded_at: str = ""
    source: str = "manual"


class PHRService:
    def __init__(self, document_service: PlatformDocumentService | None = None) -> None:
        self._document_service = document_service or PlatformDocumentService()
        self._metrics: dict[str, list[HealthMetric]] = {}
        self._documents: dict[str, list[PHRDocument]] = {}
        self._health_data: dict[str, dict[str, Any]] = {}

    def record_metric(self, citizen_id: str, metric: HealthMetric) -> None:
        if citizen_id not in self._metrics:
            self._metrics[citizen_id] = []
        self._metrics[citizen_id].append(metric)

    def get_metrics(
        self,
        citizen_id: str,
        metric_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> list[HealthMetric]:
        metrics = self._metrics.get(citizen_id, [])
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        if from_date:
            metrics = [m for m in metrics if m.recorded_at >= from_date]
        if to_date:
            metrics = [m for m in metrics if m.recorded_at <= to_date]
        metrics.sort(key=lambda m: m.recorded_at, reverse=True)
        return metrics[:limit]

    def get_latest_metric(self, citizen_id: str, metric_type: str) -> HealthMetric | None:
        metrics = [m for m in self._metrics.get(citizen_id, []) if m.metric_type == metric_type]
        if not metrics:
            return None
        return max(metrics, key=lambda m: m.recorded_at)

    def update_health_data(
        self, citizen_id: str, data_type: str, data: dict[str, Any],
    ) -> None:
        if citizen_id not in self._health_data:
            self._health_data[citizen_id] = {}
        self._health_data[citizen_id][data_type] = {
            **self._health_data[citizen_id].get(data_type, {}),
            **data,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def get_health_data(self, citizen_id: str, data_type: str) -> dict[str, Any] | None:
        return self._health_data.get(citizen_id, {}).get(data_type)

    def get_all_health_data(self, citizen_id: str) -> dict[str, Any]:
        return self._health_data.get(citizen_id, {})


class DocumentUploader:
    def __init__(self, document_service: PlatformDocumentService) -> None:
        self._document_service = document_service

    def upload_document(
        self,
        citizen_id: str,
        filename: str,
        content: bytes,
        document_type: str,
        mime_type: str = "application/octet-stream",
        description: str = "",
        tags: list[str] | None = None,
    ) -> PHRDocument:
        doc = self._document_service.upload(filename, content, mime_type)
        return PHRDocument(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            document_type=document_type,
            filename=filename,
            mime_type=mime_type,
            size_bytes=doc.size_bytes,
            storage_path=doc.storage_path,
            uploaded_at=datetime.now(UTC).isoformat(),
            description=description,
            tags=tags or [],
        )

    def download_document(self, document_id: str) -> bytes | None:
        return self._document_service.download(document_id)

    def delete_document(self, document_id: str) -> bool:
        return self._document_service.delete(document_id)


class StorageService:
    def __init__(self, base_path: str = "/app/data/citizen_storage") -> None:
        self._base_path = base_path
        self._storage_quota: dict[str, int] = {}

    def get_storage_usage(self, citizen_id: str) -> dict[str, Any]:
        import os

        citizen_path = os.path.join(self._base_path, citizen_id)
        total_size = 0
        file_count = 0
        if os.path.exists(citizen_path):
            for dirpath, _dirnames, filenames in os.walk(citizen_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
                        file_count += 1
        quota = self._storage_quota.get(citizen_id, 100 * 1024 * 1024)
        return {
            "citizen_id": citizen_id,
            "used_bytes": total_size,
            "file_count": file_count,
            "quota_bytes": quota,
            "usage_percent": round((total_size / quota) * 100, 2) if quota > 0 else 0,
        }

    def set_quota(self, citizen_id: str, quota_bytes: int) -> None:
        self._storage_quota[citizen_id] = quota_bytes
