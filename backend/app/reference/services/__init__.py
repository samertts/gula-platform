"""Service layer — depends ONLY on domain.

Coordinates domain services + repository interfaces.
No FastAPI, SQLAlchemy, or Pydantic imports.

Re-exports domain types so routes never import domain directly.
"""

from app.reference.domain.exceptions import (
    CriticalResultError as CriticalResultError,
)
from app.reference.domain.exceptions import (
    DomainError as DomainError,
)
from app.reference.domain.exceptions import (
    DuplicatePatientError as DuplicatePatientError,
)
from app.reference.domain.exceptions import (
    InvalidOrderError as InvalidOrderError,
)
from app.reference.domain.exceptions import (
    InvalidPatientDataError as InvalidPatientDataError,
)
from app.reference.domain.exceptions import (
    OrderNotFoundError as OrderNotFoundError,
)
from app.reference.domain.exceptions import (
    PatientNotFoundError as PatientNotFoundError,
)
from app.reference.domain.exceptions import (
    ResultNotFoundError as ResultNotFoundError,
)
from app.reference.domain.models import (
    Gender as Gender,
)
from app.reference.domain.models import (
    LabOrderDomain as LabOrderDomain,
)
from app.reference.domain.models import (
    LabResultDomain as LabResultDomain,
)
from app.reference.domain.models import (
    OrderStatus as OrderStatus,
)
from app.reference.domain.models import (
    PatientDomain as PatientDomain,
)
from app.reference.domain.models import (
    Priority as Priority,
)
from app.reference.domain.models import (
    ReferenceRange as ReferenceRange,
)
