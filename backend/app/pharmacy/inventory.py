from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, cast

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.pharmacy.enums import StockMovementType, StorageCondition
from app.pharmacy.models import (
    DrugBatch,
    DrugCatalog,
    InventoryForecast,
    Recall,
    StockLevel,
    StockMovement,
)
from app.services.audit_service import log_action

logger = logging.getLogger("gula.pharmacy.inventory")


class StockAdjustmentService:
    """Server-authoritative stock changes.

    Every quantity change writes both the new :class:`StockLevel` state and an
    append-only :class:`StockMovement`, in one transaction, so the movement log
    always explains the level. Quantities are floats because the physical
    columns are ``DOUBLE PRECISION``: a dispensed amount can be fractional
    (half a tablet, millilitres) and an integer would silently truncate it.

    Identifiers here are INTERNAL keys. Callers holding a public identifier
    resolve it first; the internal key is never a public identity (contract §3).
    """

    def __init__(self, db: Session, user_id: int | None = None, lab_id: int | None = None):
        self.db = db
        self.user_id = user_id
        self.lab_id = lab_id

    def _audit(self, action: str, resource_type: str, resource_id: str | None = None, details: str | None = None):
        log_action(
            db=self.db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=self.user_id,
            details=details,
        )

    def _actor(self) -> int:
        """The user a movement is attributed to.

        ``pharmacy_stock_movements.performed_by`` is NOT NULL: an inventory
        change is always somebody's action. Failing here is better than letting
        the database reject the write after the level has been recomputed.
        """
        if self.user_id is None:
            raise ValueError("a stock movement requires an acting user")
        return self.user_id

    def _stock_row(
        self, drug_id: int, batch_id: int | None, warehouse_id: int | None, store_id: int | None
    ) -> StockLevel | None:
        query = self.db.query(StockLevel).filter(
            StockLevel.drug_id == drug_id,
            StockLevel.batch_id == batch_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.store_id == store_id,
            ~StockLevel.is_deleted,
        )
        if self.lab_id is not None:
            query = query.filter(StockLevel.lab_id == self.lab_id)
        # Serialise concurrent adjustments of the same row: two callers must not
        # both read the same quantity and each write their own total back.
        return cast(StockLevel | None, query.with_for_update().first())

    def _record_movement(
        self,
        *,
        drug_id: int,
        batch_id: int | None,
        movement_type: StockMovementType,
        quantity: float,
        unit: str,
        reason: str,
        reference_type: str | None = None,
        reference_id: int | None = None,
    ) -> StockMovement:
        movement = StockMovement(
            lab_id=self.lab_id,
            drug_id=drug_id,
            batch_id=batch_id,
            movement_type=movement_type.value,
            quantity=quantity,
            unit=unit,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=self._actor(),
            performed_at=datetime.now(UTC),
        )
        self.db.add(movement)
        return movement

    def add_stock(
        self,
        drug_id: int,
        batch_id: int,
        quantity: float,
        warehouse_id: int | None = None,
        store_id: int | None = None,
        reason: str = "Stock receipt",
        unit: str = "unit",
    ) -> StockLevel:
        if quantity <= 0:
            raise ValueError("stock quantity must be positive")
        if self.lab_id is None:
            raise ValueError("institutional pharmacy context is required")

        stock = self._stock_row(drug_id, batch_id, warehouse_id, store_id)
        if stock:
            stock.quantity_on_hand += quantity
            stock.quantity_available = stock.quantity_on_hand - (stock.quantity_reserved or 0)
        else:
            stock = StockLevel(
                lab_id=self.lab_id,
                drug_id=drug_id,
                batch_id=batch_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                quantity_on_hand=quantity,
                quantity_reserved=0,
                quantity_available=quantity,
                unit=unit,
            )
            self.db.add(stock)
        self.db.flush()

        self._record_movement(
            drug_id=drug_id,
            batch_id=batch_id,
            movement_type=StockMovementType.RECEIVED,
            quantity=quantity,
            unit=unit,
            reason=reason,
        )
        self.db.flush()

        batch = self._batch(batch_id)
        if batch:
            batch.quantity_remaining += quantity
            self.db.flush()

        self._audit(
            "inventory.add_stock", "stock_level", str(stock.id), f"Added {quantity} units: {reason}"
        )
        return stock

    def remove_stock(
        self,
        drug_id: int,
        batch_id: int,
        quantity: float,
        warehouse_id: int | None = None,
        store_id: int | None = None,
        reason: str = "Stock removal",
        movement_type: StockMovementType = StockMovementType.DISPENSED,
        unit: str = "unit",
    ) -> StockLevel | None:
        if quantity <= 0:
            raise ValueError("stock quantity must be positive")

        stock = self._stock_row(drug_id, batch_id, warehouse_id, store_id)
        if not stock or stock.quantity_available < quantity:
            logger.warning(
                "Insufficient stock for removal: have %s, need %s",
                stock.quantity_available if stock else 0,
                quantity,
            )
            return None

        stock.quantity_on_hand -= quantity
        stock.quantity_available = stock.quantity_on_hand - (stock.quantity_reserved or 0)
        self.db.flush()

        self._record_movement(
            drug_id=drug_id,
            batch_id=batch_id,
            movement_type=movement_type,
            quantity=quantity,
            unit=stock.unit or unit,
            reason=reason,
        )
        self.db.flush()

        batch = self._batch(batch_id)
        if batch:
            batch.quantity_remaining = max(0.0, batch.quantity_remaining - quantity)
            self.db.flush()

        self._audit(
            "inventory.remove_stock", "stock_level", str(stock.id), f"Removed {quantity} units: {reason}"
        )
        return stock

    def adjust_stock(
        self,
        drug_id: int,
        batch_id: int,
        new_quantity: float,
        warehouse_id: int | None = None,
        store_id: int | None = None,
        reason: str = "Physical count adjustment",
        unit: str = "unit",
    ) -> StockLevel:
        if new_quantity < 0:
            raise ValueError("counted stock cannot be negative")
        if self.lab_id is None:
            raise ValueError("institutional pharmacy context is required")

        stock = self._stock_row(drug_id, batch_id, warehouse_id, store_id)
        if stock:
            delta = new_quantity - stock.quantity_on_hand
            stock.quantity_on_hand = new_quantity
            stock.quantity_available = new_quantity - (stock.quantity_reserved or 0)
            stock.last_counted_at = datetime.now(UTC)
            stock.last_counted_by = self.user_id
        else:
            stock = StockLevel(
                lab_id=self.lab_id,
                drug_id=drug_id,
                batch_id=batch_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                quantity_on_hand=new_quantity,
                quantity_reserved=0,
                quantity_available=new_quantity,
                unit=unit,
                last_counted_at=datetime.now(UTC),
                last_counted_by=self.user_id,
            )
            self.db.add(stock)
            delta = new_quantity
        self.db.flush()

        if delta != 0:
            self._record_movement(
                drug_id=drug_id,
                batch_id=batch_id,
                movement_type=StockMovementType.ADJUSTED,
                quantity=abs(delta),
                unit=stock.unit or unit,
                reason=reason,
            )
            self.db.flush()

            batch = self._batch(batch_id)
            if batch:
                batch.quantity_remaining = max(0.0, batch.quantity_remaining + delta)
                self.db.flush()

        self._audit(
            "inventory.adjust_stock", "stock_level", str(stock.id), f"Set to {new_quantity}: {reason}"
        )
        return stock

    def _batch(self, batch_id: int | None) -> DrugBatch | None:
        if batch_id is None:
            return None
        query = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id, ~DrugBatch.is_deleted)
        if self.lab_id is not None:
            query = query.filter(DrugBatch.lab_id == self.lab_id)
        return cast(DrugBatch | None, query.with_for_update().first())


