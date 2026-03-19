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
            "hl7_fhir_r4": "Implemented - Patient, Observation, DiagnosticReport, ServiceRequest resources",
            "dhis2": "Aggregate export endpoint available at /compliance/dhis2/aggregate",
            "iso_27001": "Security controls implemented (ISMS in progress)",
            "owasp_api_security": "OWASP API Security Top 10 addressed",
            "arabic_language": "Full Arabic RTL UI and bilingual error messages",
            "data_residency": "All data stored locally - no external transfers",
            "api_versioning": "URL-path versioning supported: /api/v1/ (current stable)",
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
            "authentication": "Bearer JWT Token (mobile) / httpOnly Cookie (web)",
            "documentation": "/docs (Swagger UI) and /redoc (ReDoc)",
            "versioning": "URL-path versioning: /api/v1/ | Platform version: " + APP_VERSION,
            "mobile_support": "Android and iOS via /auth/refresh and /mobile/*",
            "fhir_endpoints": [
                "/compliance/fhir/patient/{id}",
                "/compliance/fhir/observation/{order_id}",
                "/compliance/fhir/diagnostic-report/{order_id}",
                "/compliance/fhir/service-request/{order_id}",
            ],
            "moh_integration": "/compliance/dhis2/aggregate (DHIS2 aggregate export)",
            "languages": ["Arabic (ar)", "English (en)"],
        },
        "government_contacts": {
            "cmc": "cmc.iq - Communications and Media Commission (platform registration)",
            "ndc": "ndc.egov.iq - National Data Center (government cloud hosting)",
            "moh": "moh.gov.iq - Ministry of Health (health platform approval)",
            "kimadia": "kimadia.gov.iq - State Company for lab product registration",
            "cosqc": "cosqc.gov.iq - ISO certification authority",
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


@router.get("/fhir/diagnostic-report/{order_id}", summary="FHIR DiagnosticReport resource")
def get_fhir_diagnostic_report(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns lab order as HL7 FHIR R4 DiagnosticReport resource.
    تقرير التشخيص بتنسيق HL7 FHIR R4.

    DiagnosticReport is the primary FHIR resource for lab results — it wraps
    all Observations from a single order into a single reportable document.
    Required for Ministry of Health interoperability and DHIS2 integration.
    """
    from fastapi import HTTPException

    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    results = db.query(LabResult).filter(LabResult.order_id == order_id).all()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first()

    # Determine report status
    status_map = {
        "completed": "final",
        "pending": "registered",
        "cancelled": "cancelled",
    }
    report_status = status_map.get(order.status or "pending", "partial")

    observations_refs = [
        {"reference": f"Observation/{r.id}", "display": r.test_name}
        for r in results
    ]

    report = {
        "resourceType": "DiagnosticReport",
        "id": str(order_id),
        "meta": {
            "versionId": "1",
            "lastUpdated": order.created_at.isoformat() if order.created_at else None,
            "profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"],
        },
        "identifier": [
            {
                "system": "https://gula-platform.org/fhir/order-id",
                "value": str(order_id),
            }
        ],
        "status": report_status,
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report",
                }
            ],
            "text": "Laboratory Report",
        },
        "subject": {
            "reference": f"Patient/{patient.health_id if patient else order.patient_id}",
            "display": patient.full_name if patient else None,
        },
        "effectiveDateTime": order.created_at.isoformat() if order.created_at else None,
        "issued": order.created_at.isoformat() if order.created_at else None,
        "performer": [
            {
                "reference": f"Organization/{order.lab_id}",
                "display": lab.name if lab else None,
            }
        ],
        "result": observations_refs,
        "conclusion": _build_conclusion(results),
    }

    if order.doctor_name:
        report["basedOn"] = [
            {
                "reference": f"ServiceRequest/{order_id}",
                "display": f"Order by Dr. {order.doctor_name}",
            }
        ]

    return report


@router.get("/fhir/service-request/{order_id}", summary="FHIR ServiceRequest resource")
def get_fhir_service_request(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns lab order as HL7 FHIR R4 ServiceRequest resource.
    طلب الخدمة بتنسيق HL7 FHIR R4.

    ServiceRequest represents the original test order from a clinician.
    Used for order tracking and clinical workflow integration.
    """
    from fastapi import HTTPException

    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    results = db.query(LabResult).filter(LabResult.order_id == order_id).all()

    intent_map = {"pending": "original-order", "completed": "original-order", "cancelled": "original-order"}

    service_request = {
        "resourceType": "ServiceRequest",
        "id": str(order_id),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/ServiceRequest"],
        },
        "identifier": [
            {
                "system": "https://gula-platform.org/fhir/service-request-id",
                "value": str(order_id),
            }
        ],
        "status": "completed" if order.status == "completed" else "active",
        "intent": "original-order",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "108252007",
                        "display": "Laboratory procedure",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report",
                }
            ],
            "text": "Laboratory Tests",
        },
        "subject": {
            "reference": f"Patient/{patient.health_id if patient else order.patient_id}",
            "display": patient.full_name if patient else None,
        },
        "authoredOn": order.created_at.isoformat() if order.created_at else None,
        "performer": [{"reference": f"Organization/{order.lab_id}"}],
        "orderDetail": [
            {"text": r.test_name}
            for r in results
        ],
    }

    if order.doctor_name:
        service_request["requester"] = {
            "display": f"Dr. {order.doctor_name}",
        }

    return service_request


