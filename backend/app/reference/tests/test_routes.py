from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.reference.domain.exceptions import (
    CriticalResultError,
    DuplicatePatientError,
    InvalidOrderError,
    InvalidPatientDataError,
    OrderNotFoundError,
    PatientNotFoundError,
    ResultNotFoundError,
)
from app.reference.domain.models import (
    Gender,
    LabOrderDomain,
    LabResultDomain,
    OrderStatus,
    PatientDomain,
    Priority,
    ReferenceRange,
)
from app.reference.domain.services import (
    OrderProcessingService,
    PatientValidationService,
    ResultValidationService,
)
from app.reference.services.order_service import OrderService
from app.reference.services.patient_service import PatientService
from app.reference.services.result_service import ResultService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_patient_service() -> MagicMock:
    svc = MagicMock(spec=PatientService)
    svc.create_patient = AsyncMock()
    svc.get_patient = AsyncMock()
    svc.search_patients = AsyncMock()
    return svc


@pytest.fixture
def mock_order_service() -> MagicMock:
    svc = MagicMock(spec=OrderService)
    svc.create_order = AsyncMock()
    svc.get_order = AsyncMock()
    svc.list_patient_orders = AsyncMock()
    return svc


@pytest.fixture
def mock_result_service() -> MagicMock:
    svc = MagicMock(spec=ResultService)
    svc.submit_result = AsyncMock()
    svc.get_result = AsyncMock()
    svc.list_order_results = AsyncMock()
    svc.list_critical_results = AsyncMock()
    svc.bulk_submit_results = AsyncMock()
    return svc


SAMPLE_PATIENT = PatientDomain(
    patient_id="p-123",
    name="علي أحمد",
    date_of_birth=date(1990, 5, 15),
    gender=Gender.MALE,
    phone="+9647701234567",
    lab_id="lab-1",
    national_id="123456789012",
    address="بغداد، العراق",
    created_at=datetime(2025, 1, 1, 10, 0, 0),
    updated_at=datetime(2025, 1, 1, 10, 0, 0),
)

SAMPLE_ORDER = LabOrderDomain(
    order_id="o-123",
    patient_id="p-123",
    lab_id="lab-1",
    test_type="CBC",
    status=OrderStatus.PENDING,
    priority=Priority.ROUTINE,
    notes="",
    created_at=datetime(2025, 1, 1, 10, 30, 0),
    updated_at=datetime(2025, 1, 1, 10, 30, 0),
)

SAMPLE_RESULT = LabResultDomain(
    result_id="r-123",
    order_id="o-123",
    analyte="WBC",
    value=Decimal("7.5"),
    unit="x10^9/L",
    reference_range=ReferenceRange(
        analyte="WBC",
        unit="x10^9/L",
        min_value=Decimal("4.0"),
        max_value=Decimal("11.0"),
    ),
    is_critical=False,
    flagged="طبيعي",
    created_at=datetime(2025, 1, 1, 11, 0, 0),
)


def _make_app_with_overrides(
    patient_service: MagicMock | None = None,
    order_service: MagicMock | None = None,
    result_service: MagicMock | None = None,
) -> FastAPI:
    """Create a FastAPI app with overridden dependencies.

    Uses FastAPI's dependency_overrides mechanism so that Depends()
    resolves to the provided mocks instead of the real implementation.
    """
    from app.reference.infrastructure.dependencies import (
        get_order_service,
        get_patient_service,
        get_result_service,
    )
    from app.reference.routes.orders import router as orders_router
    from app.reference.routes.patients import router as patients_router
    from app.reference.routes.results import router as results_router

    application = FastAPI()
    application.include_router(patients_router)
    application.include_router(orders_router)
    application.include_router(results_router)

    if patient_service is not None:
        application.dependency_overrides[get_patient_service] = (
            lambda: patient_service
        )
    if order_service is not None:
        application.dependency_overrides[get_order_service] = (
            lambda: order_service
        )
    if result_service is not None:
        application.dependency_overrides[get_result_service] = (
            lambda: result_service
        )

    return application


# ---------------------------------------------------------------------------
# Patient Route Tests
# ---------------------------------------------------------------------------


