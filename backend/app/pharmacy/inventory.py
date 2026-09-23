from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

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

    def add_stock(
        self,
        drug_catalog_id: str,
        batch_id: str,
        quantity: int,
        warehouse_id: str | None = None,
        store_id: str | None = None,
        reason: str = "Stock receipt",
    ) -> StockLevel:
        stock = self.db.query(StockLevel).filter(
            StockLevel.drug_catalog_id == drug_catalog_id,
            StockLevel.batch_id == batch_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.store_id == store_id,
        ).first()

        if stock:
            stock.quantity += quantity
            stock.available_quantity = stock.quantity - stock.reserved_quantity
        else:
            stock = StockLevel(
                drug_catalog_id=drug_catalog_id,
                batch_id=batch_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                quantity=quantity,
                reserved_quantity=0,
                available_quantity=quantity,
            )
            if self.lab_id:
                stock.lab_id = self.lab_id
            self.db.add(stock)

        self.db.flush()

        movement = StockMovement(
            drug_catalog_id=drug_catalog_id,
            batch_id=batch_id,
            warehouse_id=warehouse_id,
            store_id=store_id,
            movement_type=StockMovementType.RECEIVED,
            quantity=quantity,
            reason=reason,
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id).first()
        if batch:
            batch.quantity_remaining += quantity
            self.db.flush()

        self._audit("inventory.add_stock", "stock_level", stock.id, f"Added {quantity} units: {reason}")
        return stock

    def remove_stock(
        self,
        drug_catalog_id: str,
        batch_id: str,
        quantity: int,
        warehouse_id: str | None = None,
        store_id: str | None = None,
        reason: str = "Stock removal",
        movement_type: StockMovementType = StockMovementType.DISPENSED,
    ) -> StockLevel | None:
        stock = self.db.query(StockLevel).filter(
            StockLevel.drug_catalog_id == drug_catalog_id,
            StockLevel.batch_id == batch_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.store_id == store_id,
        ).first()

        if not stock or stock.available_quantity < quantity:
            logger.warning("Insufficient stock for removal: have %d, need %d", stock.available_quantity if stock else 0, quantity)
            return None

        stock.quantity -= quantity
        stock.available_quantity = stock.quantity - stock.reserved_quantity
        self.db.flush()

        movement = StockMovement(
            drug_catalog_id=drug_catalog_id,
            batch_id=batch_id,
            warehouse_id=warehouse_id,
            store_id=store_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id).first()
        if batch:
            batch.quantity_remaining = max(0, batch.quantity_remaining - quantity)
            self.db.flush()

        self._audit("inventory.remove_stock", "stock_level", stock.id, f"Removed {quantity} units: {reason}")
        return stock

    def adjust_stock(
        self,
        drug_catalog_id: str,
        batch_id: str,
        new_quantity: int,
        warehouse_id: str | None = None,
        store_id: str | None = None,
        reason: str = "Physical count adjustment",
    ) -> StockLevel:
        stock = self.db.query(StockLevel).filter(
            StockLevel.drug_catalog_id == drug_catalog_id,
            StockLevel.batch_id == batch_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.store_id == store_id,
        ).first()

        if stock:
            delta = new_quantity - stock.quantity
            stock.quantity = new_quantity
            stock.available_quantity = new_quantity - stock.reserved_quantity
            stock.last_count_date = datetime.now(UTC)
        else:
            stock = StockLevel(
                drug_catalog_id=drug_catalog_id,
                batch_id=batch_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                quantity=new_quantity,
                reserved_quantity=0,
                available_quantity=new_quantity,
            )
            if self.lab_id:
                stock.lab_id = self.lab_id
            self.db.add(stock)
            delta = new_quantity

        self.db.flush()

        if delta != 0:
            movement = StockMovement(
                drug_catalog_id=drug_catalog_id,
                batch_id=batch_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                movement_type=StockMovementType.ADJUSTED,
                quantity=abs(delta),
                reason=reason,
                performed_by=str(self.user_id) if self.user_id else None,
            )
            if self.lab_id:
                movement.lab_id = self.lab_id
            self.db.add(movement)
            self.db.flush()

            batch = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id).first()
            if batch:
                batch.quantity_remaining = max(0, batch.quantity_remaining + delta)
                self.db.flush()

        self._audit("inventory.adjust_stock", "stock_level", stock.id, f"Set to {new_quantity}: {reason}")
        return stock


