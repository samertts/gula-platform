from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.pharmacy.enums import DispenseStatus, PrescriptionStatus, StockMovementType
from app.pharmacy.models import (
    DispenseQueue,
    DispenseRecord,
    DrugBatch,
    DrugCatalog,
    DrugReturn,
    DrugSupplier,
    InventoryForecast,
    InventoryTransfer,
    InventoryTransferItem,
    Prescription,
    PrescriptionItem,
    Recall,
    StockLevel,
    StockMovement,
    WasteRecord,
)
from app.services.audit_service import log_action

logger = logging.getLogger("gula.pharmacy.services")


class PharmacyService:
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

    # ── Catalog Management ─────────────────────────────────────────────────────

    def create_drug(self, data: dict[str, Any]) -> DrugCatalog:
        drug = DrugCatalog(**{k: v for k, v in data.items() if hasattr(DrugCatalog, k)})
        if self.lab_id:
            drug.lab_id = self.lab_id
        self.db.add(drug)
        self.db.flush()
        self._audit("pharmacy.drug.create", "drug_catalog", drug.id, f"Created drug {data.get('code')}")
        return drug

    def get_drug(self, drug_id: str) -> DrugCatalog | None:
        q = self.db.query(DrugCatalog).filter(DrugCatalog.id == drug_id, ~DrugCatalog.is_deleted)
        if self.lab_id:
            q = q.filter(DrugCatalog.lab_id == self.lab_id)
        return q.first()

    def update_drug(self, drug_id: str, data: dict[str, Any]) -> DrugCatalog | None:
        drug = self.get_drug(drug_id)
        if not drug:
            return None
        for key, value in data.items():
            if hasattr(drug, key) and value is not None:
                setattr(drug, key, value)
        self.db.flush()
        self._audit("pharmacy.drug.update", "drug_catalog", drug_id, "Updated drug catalog entry")
        return drug

    def delete_drug(self, drug_id: str) -> bool:
        drug = self.get_drug(drug_id)
        if not drug:
            return False
        drug.soft_delete()
        self.db.flush()
        self._audit("pharmacy.drug.delete", "drug_catalog", drug_id)
        return True

    def search_drugs(
        self,
        query: str | None = None,
        category: str | None = None,
        atc_code: str | None = None,
        therapeutic_class: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DrugCatalog], int]:
        q = self.db.query(DrugCatalog).filter(~~DrugCatalog.is_deleted)
        if self.lab_id:
            q = q.filter(DrugCatalog.lab_id == self.lab_id)
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    DrugCatalog.name.ilike(pattern),
                    DrugCatalog.name_ar.ilike(pattern),
                    DrugCatalog.generic_name.ilike(pattern),
                    DrugCatalog.brand_name.ilike(pattern),
                    DrugCatalog.code.ilike(pattern),
                ),
            )
        if category:
            q = q.filter(DrugCatalog.category == category)
        if atc_code:
            q = q.filter(DrugCatalog.atc_code == atc_code)
        if therapeutic_class:
            q = q.filter(DrugCatalog.therapeutic_class == therapeutic_class)
        total = q.count()
        items = q.order_by(DrugCatalog.name).offset(skip).limit(limit).all()
        return items, total

    def get_drugs_by_atc(self, atc_code: str) -> list[DrugCatalog]:
        q = self.db.query(DrugCatalog).filter(
            DrugCatalog.atc_code == atc_code,
            ~DrugCatalog.is_deleted,
        )
        if self.lab_id:
            q = q.filter(DrugCatalog.lab_id == self.lab_id)
        return q.all()

    def create_batch(self, drug_id: str, data: dict[str, Any]) -> DrugBatch | None:
        drug = self.get_drug(drug_id)
        if not drug:
            return None
        batch = DrugBatch(drug_catalog_id=drug_id, **{k: v for k, v in data.items() if hasattr(DrugBatch, k) and k != "drug_catalog_id"})
        if self.lab_id:
            batch.lab_id = self.lab_id
        self.db.add(batch)
        self.db.flush()

        stock = StockLevel(
            drug_catalog_id=drug_id,
            batch_id=batch.id,
            quantity=data.get("quantity_initial", 0),
            reserved_quantity=0,
            available_quantity=data.get("quantity_initial", 0),
        )
        if self.lab_id:
            stock.lab_id = self.lab_id
        self.db.add(stock)
        self.db.flush()

        self._audit("pharmacy.batch.create", "drug_batch", batch.id, f"Created batch {data.get('batch_number')}")
        return batch

    def get_batches(self, drug_id: str) -> list[DrugBatch]:
        q = self.db.query(DrugBatch).filter(
            DrugBatch.drug_catalog_id == drug_id,
            ~DrugBatch.is_deleted,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)
        return q.order_by(DrugBatch.expiry_date).all()

    def get_batch(self, batch_id: str) -> DrugBatch | None:
        q = self.db.query(DrugBatch).filter(DrugBatch.id == batch_id, ~DrugBatch.is_deleted)
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)
        return q.first()

    def get_expiring_batches(self, days: int = 90) -> list[DrugBatch]:
        expiry_cutoff = date.today() + timedelta(days=days)
        q = self.db.query(DrugBatch).filter(
            DrugBatch.expiry_date <= expiry_cutoff,
            DrugBatch.expiry_date >= date.today(),
            ~DrugBatch.is_deleted,
            not DrugBatch.is_quarantined,
            DrugBatch.quantity_remaining > 0,
        )
        if self.lab_id:
            q = q.filter(DrugBatch.lab_id == self.lab_id)
        return q.order_by(DrugBatch.expiry_date).all()

    def create_supplier(self, data: dict[str, Any]) -> DrugSupplier:
        supplier = DrugSupplier(**{k: v for k, v in data.items() if hasattr(DrugSupplier, k)})
        if self.lab_id:
            supplier.lab_id = self.lab_id
        self.db.add(supplier)
        self.db.flush()
        self._audit("pharmacy.supplier.create", "drug_supplier", supplier.id, f"Created supplier {data.get('name')}")
        return supplier

    def list_suppliers(self) -> list[DrugSupplier]:
        q = self.db.query(DrugSupplier).filter(~~DrugSupplier.is_deleted)
        if self.lab_id:
            q = q.filter(DrugSupplier.lab_id == self.lab_id)
        return q.order_by(DrugSupplier.name).all()

    # ── Prescription Workflow ──────────────────────────────────────────────────

    def create_prescription(self, data: dict[str, Any]) -> Prescription:
        rx = Prescription(**{k: v for k, v in data.items() if hasattr(Prescription, k)})
        if self.lab_id:
            rx.lab_id = self.lab_id
        self.db.add(rx)
        self.db.flush()
        self._audit("pharmacy.rx.create", "prescription", rx.id, f"Created prescription {data.get('prescription_number')}")
        return rx

    def get_prescription(self, rx_id: str) -> Prescription | None:
        q = self.db.query(Prescription).filter(Prescription.id == rx_id, ~Prescription.is_deleted)
        if self.lab_id:
            q = q.filter(Prescription.lab_id == self.lab_id)
        return q.first()

    def update_prescription_status(self, rx_id: str, status: PrescriptionStatus) -> Prescription | None:
        rx = self.get_prescription(rx_id)
        if not rx:
            return None
        rx.status = status
        self.db.flush()
        self._audit("pharmacy.rx.status_update", "prescription", rx_id, f"Status changed to {status.value}")
        return rx

    def cancel_prescription(self, rx_id: str) -> Prescription | None:
        return self.update_prescription_status(rx_id, PrescriptionStatus.CANCELLED)

    def renew_prescription(self, rx_id: str) -> Prescription | None:
        original = self.get_prescription(rx_id)
        if not original:
            return None
        renewal = Prescription(
            patient_id=original.patient_id,
            encounter_id=original.encounter_id,
            prescriber_id=original.prescriber_id,
            prescription_number=f"{original.prescription_number}-R{int(original.prescription_number.split('-R')[-1]) + 1 if '-R' in original.prescription_number else 1}",
            status=PrescriptionStatus.ACTIVE,
            intent=original.intent,
            priority=original.priority,
            diagnosis=original.diagnosis,
            diagnosis_code=original.diagnosis_code,
            diagnosis_system=original.diagnosis_system,
            substitution_allowed=original.substitution_allowed,
            note=original.note,
        )
        if self.lab_id:
            renewal.lab_id = self.lab_id
        self.db.add(renewal)
        self.db.flush()

        for item in self.db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == rx_id).all():
            new_item = PrescriptionItem(
                prescription_id=renewal.id,
                drug_catalog_id=item.drug_catalog_id,
                medication_code=item.medication_code,
                medication_name=item.medication_name,
                strength_value=item.strength_value,
                strength_unit=item.strength_unit,
                form=item.form,
                route=item.route,
                dose_quantity=item.dose_quantity,
                dose_unit=item.dose_unit,
                frequency=item.frequency,
                duration=item.duration,
                duration_unit=item.duration_unit,
                quantity=item.quantity,
                quantity_unit=item.quantity_unit,
                refills=item.refills,
                instructions=item.instructions,
                substitution_allowed=item.substitution_allowed,
            )
            if self.lab_id:
                new_item.lab_id = self.lab_id
            self.db.add(new_item)

        self.db.flush()
        self._audit("pharmacy.rx.renew", "prescription", renewal.id, f"Renewed from {rx_id}")
        return renewal

    def add_prescription_item(self, rx_id: str, data: dict[str, Any]) -> PrescriptionItem | None:
        rx = self.get_prescription(rx_id)
        if not rx:
            return None
        item = PrescriptionItem(prescription_id=rx_id, **{k: v for k, v in data.items() if hasattr(PrescriptionItem, k) and k != "prescription_id"})
        if self.lab_id:
            item.lab_id = self.lab_id
        self.db.add(item)
        self.db.flush()
        self._audit("pharmacy.rx.add_item", "prescription_item", item.id, f"Item added to RX {rx_id}")
        return item

    def substitute_prescription_item(self, rx_id: str, item_id: str, new_drug_id: str) -> PrescriptionItem | None:
        item = self.db.query(PrescriptionItem).filter(
            PrescriptionItem.id == item_id,
            PrescriptionItem.prescription_id == rx_id,
        ).first()
        if not item:
            return None
        new_drug = self.get_drug(new_drug_id)
        if not new_drug:
            return None
        item.drug_catalog_id = new_drug_id
        item.medication_code = new_drug.code
        item.medication_name = new_drug.name
        self.db.flush()
        self._audit("pharmacy.rx.substitute", "prescription_item", item_id, f"Substituted with {new_drug_id}")
        return item

    # ── Dispensing Workflow ────────────────────────────────────────────────────

    def get_dispense_queue(
        self, status: str | None = None, priority: str | None = None, skip: int = 0, limit: int = 50,
    ) -> tuple[list[DispenseQueue], int]:
        q = self.db.query(DispenseQueue).filter(~~DispenseQueue.is_deleted)
        if self.lab_id:
            q = q.filter(DispenseQueue.lab_id == self.lab_id)
        if status:
            q = q.filter(DispenseQueue.status == status)
        if priority:
            q = q.filter(DispenseQueue.priority == priority)
        total = q.count()
        items = q.order_by(
            case(
                (DispenseQueue.priority == "stat", 0),
                (DispenseQueue.priority == "urgent", 1),
                (DispenseQueue.priority == "normal", 2),
                else_=3,
            ),
            DispenseQueue.queued_at,
        ).offset(skip).limit(limit).all()
        return items, total

    def prepare_dispense(self, queue_id: str) -> DispenseQueue | None:
        entry = self.db.query(DispenseQueue).filter(DispenseQueue.id == queue_id).first()
        if not entry:
            return None
        entry.status = DispenseStatus.PREPARED
        entry.assigned_to = str(self.user_id) if self.user_id else None
        self.db.flush()
        self._audit("pharmacy.dispense.prepare", "dispense_queue", queue_id)
        return entry

    def verify_dispense(self, queue_id: str) -> DispenseQueue | None:
        entry = self.db.query(DispenseQueue).filter(DispenseQueue.id == queue_id).first()
        if not entry:
            return None
        entry.status = DispenseStatus.VERIFIED
        self.db.flush()
        self._audit("pharmacy.dispense.verify", "dispense_queue", queue_id)
        return entry

    def complete_dispense(self, queue_id: str) -> DispenseQueue | None:
        entry = self.db.query(DispenseQueue).filter(DispenseQueue.id == queue_id).first()
        if not entry:
            return None
        entry.status = DispenseStatus.DISPENSED
        entry.completion_time = datetime.now(UTC)
        self.db.flush()

        rx = self.db.query(Prescription).filter(Prescription.id == entry.prescription_id).first()
        if rx:
            rx.status = PrescriptionStatus.COMPLETED
            self.db.flush()

        self._audit("pharmacy.dispense.complete", "dispense_queue", queue_id)
        return entry

    def partial_dispense(self, queue_id: str) -> DispenseQueue | None:
        entry = self.db.query(DispenseQueue).filter(DispenseQueue.id == queue_id).first()
        if not entry:
            return None
        entry.status = DispenseStatus.PARTIAL
        self.db.flush()
        self._audit("pharmacy.dispense.partial", "dispense_queue", queue_id)
        return entry

    def cancel_dispense(self, queue_id: str) -> DispenseQueue | None:
        entry = self.db.query(DispenseQueue).filter(DispenseQueue.id == queue_id).first()
        if not entry:
            return None
        entry.status = DispenseStatus.CANCELLED
        self.db.flush()
        self._audit("pharmacy.dispense.cancel", "dispense_queue", queue_id)
        return entry

    def create_dispense_record(self, data: dict[str, Any]) -> DispenseRecord:
        record = DispenseRecord(**{k: v for k, v in data.items() if hasattr(DispenseRecord, k)})
        if self.lab_id:
            record.lab_id = self.lab_id
        self.db.add(record)
        self.db.flush()

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == record.batch_id).first()
        if batch:
            batch.quantity_remaining -= record.quantity_dispensed
            self.db.flush()

        stock = self.db.query(StockLevel).filter(
            StockLevel.batch_id == record.batch_id,
            StockLevel.drug_catalog_id == data.get("drug_catalog_id"),
        ).first()
        if stock:
            stock.quantity -= record.quantity_dispensed
            stock.available_quantity = stock.quantity - stock.reserved_quantity
            self.db.flush()

        movement = StockMovement(
            drug_catalog_id=data.get("drug_catalog_id"),
            batch_id=record.batch_id,
            movement_type=StockMovementType.DISPENSED,
            quantity=record.quantity_dispensed,
            reference_type="dispense",
            reference_id=record.id,
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        self._audit("pharmacy.dispense.record", "dispense_record", record.id)
        return record

    def get_dispense_records(self, patient_id: str) -> list[DispenseRecord]:
        q = self.db.query(DispenseRecord).filter(
            DispenseRecord.patient_id == patient_id,
            ~DispenseRecord.is_deleted,
        )
        if self.lab_id:
            q = q.filter(DispenseRecord.lab_id == self.lab_id)
        return q.order_by(DispenseRecord.dispensed_at.desc()).all()

    # ── Inventory Management ───────────────────────────────────────────────────

    def get_stock_levels(
        self,
        warehouse_id: str | None = None,
        store_id: str | None = None,
        drug_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[StockLevel], int]:
        q = self.db.query(StockLevel).filter(~~StockLevel.is_deleted)
        if self.lab_id:
            q = q.filter(StockLevel.lab_id == self.lab_id)
        if warehouse_id:
            q = q.filter(StockLevel.warehouse_id == warehouse_id)
        if store_id:
            q = q.filter(StockLevel.store_id == store_id)
        if drug_id:
            q = q.filter(StockLevel.drug_catalog_id == drug_id)
        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    def get_stock_alerts(self) -> dict[str, list[dict[str, Any]]]:
        alerts: dict[str, list[dict[str, Any]]] = {"low_stock": [], "overstocked": [], "expiring_soon": []}
        q = self.db.query(StockLevel).filter(
            ~~StockLevel.is_deleted,
            StockLevel.available_quantity > 0,
        )
        if self.lab_id:
            q = q.filter(StockLevel.lab_id == self.lab_id)

        for stock in q.all():
            if stock.reorder_point and stock.available_quantity <= stock.reorder_point:
                drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == stock.drug_catalog_id).first()
                alerts["low_stock"].append({
                    "stock_id": stock.id,
                    "drug_id": stock.drug_catalog_id,
                    "drug_name": drug.name if drug else "Unknown",
                    "available": stock.available_quantity,
                    "reorder_point": stock.reorder_point,
                })
            if stock.max_level and stock.available_quantity >= stock.max_level:
                drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == stock.drug_catalog_id).first()
                alerts["overstocked"].append({
                    "stock_id": stock.id,
                    "drug_id": stock.drug_catalog_id,
                    "drug_name": drug.name if drug else "Unknown",
                    "available": stock.available_quantity,
                    "max_level": stock.max_level,
                })

        expiring = self.get_expiring_batches(90)
        for batch in expiring:
            drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == batch.drug_catalog_id).first()
            alerts["expiring_soon"].append({
                "batch_id": batch.id,
                "drug_id": batch.drug_catalog_id,
                "drug_name": drug.name if drug else "Unknown",
                "expiry_date": batch.expiry_date.isoformat(),
                "quantity_remaining": batch.quantity_remaining,
            })

        return alerts

    def adjust_stock(self, data: dict[str, Any]) -> StockLevel | None:
        stock = self.db.query(StockLevel).filter(
            StockLevel.drug_catalog_id == data.get("drug_catalog_id"),
            StockLevel.batch_id == data.get("batch_id"),
        ).first()
        if not stock:
            stock = StockLevel(
                drug_catalog_id=data.get("drug_catalog_id"),
                batch_id=data.get("batch_id"),
                warehouse_id=data.get("warehouse_id"),
                store_id=data.get("store_id"),
            )
            if self.lab_id:
                stock.lab_id = self.lab_id
            self.db.add(stock)

        adjustment = data.get("adjustment", 0)
        stock.quantity += adjustment
        stock.available_quantity = stock.quantity - stock.reserved_quantity
        self.db.flush()

        movement = StockMovement(
            drug_catalog_id=data.get("drug_catalog_id"),
            batch_id=data.get("batch_id"),
            warehouse_id=data.get("warehouse_id"),
            store_id=data.get("store_id"),
            movement_type=StockMovementType.ADJUSTED,
            quantity=abs(adjustment),
            reason=data.get("reason", "Manual adjustment"),
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        self._audit("pharmacy.stock.adjust", "stock_level", stock.id, f"Adjusted by {adjustment}")
        return stock

    def get_movements(
        self, drug_id: str | None = None, movement_type: str | None = None, skip: int = 0, limit: int = 50,
    ) -> tuple[list[StockMovement], int]:
        q = self.db.query(StockMovement).filter(~~StockMovement.is_deleted)
        if self.lab_id:
            q = q.filter(StockMovement.lab_id == self.lab_id)
        if drug_id:
            q = q.filter(StockMovement.drug_catalog_id == drug_id)
        if movement_type:
            q = q.filter(StockMovement.movement_type == movement_type)
        total = q.count()
        items = q.order_by(StockMovement.movement_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def create_movement(self, data: dict[str, Any]) -> StockMovement:
        movement = StockMovement(**{k: v for k, v in data.items() if hasattr(StockMovement, k)})
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()
        self._audit("pharmacy.movement.create", "stock_movement", movement.id, f"Movement {data.get('movement_type')}")
        return movement

    def create_transfer(self, data: dict[str, Any]) -> InventoryTransfer:
        transfer = InventoryTransfer(**{k: v for k, v in data.items() if hasattr(InventoryTransfer, k)})
        if self.lab_id:
            transfer.lab_id = self.lab_id
        self.db.add(transfer)
        self.db.flush()
        self._audit("pharmacy.transfer.create", "inventory_transfer", transfer.id)
        return transfer

    def get_transfers(self, status: str | None = None, skip: int = 0, limit: int = 50) -> tuple[list[InventoryTransfer], int]:
        q = self.db.query(InventoryTransfer).filter(~~InventoryTransfer.is_deleted)
        if self.lab_id:
            q = q.filter(InventoryTransfer.lab_id == self.lab_id)
        if status:
            q = q.filter(InventoryTransfer.status == status)
        total = q.count()
        items = q.order_by(InventoryTransfer.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def approve_transfer(self, transfer_id: str) -> InventoryTransfer | None:
        transfer = self.db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
        if not transfer:
            return None
        transfer.status = "approved"
        transfer.approved_by = str(self.user_id) if self.user_id else None
        transfer.dispatch_date = datetime.now(UTC)
        self.db.flush()
        self._audit("pharmacy.transfer.approve", "inventory_transfer", transfer_id)
        return transfer

    def receive_transfer(self, transfer_id: str) -> InventoryTransfer | None:
        transfer = self.db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
        if not transfer:
            return None
        transfer.status = "completed"
        transfer.received_date = datetime.now(UTC)
        self.db.flush()

        for item in self.db.query(InventoryTransferItem).filter(InventoryTransferItem.transfer_id == transfer_id).all():
            stock = self.db.query(StockLevel).filter(
                StockLevel.drug_catalog_id == item.drug_catalog_id,
                StockLevel.batch_id == item.batch_id,
            ).first()
            if stock:
                stock.quantity += (item.quantity_received or item.quantity_shipped or 0)
                stock.available_quantity = stock.quantity - stock.reserved_quantity
                self.db.flush()

        self._audit("pharmacy.transfer.receive", "inventory_transfer", transfer_id)
        return transfer

    def create_return(self, data: dict[str, Any]) -> DrugReturn:
        ret = DrugReturn(**{k: v for k, v in data.items() if hasattr(DrugReturn, k)})
        if self.lab_id:
            ret.lab_id = self.lab_id
        self.db.add(ret)
        self.db.flush()

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == data.get("batch_id")).first()
        if batch:
            batch.quantity_remaining += data.get("quantity", 0)
            self.db.flush()

        movement = StockMovement(
            drug_catalog_id=data.get("drug_catalog_id"),
            batch_id=data.get("batch_id"),
            movement_type=StockMovementType.RETURNED,
            quantity=data.get("quantity", 0),
            reference_type="return",
            reference_id=ret.id,
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        self._audit("pharmacy.return.create", "drug_return", ret.id)
        return ret

    def create_waste(self, data: dict[str, Any]) -> WasteRecord:
        waste = WasteRecord(**{k: v for k, v in data.items() if hasattr(WasteRecord, k)})
        if self.lab_id:
            waste.lab_id = self.lab_id
        self.db.add(waste)
        self.db.flush()

        batch = self.db.query(DrugBatch).filter(DrugBatch.id == data.get("batch_id")).first()
        if batch:
            batch.quantity_remaining -= data.get("quantity", 0)
            self.db.flush()

        movement = StockMovement(
            drug_catalog_id=data.get("drug_catalog_id"),
            batch_id=data.get("batch_id"),
            movement_type=StockMovementType.WASTED,
            quantity=data.get("quantity", 0),
            reference_type="waste",
            reference_id=waste.id,
            performed_by=str(self.user_id) if self.user_id else None,
        )
        if self.lab_id:
            movement.lab_id = self.lab_id
        self.db.add(movement)
        self.db.flush()

        self._audit("pharmacy.waste.create", "waste_record", waste.id)
        return waste

    def list_recalls(self, status: str | None = None, skip: int = 0, limit: int = 50) -> tuple[list[Recall], int]:
        q = self.db.query(Recall).filter(~~Recall.is_deleted)
        if self.lab_id:
            q = q.filter(Recall.lab_id == self.lab_id)
        if status:
            q = q.filter(Recall.status == status)
        total = q.count()
        items = q.order_by(Recall.recall_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def create_recall(self, data: dict[str, Any]) -> Recall:
        recall = Recall(**{k: v for k, v in data.items() if hasattr(Recall, k)})
        if self.lab_id:
            recall.lab_id = self.lab_id
        self.db.add(recall)
        self.db.flush()
        self._audit("pharmacy.recall.create", "recall", recall.id, f"Recall for drug {data.get('drug_catalog_id')}")
        return recall

    def get_inventory_forecast(self, drug_id: str) -> list[InventoryForecast]:
        q = self.db.query(InventoryForecast).filter(
            InventoryForecast.drug_catalog_id == drug_id,
            ~InventoryForecast.is_deleted,
        )
        if self.lab_id:
            q = q.filter(InventoryForecast.lab_id == self.lab_id)
        return q.order_by(InventoryForecast.period_start.desc()).all()

    def generate_reorder_recommendations(self) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        q = self.db.query(StockLevel).filter(
            ~~StockLevel.is_deleted,
            StockLevel.reorder_point.isnot(None),
            StockLevel.available_quantity <= StockLevel.reorder_point,
        )
        if self.lab_id:
            q = q.filter(StockLevel.lab_id == self.lab_id)

        for stock in q.all():
            drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == stock.drug_catalog_id).first()
            if not drug:
                continue
            reorder_qty = stock.reorder_quantity or (stock.max_level or 0) * 2
            recommendations.append({
                "drug_id": stock.drug_catalog_id,
                "drug_name": drug.name,
                "current_stock": stock.available_quantity,
                "reorder_point": stock.reorder_point,
                "recommended_quantity": reorder_qty,
                "priority": "high" if stock.available_quantity == 0 else "medium",
            })

        return recommendations

    # ── Dashboard ──────────────────────────────────────────────────────────────

    def get_dashboard(self) -> dict[str, Any]:
        rx_q = self.db.query(Prescription).filter(~~Prescription.is_deleted)
        queue_q = self.db.query(DispenseQueue).filter(~~DispenseQueue.is_deleted)
        if self.lab_id:
            rx_q = rx_q.filter(Prescription.lab_id == self.lab_id)
            queue_q = queue_q.filter(DispenseQueue.lab_id == self.lab_id)

        total_prescriptions = rx_q.count()
        active_prescriptions = rx_q.filter(Prescription.status == PrescriptionStatus.ACTIVE).count()
        pending_queue = queue_q.filter(DispenseQueue.status == DispenseStatus.PENDING).count()
        dispensed_today = queue_q.filter(
            DispenseQueue.status == DispenseStatus.DISPENSED,
            func.date(DispenseQueue.completion_time) == date.today(),
        ).count()

        return {
            "total_prescriptions": total_prescriptions,
            "active_prescriptions": active_prescriptions,
            "pending_queue": pending_queue,
            "dispensed_today": dispensed_today,
        }

    def get_queue_summary(self) -> dict[str, Any]:
        q = self.db.query(DispenseQueue).filter(~~DispenseQueue.is_deleted)
        if self.lab_id:
            q = q.filter(DispenseQueue.lab_id == self.lab_id)

        total = q.count()
        by_status = {
            DispenseStatus.PENDING.value: q.filter(DispenseQueue.status == DispenseStatus.PENDING).count(),
            DispenseStatus.PREPARED.value: q.filter(DispenseQueue.status == DispenseStatus.PREPARED).count(),
            DispenseStatus.VERIFIED.value: q.filter(DispenseQueue.status == DispenseStatus.VERIFIED).count(),
        }

        wait_times = self.db.query(
            func.avg(
                func.extract("epoch", DispenseQueue.completion_time - DispenseQueue.queued_at),
            ),
        ).filter(
            DispenseQueue.status == DispenseStatus.DISPENSED,
            DispenseQueue.completion_time.isnot(None),
        ).scalar()

        return {
            "total_in_queue": total,
            "by_status": by_status,
            "average_wait_time_seconds": round(wait_times) if wait_times else 0,
        }

    def get_expiry_alerts(self) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for days, label in [(30, "critical"), (60, "warning"), (90, "info")]:
            batches = self.get_expiring_batches(days)
            for batch in batches:
                if batch.expiry_date and batch.expiry_date >= date.today():
                    drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == batch.drug_catalog_id).first()
                    alerts.append({
                        "batch_id": batch.id,
                        "drug_id": batch.drug_catalog_id,
                        "drug_name": drug.name if drug else "Unknown",
                        "expiry_date": batch.expiry_date.isoformat(),
                        "days_remaining": (batch.expiry_date - date.today()).days,
                        "quantity_remaining": batch.quantity_remaining,
                        "severity": label,
                    })
        return alerts