class ExpiryMonitoringService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def _batch_summary(self, batch: DrugBatch) -> dict[str, Any]:
        """Public shape of a batch. Identifiers are public, never internal keys."""
        drug = batch.drug
        return {
            "batch_id": str(batch.batch_id),
            "drug_catalog_id": str(drug.drug_id) if drug else None,
            "drug_name": drug.drug_name if drug else "Unknown",
            "drug_name_ar": drug.drug_name_ar if drug else None,
            "batch_number": batch.batch_number,
            "expiry_date": batch.expiry_date.isoformat(),
            "quantity_remaining": batch.quantity_remaining,
            "storage_condition": batch.storage_condition,
            "is_quarantined": bool(batch.is_quarantined),
        }

    def get_expiring_batches(self, within_days: int = 90) -> list[dict[str, Any]]:
        cutoff = date.today() + timedelta(days=within_days)
        q = self.db.query(DrugBatch).filter(
            DrugBatch.expiry_date <= cutoff,
            DrugBatch.expiry_date >= date.today(),
            ~DrugBatch.is_deleted,
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)

        results: list[dict[str, Any]] = []
        for batch in q.order_by(DrugBatch.expiry_date).all():
            summary = self._batch_summary(batch)
            summary["days_remaining"] = (batch.expiry_date - date.today()).days
            results.append(summary)
        return results

    def get_expired_batches(self) -> list[dict[str, Any]]:
        q = self.db.query(DrugBatch).filter(
            DrugBatch.expiry_date < date.today(),
            ~DrugBatch.is_deleted,
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)

        results: list[dict[str, Any]] = []
        for batch in q.order_by(DrugBatch.expiry_date).all():
            summary = self._batch_summary(batch)
            summary["days_expired"] = (date.today() - batch.expiry_date).days
            results.append(summary)
        return results

    def auto_quarantine_expired(self) -> int:
        expired = self.db.query(DrugBatch).filter(
            DrugBatch.expiry_date < date.today(),
            ~DrugBatch.is_deleted,
            # Previously `not DrugBatch.is_quarantined`, which is Python's `not`
            # applied to a column object rather than a SQL predicate. The column
            # is nullable, so `isnot(True)` is what selects "not quarantined",
            # including the rows where the flag was never set.
            DrugBatch.is_quarantined.isnot(True),
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            expired = expired.filter(DrugBatch.lab_id == self.lab_id)

        count = 0
        for batch in expired.all():
            batch.is_quarantined = True
            batch.quarantine_reason = f"expired {batch.expiry_date.isoformat()}"
            batch.status = "quarantined"
            self.db.flush()

            # Quarantined stock is not available to dispense, but it is still
            # physically on hand: only the available figure drops.
            levels = self.db.query(StockLevel).filter(
                StockLevel.batch_id == batch.id,
                ~StockLevel.is_deleted,
            ).all()
            for stock in levels:
                stock.quantity_available = 0
            self.db.flush()

            count += 1
            logger.info("Auto-quarantined batch %s (expired %s)", batch.batch_number, batch.expiry_date)

        self.db.flush()
        return count


class ReorderService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def _scoped(self, query: Any, model: Any) -> Any:
        """Inventory is tenant data: never aggregate across laboratories."""
        if self.lab_id is not None:
            query = query.filter(model.lab_id == self.lab_id)
        return query

    def calculate_reorder_quantity(
        self,
        drug_id: int,
        lead_time_days: int = 7,
        safety_stock_days: int = 3,
        average_daily_usage: float | None = None,
    ) -> dict[str, Any]:
        if average_daily_usage is None:
            average_daily_usage = self._calculate_average_usage(drug_id, days=90)

        stock = self._scoped(
            self.db.query(StockLevel).filter(
                StockLevel.drug_id == drug_id,
                ~StockLevel.is_deleted,
            ),
            StockLevel,
        ).first()

        current_stock = stock.quantity_available if stock else 0.0
        reorder_point = (
            stock.reorder_point
            if stock and stock.reorder_point
            else average_daily_usage * (lead_time_days + safety_stock_days)
        )

        if current_stock <= reorder_point:
            reorder_qty = max(
                average_daily_usage * (lead_time_days + safety_stock_days) - current_stock,
                average_daily_usage * safety_stock_days,
            )
            needs_reorder = True
        else:
            reorder_qty = 0.0
            needs_reorder = False

        maximum_level = (
            stock.maximum_level if stock and stock.maximum_level else reorder_point * 2
        )

        drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == drug_id).first()
        return {
            # The drug's public identity, not the internal foreign key.
            "drug_catalog_id": str(drug.drug_id) if drug else None,
            "current_stock": current_stock,
            "average_daily_usage": average_daily_usage,
            "lead_time_days": lead_time_days,
            "safety_stock_days": safety_stock_days,
            "reorder_point": reorder_point,
            "reorder_quantity": reorder_qty,
            "max_level": maximum_level,
            "needs_reorder": needs_reorder,
        }

    def _calculate_average_usage(self, drug_id: int, days: int = 90) -> float:
        start_date = datetime.now(UTC) - timedelta(days=days)
        result = self._scoped(
            self.db.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(
                StockMovement.drug_id == drug_id,
                StockMovement.movement_type.in_(
                    [StockMovementType.DISPENSED.value, StockMovementType.WASTED.value]
                ),
                StockMovement.performed_at >= start_date,
            ),
            StockMovement,
        ).scalar()

        return max(1.0, float(result) / days) if result else 1.0

    def generate_reorder_list(self) -> list[dict[str, Any]]:
        reorder_list: list[dict[str, Any]] = []

        # Previously `~~StockLevel.is_deleted`: the double negation cancels, so
        # the list was built from the soft-deleted rows and only those.
        drug_ids_q = self._scoped(
            self.db.query(StockLevel.drug_id).filter(
                ~StockLevel.is_deleted,
                StockLevel.reorder_point.isnot(None),
            ),
            StockLevel,
        )

        for drug_id in {row[0] for row in drug_ids_q.all()}:
            try:
                calc = self.calculate_reorder_quantity(drug_id)
            except Exception as exc:
                logger.warning("Failed to calculate reorder for drug %s: %s", drug_id, exc)
                continue
            if calc["needs_reorder"]:
                drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == drug_id).first()
                calc["drug_name"] = drug.drug_name if drug else "Unknown"
                reorder_list.append(calc)

        return sorted(reorder_list, key=lambda r: r["current_stock"] / max(r["reorder_point"], 1))