class TestPatientRoutes:
    async def test_get_patient_found(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.get_patient.return_value = SAMPLE_PATIENT
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/reference/patients/p-123")

        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-123"
        assert data["name"] == "علي أحمد"
        assert data["gender"] == "ذكر"
        mock_patient_service.get_patient.assert_awaited_once_with("p-123")

    async def test_get_patient_not_found(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.get_patient.side_effect = PatientNotFoundError("p-999")
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/reference/patients/p-999")

        assert response.status_code == 404

    async def test_create_patient_success(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.create_patient.return_value = SAMPLE_PATIENT
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/patients",
                params={
                    "name": "علي أحمد",
                    "date_of_birth": "1990-05-15",
                    "gender": "ذكر",
                    "phone": "+9647701234567",
                    "lab_id": "lab-1",
                    "national_id": "123456789012",
                    "address": "بغداد، العراق",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-123"
        assert data["name"] == "علي أحمد"

    async def test_create_patient_duplicate(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.create_patient.side_effect = DuplicatePatientError(
            "name", "علي أحمد"
        )
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/patients",
                params={
                    "name": "علي أحمد",
                    "phone": "+9647701234567",
                    "lab_id": "lab-1",
                },
            )

        assert response.status_code == 409

    async def test_create_patient_invalid_data(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.create_patient.side_effect = InvalidPatientDataError(
            "اسم المريض قصير جدًا"
        )
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/patients",
                params={
                    "name": "أ",
                    "lab_id": "lab-1",
                },
            )

        assert response.status_code == 400

    async def test_search_patients(
        self,
        mock_patient_service: MagicMock,
    ) -> None:
        mock_patient_service.search_patients.return_value = ([SAMPLE_PATIENT], 1)
        app = _make_app_with_overrides(patient_service=mock_patient_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/reference/patients",
                params={"name": "علي", "lab_id": "lab-1"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "علي أحمد"


# ---------------------------------------------------------------------------
# Order Route Tests
# ---------------------------------------------------------------------------


class TestOrderRoutes:
    async def test_create_order_success(
        self,
        mock_order_service: MagicMock,
    ) -> None:
        mock_order_service.create_order.return_value = SAMPLE_ORDER
        app = _make_app_with_overrides(order_service=mock_order_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/orders",
                params={
                    "patient_id": "p-123",
                    "lab_id": "lab-1",
                    "test_type": "CBC",
                    "priority": "روتيني",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "o-123"
        assert data["test_type"] == "CBC"

    async def test_create_order_invalid(
        self,
        mock_order_service: MagicMock,
    ) -> None:
        mock_order_service.create_order.side_effect = InvalidOrderError(
            "الحقول المطلوبة مفقودة"
        )
        app = _make_app_with_overrides(order_service=mock_order_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/orders",
                params={
                    "patient_id": "p-123",
                    "lab_id": "lab-1",
                    "test_type": "CBC",
                },
            )

        assert response.status_code == 400

    async def test_get_order_found(
        self,
        mock_order_service: MagicMock,
    ) -> None:
        mock_order_service.get_order.return_value = SAMPLE_ORDER
        app = _make_app_with_overrides(order_service=mock_order_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/reference/orders/o-123")

        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "o-123"

    async def test_get_order_not_found(
        self,
        mock_order_service: MagicMock,
    ) -> None:
        mock_order_service.get_order.side_effect = OrderNotFoundError("o-999")
        app = _make_app_with_overrides(order_service=mock_order_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/reference/orders/o-999")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Result Route Tests
# ---------------------------------------------------------------------------


class TestResultRoutes:
    async def test_submit_result_success(
        self,
        mock_result_service: MagicMock,
    ) -> None:
        mock_result_service.submit_result.return_value = SAMPLE_RESULT
        app = _make_app_with_overrides(result_service=mock_result_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/results",
                params={
                    "order_id": "o-123",
                    "analyte": "WBC",
                    "value": 7.5,
                    "unit": "x10^9/L",
                    "min_value": 4.0,
                    "max_value": 11.0,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == "r-123"
        assert data["analyte"] == "WBC"
        assert data["is_critical"] is False

    async def test_submit_critical_result(
        self,
        mock_result_service: MagicMock,
    ) -> None:
        mock_result_service.submit_result.side_effect = CriticalResultError(
            "Potassium", "7.0", "mmol/L"
        )
        app = _make_app_with_overrides(result_service=mock_result_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/reference/results",
                params={
                    "order_id": "o-123",
                    "analyte": "Potassium",
                    "value": 7.0,
                    "unit": "mmol/L",
                    "min_value": 3.5,
                    "max_value": 5.5,
                    "min_critical": 2.5,
                    "max_critical": 6.5,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_critical"] is True
        assert "critical_warning" in data

    async def test_list_critical_results(
        self,
        mock_result_service: MagicMock,
    ) -> None:
        critical_result = LabResultDomain(
            result_id="r-456",
            order_id="o-123",
            analyte="Potassium",
            value=Decimal("7.0"),
            unit="mmol/L",
            reference_range=ReferenceRange(
                analyte="Potassium",
                unit="mmol/L",
                min_value=Decimal("3.5"),
                max_value=Decimal("5.5"),
                max_critical=Decimal("6.5"),
            ),
            is_critical=True,
            flagged="حرج",
            created_at=datetime(2025, 1, 1, 11, 0, 0),
        )
        mock_result_service.list_critical_results.return_value = (
            [critical_result],
            1,
        )
        app = _make_app_with_overrides(result_service=mock_result_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/reference/results/critical",
                params={"lab_id": "lab-1"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["is_critical"] is True
        assert data["results"][0]["flagged"] == "حرج"

    async def test_get_result_not_found(
        self,
        mock_result_service: MagicMock,
    ) -> None:
        mock_result_service.get_result.side_effect = ResultNotFoundError("r-999")
        app = _make_app_with_overrides(result_service=mock_result_service)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/reference/results/r-999")

        assert response.status_code == 404
