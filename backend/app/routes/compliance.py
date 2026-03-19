"""
Government Compliance Endpoints - GULA Platform
نقاط التوافق الحكومي - منصة غولا

Designed for Iraqi Ministry of Health and National Data Center (NIC) testing.
مصمم لاختبار وزارة الصحة العراقية ومركز البيانات الوطني.

Implements:
- System information for government audit
- Data classification labels
- Compliance status reporting
- HL7 FHIR-compatible patient resource (basic)
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.audit_log import AuditLog
from ..security.dependencies import get_current_user, get_current_lab
from ..config import APP_VERSION, APP_NAME

logger = logging.getLogger("gula.compliance")

router = APIRouter(prefix="/compliance", tags=["government compliance"])


@router.get("/info", summary="System information for government audit")
def system_info():
    """
    Returns comprehensive system information for government compliance verification.
    المعلومات الكاملة للنظام للتحقق من الامتثال الحكومي.

    For use by:
    - Ministry of Health IT inspectors
    - National Data Center (NIC) testers
    - Security auditors
    """
    return {
        "platform": {
            "name": APP_NAME,
            "name_ar": "منصة غولا الصحية للمختبرات",
            "version": APP_VERSION,
            "type": "Medical Laboratory Information System (LIS)",
            "type_ar": "نظام معلومات المختبرات الطبية",
        },
        "standards_compliance": {
            "hl7_fhir": "Partial - Patient and Observation resources",
            "iso_27001": "Security controls implemented",
            "owasp_api_security": "OWASP API Security Top 10 addressed",
            "arabic_language": "Full Arabic UI and bilingual error messages",
            "data_residency": "All data stored locally - no external transfers",
        },
        "security_features": [
            "JWT Bearer Token authentication (HS256)",
            "Refresh token support for mobile apps",
            "Role-based access control (RBAC)",
            "Per-lab data isolation (multi-tenant)",
            "Bcrypt password hashing",
            "Fernet symmetric encryption for sensitive data",
            "HMAC-SHA256 national ID hashing (one-way)",
            "Rate limiting (auth: 10/min, API: 100/min)",
            "Intrusion detection with automatic blocking",
            "Comprehensive audit trail",
            "Request body size limits",
            "Security HTTP headers (CSP, HSTS, X-Frame-Options)",
            "No sensitive data in logs",
            "No passwords written to filesystem",
        ],
        "data_protection": {
            "patient_data_isolation": "Each lab can only access its own patients",
            "national_id_storage": "Hashed with HMAC-SHA256 - not reversible",
            "audit_log": "All actions logged with IP address and timestamp",
            "data_encryption_at_rest": "Fernet encryption available for sensitive fields",
            "data_in_transit": "HTTPS/TLS via nginx (production)",
            "result_access": "Token-based with optional expiry (90 days default)",
        },
        "api_info": {
            "type": "RESTful JSON API",
            "authentication": "Bearer JWT Token",
            "documentation": "/docs (Swagger UI) and /redoc (ReDoc)",
            "versioning": "Semantic versioning (current: v" + APP_VERSION + ")",
            "mobile_support": "Android and iOS via /auth/refresh and /mobile/*",
            "languages": ["Arabic (ar)", "English (en)"],
        },
        "contact": {
            "technical": "tech@gula-platform.org",
            "support": "support@gula-platform.org",
            "website": "https://gula-platform.org",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/audit-summary", summary="Audit summary for compliance (authenticated)")
def audit_summary(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns audit log statistics for compliance reporting.
    ملخص سجل التدقيق لتقارير الامتثال.

    Provides counts of actions by type for the current lab.
    """
    from sqlalchemy import text

    # Count audit actions for this lab's users
    lab_user_ids = [u.id for u in db.query(LabUser.id).filter(
        LabUser.lab_id == current_user.lab_id
    ).all()]

    if not lab_user_ids:
        return {"message": "No audit data", "actions": {}}

    actions = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label("count")
    ).filter(
        AuditLog.user_id.in_(lab_user_ids)
    ).group_by(AuditLog.action).all()

    total_events = db.query(func.count(AuditLog.id)).filter(
        AuditLog.user_id.in_(lab_user_ids)
    ).scalar() or 0

    return {
        "lab_id": current_user.lab_id,
        "total_audit_events": total_events,
        "actions_breakdown": {a.action: a.count for a in actions},
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Audit logs include all create, update, view, login, and admin actions",
        "note_ar": "سجلات التدقيق تشمل جميع عمليات الإنشاء والتحديث والعرض وتسجيل الدخول والإدارة",
    }


