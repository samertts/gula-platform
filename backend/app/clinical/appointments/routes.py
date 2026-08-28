from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.clinical.appointments.authorization import AppointmentAuthorizationError
from app.clinical.appointments.schemas import (
    AppointmentConfirmRequest,
    AppointmentListResponse,
    AppointmentRequest,
    AppointmentResponse,
    AppointmentSlotCreateRequest,
    SlotListResponse,
    SlotResponse,
)
from app.clinical.appointments.service import (
    AppointmentError,
    CoreAppointmentService,
    PreconditionRequiredError,
    ValidationError,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService
from app.security.rate_limit import rate_limit_user

logger = logging.getLogger("gula.clinical.appointments.api")
router = APIRouter(prefix="/api/v1/appointments", tags=["Core Appointments"])


_ERROR_MESSAGES: dict[str, tuple[int, str, str]] = {
    "VALIDATION_ERROR": (400, "The appointment request is invalid.", "طلب الموعد غير صالح."),
    "IDEMPOTENCY_CONFLICT": (409, "The request key conflicts with an earlier request.", "مفتاح الطلب يتعارض مع طلب سابق."),
    "VERSION_CONFLICT": (409, "The appointment changed before this operation.", "تغير الموعد قبل تنفيذ العملية."),
    "PRECONDITION_REQUIRED": (428, "If-Match is required for this state change.", "يجب إرسال If-Match لتغيير حالة الموعد."),
    "SLOT_UNAVAILABLE": (409, "The requested slot is not available.", "الفترة المطلوبة غير متاحة."),
    "CONFLICT": (409, "The appointment operation conflicts with current state.", "تتعارض عملية الموعد مع حالته الحالية."),
    "NOT_FOUND": (404, "The requested appointment resource was not found.", "لم يتم العثور على مورد الموعد المطلوب."),
    "UNAUTHORIZED": (401, "Authentication is required.", "المصادقة مطلوبة."),
    "FORBIDDEN": (403, "This appointment operation is not permitted.", "عملية الموعد هذه غير مسموحة."),
    "INTERNAL_ERROR": (500, "The appointment operation could not be completed.", "تعذر إكمال عملية الموعد."),
    "ENCOUNTER_NOT_FOUND": (404, "The encounter was not found.", "لم يتم العثور على الزيارة السريرية."),
    "APPOINTMENT_NOT_ELIGIBLE": (409, "The appointment is not eligible for this operation.", "الموعد غير مؤهل لهذه العملية."),
    "ALREADY_CHECKED_IN": (409, "The appointment is already checked in.", "تم تسجيل حضور الموعد مسبقاً."),
    "ENCOUNTER_STATE_CONFLICT": (409, "The encounter state does not allow this operation.", "حالة الزيارة لا تسمح بهذه العملية."),
    "CLINICAL_NOTE_NOT_FOUND": (404, "The clinical note was not found.", "لم يتم العثور على الملاحظة السريرية."),
    "CLINICAL_NOTE_IMMUTABLE": (409, "The clinical note requires an explicit amendment.", "الملاحظة السريرية تتطلب تعديلاً صريحاً."),
    "LAB_ORDER_NOT_FOUND": (404, "The laboratory order was not found.", "لم يتم العثور على طلب المختبر."),
    "LAB_ORDER_STATE_CONFLICT": (409, "The laboratory order state does not allow this operation.", "حالة طلب المختبر لا تسمح بهذه العملية."),
    "SPECIMEN_NOT_FOUND": (404, "The specimen was not found.", "لم يتم العثور على العينة."),
    "SPECIMEN_STATE_CONFLICT": (409, "The specimen state does not allow this operation.", "حالة العينة لا تسمح بهذه العملية."),
    "SPECIMEN_ALREADY_EXISTS": (409, "A specimen already exists for this order item.", "توجد عينة لهذا العنصر مسبقاً."),
    "RESULT_NOT_FOUND": (404, "The laboratory result was not found.", "لم يتم العثور على نتيجة المختبر."),
    "RESULT_STATE_CONFLICT": (409, "The result state does not allow this operation.", "حالة النتيجة لا تسمح بهذه العملية."),
    "CRITICAL_ACK_REQUIRED": (409, "Critical-result acknowledgement is required.", "يجب تأكيد النتيجة الحرجة أولاً."),
    "CRITICAL_RESULT_NOT_FOUND": (404, "No critical-result event was found.", "لم يتم العثور على حدث نتيجة حرجة."),
    "SEPARATION_OF_DUTIES_REQUIRED": (403, "Separate authorized actors are required.", "يلزم مستخدمان مخولان منفصلان."),
    "ACCESS_GRANT_NOT_FOUND": (404, "The access grant was not found.", "لم يتم العثور على منح الوصول."),
    "ACCESS_NOT_GRANTED": (403, "Access to this clinical resource is not granted.", "لا توجد صلاحية للوصول إلى هذا المورد السريري."),
    "ACCESS_EXPIRED": (403, "Access to this clinical resource has expired.", "انتهت صلاحية الوصول إلى هذا المورد السريري."),
    "ACCESS_REVOKED": (403, "Access to this clinical resource was revoked.", "تم سحب صلاحية الوصول إلى هذا المورد السريري."),
    "DUPLICATE_ACCESS_GRANT": (409, "An active access grant already exists.", "توجد صلاحية وصول فعالة مسبقاً."),
    "ACCESS_STATE_CONFLICT": (409, "The access grant state does not allow this operation.", "حالة منحة الوصول لا تسمح بهذه العملية."),
    "PHARMACY_RESOURCE_NOT_FOUND": (404, "The pharmacy resource was not found.", "لم يتم العثور على مورد الصيدلة."),
    "MEDICATION_NOT_FOUND": (404, "The medication was not found.", "لم يتم العثور على الدواء."),
    "PRESCRIPTION_NOT_FOUND": (404, "The prescription was not found.", "لم يتم العثور على الوصفة."),
    "DISPENSE_NOT_FOUND": (404, "The dispense record was not found.", "لم يتم العثور على سجل الصرف."),
    "MEDICATION_CODE_EXISTS": (409, "The medication code already exists.", "رمز الدواء موجود مسبقاً."),
    "PRESCRIPTION_NOT_SIGNABLE": (409, "The prescription cannot be signed in its current state.", "لا يمكن توقيع الوصفة في حالتها الحالية."),
    "PRESCRIPTION_NOT_AMENDABLE": (409, "The prescription cannot be amended in its current state.", "لا يمكن تعديل الوصفة في حالتها الحالية."),
    "PRESCRIPTION_NOT_DISPENSABLE": (409, "The prescription is not eligible for dispensing.", "الوصفة غير مؤهلة للصرف."),
    "SUBSTITUTION_NOT_ALLOWED": (422, "Automatic substitution is not permitted.", "الاستبدال التلقائي غير مسموح."),
    "DUPLICATE_MEDICATION": (422, "A medication may appear only once in a prescription.", "لا يجوز تكرار الدواء داخل الوصفة."),
    "CONTROLLED_MEDICATION_POLICY_REQUIRED": (422, "Controlled medication requires an explicit policy review.", "الدواء المقيد يحتاج مراجعة سياسة صريحة."),
    "INVENTORY_CONFLICT": (409, "The inventory operation conflicts with current stock.", "تتعارض العملية مع المخزون الحالي."),
    "BATCH_NOT_FOUND": (404, "The medication batch was not found.", "لم يتم العثور على دفعة الدواء."),
    "EXPIRED_MEDICATION": (409, "Expired or quarantined medication cannot be used.", "لا يمكن استخدام دواء منتهٍ أو محجور."),
    "MEDICATION_BATCH_MISMATCH": (409, "The batch does not match the prescribed medication.", "الدفعة لا تطابق الدواء الموصوف."),
    "DISPENSE_NOT_PREPARED": (409, "The dispense is not prepared for completion.", "سجل الصرف غير محضر للإتمام."),
    "OVER_DISPENSE": (409, "The requested quantity exceeds the remaining prescription.", "الكمية المطلوبة تتجاوز المتبقي من الوصفة."),
    "IMAGING_RESOURCE_NOT_FOUND": (404, "The imaging resource was not found.", "لم يتم العثور على مورد التصوير."),
    "STUDY_NOT_FOUND": (404, "The imaging study was not found.", "لم يتم العثور على دراسة التصوير."),
    "REPORT_NOT_FOUND": (404, "The imaging report was not found.", "لم يتم العثور على تقرير التصوير."),
    "ORDER_NOT_FOUND": (404, "The imaging order was not found.", "لم يتم العثور على طلب التصوير."),
    "ORDER_STATE_CONFLICT": (409, "The imaging order state does not allow this operation.", "حالة طلب التصوير لا تسمح بهذه العملية."),
    "STUDY_STATE_CONFLICT": (409, "The imaging study state does not allow this operation.", "حالة دراسة التصوير لا تسمح بهذه العملية."),
    "ORDER_NOT_INGESTIBLE": (409, "The order is not eligible for imaging ingestion.", "الطلب غير مؤهل لاستلام بيانات التصوير."),
    "STUDY_NOT_COMPLETE": (409, "The imaging study is not complete.", "دراسة التصوير غير مكتملة."),
    "STUDY_QUARANTINED": (409, "The imaging study is quarantined.", "دراسة التصوير محجورة."),
    "DICOM_DUPLICATE": (409, "The DICOM object was already ingested.", "تم استلام كائن DICOM مسبقاً."),
    "DICOM_INVALID": (422, "The DICOM metadata is invalid.", "بيانات DICOM غير صالحة."),
    "REPORT_ALREADY_FINAL": (409, "The final report is immutable; create an amendment.", "التقرير النهائي غير قابل للتعديل؛ أنشئ تعديلاً."),
    "CRITICAL_FINDING_NOT_FOUND": (404, "The critical imaging finding was not found.", "لم يتم العثور على النتيجة التصويرية الحرجة."),
    "CRITICAL_ACK_STATE_CONFLICT": (409, "The critical finding is not awaiting acknowledgement.", "النتيجة الحرجة لا تنتظر التأكيد."),
    "CLINICAL_RECORD_ERROR": (400, "The clinical-record request is invalid.", "طلب السجل السريري غير صالح."),
    "RECORD_NOT_FOUND": (404, "The clinical record was not found.", "لم يتم العثور على السجل السريري."),
    "INVALID_RECORD_SECTION": (422, "The clinical-record section is invalid.", "قسم السجل السريري غير صالح."),
    "INVALID_RECORD_CURSOR": (422, "The clinical-record cursor is invalid.", "مؤشر السجل السريري غير صالح."),
    "HOSPITAL_RESOURCE_NOT_FOUND": (404, "The hospital resource was not found.", "لم يتم العثور على مورد المستشفى."),
    "HOSPITAL_STATE_CONFLICT": (409, "The hospital workflow conflicts with its current state.", "تتعارض عملية المستشفى مع الحالة الحالية."),
    "WARD_NOT_FOUND": (404, "The hospital ward was not found.", "لم يتم العثور على جناح المستشفى."),
    "ROOM_NOT_FOUND": (404, "The hospital room was not found.", "لم يتم العثور على غرفة المستشفى."),
    "BED_NOT_FOUND": (404, "The hospital bed was not found.", "لم يتم العثور على سرير المستشفى."),
    "ENCOUNTER_NOT_FOUND": (404, "The clinical encounter was not found.", "لم يتم العثور على الزيارة السريرية."),
    "ADMISSION_NOT_FOUND": (404, "The hospital admission was not found.", "لم يتم العثور على قبول المستشفى."),
    "TASK_NOT_FOUND": (404, "The nursing task was not found.", "لم يتم العثور على مهمة التمريض."),
    "EMAR_NOT_FOUND": (404, "The medication administration was not found.", "لم يتم العثور على سجل إعطاء الدواء."),
    "TRANSFER_NOT_FOUND": (404, "The patient transfer was not found.", "لم يتم العثور على نقل المريض."),
    "DISCHARGE_NOT_FOUND": (404, "The discharge workflow was not found.", "لم يتم العثور على مسار الخروج."),
    "DISCHARGE_SUMMARY_NOT_FOUND": (404, "The discharge summary was not found.", "لم يتم العثور على ملخص الخروج."),
    "WARD_EXISTS": (409, "A ward with this code already exists in the facility.", "يوجد جناح بهذا الرمز في المنشأة."),
    "ROOM_EXISTS": (409, "A room with this code already exists in the ward.", "توجد غرفة بهذا الرمز في الجناح."),
    "BED_EXISTS": (409, "A bed with this code already exists in the room.", "يوجد سرير بهذا الرمز في الغرفة."),
    "ROOM_CAPACITY_REACHED": (409, "The room capacity has been reached.", "تم بلوغ سعة الغرفة."),
    "WARD_SCOPE_MISMATCH": (409, "The bed is outside the admission ward.", "السرير خارج جناح القبول."),
    "ADMISSION_REQUEST_EXISTS": (409, "This admission request already exists.", "طلب القبول موجود مسبقاً."),
    "CARE_TEAM_ACCOUNT_NOT_FOUND": (404, "The care-team account was not found.", "لم يتم العثور على حساب عضو فريق الرعاية."),
    "CARE_TEAM_MEMBER_EXISTS": (409, "This account is already on the active care team.", "الحساب عضو فعّال بالفعل في فريق الرعاية."),
    "CARE_TEAM_ROLE_INVALID": (422, "The care-team role is not allowed.", "دور عضو فريق الرعاية غير مسموح."),
    "CARE_TEAM_TIME_INVALID": (422, "The care-team time window is invalid.", "الفترة الزمنية لفريق الرعاية غير صالحة."),
    "DISCHARGE_EXISTS": (409, "This discharge request already exists.", "طلب الخروج موجود مسبقاً."),
    "DISCHARGE_SUMMARY_EXISTS": (409, "A draft discharge summary already exists.", "يوجد ملخص خروج مسودة بالفعل."),
    "DISCHARGE_SUMMARY_IMMUTABLE": (409, "A signed discharge summary is immutable.", "ملخص الخروج الموقع غير قابل للتعديل."),
    "DISCHARGE_NOT_READY": (409, "Discharge prerequisites are incomplete.", "متطلبات الخروج غير مكتملة."),
    "DISCHARGE_NOT_COMPLETABLE": (409, "The discharge is not completable in its current state.", "لا يمكن إتمام الخروج في حالته الحالية."),
    "PRESCRIPTION_NOT_ADMINISTRABLE": (409, "The prescription is not eligible for administration.", "الوصفة غير مؤهلة لإعطاء الدواء."),
    "PRESCRIPTION_PATIENT_MISMATCH": (409, "The prescription does not belong to the admitted patient.", "الوصفة لا تخص المريض المقبول."),
    "MEDICATION_MISMATCH": (409, "The medication identity could not be verified.", "تعذر التحقق من هوية الدواء."),
    "EMAR_REASON_REQUIRED": (422, "A reason is required for this medication outcome.", "يلزم سبب لهذه النتيجة الدوائية."),
    "DUPLICATE_ADMINISTRATION": (409, "This medication administration key already exists.", "مفتاح إعطاء الدواء موجود مسبقاً."),
    "TRANSFER_EXISTS": (409, "This transfer request already exists.", "طلب النقل موجود مسبقاً."),
    "TRANSFER_SAME_WARD": (409, "The transfer must target a different ward.", "يجب أن يستهدف النقل جناحاً مختلفاً."),
    "EMERGENCY_RESOURCE_NOT_FOUND": (404, "The emergency resource was not found.", "لم يتم العثور على مورد الطوارئ."),
    "EMERGENCY_STATE_CONFLICT": (409, "The emergency workflow conflicts with its current state.", "تتعارض عملية الطوارئ مع الحالة الحالية."),
    "TEMPORARY_SUBJECT_NOT_FOUND": (404, "The temporary emergency subject was not found.", "لم يتم العثور على هوية الطوارئ المؤقتة."),
    "INCIDENT_NOT_FOUND": (404, "The emergency incident was not found.", "لم يتم العثور على حادثة الطوارئ."),
    "DISPATCH_NOT_FOUND": (404, "The EMS dispatch was not found.", "لم يتم العثور على إرسال الإسعاف."),
    "PREALERT_NOT_FOUND": (404, "The hospital pre-alert was not found.", "لم يتم العثور على التنبيه المسبق للمستشفى."),
    "HANDOVER_NOT_FOUND": (404, "The emergency handover was not found.", "لم يتم العثور على تسليم الطوارئ."),
    "EPCR_NOT_FOUND": (404, "The emergency care report was not found.", "لم يتم العثور على تقرير الرعاية الإسعافية."),
    "SUBJECT_REFERENCE_INVALID": (422, "Exactly one known patient or temporary subject is required.", "يجب تحديد مريض معروف أو هوية مؤقتة واحدة فقط."),
    "TEMPORARY_SUBJECT_NOT_ACTIVE": (409, "The temporary emergency subject is not active.", "هوية الطوارئ المؤقتة غير فعالة."),
    "INCIDENT_EXISTS": (409, "An emergency incident with this reference already exists.", "توجد حادثة طوارئ بهذا المرجع مسبقاً."),
    "TRIAGE_EXISTS": (409, "A triage assessment with this reference already exists.", "يوجد تقييم فرز بهذا المرجع مسبقاً."),
    "DISPATCH_EXISTS": (409, "A dispatch request with this reference already exists.", "يوجد طلب إرسال بهذا المرجع مسبقاً."),
    "TREATMENT_EXISTS": (409, "A treatment request with this reference already exists.", "يوجد طلب علاج بهذا المرجع مسبقاً."),
    "PREALERT_EXISTS": (409, "A pre-alert request with this reference already exists.", "يوجد طلب تنبيه مسبق بهذا المرجع مسبقاً."),
    "HANDOVER_EXISTS": (409, "A handover request with this reference already exists.", "يوجد طلب تسليم بهذا المرجع مسبقاً."),
    "EPCR_EXISTS": (409, "An emergency care report with this reference already exists.", "يوجد تقرير رعاية إسعافية بهذا المرجع مسبقاً."),
    "PREALERT_NOT_PENDING": (409, "Only a pending pre-alert can be acknowledged.", "لا يمكن تأكيد إلا التنبيه المسبق المعلّق."),
    "HANDOVER_NOT_PENDING": (409, "Only a submitted handover can be acknowledged.", "لا يمكن تأكيد إلا التسليم المرسل."),
    "DEDICATED_WORKFLOW_REQUIRED": (409, "This emergency transition must use its dedicated workflow.", "يجب استخدام مسار الطوارئ المخصص لهذا الانتقال."),
    "EPCR_IMMUTABLE": (409, "A signed emergency care report is immutable; create an amendment.", "تقرير الرعاية الموقع غير قابل للتعديل؛ أنشئ تعديلاً."),
    "EPCR_SIGNATURE_REQUIRED": (422, "Signature evidence is required before signing the emergency care report.", "يلزم دليل التوقيع قبل توقيع تقرير الرعاية الإسعافية."),
    "RECONCILIATION_ALREADY_FINAL": (409, "This temporary identity requires an explicit correction workflow.", "هذه الهوية المؤقتة تحتاج مسار تصحيح صريحاً."),
    "RECONCILIATION_PERSON_REQUIRED": (422, "A person reference is required for a matched resolution.", "يلزم مرجع الشخص عند اعتماد المطابقة."),
    "RECONCILIATION_PERSON_INVALID": (422, "A person reference is only allowed for a matched resolution.", "لا يسمح بمرجع الشخص إلا عند اعتماد المطابقة."),
    "RECONCILIATION_PERSON_NOT_FOUND": (404, "The reconciliation person was not found.", "لم يتم العثور على الشخص المطلوب للمطابقة."),
    "HANDOVER_AMENDMENT_INVALID": (409, "The handover cannot be amended in its current state.", "لا يمكن تعديل التسليم في حالته الحالية."),
    "EPCR_AMENDMENT_REQUIRES_SIGNED": (409, "Only a signed ePCR can be amended.", "لا يمكن تعديل إلا تقرير رعاية إسعافية موقع."),
    "EPCR_AMENDMENT_PENDING": (409, "An ePCR amendment is already pending signature.", "يوجد تعديل لتقرير الرعاية بانتظار التوقيع."),
    "HEALTH_IDENTITY_ERROR": (409, "The health-identity workflow conflicts with its current state.", "تتعارض عملية الهوية الصحية مع الحالة الحالية."),
    "HEALTH_IDENTITY_RESOURCE_NOT_FOUND": (404, "The health-identity resource was not found.", "لم يتم العثور على مورد الهوية الصحية."),
    "VERIFICATION_PROVIDER_UNAVAILABLE": (503, "The verification provider is not connected; no verification was asserted.", "مزود التحقق غير متصل؛ لم يتم إثبات التحقق."),
    "VERIFICATION_PROOF_REJECTED": (422, "The verification proof was rejected.", "تم رفض دليل التحقق."),
    "VERIFICATION_REQUIRED": (422, "Verified identity evidence is required.", "يلزم دليل هوية متحقق منه."),
    "CONSENT_EXPIRY_INVALID": (422, "Consent expiry is outside the allowed bound.", "مدة الموافقة خارج الحد المسموح."),
    "CONSENT_SCOPE_INVALID": (422, "Consent scope must be explicit and non-public.", "يجب أن يكون نطاق الموافقة صريحاً وغير عام."),
    "DEVICE_OWNERSHIP_CONFLICT": (403, "The device is bound to another identity.", "الجهاز مرتبط بهوية أخرى."),
    "SESSION_INVALID": (403, "An active account session is required.", "يلزم وجود جلسة حساب فعالة."),
    "RECOVERY_PROOF_REJECTED": (422, "The recovery proof was rejected.", "تم رفض دليل الاسترداد."),
    "RECOVERY_EXPIRED": (409, "The recovery operation has expired.", "انتهت عملية استرداد الحساب."),
    "VERIFICATION_NOT_PENDING": (409, "The verification operation is no longer pending.", "عملية التحقق لم تعد معلقة."),
    "IDENTITY_PERSON_UNRESOLVED": (403, "The identity is not linked to an active person.", "الهوية غير مرتبطة بشخص فعال."),
    "CONSENT_NOT_ACTIVE": (409, "The consent is not active.", "الموافقة غير فعالة."),
    "CONSENT_SELF_GRANT": (422, "Self-consent is implicit and cannot be created as a sharing grant.", "الموافقة الذاتية ضمنية ولا تنشأ كمنحة مشاركة."),
    "ONE_PERSON_HEALTH_ID_CONFLICT": (409, "Multiple Health IDs exist for one person; manual review is required.", "توجد معرفات صحية متعددة لشخص واحد؛ تلزم مراجعة بشرية."),
    "RECOVERY_OPERATION_INVALID": (409, "The recovery operation is invalid.", "عملية الاسترداد غير صالحة."),
    "RECOVERY_NOT_PENDING": (409, "The recovery operation is no longer pending.", "عملية الاسترداد لم تعد معلقة."),
}


def _correlation_id(request: Request) -> str:
    candidate = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    if candidate and len(candidate) <= 120:
        return candidate
    return str(uuid.uuid4())


def _actor_snapshot(actor: NiamActor) -> tuple[str, str, str]:
    return actor.account.id, actor.account.identity_id, actor.session.uuid


def _require_idempotency_key(value: str | None) -> str:
    if not value or not value.strip() or len(value.strip()) > 128:
        raise ValidationError("Idempotency-Key is required and must be at most 128 characters.")
    return value.strip()


def _require_if_match(value: str | None) -> int:
    if value is None:
        raise PreconditionRequiredError("If-Match is required for this state change.")
    try:
        return int(value.strip().strip('"'))
    except (AttributeError, ValueError) as exc:
        raise ValidationError("If-Match must contain an integer version.") from exc


def _raise_safe(code: str, correlation_id: str, *, fallback_status: int = 500) -> None:
    default = (fallback_status, "The clinical operation was rejected.", "تم رفض العملية السريرية.")
    http_status, message, message_ar = _ERROR_MESSAGES.get(code, default)
    raise AppointmentError(
        message,
        status_code=http_status,
        code=code,
        details={"correlation_id": correlation_id, "message_ar": message_ar},
    )


def _record_denial(
    db: Session,
    actor: NiamActor,
    *,
    operation: str,
    target_type: str,
    target_id: str | None,
    reason: str,
    correlation_id: str,
    request: Request,
    organization_id: str | None = None,
    facility_id: str | None = None,
    workspace_id: str | None = None,
    actor_snapshot: tuple[str, str, str] | None = None,
) -> None:
    actor_id, actor_identity_id, session_id = actor_snapshot or _actor_snapshot(actor)
    db.rollback()
    try:
        SyncCanonicalAuditService(db).record(
            AuditEventInput(
                event_type="APPOINTMENT_AUTHORIZATION_DENIED",
                category="clinical_appointment",
                action=operation,
                actor_id=actor_id,
                actor_identity_id=actor_identity_id,
                actor_type="account",
                organization_id=organization_id,
                facility_id=facility_id,
                workspace_id=workspace_id,
                target_type=target_type,
                target_id=target_id,
                decision="deny",
                reason_code=reason,
                request_id=getattr(request.state, "request_id", None),
                correlation_id=correlation_id,
                session_id=session_id,
                source="api",
                data_classification="INTERNAL",
                context={"operation": operation},
                outcome="denied",
            ),
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not persist appointment authorization denial")
        raise


def _handle_error(
    exc: Exception,
    *,
    db: Session,
    actor: NiamActor,
    request: Request,
    operation: str,
    target_type: str,
    target_id: str | None = None,
    organization_id: str | None = None,
    facility_id: str | None = None,
    workspace_id: str | None = None,
    actor_snapshot: tuple[str, str, str] | None = None,
) -> None:
    correlation_id = _correlation_id(request)
    actor_id, actor_identity_id, session_id = actor_snapshot or _actor_snapshot(actor)
    db.rollback()
    if isinstance(exc, AppointmentAuthorizationError):
        _record_denial(
            db,
            actor,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            reason=exc.reason,
            correlation_id=correlation_id,
            request=request,
            organization_id=exc.organization_id or organization_id,
            facility_id=exc.facility_id or facility_id,
            workspace_id=exc.workspace_id or workspace_id,
            actor_snapshot=(actor_id, actor_identity_id, session_id),
        )
        _raise_safe("FORBIDDEN", correlation_id)
    if isinstance(exc, AppointmentError):
        try:
            SyncCanonicalAuditService(db).record(
                AuditEventInput(
                    event_type="APPOINTMENT_OPERATION_REJECTED",
                    category="clinical_appointment",
                    action=operation,
                    actor_id=actor_id,
                    actor_identity_id=actor_identity_id,
                    actor_type="account",
                    organization_id=organization_id,
                    facility_id=facility_id,
                    workspace_id=workspace_id,
                    target_type=target_type,
                    target_id=target_id,
                    decision="deny",
                    reason_code=exc.code,
                    request_id=getattr(request.state, "request_id", None),
                    correlation_id=correlation_id,
                    session_id=session_id,
                    source="api",
                    data_classification="INTERNAL",
                    context={"operation": operation},
                    outcome="rejected",
                ),
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Could not persist appointment rejection")
            raise
        _raise_safe(exc.code, correlation_id, fallback_status=getattr(exc, "status_code", 500))
    logger.exception("Unexpected appointment operation failure; correlation_id=%s", correlation_id)
    _raise_safe("INTERNAL_ERROR", correlation_id)


def _actor_rate_limit(request: Request, actor: NiamActor) -> None:
    rate_limit_user(request, actor.account.id, max_per_minute=30)


@router.post("/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(
    body: AppointmentSlotCreateRequest,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    key = _require_idempotency_key(idempotency_key)
    correlation_id = _correlation_id(request)
    try:
        result = CoreAppointmentService(db).create_slot(
            actor,
            workspace_id=body.workspace_id,
            provider_account_id=body.provider_account_id,
            service_code=body.service_code,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            idempotency_key=key,
            correlation_id=correlation_id,
            request_id=getattr(request.state, "request_id", None),
        )
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.slot.create", target_type="appointment_slot", workspace_id=body.workspace_id)


@router.get("/slots", response_model=SlotListResponse)
def list_slots(
    request: Request,
    workspace_id: str = Query(min_length=1, max_length=26),
    starts_at: datetime | None = Query(default=None),
    ends_at: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        return CoreAppointmentService(db).list_slots(
            actor,
            workspace_id=workspace_id,
            starts_at=starts_at,
            ends_at=ends_at,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.slot.list", target_type="appointment_slot", workspace_id=workspace_id)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def request_appointment(
    body: AppointmentRequest,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    key = _require_idempotency_key(idempotency_key)
    correlation_id = _correlation_id(request)
    try:
        result = CoreAppointmentService(db).request_appointment(
            actor,
            workspace_id=body.workspace_id,
            patient_person_id=body.patient_person_id,
            slot_id=body.slot_id,
            purpose=body.purpose,
            idempotency_key=key,
            correlation_id=correlation_id,
            request_id=getattr(request.state, "request_id", None),
        )
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.request", target_type="appointment", workspace_id=body.workspace_id)


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(
    appointment_id: str,
    body: AppointmentConfirmRequest,
    request: Request,
    workspace_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    key = _require_idempotency_key(idempotency_key)
    expected_version = _require_if_match(if_match)
    correlation_id = _correlation_id(request)
    try:
        result = CoreAppointmentService(db).confirm_appointment(
            actor,
            appointment_id=appointment_id,
            workspace_id=workspace_id,
            expected_version=expected_version,
            reason=body.reason,
            idempotency_key=key,
            correlation_id=correlation_id,
            request_id=getattr(request.state, "request_id", None),
        )
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.confirm", target_type="appointment", target_id=appointment_id, workspace_id=workspace_id)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: str,
    request: Request,
    workspace_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        return CoreAppointmentService(db).get_appointment(
            actor,
            appointment_id=appointment_id,
            workspace_id=workspace_id,
            correlation_id=_correlation_id(request),
        )
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.read", target_type="appointment", target_id=appointment_id, workspace_id=workspace_id)


@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    request: Request,
    workspace_id: str = Query(min_length=1, max_length=26),
    state: str | None = Query(default=None, min_length=1, max_length=24),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        return CoreAppointmentService(db).list_appointments(
            actor,
            workspace_id=workspace_id,
            state=state,
            limit=limit,
            offset=offset,
            correlation_id=_correlation_id(request),
        )
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="appointment.list", target_type="appointment", workspace_id=workspace_id)
