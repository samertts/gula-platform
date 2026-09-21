from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.reference.domain.exceptions import (
    CriticalResultError,
    DuplicatePatientError,
    InvalidOrderError,
    InvalidPatientDataError,
    PatientNotFoundError,
)
from app.reference.domain.interfaces import (
    OrderRepository,
    PatientRepository,
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

# ---------------------------------------------------------------------------
# PatientValidationService tests
# ---------------------------------------------------------------------------


class TestPatientValidationService:
    def setup_method(self) -> None:
        self.service = PatientValidationService()
        self.mock_repo = MagicMock(spec=PatientRepository)
        self.mock_repo.find_duplicate = AsyncMock(return_value=None)

    def test_validate_valid_patient(self) -> None:
        patient = PatientDomain(
            name="علي أحمد",
            date_of_birth=date(1990, 5, 15),
            gender=Gender.MALE,
            phone="+9647701234567",
            lab_id="lab-1",
        )
        result = self.service.validate_new_patient(patient, self.mock_repo)
        assert result.name == "علي أحمد"
        assert result.phone == "+9647701234567"

    def test_validate_empty_name_raises(self) -> None:
        patient = PatientDomain(name="", gender=Gender.MALE, lab_id="lab-1")
        with pytest.raises(InvalidPatientDataError) as exc:
            self.service.validate_new_patient(patient, self.mock_repo)
        assert "قصير" in str(exc.value)

    def test_validate_invalid_phone_raises(self) -> None:
        patient = PatientDomain(
            name="علي أحمد",
            phone="abc",
            gender=Gender.MALE,
            lab_id="lab-1",
        )
        with pytest.raises(InvalidPatientDataError) as exc:
            self.service.validate_new_patient(patient, self.mock_repo)
        assert "الهاتف" in str(exc.value)

    def test_validate_future_dob_raises(self) -> None:
        patient = PatientDomain(
            name="علي أحمد",
            date_of_birth=date(2099, 1, 1),
            gender=Gender.MALE,
            lab_id="lab-1",
        )
        with pytest.raises(InvalidPatientDataError) as exc:
            self.service.validate_new_patient(patient, self.mock_repo)
        assert "المستقبل" in str(exc.value)

    async def test_check_duplicate_raises(self) -> None:
        existing = PatientDomain(
            patient_id="p-1",
            name="علي أحمد",
            phone="+9647701234567",
            lab_id="lab-1",
        )
        self.mock_repo.find_duplicate = AsyncMock(return_value=existing)
        patient = PatientDomain(
            name="علي أحمد",
            phone="+9647701234567",
            lab_id="lab-1",
        )
        with pytest.raises(DuplicatePatientError):
            await self.service.check_duplicate(patient, self.mock_repo)

    async def test_check_duplicate_no_match_passes(self) -> None:
        self.mock_repo.find_duplicate = AsyncMock(return_value=None)
        patient = PatientDomain(
            name="علي أحمد",
            phone="+9647701234567",
            lab_id="lab-1",
        )
        await self.service.check_duplicate(patient, self.mock_repo)

    def test_normalize_name_removes_non_arabic(self) -> None:
        raw = "علي123 Ahmed!"
        result = PatientValidationService.normalize_name(raw)
        assert result == "علي"

    def test_normalize_name_collapses_spaces(self) -> None:
        raw = "  علي   أحمد  "
        result = PatientValidationService.normalize_name(raw)
        assert result == "علي أحمد"

    def test_compute_age(self) -> None:
        dob = date(1990, 6, 15)
        today = date.today()
        expected = (
            today.year
            - 1990
            - ((today.month, today.day) < (6, 15))
        )
        assert PatientValidationService.compute_age(dob) == expected

    def test_compute_age_none(self) -> None:
        assert PatientValidationService.compute_age(None) is None

    def test_validate_national_id_valid(self) -> None:
        patient = PatientDomain(
            name="علي أحمد",
            national_id="123456789012",
            gender=Gender.MALE,
            lab_id="lab-1",
        )
        result = self.service.validate_new_patient(patient, self.mock_repo)
        assert result.national_id == "123456789012"

    def test_validate_national_id_invalid_raises(self) -> None:
        patient = PatientDomain(
            name="علي أحمد",
            national_id="abc",
            gender=Gender.MALE,
            lab_id="lab-1",
        )
        with pytest.raises(InvalidPatientDataError):
            self.service.validate_new_patient(patient, self.mock_repo)

    def test_validate_no_gender_raises(self) -> None:
        patient = PatientDomain(name="علي أحمد", lab_id="lab-1")
        with pytest.raises(InvalidPatientDataError):
            self.service.validate_new_patient(patient, self.mock_repo)


# ---------------------------------------------------------------------------
# OrderProcessingService tests
# ---------------------------------------------------------------------------


class TestOrderProcessingService:
    def setup_method(self) -> None:
        self.service = OrderProcessingService()
        self.mock_patient_repo = MagicMock(spec=PatientRepository)
        self.mock_patient_repo.get_by_id = AsyncMock(
            return_value=PatientDomain(
                patient_id="p-1",
                name="علي أحمد",
                lab_id="lab-1",
            ),
        )

    async def test_validate_valid_order(self) -> None:
        order = LabOrderDomain(
            patient_id="p-1",
            test_type="CBC",
            lab_id="lab-1",
        )
        result = await self.service.validate_new_order(order, self.mock_patient_repo)
        assert result.patient_id == "p-1"
        assert result.test_type == "CBC"

    async def test_validate_missing_fields_raises(self) -> None:
        order = LabOrderDomain(patient_id="p-1")
        with pytest.raises(InvalidOrderError) as exc:
            await self.service.validate_new_order(order, self.mock_patient_repo)
        assert "مطلوبة" in str(exc.value)

    async def test_validate_missing_patient_raises(self) -> None:
        self.mock_patient_repo.get_by_id = AsyncMock(return_value=None)
        order = LabOrderDomain(
            patient_id="p-nonexistent",
            test_type="CBC",
            lab_id="lab-1",
        )
        with pytest.raises(PatientNotFoundError):
            await self.service.validate_new_order(order, self.mock_patient_repo)

    def test_determine_priority_stat(self) -> None:
        order = LabOrderDomain(priority=Priority.STAT)
        result = OrderProcessingService.determine_priority(order)
        assert result == Priority.STAT

    def test_determine_priority_routine_default(self) -> None:
        order = LabOrderDomain(priority=Priority.ROUTINE)
        result = OrderProcessingService.determine_priority(order)
        assert result == Priority.ROUTINE

    def test_can_cancel_pending_order(self) -> None:
        order = LabOrderDomain(status=OrderStatus.PENDING)
        assert OrderProcessingService.can_cancel(order) is True

    def test_cannot_cancel_completed_order(self) -> None:
        order = LabOrderDomain(status=OrderStatus.COMPLETED)
        assert OrderProcessingService.can_cancel(order) is False

    async def test_validate_sets_created_at(self) -> None:
        order = LabOrderDomain(
            patient_id="p-1",
            test_type="CBC",
            lab_id="lab-1",
        )
        result = await self.service.validate_new_order(order, self.mock_patient_repo)
        assert result.created_at is not None


# ---------------------------------------------------------------------------
# ResultValidationService tests
# ---------------------------------------------------------------------------


class TestResultValidationService:
    def setup_method(self) -> None:
        self.service = ResultValidationService()
        self.mock_order_repo = MagicMock(spec=OrderRepository)
        self.mock_order_repo.get_by_id = AsyncMock(
            return_value=LabOrderDomain(
                order_id="o-1",
                patient_id="p-1",
                test_type="CBC",
                lab_id="lab-1",
            ),
        )

    async def test_validate_valid_result(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("7.5"),
            unit="x10^9/L",
        )
        validated = await self.service.validate_result(result, self.mock_order_repo)
        assert validated.analyte == "WBC"

    async def test_validate_missing_order_raises(self) -> None:
        self.mock_order_repo.get_by_id = AsyncMock(return_value=None)
        result = LabResultDomain(
            order_id="o-nonexistent",
            analyte="WBC",
            value=Decimal("7.5"),
            unit="x10^9/L",
        )
        with pytest.raises(InvalidOrderError):
            await self.service.validate_result(result, self.mock_order_repo)

    async def test_validate_negative_value_raises(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal(-1),
            unit="x10^9/L",
        )
        with pytest.raises(InvalidOrderError):
            await self.service.validate_result(result, self.mock_order_repo)

    async def test_validate_empty_analyte_raises(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="",
            value=Decimal("7.5"),
            unit="x10^9/L",
        )
        with pytest.raises(InvalidOrderError):
            await self.service.validate_result(result, self.mock_order_repo)

    async def test_validate_empty_unit_raises(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("7.5"),
            unit="",
        )
        with pytest.raises(InvalidOrderError):
            await self.service.validate_result(result, self.mock_order_repo)

    def test_check_normal_result(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("7.5"),
            unit="x10^9/L",
            reference_range=ReferenceRange(
                analyte="WBC",
                unit="x10^9/L",
                min_value=Decimal("4.0"),
                max_value=Decimal("11.0"),
            ),
        )
        checked = self.service.check_critical(result)
        assert checked.is_critical is False
        assert checked.flagged == "طبيعي"

    def test_check_high_result(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("14.0"),
            unit="x10^9/L",
            reference_range=ReferenceRange(
                analyte="WBC",
                unit="x10^9/L",
                min_value=Decimal("4.0"),
                max_value=Decimal("11.0"),
            ),
        )
        checked = self.service.check_critical(result)
        assert checked.is_critical is False
        assert checked.flagged == "مرتفع"

    def test_check_low_result(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("2.0"),
            unit="x10^9/L",
            reference_range=ReferenceRange(
                analyte="WBC",
                unit="x10^9/L",
                min_value=Decimal("4.0"),
                max_value=Decimal("11.0"),
            ),
        )
        checked = self.service.check_critical(result)
        assert checked.is_critical is False
        assert checked.flagged == "منخفض"

    def test_check_critical_high_raises(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="Potassium",
            value=Decimal("7.0"),
            unit="mmol/L",
            reference_range=ReferenceRange(
                analyte="Potassium",
                unit="mmol/L",
                min_value=Decimal("3.5"),
                max_value=Decimal("5.5"),
                min_critical=Decimal("2.5"),
                max_critical=Decimal("6.5"),
            ),
        )
        with pytest.raises(CriticalResultError) as exc:
            self.service.check_critical(result)
        assert "Potassium" in str(exc.value)

    def test_check_critical_low_raises(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="Potassium",
            value=Decimal("2.0"),
            unit="mmol/L",
            reference_range=ReferenceRange(
                analyte="Potassium",
                unit="mmol/L",
                min_value=Decimal("3.5"),
                max_value=Decimal("5.5"),
                min_critical=Decimal("2.5"),
                max_critical=Decimal("6.5"),
            ),
        )
        with pytest.raises(CriticalResultError) as exc:
            self.service.check_critical(result)
        assert "Potassium" in str(exc.value)

    def test_check_no_reference_range(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="WBC",
            value=Decimal("7.5"),
            unit="x10^9/L",
            reference_range=None,
        )
        checked = self.service.check_critical(result)
        assert checked.is_critical is False
        assert checked.flagged == "طبيعي"

    def test_bulk_check_critical(self) -> None:
        results = [
            LabResultDomain(
                order_id="o-1",
                analyte="WBC",
                value=Decimal("7.5"),
                unit="x10^9/L",
                reference_range=ReferenceRange(
                    analyte="WBC",
                    unit="x10^9/L",
                    min_value=Decimal("4.0"),
                    max_value=Decimal("11.0"),
                ),
            ),
            LabResultDomain(
                order_id="o-1",
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
            ),
        ]
        flagged = ResultValidationService.bulk_check_critical(results)
        assert len(flagged) == 1
        assert flagged[0].analyte == "Potassium"
        assert flagged[0].is_critical is True

    def test_check_critical_edge_exact_boundary(self) -> None:
        result = LabResultDomain(
            order_id="o-1",
            analyte="Potassium",
            value=Decimal("6.5"),
            unit="mmol/L",
            reference_range=ReferenceRange(
                analyte="Potassium",
                unit="mmol/L",
                min_value=Decimal("3.5"),
                max_value=Decimal("5.5"),
                max_critical=Decimal("6.5"),
            ),
        )
        with pytest.raises(CriticalResultError):
            self.service.check_critical(result)