class ExpiryMonitoringService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

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
            drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == batch.drug_catalog_id).first()
            results.append({
                "batch_id": batch.id,
                "drug_catalog_id": batch.drug_catalog_id,
                "drug_name": drug.name if drug else "Unknown",
                "drug_name_ar": drug.name_ar if drug else None,
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date.isoformat(),
                "days_remaining": (batch.expiry_date - date.today()).days,
                "quantity_remaining": batch.quantity_remaining,
                "storage_condition": batch.storage_condition.value if batch.storage_condition else None,
                "is_quarantined": batch.is_quarantined,
            })

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
            drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == batch.drug_catalog_id).first()
            results.append({
                "batch_id": batch.id,
                "drug_catalog_id": batch.drug_catalog_id,
                "drug_name": drug.name if drug else "Unknown",
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date.isoformat(),
                "days_expired": (date.today() - batch.expiry_date).days,
                "quantity_remaining": batch.quantity_remaining,
            })

        return results

    def auto_quarantine_expired(self) -> int:
        expired = self.db.query(DrugBatch).filter(
            DrugBatch.expiry_date < date.today(),
            ~DrugBatch.is_deleted,
            ~DrugBatch.is_quarantined,
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            expired = expired.filter(DrugBatch.lab_id == self.lab_id)

        count = 0
        for batch in expired.all():
            batch.is_quarantined = True
            self.db.flush()

            stock = self.db.query(StockLevel).filter(
                StockLevel.batch_id == batch.id,
                ~StockLevel.is_deleted,
            ).first()
            if stock:
                stock.available_quantity = 0
                self.db.flush()

            count += 1
            logger.info("Auto-quarantined batch %s (expired %s)", batch.batch_number, batch.expiry_date)

        self.db.flush()
        return count


class ReorderService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def calculate_reorder_quantity(
        self,
        drug_catalog_id: str,
        lead_time_days: int = 7,
        safety_stock_days: int = 3,
        average_daily_usage: int | None = None,
    ) -> dict[str, Any]:
        if average_daily_usage is None:
            average_daily_usage = self._calculate_average_usage(drug_catalog_id, days=90)

        stock = self.db.query(StockLevel).filter(
            StockLevel.drug_catalog_id == drug_catalog_id,
            ~StockLevel.is_deleted,
        ).first()

        current_stock = stock.available_quantity if stock else 0
        reorder_point = stock.reorder_point if stock and stock.reorder_point else (average_daily_usage * (lead_time_days + safety_stock_days))

        if current_stock <= reorder_point:
            reorder_qty = max(
                average_daily_usage * (lead_time_days + safety_stock_days) - current_stock,
                average_daily_usage * safety_stock_days,
            )
            needs_reorder = True
        else:
            reorder_qty = 0
            needs_reorder = False

        max_level = stock.max_level if stock and stock.max_level else (reorder_point * 2)

        return {
            "drug_catalog_id": drug_catalog_id,
            "current_stock": current_stock,
            "average_daily_usage": average_daily_usage,
            "lead_time_days": lead_time_days,
            "safety_stock_days": safety_stock_days,
            "reorder_point": reorder_point,
            "reorder_quantity": reorder_qty,
            "max_level": max_level,
            "needs_reorder": needs_reorder,
        }

    def _calculate_average_usage(self, drug_catalog_id: str, days: int = 90) -> int:
        start_date = datetime.now(UTC) - timedelta(days=days)
        result = self.db.query(
            func.coalesce(func.sum(StockMovement.quantity), 0),
        ).filter(
            StockMovement.drug_catalog_id == drug_catalog_id,
            StockMovement.movement_type.in_([StockMovementType.DISPENSED, StockMovementType.WASTED]),
            StockMovement.movement_date >= start_date,
        ).scalar()

        return max(1, round(result / days)) if result else 1

    def generate_reorder_list(self) -> list[dict[str, Any]]:
        reorder_list: list[dict[str, Any]] = []

        drug_ids_q = self.db.query(StockLevel.drug_catalog_id).filter(
            ~~StockLevel.is_deleted,
            StockLevel.reorder_point.isnot(None),
        )
        if self.lab_id:
            drug_ids_q = drug_ids_q.filter(StockLevel.lab_id == self.lab_id)

        drug_ids = {row[0] for row in drug_ids_q.all()}
        for drug_id in drug_ids:
            try:
                calc = self.calculate_reorder_quantity(drug_id)
                if calc["needs_reorder"]:
                    drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == drug_id).first()
                    calc["drug_name"] = drug.name if drug else "Unknown"
                    reorder_list.append(calc)
            except Exception as exc:
                logger.warning("Failed to calculate reorder for %s: %s", drug_id, exc)

        return sorted(reorder_list, key=lambda r: r["current_stock"] / max(r["reorder_point"], 1))