class ColdChainService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id
        self._excursions: list[dict[str, Any]] = []

    def get_cold_chain_drugs(self) -> list[dict[str, Any]]:
        q = self.db.query(DrugBatch).filter(
            # storage_condition is VARCHAR physically, so match on the enum's
            # values rather than on the enum members.
            DrugBatch.storage_condition.in_([
                StorageCondition.COLD_CHAIN.value,
                StorageCondition.REFRIGERATED.value,
                StorageCondition.FROZEN.value,
            ]),
            ~DrugBatch.is_deleted,
            # Previously `not DrugBatch.is_quarantined` — Python's `not` on a
            # column, not a SQL predicate.
            DrugBatch.is_quarantined.isnot(True),
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)

        results: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for batch in q.all():
            drug = batch.drug
            results[batch.storage_condition].append({
                "batch_id": str(batch.batch_id),
                "drug_catalog_id": str(drug.drug_id) if drug else None,
                "drug_name": drug.drug_name if drug else "Unknown",
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "quantity_remaining": batch.quantity_remaining,
                "storage_condition": batch.storage_condition,
                "location": batch.location,
            })

        return [
            {"condition": condition, "items": items}
            for condition, items in results.items()
        ]

    def log_temperature_excursion(
        self,
        batch_id: str,
        recorded_temp: float,
        min_temp: float,
        max_temp: float,
        duration_minutes: int,
        location: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        excursion: dict[str, Any] = {
            "batch_id": batch_id,
            "recorded_temperature": recorded_temp,
            "min_temperature": min_temp,
            "max_temperature": max_temp,
            "duration_minutes": duration_minutes,
            "location": location,
            "timestamp": datetime.now(UTC).isoformat(),
            "notes": notes,
            "severity": self._classify_excursion(recorded_temp, min_temp, max_temp, duration_minutes),
        }
        self._excursions.append(excursion)
        logger.warning(
            "Temperature excursion for batch %s: %.1f°C (range %.1f-%.1f) for %d min",
            batch_id, recorded_temp, min_temp, max_temp, duration_minutes,
        )

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id).first()
        if batch and excursion["severity"] in ("critical", "high"):
            batch.is_quarantined = True
            self.db.flush()
            logger.info("Batch %s quarantined due to temperature excursion", batch_id)

        return excursion

    def _classify_excursion(self, temp: float, min_temp: float, max_temp: float, duration_min: int) -> str:
        deviation = max(abs(temp - min_temp), abs(temp - max_temp)) if temp < min_temp or temp > max_temp else 0
        if deviation > 15 or duration_min > 120:
            return "critical"
        if deviation > 8 or duration_min > 60:
            return "high"
        if deviation > 3 or duration_min > 30:
            return "moderate"
        return "low"

    def get_excursion_log(self, batch_id: str | None = None) -> list[dict[str, Any]]:
        if batch_id:
            return [e for e in self._excursions if e.get("batch_id") == batch_id]
        return list(self._excursions)


