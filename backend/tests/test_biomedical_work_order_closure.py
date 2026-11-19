"""A biomedical work order closes once, for its own tenant, and only returns a
device to service when the device is actually safe to use.

THE THREE DEFECTS, all reproduced against real PostgreSQL before the repair.

`BiomedicalService.complete_work_order` was:

    model = self.db.query(WorkOrderModel).filter_by(id=wo_id).first()
    if not model:
        raise WorkOrderNotFoundError()
    model.status = WorkOrderStatus.COMPLETED.value
    ...
    if model.device_id:
        device = self.db.query(MedicalDeviceModel).filter_by(id=model.device_id).first()
        if device:
            device.status = DeviceStatus.AVAILABLE.value

1. NO TENANT SCOPE. `filter_by(id=wo_id)` selected across every laboratory, and
   the service had no tenant context at all to scope it with. Reproduced: a
   caller acting for lab A completed lab B's work order and flipped lab B's
   device to available.

2. A DEVICE WAS RETURNED TO CLINICAL SERVICE ON THE STRENGTH OF ONE TICKET.
   Closing any work order set `device.status = AVAILABLE` unconditionally.
   Reproduced: a class III ventilator held `out_of_service` with two open work
   orders became `available` when only the first was completed — the second
   fault was never touched. This is the reason the repair is not cosmetic:
   returning a device to service is a clinical-safety decision, and closing one
   ticket says nothing about the faults the other tickets were raised for.

3. NO ROW LOCK AND NO TERMINAL-STATE GUARD. Reproduced with two real
   PostgreSQL sessions released from a barrier: both committed the same
   terminal transition, the later write silently overwrote the earlier one's
   cost and action record, and `version` never moved off 1 even though the
   model carries the optimistic-lock column.

THE REPAIR mirrors the mechanism this platform already uses elsewhere: select
the row `.with_for_update()`, refuse a repeat of a terminal transition, scope
every read to the authenticated subject's tenant, and bump `version`.

`actor_lab_id` is keyword-only with no default, so a caller that forgets it
raises TypeError rather than silently reaching across tenants. A default would
reinstate exactly the defect being fixed.

EVIDENCE LEVEL. These tests need real PostgreSQL: defect 3 is row-lock
behaviour under genuine concurrent transactions, which SQLite cannot reproduce.
They skip, never pass, when BIOMED_POSTGRES_URL is unset.
"""

from __future__ import annotations

import inspect
import os
import threading
from datetime import UTC, datetime

import pytest
from app.biomedical.application.service import BiomedicalService
from app.biomedical.exceptions import (
    WorkOrderAlreadyClosedError,
    WorkOrderNotFoundError,
)
from app.biomedical.infrastructure.models import MedicalDeviceModel, WorkOrderModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = os.getenv("BIOMED_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="BIOMED_POSTGRES_URL is not configured"
)

LAB_A, LAB_B = 8801, 8802


