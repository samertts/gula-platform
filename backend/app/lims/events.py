"""National LIMS domain events — all events emitted by LIMS operations.

Every event is a simple dataclass that gets serialised into the
transactional outbox (OutboxEvent) for guaranteed delivery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LIMSEvent:
    """Base LIMS event with standard envelope fields."""

    event_type: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    lab_id: int | None = None
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Specimen Lifecycle Events ──────────────────────────────────────────

class SpecimenOrdered(LIMSEvent):
    event_type = "lims.specimen.ordered"

class SpecimenRegistered(LIMSEvent):
    event_type = "lims.specimen.registered"

class SpecimenCollected(LIMSEvent):
    event_type = "lims.specimen.collected"

class SpecimenTransporting(LIMSEvent):
    event_type = "lims.specimen.transporting"

class SpecimenReceived(LIMSEvent):
    event_type = "lims.specimen.received"

class SpecimenAccepted(LIMSEvent):
    event_type = "lims.specimen.accepted"

class SpecimenRejected(LIMSEvent):
    event_type = "lims.specimen.rejected"

class SpecimenAliquoted(LIMSEvent):
    event_type = "lims.specimen.aliquoted"

class SpecimenAnalysisStarted(LIMSEvent):
    event_type = "lims.specimen.analysis_started"

class SpecimenAnalyzed(LIMSEvent):
    event_type = "lims.specimen.analyzed"

class SpecimenVerified(LIMSEvent):
    event_type = "lims.specimen.verified"

class SpecimenValidated(LIMSEvent):
    event_type = "lims.specimen.validated"

class SpecimenReleased(LIMSEvent):
    event_type = "lims.specimen.released"

class SpecimenArchived(LIMSEvent):
    event_type = "lims.specimen.archived"

class SpecimenDisposed(LIMSEvent):
    event_type = "lims.specimen.disposed"


# ── Order Lifecycle Events ─────────────────────────────────────────────

class OrderAccessioned(LIMSEvent):
    event_type = "lims.order.accessioned"

class OrderCompleted(LIMSEvent):
    event_type = "lims.order.completed"

class OrderValidated(LIMSEvent):
    event_type = "lims.order.validated"

class OrderReleased(LIMSEvent):
    event_type = "lims.order.released"

class OrderCancelled(LIMSEvent):
    event_type = "lims.order.cancelled"

class OrderCorrected(LIMSEvent):
    event_type = "lims.order.corrected"


# ── Result Events ──────────────────────────────────────────────────────

class ResultCreated(LIMSEvent):
    event_type = "lims.result.created"

class ResultUpdated(LIMSEvent):
    event_type = "lims.result.updated"

class ResultAutoValidated(LIMSEvent):
    event_type = "lims.result.auto_validated"

class ResultValidated(LIMSEvent):
    event_type = "lims.result.validated"

class ResultFlagged(LIMSEvent):
    event_type = "lims.result.flagged"

class CriticalResultDetected(LIMSEvent):
    event_type = "lims.result.critical"

class DeltaCheckFailed(LIMSEvent):
    event_type = "lims.result.delta_check_failed"


# ── Quality Events ─────────────────────────────────────────────────────

class IQCRun(LIMSEvent):
    event_type = "lims.qc.iqc_run"

class IQCOutOfControl(LIMSEvent):
    event_type = "lims.qc.iqc_out_of_control"

class EQASubmitted(LIMSEvent):
    event_type = "lims.qc.eqa_submitted"

class EQAResultReceived(LIMSEvent):
    event_type = "lims.qc.eqa_result_received"

class CalibrationPerformed(LIMSEvent):
    event_type = "lims.qc.calibration_performed"

class CalibrationFailed(LIMSEvent):
    event_type = "lims.qc.calibration_failed"


# ── Instrument Events ──────────────────────────────────────────────────

class InstrumentOnline(LIMSEvent):
    event_type = "lims.instrument.online"

class InstrumentOffline(LIMSEvent):
    event_type = "lims.instrument.offline"

class InstrumentError(LIMSEvent):
    event_type = "lims.instrument.error"

class MaintenanceDue(LIMSEvent):
    event_type = "lims.instrument.maintenance_due"

class MaintenancePerformed(LIMSEvent):
    event_type = "lims.instrument.maintenance_performed"


# ── Inventory Events ───────────────────────────────────────────────────

class ReagentLow(LIMSEvent):
    event_type = "lims.inventory.reagent_low"

class LotExpiring(LIMSEvent):
    event_type = "lims.inventory.lot_expiring"

class LotExpired(LIMSEvent):
    event_type = "lims.inventory.lot_expired"


# ── Report Events ──────────────────────────────────────────────────────

class ReportGenerated(LIMSEvent):
    event_type = "lims.report.generated"

class ReportFinalized(LIMSEvent):
    event_type = "lims.report.finalized"

class ReportCorrected(LIMSEvent):
    event_type = "lims.report.corrected"