@router.get("/dhis2/aggregate", summary="DHIS2 aggregate data export for MoH reporting")
def get_dhis2_aggregate(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregate lab statistics in DHIS2-compatible format.
    إحصائيات المختبر التجميعية بتنسيق DHIS2.

    DHIS2 (District Health Information Software 2) is used by Iraq's Ministry
    of Health across 1,848 health institutions for national health reporting.
    This endpoint exports non-patient-identifying aggregate counts suitable
    for submission to the MoH DHIS2 national health information system.

    Data exported: total tests by type, result flag distribution, monthly counts.
    No patient PII is included in this response.
    """
    from sqlalchemy import text, extract
    from datetime import date

    # Aggregate test counts by type (no patient data)
    test_counts = db.execute(text("""
        SELECT test_name, COUNT(*) as count,
               SUM(CASE WHEN flag IN ('high', 'critical_high') THEN 1 ELSE 0 END) as abnormal_high,
               SUM(CASE WHEN flag IN ('low', 'critical_low') THEN 1 ELSE 0 END) as abnormal_low,
               SUM(CASE WHEN flag = 'normal' OR flag IS NULL THEN 1 ELSE 0 END) as normal
        FROM lab_results
        WHERE lab_id = :lab_id
        GROUP BY test_name
        ORDER BY count DESC
        LIMIT 50
    """), {"lab_id": current_user.lab_id}).fetchall()

    # Monthly order counts for trend analysis
    monthly_counts = db.execute(text("""
        SELECT
            EXTRACT(YEAR FROM created_at) as year,
            EXTRACT(MONTH FROM created_at) as month,
            COUNT(*) as order_count
        FROM lab_orders
        WHERE lab_id = :lab_id
          AND created_at >= NOW() - INTERVAL '12 months'
        GROUP BY year, month
        ORDER BY year, month
    """), {"lab_id": current_user.lab_id}).fetchall()

    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.lab_id == current_user.lab_id
    ).scalar() or 0

    total_orders = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == current_user.lab_id
    ).scalar() or 0

    # Build DHIS2-compatible dataValueSets format
    data_values = []
    for row in test_counts:
        data_values.extend([
            {
                "dataElement": f"GULA_TEST_{row.test_name.upper().replace(' ', '_')}_TOTAL",
                "value": str(row.count),
                "comment": f"Total {row.test_name} tests",
            },
            {
                "dataElement": f"GULA_TEST_{row.test_name.upper().replace(' ', '_')}_ABNORMAL",
                "value": str((row.abnormal_high or 0) + (row.abnormal_low or 0)),
                "comment": f"Abnormal {row.test_name} results",
            },
        ])

    return {
        "dataSet": "GULA_LAB_AGGREGATE",
        "completeDate": datetime.now(timezone.utc).date().isoformat(),
        "period": datetime.now(timezone.utc).strftime("%Y%m"),
        "orgUnit": f"LAB_{current_user.lab_id}",
        "dataValues": data_values,
        "summary": {
            "total_patients": total_patients,
            "total_orders": total_orders,
            "tests_by_type": [
                {
                    "test_name": row.test_name,
                    "total": row.count,
                    "abnormal_high": row.abnormal_high or 0,
                    "abnormal_low": row.abnormal_low or 0,
                    "normal": row.normal or 0,
                }
                for row in test_counts
            ],
            "monthly_trends": [
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "order_count": row.order_count,
                }
                for row in monthly_counts
            ],
        },
        "metadata": {
            "format": "DHIS2 dataValueSets",
            "version": "2.40",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": "GULA Medical Laboratory Platform",
            "note": "Aggregate statistics only - no patient PII included",
            "note_ar": "إحصائيات تجميعية فقط - لا تشمل بيانات المرضى الشخصية",
        },
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_conclusion(results) -> str | None:
    """Summarize abnormal findings for DiagnosticReport conclusion field."""
    abnormal = [r.test_name for r in results if r.flag in ("high", "low", "critical_high", "critical_low")]
    if not abnormal:
        return None
    return f"Abnormal values found in: {', '.join(abnormal)}"


def _fhir_gender(gender: str | None) -> str:
    mapping = {"M": "male", "F": "female", "male": "male", "female": "female"}
    return mapping.get(gender or "", "unknown")


def _fhir_interpretation(flag: str | None) -> str:
    mapping = {
        "high": "H", "low": "L", "critical_high": "HH",
        "critical_low": "LL", "normal": "N", "unknown": "U",
    }
    return mapping.get(flag or "", "N")