@pytest.fixture(scope="module")
def Session():
    engine = create_engine(POSTGRES_URL, future=True)
    for model in (MedicalDeviceModel, WorkOrderModel):
        model.__table__.create(engine, checkfirst=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def clean(Session):
    def _wipe():
        with Session() as s:
            s.execute(text("DELETE FROM biomed_work_orders"))
            s.execute(text("DELETE FROM biomed_devices"))
            s.commit()

    _wipe()
    yield
    _wipe()


def _seed(Session, *, lab=LAB_A, device_status="out_of_service", n_orders=1, tag="t"):
    with Session() as s:
        device = MedicalDeviceModel(
            lab_id=lab, device_name="Ventilator VX-9", risk_class="class_iii",
            serial_number=f"SN-{lab}-{tag}", status=device_status,
        )
        s.add(device)
        s.flush()
        order_ids = []
        for i in range(n_orders):
            order = WorkOrderModel(
                lab_id=lab, device_id=device.id, status="in_progress",
                work_order_number=f"WO-{lab}-{tag}-{i}",
                reported_date=datetime.now(UTC), title=f"fault {i}",
            )
            s.add(order)
            s.flush()
            order_ids.append(order.id)
        s.commit()
        return device.id, order_ids


def test_a_actor_lab_id_is_required_and_keyword_only():
    """The structural control, and the positive control for the module.

    If the parameter did not exist the behavioural tests could pass for reasons
    unrelated to tenancy.
    """
    params = inspect.signature(BiomedicalService.complete_work_order).parameters
    assert "actor_lab_id" in params
    assert params["actor_lab_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["actor_lab_id"].default is inspect.Parameter.empty, (
        "a default would let a caller silently complete another tenant's work order"
    )


def test_b_a_work_order_can_be_completed_by_its_own_tenant(Session, clean):
    """Positive control. Without it, a method that refused everything would pass
    every assertion below while being useless."""
    device_id, orders = _seed(Session, tag="b")
    with Session() as s:
        result = BiomedicalService(s).complete_work_order(
            orders[0], {"action_taken": "replaced sensor"}, actor_lab_id=LAB_A,
        )
    assert result.status == "completed"

    with Session() as s:
        assert s.get(WorkOrderModel, orders[0]).status == "completed"
        # Sole open fault cleared, so the device legitimately returns to service.
        assert s.get(MedicalDeviceModel, device_id).status == "available"


def test_c_another_tenants_work_order_is_not_reachable(Session, clean):
    """Defect 1. The work order belongs to lab B; the caller acts for lab A."""
    device_id, orders = _seed(Session, lab=LAB_B, tag="c")

    with Session() as s, pytest.raises(WorkOrderNotFoundError):
        BiomedicalService(s).complete_work_order(
            orders[0], {"action_taken": "wrong lab"}, actor_lab_id=LAB_A,
        )

    with Session() as s:
        assert s.get(WorkOrderModel, orders[0]).status == "in_progress"
        assert s.get(MedicalDeviceModel, device_id).status == "out_of_service", (
            "lab A's call must not have touched lab B's device"
        )


def test_d_device_stays_out_of_service_while_another_fault_is_open(Session, clean):
    """Defect 2 — the clinical-safety one.

    Two open work orders on one class III device. Completing the first says
    nothing about the second, so the device must not return to service.
    """
    device_id, orders = _seed(Session, n_orders=2, tag="d")

    with Session() as s:
        BiomedicalService(s).complete_work_order(
            orders[0], {"action_taken": "fixed fault 0 only"}, actor_lab_id=LAB_A,
        )

    with Session() as s:
        device = s.get(MedicalDeviceModel, device_id)
        still_open = (
            s.query(WorkOrderModel)
            .filter(
                WorkOrderModel.device_id == device_id,
                WorkOrderModel.status.notin_(["completed", "verified", "cancelled"]),
            )
            .count()
        )
        assert still_open == 1
        assert device.status == "out_of_service", (
            f"device is {device.status!r} with {still_open} fault(s) still open — "
            "an unsafe device was returned to clinical service"
        )

    # Closing the last open fault does release it.
    with Session() as s:
        BiomedicalService(s).complete_work_order(
            orders[1], {"action_taken": "fixed fault 1"}, actor_lab_id=LAB_A,
        )
    with Session() as s:
        assert s.get(MedicalDeviceModel, device_id).status == "available"


def test_e_a_closed_work_order_cannot_be_closed_again(Session, clean):
    """Defect 3, sequentially: the terminal-state guard."""
    _, orders = _seed(Session, tag="e")
    with Session() as s:
        BiomedicalService(s).complete_work_order(
            orders[0], {"action_taken": "first", "cost_parts": 100.0, "cost_labor": 0},
            actor_lab_id=LAB_A,
        )
    with Session() as s, pytest.raises(WorkOrderAlreadyClosedError):
        BiomedicalService(s).complete_work_order(
            orders[0], {"action_taken": "second", "cost_parts": 999.0, "cost_labor": 0},
            actor_lab_id=LAB_A,
        )
    with Session() as s:
        order = s.get(WorkOrderModel, orders[0])
        assert order.cost_total == 100.0, "the refused repeat overwrote the real record"
        assert order.action_taken == "first"


def test_f_two_concurrent_completions_commit_exactly_once(Session, clean):
    """Defect 3, concurrently — the reason this module needs PostgreSQL.

    Two real sessions, released together from a barrier, race the same terminal
    transition. `with_for_update()` serialises them; the terminal-state guard
    then refuses the loser. Before the repair both committed and the later cost
    silently replaced the earlier one.
    """
    device_id, orders = _seed(Session, tag="f")
    barrier = threading.Barrier(2)
    outcomes: list[tuple[str, str]] = []
    lock = threading.Lock()

    def attempt(tag: str, cost: float) -> None:
        with Session() as s:
            service = BiomedicalService(s)
            barrier.wait(timeout=10)
            try:
                service.complete_work_order(
                    orders[0], {"action_taken": tag, "cost_parts": cost, "cost_labor": 0},
                    actor_lab_id=LAB_A,
                )
                verdict = "committed"
            except WorkOrderAlreadyClosedError:
                verdict = "refused"
            with lock:
                outcomes.append((tag, verdict))

    threads = [
        threading.Thread(target=attempt, args=("T1", 100.0)),
        threading.Thread(target=attempt, args=("T2", 999.0)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    committed = [t for t, v in outcomes if v == "committed"]
    refused = [t for t, v in outcomes if v == "refused"]
    assert len(committed) == 1, f"a terminal transition committed {len(committed)} times: {outcomes}"
    assert len(refused) == 1, f"expected exactly one refusal: {outcomes}"

    with Session() as s:
        order = s.get(WorkOrderModel, orders[0])
        assert order.status == "completed"
        assert order.version == 2, "the optimistic-lock column must advance on the transition"
        # The record belongs to whichever transaction won; it must not be a blend.
        assert order.cost_total in (100.0, 999.0)
        assert order.action_taken == ("T1" if order.cost_total == 100.0 else "T2")
        assert s.get(MedicalDeviceModel, device_id).status == "available"
