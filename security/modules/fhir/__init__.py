GSF-017: FHIR Module — FHIR R4 security enforcement.

Provides FHIR R4-specific security enforcement for the GULA platform
including security label enforcement, consent directive evaluation,
SMART-on-FHIR authorization, and FHIR audit event generation.
Implements the FHIR Security and Privacy Implementation Guide
requirements for Iraqi national healthcare interoperability.

Exports:
    FhirSecurityEngine: FHIR security orchestration
    SecurityLabelEnforcer: FHIR security label (Resource.security) enforcement
    ConsentDirectiveEvaluator: Consent directive evaluation and enforcement
    SmartOnFhirAuthorizer: SMART-on-FHIR authorization flow
    FhirAuditEventGenerator: FHIR AuditEvent resource generation
    ProvenanceRecorder: FHIR Provenance resource recording
"""

from security.modules.fhir.engine import FhirSecurityEngine
from security.modules.fhir.labels import SecurityLabelEnforcer
from security.modules.fhir.consent import ConsentDirectiveEvaluator
from security.modules.fhir.smart import SmartOnFhirAuthorizer
from security.modules.fhir.audit import FhirAuditEventGenerator
from security.modules.fhir.provenance import ProvenanceRecorder

__all__ = [
    "FhirSecurityEngine",
    "SecurityLabelEnforcer",
    "ConsentDirectiveEvaluator",
    "SmartOnFhirAuthorizer",
    "FhirAuditEventGenerator",
    "ProvenanceRecorder",
]
