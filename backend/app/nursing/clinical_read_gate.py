"""Deny-by-default gate for read-only clinical nursing tasks.

The nursing task model still carries a legacy lab scope, not a facility foreign
key.  This gate therefore proves the current user's canonical identity,
assignment, lab-to-facility binding, and exact policy before the route performs
the existing *own-task* laboratory query.  It must not be used for task state
changes or any nursing write operation.
"""

from app.radiology.clinical_read_gate import (
    ClinicalRadiologyReadContext,
    ClinicalRadiologyReadDenied,
    ClinicalRadiologyReadGate,
)


ClinicalNursingTaskReadContext = ClinicalRadiologyReadContext
ClinicalNursingTaskReadDenied = ClinicalRadiologyReadDenied


class ClinicalNursingTaskReadGate(ClinicalRadiologyReadGate):
    """Apply the shared clinical proof to the narrow nursing own-task read."""

    permission = "clinical.nursing.task.read"
    resource_type = "clinical_nursing_task_read"
