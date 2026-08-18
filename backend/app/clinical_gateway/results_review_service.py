from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult


class ResultsReviewService:
    def __init__(self, db: Session):
        self.db = db

    def review(
        self,
        *,
        access: ClinicalAccessContext,
        order_id: int,
        result_id: int,
        expected_version: int,
        decision: str,
        note: str | None = None,
    ) -> LabResult:
        access.require_operation("validate")
        if decision not in {"ACCEPTED", "REJECTED"}:
            raise ClinicalGatewayBlocked("invalid_result_review_decision")
        order = (
            self.db.query(LabOrder)
            .filter(
                LabOrder.id == order_id,
                LabOrder.lab_id == access.legacy_lab_id,
                LabOrder.tenant_id == access.tenant_id,
                LabOrder.organization_id == access.operational_organization_id,
                LabOrder.facility_id == access.operational_facility_id,
                LabOrder.workspace_id == access.workspace_id,
            )
            .one_or_none()
        )
        if order is None:
            raise ClinicalGatewayBlocked("result_order_scope_denied")
        result = (
            self.db.query(LabResult)
            .filter(LabResult.id == result_id, LabResult.order_id == order_id)
            .one_or_none()
        )
        if result is None:
            raise ClinicalGatewayBlocked("result_scope_denied")
        if result.version != expected_version:
            raise ClinicalGatewayBlocked("result_version_conflict")
        if result.review_status != "UNREVIEWED":
            raise ClinicalGatewayBlocked("result_review_immutable")
        result.review_status = decision
        result.reviewed_by = str(access.legacy_user_id)
        result.reviewed_at = datetime.now(UTC)
        result.review_note = note.strip() if note and note.strip() else None
        result.version = expected_version + 1
        self.db.flush()
        return result

    @staticmethod
    def to_safe_dict(result: LabResult) -> dict[str, Any]:
        return {
            "id": result.id,
            "order_id": result.order_id,
            "test_name": result.test_name,
            "value": result.value,
            "value_text": result.value_text,
            "unit": result.unit,
            "flag": result.flag,
            "review_status": result.review_status,
            "reviewed_by": result.reviewed_by,
            "reviewed_at": result.reviewed_at,
            "review_note": result.review_note,
            "version": result.version,
        }
