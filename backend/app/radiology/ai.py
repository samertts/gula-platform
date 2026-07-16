from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Session

from app._compat import UTC
from app.radiology.enums import FindingCriticality
from app.radiology.models import CriticalFinding, RadiologyExam

from .base import RadiologyBaseEntity

logger = logging.getLogger("gula.radiology.ai")


# ==============================================================================
# AI Analysis Job Model
# ==============================================================================


class AIAnalysisJob(RadiologyBaseEntity):
    __tablename__ = "radiology_ai_jobs"

    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    model_id = Column(String(64), nullable=False, index=True)
    model_version = Column(String(32), nullable=True)
    status = Column(String(20), default="pending")
    requested_by = Column(String(26), nullable=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    findings = Column(JSON, default=dict)
    confidence_score = Column(Float, nullable=True)
    is_urgent = Column(bool, default=False)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    metadata = Column(JSON, default=dict)


# ==============================================================================
# ModelRegistryHook
# ==============================================================================


class ModelRegistryHook:
    MODELS: dict[str, dict[str, Any]] = {
        "chest-xray-abnormality": {
            "name": "Chest X-Ray Abnormality Detection",
            "modalities": ["XR"],
            "version": "2.1.0",
            "status": "active",
            "criticality": FindingCriticality.ACTIONABLE,
        },
        "chest-xray-critical": {
            "name": "Chest X-Ray Critical Findings",
            "modalities": ["XR"],
            "version": "2.0.0",
            "status": "active",
            "criticality": FindingCriticality.CRITICAL_RED,
        },
        "ct-brain-hemorrhage": {
            "name": "CT Brain Hemorrhage Detection",
            "modalities": ["CT"],
            "version": "1.3.0",
            "status": "active",
            "criticality": FindingCriticality.CRITICAL_RED,
        },
        "ct-pulmonary-embolism": {
            "name": "CT Pulmonary Embolism",
            "modalities": ["CT"],
            "version": "1.1.0",
            "status": "active",
            "criticality": FindingCriticality.CRITICAL,
        },
        "mri-brain-tumor": {
            "name": "MRI Brain Tumor Segmentation",
            "modalities": ["MRI"],
            "version": "1.0.0",
            "status": "beta",
            "criticality": FindingCriticality.ACTIONABLE,
        },
        "mammography-density": {
            "name": "Mammography Breast Density",
            "modalities": ["MG"],
            "version": "1.0.0",
            "status": "active",
            "criticality": FindingCriticality.NON_CRITICAL,
        },
        "chest-xray-quality": {
            "name": "Chest X-Ray Image Quality",
            "modalities": ["XR"],
            "version": "1.0.0",
            "status": "active",
            "criticality": FindingCriticality.NON_CRITICAL,
        },
        "ct-pneumothorax": {
            "name": "CT Pneumothorax Detection",
            "modalities": ["CT"],
            "version": "1.0.0",
            "status": "active",
            "criticality": FindingCriticality.CRITICAL_RED,
        },
        "us-renal-stone": {
            "name": "Ultrasound Renal Stone Detection",
            "modalities": ["US"],
            "version": "1.0.0",
            "status": "active",
            "criticality": FindingCriticality.ACTIONABLE,
        },
    }

    def register_model(self, model_id: str, model_info: dict[str, Any]) -> bool:
        if model_id in self.MODELS:
            logger.warning("Model %s already registered, use update instead", model_id)
            return False
        self.MODELS[model_id] = model_info
        logger.info("AI model registered: %s", model_id)
        return True

    def update_model(self, model_id: str, model_info: dict[str, Any]) -> bool:
        if model_id not in self.MODELS:
            logger.warning("Model %s not found, cannot update", model_id)
            return False
        self.MODELS[model_id].update(model_info)
        logger.info("AI model updated: %s", model_id)
        return True

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        return self.MODELS.get(model_id)

    def list_models(self, modality: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        results = []
        for mid, info in self.MODELS.items():
            if modality and modality not in info.get("modalities", []):
                continue
            if status and info.get("status") != status:
                continue
            results.append({"model_id": mid, **info})
        return results

    def get_models_for_modality(self, modality: str) -> list[dict[str, Any]]:
        return self.list_models(modality=modality)

    def get_active_models(self) -> list[dict[str, Any]]:
        return self.list_models(status="active")


# ==============================================================================
# TriageService
# ==============================================================================


class TriageService:
    def __init__(self, db: Session):
        self.db = db

    def triage_from_ai_findings(
        self,
        exam_id: str,
        ai_findings: dict[str, Any],
        confidence_threshold: float = 0.85,
    ) -> list[CriticalFinding]:
        critical_findings: list[CriticalFinding] = []
        findings_list = ai_findings.get("findings", [])
        for finding in findings_list:
            finding_type = finding.get("type", "")
            finding_description = finding.get("description", "")
            confidence = finding.get("confidence", 0.0)
            criticality = finding.get("criticality", FindingCriticality.NON_CRITICAL.value)

            if confidence < confidence_threshold:
                continue

            if criticality in (
                FindingCriticality.CRITICAL_RED.value,
                FindingCriticality.CRITICAL.value,
                FindingCriticality.ACTIONABLE.value,
            ):
                cf = CriticalFinding(
                    exam_id=exam_id,
                    finding_type=finding_type,
                    finding_description=finding_description,
                    status="pending",
                    metadata={
                        "source": "ai_triage",
                        "confidence": confidence,
                        "criticality": criticality,
                        "ai_model": ai_findings.get("model_id", ""),
                    },
                )
                self.db.add(cf)
                critical_findings.append(cf)
                logger.warning(
                    "AI triage flagged critical finding on exam %s: %s (confidence=%.2f)",
                    exam_id, finding_type, confidence,
                )

        if critical_findings:
            self.db.commit()
            for cf in critical_findings:
                self.db.refresh(cf)
                self._update_exam_critical_flag(exam_id)

        return critical_findings

    def _update_exam_critical_flag(self, exam_id: str) -> None:
        exam = self.db.query(RadiologyExam).filter(RadiologyExam.id == exam_id).first()
        if exam:
            exam.metadata = exam.metadata or {}
            exam.metadata["has_ai_critical_finding"] = True
            self.db.commit()

    def get_critical_exams(self, date_from: datetime | None = None, date_to: datetime | None = None) -> list[RadiologyExam]:
        q = self.db.query(RadiologyExam).filter(
            ~~RadiologyExam.is_deleted,
            RadiologyExam.metadata["has_ai_critical_finding"].astext == "true",
        )
        if date_from:
            q = q.filter(RadiologyExam.created_at >= date_from)
        if date_to:
            q = q.filter(RadiologyExam.created_at <= date_to)
        return q.all()


# ==============================================================================
# QualityDetectionService
# ==============================================================================


class QualityDetectionService:
    QUALITY_THRESHOLDS: dict[str, dict[str, float]] = {
        "XR": {"min_kvp": 40.0, "max_kvp": 150.0, "min_mas": 0.1, "max_mas": 50.0},
        "CT": {"min_kvp": 80.0, "max_kvp": 140.0, "min_mas": 10.0, "max_mas": 800.0},
        "MRI": {"min_slice_thickness": 0.5, "max_slice_thickness": 10.0},
        "MG": {"min_kvp": 22.0, "max_kvp": 35.0, "min_mas": 10.0, "max_mas": 200.0},
    }

    def assess_image_quality(self, exam_id: str) -> dict[str, Any]:
        exam = self.db.query(RadiologyExam).filter(RadiologyExam.id == exam_id).first()
        if not exam:
            return {"exam_id": exam_id, "quality": "unknown", "issues": ["Exam not found"]}

        modalities = self.db.query(RadiologyExam.modality).filter(RadiologyExam.id == exam_id).first()
        modality = modalities[0].value if modalities and hasattr(modalities[0], "value") else str(modalities[0]) if modalities else ""

        issues: list[str] = []
        score = 100.0

        if exam.images_count is not None and exam.images_count == 0:
            issues.append("No images acquired")
            score -= 50

        if exam.image_quality:
            quality_map = {
                "excellent": 0,
                "good": -10,
                "fair": -25,
                "poor": -40,
                "non_diagnostic": -60,
            }
            penalty = quality_map.get(exam.image_quality.value if hasattr(exam.image_quality, "value") else str(exam.image_quality), 0)
            score += penalty
            if penalty < -30:
                issues.append(f"Image quality rated as {exam.image_quality}")

        thresholds = self.QUALITY_THRESHOLDS.get(modality, {})
        series = self.db.query(RadiologyExam).filter(RadiologyExam.id == exam_id).first()
        if thresholds and series:
            kvp = getattr(series, "kvp", None)
            getattr(series, "mas", None)
            if kvp is not None and "min_kvp" in thresholds and kvp < thresholds["min_kvp"]:
                issues.append(f"KVP too low: {kvp}")
                score -= 15
            if kvp is not None and "max_kvp" in thresholds and kvp > thresholds["max_kvp"]:
                issues.append(f"KVP too high: {kvp}")
                score -= 10

        return {
            "exam_id": exam_id,
            "modality": modality,
            "quality_score": max(0, score),
            "issues": issues,
            "recommendation": "repeat" if score < 30 else "acceptable" if score < 60 else "good",
        }

    def recommend_rejection(self, exam_id: str) -> dict[str, Any]:
        assessment = self.assess_image_quality(exam_id)
        return {
            "exam_id": exam_id,
            "reject": assessment["quality_score"] < 40,
            "reason": "; ".join(assessment["issues"]) if assessment["issues"] else "Meets quality standards",
            "quality_score": assessment["quality_score"],
        }


# ==============================================================================
# HumanApprovalService
# ==============================================================================


class HumanApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def request_approval(self, job_id: str, ai_report: dict[str, Any]) -> dict[str, Any]:
        job = self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()
        if not job:
            return {"approved": False, "error": "Job not found"}
        return {
            "job_id": job_id,
            "status": "pending_approval",
            "ai_report": ai_report,
            "requires_human_review": True,
            "approved": False,
        }

    def approve_findings(self, job_id: str, approved_by: str, modifications: dict[str, Any] | None = None) -> dict[str, Any]:
        job = self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()
        if not job:
            return {"success": False, "error": "Job not found"}
        job.metadata = job.metadata or {}
        job.metadata["approved_by"] = approved_by
        job.metadata["approved_at"] = datetime.now(UTC).isoformat()
        job.metadata["modifications"] = modifications or {}
        job.status = "approved"
        self.db.commit()
        logger.info("AI findings approved for job %s by %s", job_id, approved_by)
        return {"success": True, "job_id": job_id, "approved_by": approved_by}

    def reject_findings(self, job_id: str, rejected_by: str, reason: str) -> dict[str, Any]:
        job = self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()
        if not job:
            return {"success": False, "error": "Job not found"}
        job.metadata = job.metadata or {}
        job.metadata["rejected_by"] = rejected_by
        job.metadata["rejection_reason"] = reason
        job.status = "rejected"
        self.db.commit()
        logger.info("AI findings rejected for job %s by %s: %s", job_id, rejected_by, reason)
        return {"success": True, "job_id": job_id, "rejected_by": rejected_by, "reason": reason}

    def submit_job(
        self,
        exam_id: str,
        model_id: str,
        requested_by: str | None = None,
        is_urgent: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> AIAnalysisJob:
        job = AIAnalysisJob(
            exam_id=exam_id,
            model_id=model_id,
            status="pending",
            requested_by=requested_by,
            is_urgent=is_urgent,
            metadata=metadata or {},
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info("AI analysis job submitted: %s for exam %s", model_id, exam_id)
        return job

    def complete_job(
        self,
        job_id: str,
        findings: dict[str, Any],
        confidence_score: float,
        processing_time_ms: int | None = None,
    ) -> AIAnalysisJob | None:
        job = self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()
        if not job:
            return None
        job.status = "completed"
        job.findings = findings
        job.confidence_score = confidence_score
        job.completed_at = datetime.now(UTC)
        job.processing_time_ms = processing_time_ms
        self.db.commit()
        self.db.refresh(job)
        return job

    def fail_job(self, job_id: str, error_message: str) -> AIAnalysisJob | None:
        job = self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()
        if not job:
            return None
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> AIAnalysisJob | None:
        return self.db.query(AIAnalysisJob).filter(AIAnalysisJob.id == job_id).first()

    def list_jobs(
        self,
        exam_id: str | None = None,
        model_id: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AIAnalysisJob]:
        q = self.db.query(AIAnalysisJob).filter(~~AIAnalysisJob.is_deleted)
        if exam_id:
            q = q.filter(AIAnalysisJob.exam_id == exam_id)
        if model_id:
            q = q.filter(AIAnalysisJob.model_id == model_id)
        if status:
            q = q.filter(AIAnalysisJob.status == status)
        q = q.order_by(AIAnalysisJob.requested_at.desc())
        return q.offset(skip).limit(limit).all()
