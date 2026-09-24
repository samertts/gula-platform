from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.services.audit_service import log_action

logger = logging.getLogger("gula.nursing.coordination")


class CareCoordinatorService:

    @staticmethod
    def send_physician_message(
        db: Session, lab_id: int, user_id: int,
        physician_id: str, patient_id: int, subject: str, body: str,
        priority: str = "normal",
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        msg = {
            "lab_id": lab_id,
            "from_user_id": user_id,
            "to_user_id": physician_id,
            "patient_id": patient_id,
            "subject": subject,
            "body": body,
            "priority": priority,
            "status": "sent",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.physician_message", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=msg)
        return msg

    @staticmethod
    def request_lab_collection(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, tests: list[dict[str, Any]],
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        req = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "requested_by": user_id,
            "tests": tests,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.lab_request", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=req)
        return {
            "detail": "Lab collection requested",
            "detail_ar": "تم طلب التحاليل المخبرية",
            "request": req,
        }

    @staticmethod
    def coordinate_radiology(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, exam_type: str, urgency: str = "routine",
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        order = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "exam_type": exam_type,
            "urgency": urgency,
            "requested_by": user_id,
            "status": "ordered",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.radiology", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=order)
        return {
            "detail": "Radiology order created",
            "detail_ar": "تم إنشاء طلب الأشعة",
            "order": order,
        }

    @staticmethod
    def coordinate_pharmacy(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, medication: str, dose: str, route: str,
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        req = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "medication": medication,
            "dose": dose,
            "route": route,
            "requested_by": user_id,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.pharmacy", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=req)
        return {
            "detail": "Pharmacy request created",
            "detail_ar": "تم إنشاء طلب الصيدلية",
            "request": req,
        }

    @staticmethod
    def manage_referral(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, to_specialty: str, reason: str,
        urgency: str = "routine",
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        referral = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "from_user_id": user_id,
            "to_specialty": to_specialty,
            "reason": reason,
            "urgency": urgency,
            "status": "created",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.referral", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=referral)
        return {
            "detail": "Referral created",
            "detail_ar": "تم إنشاء التحويل",
            "referral": referral,
        }

    @staticmethod
    def plan_discharge(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, expected_date: date,
        discharge_needs: dict[str, Any] | None = None,
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        plan = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "expected_date": expected_date.isoformat() if isinstance(expected_date, date) else expected_date,
            "discharge_needs": discharge_needs or {},
            "planned_by": user_id,
            "status": "planned",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.discharge_plan", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=plan)
        return {
            "detail": "Discharge plan created",
            "detail_ar": "تم إنشاء خطة الخروج",
            "plan": plan,
        }

    @staticmethod
    def family_communication(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, family_contact: str, message: str,
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        log_entry = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "family_contact": family_contact,
            "message": message,
            "communicated_by": user_id,
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.family_communication", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=log_entry)
        return {
            "detail": "Family communication logged",
            "detail_ar": "تم تسجيل التواصل مع العائلة",
            "log": log_entry,
        }

    @staticmethod
    def home_care_handover(
        db: Session, lab_id: int, user_id: int,
        patient_id: int, home_care_provider: str,
        summary: str,
        *,
        actor_role: str,
    ) -> dict[str, Any]:
        handover = {
            "lab_id": lab_id,
            "patient_id": patient_id,
            "home_care_provider": home_care_provider,
            "summary": summary,
            "prepared_by": user_id,
            "status": "handed_over",
            "created_at": datetime.now(UTC).isoformat(),
        }
        log_action(db, "nursing.coordination.home_care_handover", "coordination", None, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=handover)
        return {
            "detail": "Home care handover document created",
            "detail_ar": "تم إنشاء مستند تسليم الرعاية المنزلية",
            "handover": handover,
        }