class RecallService:
    def __init__(self, db: Session, user_id: int | None = None, lab_id: int | None = None):
        self.db = db
        self.user_id = user_id
        self.lab_id = lab_id

    def initiate_recall(
        self,
        drug_id: int,
        recall_reason: str,
        severity: str,
        batch_id: int | None = None,
        recall_number: str | None = None,
        recall_source: str | None = None,
        actions_taken: str | None = None,
        notes: str | None = None,
    ) -> Recall:
        if self.lab_id is None:
            raise ValueError("institutional pharmacy context is required")
        recall = Recall(
            lab_id=self.lab_id,
            drug_id=drug_id,
            batch_id=batch_id,
            recall_number=recall_number or f"RECALL-{datetime.now(UTC):%Y%m%d%H%M%S}",
            recall_reason=recall_reason,
            recall_source=recall_source,
            severity=severity,
            status="active",
            # Previously `initiated_by or str(self.user_id) if self.user_id else None`,
            # which binds as `(a or b) if self.user_id else None` — an explicitly
            # supplied initiator was discarded whenever there was no session user.
            initiated_by=self.user_id,
            initiated_at=datetime.now(UTC),
            actions_taken=actions_taken,
            notes=notes,
        )
        self.db.add(recall)
        self.db.flush()

        if batch_id is not None:
            batch = self.db.query(DrugBatch).filter(
                DrugBatch.id == batch_id,
                DrugBatch.lab_id == self.lab_id,
            ).first()
            if batch:
                batch.is_quarantined = True
                batch.quarantine_reason = f"recall {recall.recall_number}: {recall_reason}"
                batch.status = "quarantined"
                self.db.flush()

                levels = self.db.query(StockLevel).filter(
                    StockLevel.batch_id == batch_id,
                    StockLevel.lab_id == self.lab_id,
                    ~StockLevel.is_deleted,
                ).all()
                for stock in levels:
                    stock.quantity_available = 0
                self.db.flush()

        log_action(
            db=self.db,
            action="pharmacy.recall.initiate",
            resource_type="recall",
            resource_id=str(recall.id),
            user_id=self.user_id,
            details=f"Recall initiated: {recall_reason} (severity: {severity})",
        )
        return recall

    def get_active_recalls(self) -> list[Recall]:
        q = self.db.query(Recall).filter(
            Recall.status == "active",
            ~Recall.is_deleted,
        )
        if self.lab_id:
            q = q.filter(Recall.lab_id == self.lab_id)
        return cast(list[Recall], q.order_by(Recall.initiated_at.desc()).all())

    def resolve_recall(self, recall_id: int) -> Recall | None:
        # Tenant-scoped: a recall belongs to one laboratory and must not be
        # resolvable from another's session.
        q = self.db.query(Recall).filter(Recall.id == recall_id, ~Recall.is_deleted)
        if self.lab_id is not None:
            q = q.filter(Recall.lab_id == self.lab_id)
        recall = q.first()
        if not recall:
            return None
        recall.status = "resolved"
        recall.completed_at = datetime.now(UTC)
        self.db.flush()
        log_action(
            db=self.db,
            action="pharmacy.recall.resolve",
            resource_type="recall",
            resource_id=str(recall_id),
            user_id=self.user_id,
        )
        return recall

    def get_notification_status(self, recall_id: int) -> dict[str, Any]:
        """What the schema actually records about patient notification.

        The previous ``get_affected_patients`` read ``recall.affected_patients``,
        a column that does not exist. The physical table records whether
        notification is required and how many patients have been notified, not
        a patient list, so that is what this returns.
        """
        q = self.db.query(Recall).filter(Recall.id == recall_id, ~Recall.is_deleted)
        if self.lab_id is not None:
            q = q.filter(Recall.lab_id == self.lab_id)
        recall = q.first()
        if not recall:
            return {}
        return {
            "recall_number": recall.recall_number,
            "patient_notification_required": bool(recall.patient_notification_required),
            "notified_patients_count": recall.notified_patients_count or 0,
            "status": recall.status,
        }


