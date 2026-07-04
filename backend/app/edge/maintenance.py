"""Background maintenance loops for the edge plane.

These run inside the FastAPI process under the existing `_spawn(...)` helper:
no new process, no new dependencies. They do three things on a slow timer:

  - reap stale dispatched tasks (timeouts → re-queue or fail)
  - mark devices that haven't heartbeated in EDGE_HEARTBEAT_TIMEOUT_S as offline
  - prune old telemetry rows past retention

Loops are defensive — a single failure in any branch logs and continues so a
transient DB hiccup does not poison the whole worker.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from ..database import SessionLocal
from ..models.edge import EdgeDevice, EdgeEvent
from . import scheduler
from . import telemetry as tele
from .config import EDGE_HEARTBEAT_TIMEOUT_S

logger = logging.getLogger("gula.edge.maintenance")


async def edge_maintenance_loop(interval_s: int = 30) -> None:
    """Run reaper + offline marking + telemetry sweep on a slow timer."""
    await asyncio.sleep(60)  # let startup settle
    sweep_counter = 0

    while True:
        try:

            def _run_maintenance(sweep_count: int):
                db = SessionLocal()
                try:
                    n_stale = scheduler.sweep_stale(db)
                    n_off = _mark_offline_devices(db)
                    # Telemetry sweep is expensive — every 60th tick (~30 min)
                    n_tele = tele.sweep_old(db) if sweep_count % 60 == 0 else 0
                    db.commit()
                    return n_stale, n_off, n_tele
                except Exception as exc:
                    db.rollback()
                    raise exc
                finally:
                    db.close()

            loop = asyncio.get_event_loop()
            n_stale, n_off, n_tele = await loop.run_in_executor(
                None, _run_maintenance, sweep_counter
            )
            if n_stale or n_off or n_tele:
                logger.info(
                    "edge maintenance: stale=%d offline=%d tele_pruned=%d",
                    n_stale,
                    n_off,
                    n_tele,
                )
        except Exception as exc:
            logger.warning("edge maintenance error: %s", exc)

        sweep_counter += 1
        await asyncio.sleep(interval_s)


def _mark_offline_devices(db) -> int:
    cutoff = datetime.now(UTC) - timedelta(seconds=EDGE_HEARTBEAT_TIMEOUT_S)
    devices = (
        db.query(EdgeDevice)
        .filter(
            EdgeDevice.status == "active",
            EdgeDevice.last_seen_at.isnot(None),
            EdgeDevice.last_seen_at < cutoff,
        )
        .all()
    )
    n = 0
    for d in devices:
        d.status = "offline"
        db.add(
            EdgeEvent(
                lab_id=d.lab_id,
                device_id=d.device_id,
                event_type="device_offline",
                severity="warning",
                details={"last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None},
            )
        )
        n += 1
    return n
