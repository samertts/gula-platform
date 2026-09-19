from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import httpx
from sqlalchemy.orm import Session

from app._compat import UTC
from app.radiology.enums import ArchiveTier, SharingType, StorageCompressionType
from app.radiology.models import (
    DICOMStorage,
    DICOMStudy,
    ImageShare,
)

logger = logging.getLogger("gula.radiology.pacs")


def _calculate_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _generate_access_code() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:12]


# ==============================================================================
# DICOMStorageService
# ==============================================================================


class DICOMStorageService:
    def __init__(self, db: Session, storage_root: str = "/data/dicom"):
        self.db = db
        self.storage_root = storage_root

    def store(
        self,
        sop_instance_uid: str,
        study_instance_uid: str,
        series_instance_uid: str,
        patient_id: str,
        modality: str,
        file_path: str,
        file_size: int | None = None,
        study_id: str | None = None,
        body_part: str | None = None,
        checksum: str | None = None,
        compression_type: str = "none",
        retention_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DICOMStorage:
        record = DICOMStorage(
            sop_instance_uid=sop_instance_uid,
            study_instance_uid=study_instance_uid,
            series_instance_uid=series_instance_uid,
            patient_id=patient_id,
            study_id=study_id,
            modality=modality.upper(),
            body_part=body_part,
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            storage_date=datetime.now(UTC),
            storage_tier=ArchiveTier.HOT,
            compression_type=compression_type,
            retention_days=retention_days,
            metadata=metadata or {},
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("DICOM instance stored: %s", sop_instance_uid)
        return record

    def retrieve(self, sop_instance_uid: str) -> DICOMStorage | None:
        return self.db.query(DICOMStorage).filter(
            DICOMStorage.sop_instance_uid == sop_instance_uid,
            ~DICOMStorage.is_deleted,
        ).first()

    def delete(self, sop_instance_uid: str) -> bool:
        record = self.retrieve(sop_instance_uid)
        if not record:
            return False
        record.soft_delete()
        self.db.commit()
        return True

    def query(
        self,
        study_instance_uid: str | None = None,
        series_instance_uid: str | None = None,
        patient_id: str | None = None,
        modality: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DICOMStorage]:
        q = self.db.query(DICOMStorage).filter(~DICOMStorage.is_deleted)
        if study_instance_uid:
            q = q.filter(DICOMStorage.study_instance_uid == study_instance_uid)
        if series_instance_uid:
            q = q.filter(DICOMStorage.series_instance_uid == series_instance_uid)
        if patient_id:
            q = q.filter(DICOMStorage.patient_id == patient_id)
        if modality:
            q = q.filter(DICOMStorage.modality == modality.upper())
        if date_from:
            q = q.filter(DICOMStorage.storage_date >= date_from)
        if date_to:
            q = q.filter(DICOMStorage.storage_date <= date_to)
        return q.offset(skip).limit(limit).all()

    def get_study_instances(self, study_instance_uid: str) -> list[DICOMStorage]:
        return self.query(study_instance_uid=study_instance_uid)

    def get_series_instances(
        self,
        series_instance_uid: str,
        study_instance_uid: str | None = None,
    ) -> list[DICOMStorage]:
        return self.query(
            series_instance_uid=series_instance_uid,
            study_instance_uid=study_instance_uid,
        )

    def count_by_tier(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for tier in ArchiveTier:
            cnt = self.db.query(DICOMStorage).filter(
                DICOMStorage.storage_tier == tier,
                ~DICOMStorage.is_deleted,
            ).count()
            counts[tier.value] = cnt
        return counts

    def total_storage_size(self) -> int:
        result = self.db.query(DICOMStorage).filter(
            ~DICOMStorage.is_deleted,
        ).with_entities(DICOMStorage.file_size).all()
        return sum(r[0] or 0 for r in result)


# ==============================================================================
# DICOMStudyService
# ==============================================================================


class DICOMStudyService:
    def __init__(self, db: Session):
        self.db = db

    def create_study(
        self,
        study_instance_uid: str,
        patient_id: str,
        accession_number: str | None = None,
        study_date: datetime | None = None,
        study_description: str | None = None,
        modality: str | None = None,
        referring_physician: str | None = None,
        number_of_series: int = 0,
        number_of_images: int = 0,
        storage_size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> DICOMStudy:
        study = DICOMStudy(
            study_instance_uid=study_instance_uid,
            patient_id=patient_id,
            accession_number=accession_number,
            study_date=study_date or datetime.now(UTC),
            study_description=study_description,
            modality=modality.upper() if modality else None,
            referring_physician=referring_physician,
            number_of_series=number_of_series,
            number_of_images=number_of_images,
            storage_size_bytes=storage_size_bytes,
            metadata=metadata or {},
        )
        self.db.add(study)
        self.db.commit()
        self.db.refresh(study)
        return study

    def get_study(self, study_instance_uid: str) -> DICOMStudy | None:
        return self.db.query(DICOMStudy).filter(
            DICOMStudy.study_instance_uid == study_instance_uid,
            ~DICOMStudy.is_deleted,
        ).first()

    def search_studies(
        self,
        patient_id: str | None = None,
        modality: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        accession_number: str | None = None,
        study_description: str | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[DICOMStudy]:
        q = self.db.query(DICOMStudy).filter(~DICOMStudy.is_deleted)
        if patient_id:
            q = q.filter(DICOMStudy.patient_id == patient_id)
        elif patient_ids is not None:
            q = q.filter(DICOMStudy.patient_id.in_(patient_ids))
        if modality:
            q = q.filter(DICOMStudy.modality == modality.upper())
        if date_from:
            q = q.filter(DICOMStudy.study_date >= date_from)
        if date_to:
            q = q.filter(DICOMStudy.study_date <= date_to)
        if accession_number:
            q = q.filter(DICOMStudy.accession_number == accession_number)
        if study_description:
            q = q.filter(DICOMStudy.study_description.ilike(f"%{study_description}%"))
        q = q.order_by(DICOMStudy.study_date.desc())
        return q.offset(skip).limit(limit).all()

    def update_study_counts(self, study_instance_uid: str, number_of_series: int | None = None, number_of_images: int | None = None, storage_size_bytes: int | None = None) -> DICOMStudy | None:
        study = self.get_study(study_instance_uid)
        if not study:
            return None
        if number_of_series is not None:
            study.number_of_series = number_of_series
        if number_of_images is not None:
            study.number_of_images = number_of_images
        if storage_size_bytes is not None:
            study.storage_size_bytes = storage_size_bytes
        self.db.commit()
        self.db.refresh(study)
        return study


# ==============================================================================
# ImageViewerService
# ==============================================================================


class ImageViewerService:
    def __init__(self, db: Session, stream_base_url: str = "https://pixel.gula.iq/stream"):
        self.db = db
        self.stream_base_url = stream_base_url

    def get_streaming_url(self, sop_instance_uid: str) -> str | None:
        storage = self.db.query(DICOMStorage).filter(
            DICOMStorage.sop_instance_uid == sop_instance_uid,
            ~DICOMStorage.is_deleted,
        ).first()
        if not storage:
            return None
        stream_path = f"/studies/{storage.study_instance_uid}/series/{storage.series_instance_uid}/instances/{sop_instance_uid}/stream"
        return urljoin(self.stream_base_url, stream_path)

    def get_thumbnail_url(self, sop_instance_uid: str, size: int = 256) -> str | None:
        storage = self.db.query(DICOMStorage).filter(
            DICOMStorage.sop_instance_uid == sop_instance_uid,
            ~DICOMStorage.is_deleted,
        ).first()
        if not storage:
            return None
        thumb_path = f"/studies/{storage.study_instance_uid}/series/{storage.series_instance_uid}/instances/{sop_instance_uid}/thumbnail?size={size}"
        return urljoin(self.stream_base_url, thumb_path)

    def get_viewer_url(self, study_instance_uid: str) -> str:
        return urljoin(self.stream_base_url, f"/viewer?study={study_instance_uid}")

    def get_series_viewer_url(self, study_instance_uid: str, series_instance_uid: str) -> str:
        return urljoin(self.stream_base_url, f"/viewer?study={study_instance_uid}&series={series_instance_uid}")


# ==============================================================================
# ImageCompressionService
# ==============================================================================


class ImageCompressionService:
    LOSSY_FORMATS = frozenset({"jpeg", "webp", "png"})
    LOSSLESS_FORMATS = frozenset({"jp2", "dcm", "raw"})

    def should_compress(self, current_format: str, target_tier: ArchiveTier) -> bool:
        if target_tier == ArchiveTier.HOT:
            return current_format in ("raw", "dcm")
        return True

    def get_compression_type(self, tier: ArchiveTier) -> StorageCompressionType:
        if tier == ArchiveTier.HOT:
            return StorageCompressionType.NONE
        if tier == ArchiveTier.WARM:
            return StorageCompressionType.LOSSLESS_JPEG_LS
        if tier == ArchiveTier.COLD:
            return StorageCompressionType.LOSSY_JPEG
        if tier == ArchiveTier.DEEP_ARCHIVE:
            return StorageCompressionType.LOSSY_JPEG_2000
        return StorageCompressionType.LOSSLESS

    def estimate_compression_ratio(self, compression_type: StorageCompressionType) -> float:
        ratios = {
            StorageCompressionType.NONE: 1.0,
            StorageCompressionType.LOSSLESS: 0.5,
            StorageCompressionType.LOSSLESS_JPEG_LS: 0.4,
            StorageCompressionType.LOSSLESS_JPEG_2000: 0.35,
            StorageCompressionType.LOSSY_JPEG: 0.15,
            StorageCompressionType.LOSSY_JPEG_2000: 0.1,
        }
        return ratios.get(compression_type, 1.0)


# ==============================================================================
# ImageSharingService
# ==============================================================================


class ImageSharingService:
    def __init__(self, db: Session, share_base_url: str = "https://gula.iq/s/"):
        self.db = db
        self.share_base_url = share_base_url

    def create_share(
        self,
        study_uid: str,
        shared_by: str,
        shared_with: str | None = None,
        share_type: str = "link",
        expires_in_hours: int | None = 48,
        metadata: dict[str, Any] | None = None,
    ) -> ImageShare:
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)
        access_code = _generate_access_code() if share_type in ("link", "qr") else None
        share = ImageShare(
            study_uid=study_uid,
            shared_by=shared_by,
            shared_with=shared_with,
            # ImageShare.share_type is Enum(SharingType); SQLAlchemy's Enum
            # column stores/validates by member name, not by value, so the
            # raw value string ("link") must be converted to the matching
            # SharingType member (SharingType("link") -> SharingType.LINK)
            # before assignment — passing the bare string raised
            # LookupError at commit time for every share ever created.
            share_type=SharingType(share_type),
            access_code=access_code,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        share_url = f"{self.share_base_url}{share.id}"
        if access_code:
            share_url += f"?code={access_code}"
        logger.info("Image share created: %s -> %s", study_uid, shared_with or "anonymous")
        return share

    def revoke_share(self, share_id: str) -> bool:
        share = self.db.query(ImageShare).filter(ImageShare.id == share_id, not ImageShare.is_revoked).first()
        if not share:
            return False
        share.is_revoked = True
        self.db.commit()
        return True

    def access_share(self, share_id: str, access_code: str | None = None) -> str | None:
        share = self.db.query(ImageShare).filter(
            ImageShare.id == share_id,
            not ImageShare.is_revoked,
        ).first()
        if not share:
            return None
        if share.expires_at and share.expires_at < datetime.now(UTC):
            return None
        if share.access_code and share.access_code != access_code:
            return None
        share.access_count = (share.access_count or 0) + 1
        self.db.commit()
        return share.study_uid

    def list_shares(self, shared_by: str | None = None, shared_with: str | None = None) -> list[ImageShare]:
        q = self.db.query(ImageShare).filter(not ImageShare.is_revoked)
        if shared_by:
            q = q.filter(ImageShare.shared_by == shared_by)
        if shared_with:
            q = q.filter(ImageShare.shared_with == shared_with)
        q = q.order_by(ImageShare.created_at.desc())
        return q.all()

    def get_share(self, share_id: str) -> ImageShare | None:
        return self.db.query(ImageShare).filter(ImageShare.id == share_id).first()


# ==============================================================================
# ArchiveService
# ==============================================================================


class ArchiveService:
    TIER_MAP = {
        ArchiveTier.HOT: ArchiveTier.WARM,
        ArchiveTier.WARM: ArchiveTier.COLD,
        ArchiveTier.COLD: ArchiveTier.DEEP_ARCHIVE,
    }

    def __init__(self, db: Session, storage_service: DICOMStorageService, compression_service: ImageCompressionService):
        self.db = db
        self.storage_service = storage_service
        self.compression_service = compression_service

    def move_to_tier(self, sop_instance_uid: str, target_tier: ArchiveTier) -> DICOMStorage | None:
        record = self.storage_service.retrieve(sop_instance_uid)
        if not record:
            return None
        record.storage_tier = target_tier
        record.compression_type = self.compression_service.get_compression_type(target_tier)
        if target_tier != ArchiveTier.HOT:
            record.is_archived = True
        self.db.commit()
        self.db.refresh(record)
        logger.info("DICOM instance %s moved to tier %s", sop_instance_uid, target_tier.value)
        return record

    def archive_old_studies(self, older_than_days: int = 365, target_tier: ArchiveTier = ArchiveTier.COLD) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        records = self.db.query(DICOMStorage).filter(
            DICOMStorage.storage_date < cutoff,
            DICOMStorage.storage_tier == ArchiveTier.HOT,
            ~DICOMStorage.is_deleted,
        ).all()
        count = 0
        for rec in records:
            self.move_to_tier(rec.sop_instance_uid, target_tier)
            count += 1
        logger.info("Archived %d studies older than %d days to %s", count, older_than_days, target_tier.value)
        return count

    def apply_retention_policy(self) -> int:
        deleted_count = 0
        records = self.db.query(DICOMStorage).filter(
            DICOMStorage.retention_days.isnot(None),
            ~DICOMStorage.is_deleted,
        ).all()
        for rec in records:
            if rec.storage_date and rec.retention_days:
                expiry = rec.storage_date + timedelta(days=rec.retention_days)
                if expiry < datetime.now(UTC):
                    rec.soft_delete()
                    deleted_count += 1
        if deleted_count:
            self.db.commit()
            logger.info("Retention policy removed %d expired records", deleted_count)
        return deleted_count


# ==============================================================================
# DICOMQueryRetrieveService
# ==============================================================================


class DICOMQueryRetrieveService:
    def __init__(
        self,
        db: Session,
        pacs_endpoint: str = "http://pacs:8042/dicom-web",
        ae_title: str = "GULA_PACS",
        timeout: float = 30.0,
    ):
        self.db = db
        self.pacs_endpoint = pacs_endpoint
        self.ae_title = ae_title
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"Accept": "application/dicom+json"},
            )
        return self._client

    async def c_find_studies(self, params: dict[str, str]) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(
                urljoin(self.pacs_endpoint, "studies"),
                params=params,
            )
            if resp.is_success:
                return resp.json() if resp.text else []
            logger.error("C-FIND studies failed: %s", resp.text)
            return []
        except Exception as exc:
            logger.error("C-FIND studies error: %s", exc)
            return []

    async def c_find_series(self, study_uid: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(
                urljoin(self.pacs_endpoint, f"studies/{study_uid}/series"),
                params=params or {},
            )
            if resp.is_success:
                return resp.json() if resp.text else []
            return []
        except Exception as exc:
            logger.error("C-FIND series error: %s", exc)
            return []

    async def c_find_instances(self, study_uid: str, series_uid: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(
                urljoin(self.pacs_endpoint, f"studies/{study_uid}/series/{series_uid}/instances"),
                params=params or {},
            )
            if resp.is_success:
                return resp.json() if resp.text else []
            return []
        except Exception as exc:
            logger.error("C-FIND instances error: %s", exc)
            return []

    async def c_move(self, study_uid: str, destination_ae: str) -> bool:
        await self._get_client()
        move_payload = {
            "Level": "STUDY",
            "Destination": destination_ae,
            "StudyInstanceUID": study_uid,
        }
        try:
            resp = await self._client.post(
                urljoin(self.pacs_endpoint, "studies"),
                json=move_payload,
                params={"action": "move"},
            )
            return resp.is_success
        except Exception as exc:
            logger.error("C-MOVE failed: %s", exc)
            return False

    async def c_get(self, study_uid: str) -> bytes | None:
        client = await self._get_client()
        try:
            resp = await client.get(
                urljoin(self.pacs_endpoint, f"studies/{study_uid}"),
                headers={"Accept": "application/dicom"},
            )
            if resp.is_success:
                return resp.content
            return None
        except Exception as exc:
            logger.error("C-GET failed: %s", exc)
            return None

    async def c_store(self, study_uid: str, dicom_data: bytes) -> bool:
        client = await self._get_client()
        try:
            resp = await client.post(
                urljoin(self.pacs_endpoint, "studies"),
                content=dicom_data,
                headers={"Content-Type": "application/dicom"},
            )
            return resp.is_success
        except Exception as exc:
            logger.error("C-STORE failed: %s", exc)
            return False

    async def c_echo(self) -> bool:
        await self._get_client()
        try:
            resp = await self._client.get(urljoin(self.pacs_endpoint, "health"))
            return resp.is_success
        except Exception as exc:
            logger.error("C-ECHO failed: %s", exc)
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
