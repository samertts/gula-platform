"""Service layer — depends ONLY on domain.

Coordinates domain services + repository interfaces.
No FastAPI, SQLAlchemy, or Pydantic imports.

Re-exports domain types so routes never import domain directly.
"""

from app.reference.domain.exceptions import (
    CriticalResultError as CriticalResultError,
    DomainError as DomainError,
    DuplicatePatientError as DuplicatePatientError,
    InvalidOrderError as InvalidOrderError,
    InvalidPatientDataError as InvalidPatientDataError,
    OrderNotFoundError as OrderNotFoundError,
    PatientNotFoundError as PatientNotFoundError,
    ResultNotFoundError as ResultNotFoundError,
)
from app.reference.domain.models import (
    Gender as Gender,
    LabOrderDomain as LabOrderDomain,
    LabResultDomain as LabResultDomain,
    OrderStatus as OrderStatus,
    PatientDomain as PatientDomain,
    Priority as Priority,
    ReferenceRange as ReferenceRange,
)