@router.get("/fhir/patient/{patient_id}", summary="FHIR Patient resource (basic)")
def get_fhir_patient(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns patient data in HL7 FHIR R4 Patient resource format.
    بيانات المريض بتنسيق HL7 FHIR R4.

    Useful for interoperability with Ministry of Health systems.
    مفيد للتكامل مع أنظمة وزارة الصحة.
    """
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()

    if not patient:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Patient not found")

    # Build basic FHIR R4 Patient resource
    fhir_patient = {
        "resourceType": "Patient",
        "id": patient.health_id or str(patient.id),
        "meta": {
            "versionId": "1",
            "lastUpdated": patient.created_at.isoformat() if patient.created_at else None,
            "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
        },
        "identifier": [
            {
                "use": "official",
                "system": "https://gula-platform.org/fhir/patient-id",
                "value": patient.health_id,
            }
        ],
        "name": [
            {
                "use": "official",
                "text": patient.full_name,
            }
        ],
        "telecom": [],
        "gender": _fhir_gender(patient.gender),
        "birthDate": str(patient.birth_date) if patient.birth_date else None,
        "managingOrganization": {
            "reference": f"Organization/{patient.lab_id}",
        },
    }

    if patient.phone:
        fhir_patient["telecom"].append({
            "system": "phone",
            "value": patient.phone,
            "use": "mobile",
        })

    if patient.email:
        fhir_patient["telecom"].append({
            "system": "email",
            "value": patient.email,
        })

    return fhir_patient


@router.get("/fhir/observation/{order_id}", summary="FHIR Observation resource (basic)")
def get_fhir_observations(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns lab results in HL7 FHIR R4 Observation bundle format.
    نتائج المختبر بتنسيق HL7 FHIR R4 Observation bundle.
    """
    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()

    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    results = db.query(LabResult).filter(LabResult.order_id == order_id).all()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()

    observations = []
    for r in results:
        obs = {
            "resourceType": "Observation",
            "id": str(r.id),
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory",
                        }
                    ]
                }
            ],
            "code": {
                "text": r.test_name,
            },
            "subject": {
                "reference": f"Patient/{patient.health_id if patient else order.patient_id}",
                "display": patient.full_name if patient else None,
            },
            "effectiveDateTime": r.created_at.isoformat() if r.created_at else None,
            "issued": r.created_at.isoformat() if r.created_at else None,
            "performer": [
                {"reference": f"Organization/{order.lab_id}"}
            ],
            "interpretation": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": _fhir_interpretation(r.flag),
                        }
                    ]
                }
            ] if r.flag else None,
        }

        if r.value is not None:
            obs["valueQuantity"] = {
                "value": r.value,
                "unit": r.unit or "",
                "system": "http://unitsofmeasure.org",
            }
        elif r.value_text:
            obs["valueString"] = r.value_text

        if r.normal_range_low is not None and r.normal_range_high is not None:
            obs["referenceRange"] = [
                {
                    "low": {"value": r.normal_range_low, "unit": r.unit or ""},
                    "high": {"value": r.normal_range_high, "unit": r.unit or ""},
                }
            ]

        observations.append(obs)

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "total": len(observations),
        "entry": [{"resource": obs} for obs in observations],
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fhir_gender(gender: str | None) -> str:
    mapping = {"M": "male", "F": "female", "male": "male", "female": "female"}
    return mapping.get(gender or "", "unknown")


def _fhir_interpretation(flag: str | None) -> str:
    mapping = {
        "high": "H", "low": "L", "critical_high": "HH",
        "critical_low": "LL", "normal": "N", "unknown": "U",
    }
    return mapping.get(flag or "", "N")
