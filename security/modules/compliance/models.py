from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplianceFramework(str, Enum):
    OWASP_ASVS = "OWASP_ASVS"
    OWASP_API_TOP_10 = "OWASP_API_TOP_10"
    OWASP_TOP_10 = "OWASP_TOP_10"
    NIST_CSF = "NIST_CSF"
    NIST_800_53 = "NIST_800_53"
    NIST_SSDF = "NIST_SSDF"
    ISO_27001 = "ISO_27001"
    ISO_27799 = "ISO_27799"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    FHIR_SECURITY = "FHIR_SECURITY"
    IRAQI_NATIONAL = "IRAQI_NATIONAL"


class ControlStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    PLANNED = "PLANNED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComplianceControl(BaseModel):
    control_id: str
    framework: ComplianceFramework
    category: str = ""
    description: str = ""
    implementation_status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    evidence: List[str] = Field(default_factory=list)
    test_procedure: str = ""
    last_assessed: Optional[datetime] = None
    risk_if_missing: str = ""


class ComplianceReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    framework: ComplianceFramework
    overall_status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    control_count: int = 0
    passed: int = 0
    failed: int = 0
    not_applicable: int = 0
    findings: List[ComplianceControl] = Field(default_factory=list)
    remediation_plan: Dict[str, str] = Field(default_factory=dict)