class ColdChainService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id
        self._excursions: list[dict[str, Any]] = []

    def get_cold_chain_drugs(self) -> list[dict[str, Any]]:
        q = self.db.query(DrugBatch).filter(
            DrugBatch.storage_condition.in_([
                StorageCondition.COLD_CHAIN,
                StorageCondition.REFRIGERATED,
                StorageCondition.FROZEN,
            ]),
            ~DrugBatch.is_deleted,
            ~DrugBatch.is_quarantined,
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)

        results: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for batch in q.all():
            drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == batch.drug_catalog_id).first()
            results[batch.storage_condition.value].append({
                "batch_id": batch.id,
                "drug_catalog_id": batch.drug_catalog_id,
                "drug_name": drug.name if drug else "Unknown",
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "quantity_remaining": batch.quantity_remaining,
                "storage_condition": batch.storage_condition.value,
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
        drug_catalog_id: str,
        recall_reason: str,
        severity: str,
        batch_id: str | None = None,
        initiated_by: str | None = None,
        actions_taken: str | None = None,
        notes: str | None = None,
    ) -> Recall:
        recall = Recall(
            drug_catalog_id=drug_catalog_id,
            batch_id=batch_id,
            recall_reason=recall_reason,
            recall_date=datetime.now(UTC),
            initiated_by=initiated_by or str(self.user_id) if self.user_id else None,
            severity=severity,
            status="active",
            actions_taken=actions_taken,
            notes=notes,
        )
        if self.lab_id:
            recall.lab_id = self.lab_id
        self.db.add(recall)
        self.db.flush()

        if batch_id:
            batch = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id).first()
            if batch:
                batch.is_quarantined = True
                self.db.flush()

                stock = self.db.query(StockLevel).filter(
                    StockLevel.batch_id == batch_id,
                    ~StockLevel.is_deleted,
                ).first()
                if stock:
                    stock.available_quantity = 0
                    self.db.flush()

        log_action(
            db=self.db,
            action="pharmacy.recall.initiate",
            resource_type="recall",
            resource_id=recall.id,
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
        return q.order_by(Recall.recall_date.desc()).all()

    def resolve_recall(self, recall_id: str) -> Recall | None:
        recall = self.db.query(Recall).filter(Recall.id == recall_id).first()
        if not recall:
            return None
        recall.status = "resolved"
        self.db.flush()
        log_action(
            db=self.db,
            action="pharmacy.recall.resolve",
            resource_type="recall",
            resource_id=recall_id,
            user_id=self.user_id,
        )
        return recall

    def get_affected_patients(self, recall_id: str) -> list[dict[str, Any]]:
        recall = self.db.query(Recall).filter(Recall.id == recall_id).first()
        if not recall or not recall.affected_patients:
            return []
        return list(recall.affected_patients) if isinstance(recall.affected_patients, list) else []


class ForecastingService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def predict_consumption(
        self,
        drug_catalog_id: str,
        months_ahead: int = 3,
    ) -> list[dict[str, Any]]:
        historical = self._get_historical_usage(drug_catalog_id, days=180)
        if not historical:
            return []

        monthly_avg = sum(historical) / max(len(historical), 1)
        monthly_avg * months_ahead

        forecasts: list[dict[str, Any]] = []
        for i in range(months_ahead):
            period_start = date.today().replace(day=1) + timedelta(days=32 * i)
            period_start = period_start.replace(day=1)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)

            month_idx = (period_start.month - 1) % 12
            seasonal_factor = self._seasonal_factor(month_idx)
            predicted = max(1, round(monthly_avg * seasonal_factor))

            forecast = InventoryForecast(
                drug_catalog_id=drug_catalog_id,
                period_start=period_start,
                period_end=period_end,
                predicted_consumption=predicted,
                confidence_score=min(0.95, 0.5 + (len(historical) / 30) * 0.1),
            )
            if self.lab_id:
                forecast.lab_id = self.lab_id
            self.db.add(forecast)
            self.db.flush()

            forecasts.append({
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "predicted_consumption": predicted,
                "confidence_score": forecast.confidence_score,
            })

        return forecasts

    def _get_historical_usage(self, drug_catalog_id: str, days: int = 180) -> list[int]:
        start_date = datetime.now(UTC) - timedelta(days=days)
        movements = self.db.query(StockMovement).filter(
            StockMovement.drug_catalog_id == drug_catalog_id,
            StockMovement.movement_type == StockMovementType.DISPENSED,
            StockMovement.movement_date >= start_date,
        ).order_by(StockMovement.movement_date).all()

        monthly: dict[str, int] = defaultdict(int)
        for m in movements:
            key = m.movement_date.strftime("%Y-%m")
            monthly[key] += m.quantity

        return list(monthly.values())

    def _seasonal_factor(self, month_idx: int) -> float:
        factors = [1.0, 0.95, 1.05, 1.0, 0.95, 0.9, 0.85, 0.9, 1.0, 1.1, 1.15, 1.2]
        return factors[month_idx % 12]

    def get_prediction_accuracy(self, drug_catalog_id: str) -> dict[str, Any]:
        forecasts = self.db.query(InventoryForecast).filter(
            InventoryForecast.drug_catalog_id == drug_catalog_id,
            InventoryForecast.actual_consumption.isnot(None),
        ).all()

        if not forecasts:
            return {"drug_catalog_id": drug_catalog_id, "accuracy": None, "periods_analyzed": 0}

        errors: list[float] = []
        for f in forecasts:
            if f.predicted_consumption and f.predicted_consumption > 0:
                error = abs(f.predicted_consumption - f.actual_consumption) / f.predicted_consumption
                errors.append(error)

        if not errors:
            return {"drug_catalog_id": drug_catalog_id, "accuracy": None, "periods_analyzed": len(forecasts)}

        mape = (sum(errors) / len(errors)) * 100
        return {
            "drug_catalog_id": drug_catalog_id,
            "accuracy": max(0, 100 - mape),
            "mean_absolute_percentage_error": round(mape, 2),
            "periods_analyzed": len(forecasts),
        }
