"""Lab device integration - receive results from analyzers."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..domain.sample_state import enforce_transition as enforce_sample_transition
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..models.sample import Sample
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_public
from ..services.audit_service import log_action
from ..services.interpretation import get_flag

router = APIRouter(prefix="/device", tags=["device"])


class DeviceResult(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class DeviceSubmission(BaseModel):
    barcode: str  # sample barcode to match
    device_id: str | None = None
    results: list[DeviceResult]


@router.post("/results")
def receive_device_results(
    data: DeviceSubmission,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive results from a lab analyzer device.

    Matches results to an order via sample barcode, creates lab results,
    and updates sample status to 'analyzed'.
    """
    # Rate limit device submissions (max 100 per minute per IP)
    rate_limit_public(request, max_per_minute=100)

    # Limit number of results per submission
    if len(data.results) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 results per submission")

    # Find sample by barcode
    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(
            Sample.barcode == data.barcode,
            LabOrder.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    # Raises ConflictError (409) for any sample already in a terminal state
    # (rejected, or already analyzed) — closes a duplicate-ingestion gap
    # where a replayed/retried device submission could silently re-process
    # an already-analyzed sample and create duplicate LabResult rows with
    # no idempotency protection at all.
    sample_status_at_read = sample.status
    enforce_sample_transition(sample_status_at_read, "analyzed")

    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()

    from ..domain.order_state import assert_not_cancelled, assert_not_locked, enforce_transition

    assert_not_locked(order)
    assert_not_cancelled(order)
    order_status_at_read = order.status
    enforce_transition(order_status_at_read, "completed")

    # Atomic backstop for both mutations below, applied *before* any
    # LabResult rows are created so a lost race leaves nothing to unwind.
    # Reuses the same CAS pattern as services/order_service.py::cancel_order
    # and routes/samples.py::update_sample: LabOrder's existing
    # locked_at/version columns for the order, and Sample.status itself as
    # the compare-and-swap token for the sample (Sample has no version
    # column — see MUSTAFA_ACTIVE_REPAIR_QUEUE.md). Without this, a
    # concurrent cancel/validate of the same order, or a second concurrent
    # device submission for the same sample, raced between the sequential
    # checks above and the plain attribute assignments this replaced would
    # silently win.
    order_rows = (
        db.query(LabOrder)
        .filter(
            LabOrder.id == order.id,
            LabOrder.locked_at.is_(None),
            LabOrder.status == order_status_at_read,
        )
        .update(
            {"status": "completed", "version": LabOrder.version + 1},
            synchronize_session="fetch",
        )
    )
    if order_rows == 0:
        raise HTTPException(status_code=409, detail="Order changed concurrently; re-submit")

    sample_rows = (
        db.query(Sample)
        .filter(Sample.id == sample.id, Sample.status == sample_status_at_read)
        .update({"status": "analyzed"}, synchronize_session="fetch")
    )
    if sample_rows == 0:
        raise HTTPException(status_code=409, detail="Sample changed concurrently; re-submit")

    created = []
    for item in data.results:
        flag = None
        if (
            item.value is not None
            and item.normal_range_low is not None
            and item.normal_range_high is not None
        ):
            flag = get_flag(
                item.value, item.normal_range_low, item.normal_range_high, test_name=item.test_name,
            )

        import secrets

        from ..models.lab_result import hash_token

        token = secrets.token_urlsafe(32)

        result = LabResult(
            order_id=order.id,
            test_name=item.test_name,
            value=item.value,
            value_text=item.value_text,
            unit=item.unit,
            normal_range_low=item.normal_range_low,
            normal_range_high=item.normal_range_high,
            flag=flag,
            token=token,
            token_hash=hash_token(token),
        )
        db.add(result)
        created.append({"test": item.test_name, "token": token})

    log_action(
        db,
        action="device_results",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Device {data.device_id or 'unknown'}: {len(created)} results via barcode {data.barcode}",
    )
    db.commit()

    return {
        "message": f"{len(created)} results added from device",
        "barcode": data.barcode,
        "order_id": order.id,
        "results": created,
    }