class ForecastingService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def predict_consumption(self, drug_id: int, months_ahead: int = 3) -> list[dict[str, Any]]:
        if self.lab_id is None:
            raise ValueError("institutional pharmacy context is required")
        historical = self._get_historical_usage(drug_id, days=180)
        if not historical:
            return []

        monthly_avg = sum(historical) / max(len(historical), 1)
        # Confidence widens as history thins: with one month of data the band is
        # +/-50%, narrowing towards +/-10% once six months are available.
        spread = max(0.1, 0.5 - (len(historical) - 1) * 0.08)

        forecasts: list[dict[str, Any]] = []
        for i in range(months_ahead):
            period_start = (date.today().replace(day=1) + timedelta(days=32 * i)).replace(day=1)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)

            seasonal_factor = self._seasonal_factor((period_start.month - 1) % 12)
            predicted = max(1.0, monthly_avg * seasonal_factor)

            forecast = InventoryForecast(
                lab_id=self.lab_id,
                drug_id=drug_id,
                forecast_date=date.today(),
                forecast_period_start=period_start,
                forecast_period_end=period_end,
                predicted_consumption=predicted,
                predicted_consumption_unit="unit",
                confidence_lower=max(0.0, predicted * (1 - spread)),
                confidence_upper=predicted * (1 + spread),
                seasonal_factor=seasonal_factor,
                model_used="seasonal-moving-average",
            )
            self.db.add(forecast)
            self.db.flush()

            forecasts.append({
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "predicted_consumption": predicted,
                "confidence_lower": forecast.confidence_lower,
                "confidence_upper": forecast.confidence_upper,
            })

        return forecasts

    def _dispensed_between(self, drug_id: int, start: date, end: date) -> float:
        """Quantity actually dispensed in a window, from the movement log."""
        q = self.db.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(
            StockMovement.drug_id == drug_id,
            StockMovement.movement_type == StockMovementType.DISPENSED.value,
            func.date(StockMovement.performed_at) >= start,
            func.date(StockMovement.performed_at) <= end,
        )
        if self.lab_id is not None:
            q = q.filter(StockMovement.lab_id == self.lab_id)
        return float(q.scalar() or 0.0)

    def _get_historical_usage(self, drug_id: int, days: int = 180) -> list[float]:
        start_date = datetime.now(UTC) - timedelta(days=days)
        q = self.db.query(StockMovement).filter(
            StockMovement.drug_id == drug_id,
            StockMovement.movement_type == StockMovementType.DISPENSED.value,
            StockMovement.performed_at >= start_date,
        )
        if self.lab_id is not None:
            q = q.filter(StockMovement.lab_id == self.lab_id)

        monthly: dict[str, float] = defaultdict(float)
        for m in q.order_by(StockMovement.performed_at).all():
            monthly[m.performed_at.strftime("%Y-%m")] += float(m.quantity)
        return list(monthly.values())

    def _seasonal_factor(self, month_idx: int) -> float:
        factors = [1.0, 0.95, 1.05, 1.0, 0.95, 0.9, 0.85, 0.9, 1.0, 1.1, 1.15, 1.2]
        return factors[month_idx % 12]

    def get_prediction_accuracy(self, drug_id: int) -> dict[str, Any]:
        """Compare past forecasts against what was actually dispensed.

        There is no ``actual_consumption`` column — the previous implementation
        read one that does not exist. The actual figure is derived from the
        movement log, which is where dispensing is really recorded.
        """
        drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == drug_id).first()
        public_id = str(drug.drug_id) if drug else None
        today = date.today()

        q = self.db.query(InventoryForecast).filter(
            InventoryForecast.drug_id == drug_id,
            InventoryForecast.forecast_period_end < today,
            ~InventoryForecast.is_deleted,
        )
        if self.lab_id is not None:
            q = q.filter(InventoryForecast.lab_id == self.lab_id)
        forecasts = q.all()

        if not forecasts:
            return {"drug_catalog_id": public_id, "accuracy": None, "periods_analyzed": 0}

        errors: list[float] = []
        for f in forecasts:
            if not f.predicted_consumption or f.predicted_consumption <= 0:
                continue
            actual = self._dispensed_between(
                drug_id, f.forecast_period_start, f.forecast_period_end
            )
            errors.append(abs(f.predicted_consumption - actual) / f.predicted_consumption)

        if not errors:
            return {
                "drug_catalog_id": public_id,
                "accuracy": None,
                "periods_analyzed": len(forecasts),
            }

        mape = (sum(errors) / len(errors)) * 100
        return {
            "drug_catalog_id": public_id,
            "accuracy": max(0.0, 100 - mape),
            "mean_absolute_percentage_error": round(mape, 2),
            "periods_analyzed": len(forecasts),
        }
