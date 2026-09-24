from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.reference.domain.services import (
    OrderProcessingService,
    PatientValidationService,
    ResultValidationService,
)
from app.reference.infrastructure.repositories import (
    SQLOrderRepository,
    SQLPatientRepository,
    SQLResultRepository,
)
from app.reference.services.order_service import OrderService
from app.reference.services.patient_service import PatientService
from app.reference.services.result_service import ResultService


def get_patient_service(
    session: Session = Depends(get_db),
) -> PatientService:
    repository = SQLPatientRepository(session)
    validation = PatientValidationService()
    return PatientService(repository=repository, validation=validation)


def get_order_service(
    session: Session = Depends(get_db),
) -> OrderService:
    repository = SQLOrderRepository(session)
    patient_repo = SQLPatientRepository(session)
    processing = OrderProcessingService()
    return OrderService(
        repository=repository,
        patient_repo=patient_repo,
        order_processing=processing,
    )


def get_result_service(
    session: Session = Depends(get_db),
) -> ResultService:
    repository = SQLResultRepository(session)
    order_repo = SQLOrderRepository(session)
    validation = ResultValidationService()
    return ResultService(
        repository=repository,
        order_repo=order_repo,
        validation=validation,
    )
