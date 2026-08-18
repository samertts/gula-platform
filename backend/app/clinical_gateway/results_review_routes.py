from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.results_review_service import ResultsReviewService
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.models.lab_order import LabOrder

router = APIRouter(prefix="/api/v1/clinical", tags=["Canonical Clinical Result Review"])


class ResultReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    decision: str = Field(min_length=1, max_length=24)
    note: str | None = Field(default=None, max_length=1000)


@router.post("/orders/{order_id}/results/{result_id}/review")
def review_result(
    order_id: int,
    result_id: int,
    payload: ResultReviewRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        order = db.get(LabOrder, order_id)
        if order is None or order.patient_id is None:
            raise ClinicalGatewayBlocked("result_order_not_found")
        gateway = ClinicalGatewayContextResolver(db).resolve(actor)
        access = ClinicalAccessContext.from_gateway_for_patient(
            db,
            gateway,
            patient_id=int(order.patient_id),
            purpose="results.review",
            permissions=frozenset({"validate"}),
        )
        result = ResultsReviewService(db).review(
            access=access,
            order_id=order_id,
            result_id=result_id,
            expected_version=payload.expected_version,
            decision=payload.decision,
            note=payload.note,
        )
        db.commit()
        return ResultsReviewService.to_safe_dict(result)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Result review is not authorized") from exc
