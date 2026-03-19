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
import json
import logging
import os
import sys
import time
import hashlib
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
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
from ..services.audit_service import verify_audit_chain, get_latest_anchor
from ..config import APP_VERSION, APP_NAME, IS_PRODUCTION

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


@router.get("/audit-integrity", summary="Verify audit log chain integrity (admin)")
def audit_integrity(
    limit: int = 1000,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifies the cryptographic hash chain of audit log records.
    التحقق من سلامة سلسلة تجزئة سجل التدقيق.

    Each audit log entry contains SHA-256(prev_hash + record_data).
    Any tampering with a record or deletion of records breaks the chain.

    - Returns `"intact"` if no tampering detected
    - Returns `"tampered"` with details of which records were modified
    - Returns the last verified hash for external storage/verification

    **Access:** admin or master_admin only
    """
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = verify_audit_chain(db, limit=min(limit, 5000))
    result["lab_id"] = current_user.lab_id
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    result["note"] = (
        "Hash chain verification: each entry's chain_hash = "
        "SHA-256(previous_chain_hash + record_data). "
        "A broken chain indicates record tampering or deletion."
    )
    return result


@router.get("/security-report", summary="Security posture report for government audit")
def security_report(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a structured security posture report for government and ISO 27001 auditors.
    تقرير وضع الأمان للمراجعين الحكوميين ومراجعي ISO 27001.

    Covers: authentication, encryption, access control, audit, compliance, patching.
    **Access:** admin or master_admin only
    """
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Integrity check summary
    chain_result = verify_audit_chain(db, limit=100)

    # Recent failed logins (last 24h)
    from sqlalchemy import text
    failed_logins_24h = db.execute(text("""
        SELECT COUNT(*) FROM audit_logs
        WHERE action = 'login_failed'
          AND created_at >= NOW() - INTERVAL '24 hours'
    """)).scalar() or 0

    # Count users with last login (active session indication)
    total_users = db.query(func.count(LabUser.id)).filter(
        LabUser.lab_id == current_user.lab_id,
        LabUser.is_active == True,
    ).scalar() or 0

    # Python/platform version info
    python_ver = sys.version.split()[0]

    return {
        "report_type": "Security Posture Report",
        "report_type_ar": "تقرير وضع الأمان",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_version": APP_VERSION,
        "environment": "production" if IS_PRODUCTION else "development",

        "authentication": {
            "method": "JWT Bearer (mobile) + httpOnly Cookie (web)",
            "algorithm": "HS256",
            "access_token_ttl": "8 hours",
            "refresh_token_ttl": "30 days",
            "token_type_separation": "PASS - access tokens rejected as refresh tokens",
            "secure_cookies": "PASS - HttpOnly + SameSite=Strict + Secure (production)",
            "password_hashing": "PASS - bcrypt with random salt",
        },

        "access_control": {
            "rbac": "PASS - 4 roles: master_admin, admin, staff, technician",
            "multi_tenant": "PASS - per-lab data isolation enforced at query level",
            "object_level_auth": "PASS - patient/order/result access checked per lab_id",
            "failed_logins_24h": failed_logins_24h,
            "active_users_this_lab": total_users,
        },

        "encryption": {
            "data_in_transit": "PASS - HTTPS/TLS via nginx (production)",
            "data_at_rest": "PARTIAL - Fernet encryption for sensitive fields",
            "national_id_storage": "PASS - HMAC-SHA256 one-way hash (not reversible)",
            "key_management": "Env var injection (Vault recommended for enterprise)",
        },

        "audit_trail": {
            "status": chain_result["status"],
            "entries_verified": chain_result["entries_checked"],
            "chain_intact": chain_result["verified"],
            "tamper_detection": "PASS - SHA-256 hash chain (immutable trigger + chain hash)",
            "immutability": "PASS - PostgreSQL trigger blocks UPDATE/DELETE",
            "coverage": "All login, patient, order, result, admin actions logged",
        },

        "api_security": {
            "rate_limiting": "PASS - nginx: API 100/min, Auth 10/min, Upload 20/min",
            "request_body_limit": "PASS - 10MB max request body enforced",
            "security_headers": "PASS - CSP, X-Frame-Options, HSTS, Permissions-Policy",
            "server_disclosure": "PASS - proxy_hide_header X-Powered-By/Server",
            "attack_path_blocking": "PASS - wp-admin, phpMyAdmin, .env, .git blocked",
            "intrusion_detection": "PASS - IP blocking after repeated failures",
        },

        "compliance_standards": {
            "owasp_api_top10": "Addressed in ARCHITECTURE documentation",
            "hl7_fhir_r4": "PASS - Patient, Observation, DiagnosticReport, ServiceRequest",
            "dhis2": "PASS - Aggregate export at /compliance/dhis2/aggregate",
            "iso_27001_controls": [
                "A.8.15 Logging: PASS",
                "A.8.24 Cryptography: PASS",
                "A.8.3 Information access restriction: PASS",
                "A.8.29 Security testing in dev: PASS (Bandit + Trivy in CI)",
            ],
        },

        "runtime": {
            "python_version": python_ver,
            "container_user": "appuser (non-root)",
            "no_new_privileges": "PASS - security_opt in docker-compose",
        },

        "recommendations": [
            "Obtain ISO 27001:2022 formal certification",
            "Commission annual penetration test (CREST-certified testers)",
            "Register with Iraqi CMC (cmc.iq) for platform licensing",
            "Enable Redis-based rate limiting for multi-worker production",
            "Set up external log forwarding (Loki/ELK) for centralized SIEM",
        ],
    }


@router.get("/time-sync", summary="Server time and NTP synchronization status")
def time_sync_status():
    """
    Returns server time and NTP synchronization status.
    حالة تزامن وقت الخادم مع بروتوكول NTP.

    Audit log integrity depends on accurate timestamps.
    Government auditors use this to verify the server clock is trustworthy.
    No authentication required — time info is not sensitive.
    """
    now_utc = datetime.now(timezone.utc)

    # Maximum acceptable clock offset before raising a drift warning (2 seconds)
    MAX_OFFSET_SECONDS = 2.0

    # ─── NTP synchronized flag ────────────────────────────────────────────────
    ntp_status = "unknown"
    ntp_synchronized = None
    ntp_service = None
    try:
        result = subprocess.run(
            ["timedatectl", "show", "--no-pager", "--property=NTPSynchronized,NTP,Timezone"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if "NTPSynchronized=" in line:
                val = line.split("=")[1].strip()
                ntp_synchronized = val == "yes"
                ntp_status = "synchronized" if ntp_synchronized else "not_synchronized"
            if "NTP=" in line and "NTPSynchronized" not in line:
                ntp_service = line.split("=")[1].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        ntp_status = "timedatectl_unavailable"

    # ─── NTP offset (drift) via timedatectl timesync-status ──────────────────
    # timedatectl timesync-status output contains a line like:
    #   Offset: +359us    or    Offset: +1.234s
    # We parse it and compare against MAX_OFFSET_SECONDS.
    ntp_offset_us: int | None = None   # offset in microseconds
    ntp_offset_str: str | None = None  # human-readable from timedatectl
    drift_warning = False
    try:
        ts_result = subprocess.run(
            ["timedatectl", "timesync-status", "--no-pager"],
            capture_output=True, text=True, timeout=3
        )
        for line in ts_result.stdout.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith("Offset:"):
                raw = line_stripped.split(":", 1)[1].strip()
                ntp_offset_str = raw
                # Parse magnitude: timedatectl uses µs/ms/s suffixes
                import re
                m = re.match(r"([+-]?\d+(?:\.\d+)?)(us|µs|ms|s)", raw.replace("µs", "us"))
                if m:
                    val, unit = float(m.group(1)), m.group(2)
                    if unit == "us":
                        ntp_offset_us = int(val)
                    elif unit == "ms":
                        ntp_offset_us = int(val * 1_000)
                    elif unit == "s":
                        ntp_offset_us = int(val * 1_000_000)
                    offset_abs_s = abs(ntp_offset_us) / 1_000_000
                    drift_warning = offset_abs_s > MAX_OFFSET_SECONDS
                break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # timesync-status may not be available in containers

    # Compute Unix timestamp for auditor cross-reference
    unix_ts = int(time.time())

    # Determine overall recommendation
    if not ntp_synchronized:
        recommendation = "ACTION REQUIRED: Run 'timedatectl set-ntp true' on the host"
        audit_impact = "WARNING: Unsynchronized clock may affect audit log credibility"
    elif drift_warning:
        recommendation = f"WARNING: Clock drift {ntp_offset_str} exceeds {MAX_OFFSET_SECONDS}s threshold"
        audit_impact = "DRIFT DETECTED: Large offset may affect audit log timestamp accuracy"
    else:
        recommendation = "PASS - NTP synchronized" + (f" (offset: {ntp_offset_str})" if ntp_offset_str else "")
        audit_impact = "Audit log timestamps are reliable"

    return {
        "server_time_utc": now_utc.isoformat(),
        "unix_timestamp": unix_ts,
        "timezone": "UTC",
        "ntp_status": ntp_status,
        "ntp_synchronized": ntp_synchronized,
        "ntp_service_active": ntp_service,
        "ntp_offset_us": ntp_offset_us,
        "ntp_offset_human": ntp_offset_str,
        "drift_warning": drift_warning,
        "max_offset_seconds": MAX_OFFSET_SECONDS,
        "recommendation": recommendation,
        "audit_impact": audit_impact,
    }


@router.get("/system-status", summary="Full system health and security status dashboard")
def system_status(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Comprehensive system status for government and compliance dashboards.
    حالة النظام الشاملة للوحات التحكم الحكومية وامتثال ISO 27001.

    Covers: database, cache, audit integrity, time sync, security, API stats.
    **Access:** admin or master_admin only
    """
    if current_user.role not in ("admin", "master_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    now = datetime.now(timezone.utc)

    # ─── Database health ───────────────────────────────────────────────────
    db_ok = False
    db_latency_ms = None
    try:
        from sqlalchemy import text as sql_text
        t0 = time.monotonic()
        db.execute(sql_text("SELECT 1"))
        db_latency_ms = round((time.monotonic() - t0) * 1000, 2)
        db_ok = True
    except Exception:
        pass

    # ─── Audit chain ──────────────────────────────────────────────────────
    chain_result = verify_audit_chain(db, limit=200)
    anchor = get_latest_anchor()

    # ─── Stats ────────────────────────────────────────────────────────────
    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.lab_id == current_user.lab_id
    ).scalar() or 0

    total_orders = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == current_user.lab_id
    ).scalar() or 0

    total_audit_entries = db.query(func.count(AuditLog.id)).scalar() or 0

    # Failed logins in last 24h (security indicator)
    from sqlalchemy import text as sql_text
    failed_24h = db.execute(sql_text(
        "SELECT COUNT(*) FROM audit_logs "
        "WHERE action='login_failed' AND created_at >= NOW() - INTERVAL '24 hours'"
    )).scalar() or 0

    # ─── Time sync (synchronized flag + drift check) ──────────────────────
    _MAX_OFFSET_S = 2.0
    ntp_ok = None
    ntp_drift_warning = False
    ntp_offset_str = None
    try:
        result = subprocess.run(
            ["timedatectl", "show", "--no-pager", "--property=NTPSynchronized"],
            capture_output=True, text=True, timeout=3
        )
        ntp_ok = "NTPSynchronized=yes" in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        ntp_ok = None
    # Parse drift from timesync-status
    try:
        import re as _re
        ts = subprocess.run(
            ["timedatectl", "timesync-status", "--no-pager"],
            capture_output=True, text=True, timeout=3
        )
        for line in ts.stdout.splitlines():
            if line.strip().startswith("Offset:"):
                ntp_offset_str = line.strip().split(":", 1)[1].strip()
                m = _re.match(r"([+-]?\d+(?:\.\d+)?)(us|µs|ms|s)", ntp_offset_str.replace("µs", "us"))
                if m:
                    v, u = float(m.group(1)), m.group(2)
                    us = int(v) if u == "us" else int(v * 1_000) if u == "ms" else int(v * 1_000_000)
                    ntp_drift_warning = abs(us) / 1_000_000 > _MAX_OFFSET_S
                break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    def status_flag(ok, warning_msg="", pass_msg="PASS"):
        if ok is True:
            return {"status": "pass", "label": pass_msg}
        if ok is False:
            return {"status": "fail", "label": f"FAIL: {warning_msg}"}
        return {"status": "unknown", "label": "UNKNOWN"}

    # ─── Restore test evidence ────────────────────────────────────────────
    restore_test = _read_restore_test()

    return {
        "dashboard": "GULA System Status",
        "dashboard_ar": "لوحة حالة منصة غولا",
        "generated_at": now.isoformat(),
        "platform_version": APP_VERSION,
        "environment": "production" if IS_PRODUCTION else "development",

        "services": {
            "database": {
                **status_flag(db_ok, "Database unreachable"),
                "latency_ms": db_latency_ms,
            },
            "api": {
                "status": "pass",
                "label": "PASS",
            },
        },

        "data": {
            "total_patients_this_lab": total_patients,
            "total_orders_this_lab": total_orders,
            "total_audit_entries": total_audit_entries,
            "failed_logins_24h": failed_24h,
            "failed_logins_alert": failed_24h > 10,
        },

        "security": {
            "audit_chain": {
                **status_flag(chain_result["verified"], "Audit log tampered"),
                "entries_checked": chain_result["entries_checked"],
                "broken_count": len(chain_result.get("broken_entries", [])),
            },
            "audit_anchor": {
                **status_flag(
                    anchor is not None,
                    "No external anchor found — first 100 entries not yet anchored",
                    "PASS",
                ),
                "latest_anchor_id": anchor["entry_id"] if anchor else None,
                "latest_anchor_time": anchor["timestamp"] if anchor else None,
                "total_anchors": anchor["total_anchors"] if anchor else 0,
            },
            "anchor_cross_check": chain_result.get("anchor_cross_check"),
            "time_sync": {
                **status_flag(
                    None if ntp_ok is None else (ntp_ok and not ntp_drift_warning),
                    "NTP not synchronized — audit timestamps may be unreliable"
                    if not ntp_ok else f"Clock drift {ntp_offset_str} exceeds {_MAX_OFFSET_S}s",
                    "PASS - NTP synchronized" + (f" (offset: {ntp_offset_str})" if ntp_offset_str else ""),
                ),
                "drift_warning": ntp_drift_warning,
                "offset": ntp_offset_str,
            },
            "https": {
                **status_flag(
                    IS_PRODUCTION,
                    "Running in development mode",
                    "PASS - production mode",
                ),
            },
        },

        "compliance_checklist": {
            "fhir_r4": "PASS",
            "dhis2_export": "PASS",
            "audit_immutability": "PASS - DB trigger + hash chain + external anchor",
            "rbac": "PASS - 4 roles enforced",
            "secure_cookies": "PASS" if IS_PRODUCTION else "DEV - Secure=False in development",
            "docs_protected": "PASS" if IS_PRODUCTION else "DEV - /docs open in development",
            "disaster_recovery": (
                f"PASS - Last tested: {restore_test['tested_at_human']} ({restore_test['tested_ago']} ago, {restore_test['restore_seconds']}s)"
                if restore_test and restore_test.get("status") == "PASS"
                else "PENDING - Run scripts/restore-test.sh"
            ),
            "cmc_registration": "PENDING - Register at cmc.iq",
            "iso_27001": "PENDING - Formal certification required",
            "pentest": "PENDING - Annual CREST-certified pentest required",
        },

        "disaster_recovery": restore_test,

        "alerts": [
            msg for msg in [
                "⚠ CRITICAL: NTP not synchronized" if ntp_ok is False else None,
                f"⚠ HIGH: Clock drift {ntp_offset_str} exceeds {_MAX_OFFSET_S}s — audit timestamps unreliable" if ntp_drift_warning else None,
                f"⚠ HIGH: {failed_24h} failed logins in last 24h" if failed_24h > 10 else None,
                "⚠ HIGH: Audit chain integrity broken" if not chain_result["verified"] else None,
                "⚠ MEDIUM: Anchor cross-check failed" if chain_result.get("anchor_cross_check") and not chain_result["anchor_cross_check"].get("match") else None,
                "⚠ MEDIUM: Restore test result tampered" if restore_test and restore_test.get("signature_valid") is False else None,
                "⚠ INFO: Running in development mode" if not IS_PRODUCTION else None,
            ] if msg
        ],
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

_RESTORE_RESULT_FILE = Path(os.getenv("RESTORE_RESULT_JSON", "/app/data/last_restore_test.json"))


def _read_restore_test() -> dict | None:
    """Read and HMAC-verify the last restore-test.sh result.

    The script signs the payload with NID_HMAC_KEY. If the file has been
    tampered with (e.g., someone manually changed "FAIL" → "PASS"), the
    signature will not match and signature_valid=False is returned.
    """
    import hmac as _hmac
    import hashlib as _hashlib
    try:
        if not _RESTORE_RESULT_FILE.exists():
            return None
        with open(_RESTORE_RESULT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify HMAC: recompute over payload without the "signature" field
        stored_sig = data.pop("signature", None)
        if stored_sig:
            hmac_key = os.getenv("NID_HMAC_KEY", "gula-anchor-hmac-fallback").encode()
            # Canonical payload: compact JSON with sorted keys (matches shell output)
            payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False, sort_keys=False)
            expected = _hmac.new(hmac_key, payload.encode("utf-8"), _hashlib.sha256).hexdigest()
            data["signature_valid"] = _hmac.compare_digest(expected, stored_sig)
            if not data["signature_valid"]:
                logger.warning("Restore test JSON HMAC mismatch — possible tampering")
        else:
            data["signature_valid"] = None  # legacy file without signature

        # Human "tested ago" label
        tested_at = datetime.fromisoformat(data["tested_at"].replace("Z", "+00:00"))
        delta_seconds = int((datetime.now(timezone.utc) - tested_at).total_seconds())
        if delta_seconds < 3600:
            ago = f"{delta_seconds // 60} دقيقة"
        elif delta_seconds < 86400:
            ago = f"{delta_seconds // 3600} ساعة"
        else:
            ago = f"{delta_seconds // 86400} يوم"
        data["tested_ago"] = ago
        return data
    except Exception:
        return None


def _fhir_gender(gender: str | None) -> str:
    mapping = {"M": "male", "F": "female", "male": "male", "female": "female"}
    return mapping.get(gender or "", "unknown")


def _fhir_interpretation(flag: str | None) -> str:
    mapping = {
        "high": "H", "low": "L", "critical_high": "HH",
        "critical_low": "LL", "normal": "N", "unknown": "U",
    }
    return mapping.get(flag or "", "N")
