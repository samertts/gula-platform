"""Isolated, in-memory laboratory workflow for synthetic Health Core development.

This package implements lab orders, specimens, testing, results and verification
without any database, MPI, analyzer or network dependency. It is never wired into
production routes. Future integration seams live in :mod:`app.health_core.lab.contracts`
as declaration-only protocols.
"""

from __future__ import annotations

from app.health_core.lab.catalogue import (
    TEST_CATALOGUE,
    TestDefinition,
    catalogue_codes,
    get_test_definition,
    is_known_test_code,
)
from app.health_core.lab.contracts import (
    FutureAnalyzerGateway,
    FuturePatientLookup,
    FutureResultPublisher,
)
from app.health_core.lab.errors import (
    InvalidActorError,
    InvalidResultError,
    LabWorkflowError,
    UnknownLabEntityError,
    UnknownTestCodeError,
)
from app.health_core.lab.models import (
    LEGAL_SPECIMEN_TRANSITIONS,
    LEGAL_VERIFICATION_TRANSITIONS,
    CustodyEntry,
    LabOrder,
    LabOrderStatus,
    LabResult,
    Priority,
    ResultAmendment,
    Specimen,
    SpecimenStatus,
    TestExecution,
    TestExecutionStatus,
    Verification,
    VerificationDecision,
    VerificationStatus,
    new_synthetic_barcode,
)
from app.health_core.lab.repositories import (
    InMemoryCustodyRepository,
    InMemoryEventStore,
    InMemoryLabOrderRepository,
    InMemoryResultRepository,
    InMemorySpecimenRepository,
    InMemoryTestExecutionRepository,
    InMemoryVerificationRepository,
)
from app.health_core.lab.services import LabWorkflowService

__all__ = [
    "LEGAL_SPECIMEN_TRANSITIONS",
    "LEGAL_VERIFICATION_TRANSITIONS",
    "TEST_CATALOGUE",
    "CustodyEntry",
    "FutureAnalyzerGateway",
    "FuturePatientLookup",
    "FutureResultPublisher",
    "InMemoryCustodyRepository",
    "InMemoryEventStore",
    "InMemoryLabOrderRepository",
    "InMemoryResultRepository",
    "InMemorySpecimenRepository",
    "InMemoryTestExecutionRepository",
    "InMemoryVerificationRepository",
    "InvalidActorError",
    "InvalidResultError",
    "LabOrder",
    "LabOrderStatus",
    "LabResult",
    "LabWorkflowError",
    "LabWorkflowService",
    "Priority",
    "ResultAmendment",
    "Specimen",
    "SpecimenStatus",
    "TestDefinition",
    "TestExecution",
    "TestExecutionStatus",
    "UnknownLabEntityError",
    "UnknownTestCodeError",
    "Verification",
    "VerificationDecision",
    "VerificationStatus",
    "catalogue_codes",
    "get_test_definition",
    "is_known_test_code",
    "new_synthetic_barcode",
]
