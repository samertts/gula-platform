from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.billing.service import BillingService
from app.ehr.models.medication import MedicationDispense
from app.national.domain.practitioner import Practitioner
from app.national.enums import PractitionerRole
from app.models.lab_user import LabUser
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
    PharmacySale,
    PharmacySaleLine,
    Prescription,
    PrescriptionItem,
    Recall,
    StockLevel,
    StockMovement,
    WasteRecord,
)
from app.services.audit_service import log_action

logger = logging.getLogger("gula.pharmacy.services")


class PharmacyAuthorizationBlocked(Exception):
    """Raised when a pharmacy command lacks server-derived clinical proof."""


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

    def _resolve_server_practitioner_id(self, *, allowed_roles: tuple[PractitionerRole, ...]) -> str:
        user = self.db.query(LabUser).filter(LabUser.id == self.user_id, LabUser.lab_id == self.lab_id, LabUser.is_active.is_(True)).one_or_none()
        if user is None or not user.national_id_hash:
            raise PharmacyAuthorizationBlocked("server_practitioner_mapping_required")
        practitioners = (
            self.db.query(Practitioner)
            .filter(
                Practitioner.national_id_hash == user.national_id_hash,
                Practitioner.is_active.is_(True),
                Practitioner.is_verified.is_(True),
                Practitioner.role.in_(allowed_roles),
            )
            .all()
        )
        if len(practitioners) != 1:
            raise PharmacyAuthorizationBlocked("server_practitioner_mapping_missing_or_ambiguous")
        return str(practitioners[0].id)

    def create_prescription(self, data: dict[str, Any]) -> Prescription:
        payload = dict(data)
        client_prescriber_id = payload.pop("prescriber_id", None)
        prescriber_id = self._resolve_server_practitioner_id(
            allowed_roles=(PractitionerRole.DOCTOR, PractitionerRole.SPECIALIST, PractitionerRole.CONSULTANT, PractitionerRole.RESIDENT),
        )
        if client_prescriber_id is not None and str(client_prescriber_id) != prescriber_id:
            raise PharmacyAuthorizationBlocked("client_prescriber_id_not_authoritative")
        payload["prescriber_id"] = prescriber_id
        rx = Prescription(**{k: v for k, v in payload.items() if hasattr(Prescription, k)})
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
        prescriber_id = self._resolve_server_practitioner_id(
            allowed_roles=(PractitionerRole.DOCTOR, PractitionerRole.SPECIALIST, PractitionerRole.CONSULTANT, PractitionerRole.RESIDENT),
        )
        if original.prescriber_id != prescriber_id:
            raise PharmacyAuthorizationBlocked("renewal_prescriber_mismatch")
        renewal = Prescription(
            patient_id=original.patient_id,
            encounter_id=original.encounter_id,
            prescriber_id=prescriber_id,
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

    def substitute_prescription_item(self, rx_id: str, item_id: str, new_drug_id: str, reason: str) -> PrescriptionItem | None:
        if not reason or not reason.strip():
            raise PharmacyAuthorizationBlocked("substitution_reason_required")
        self._resolve_server_practitioner_id(allowed_roles=(PractitionerRole.PHARMACIST,))
        rx = self.get_prescription(rx_id)
        item = self.db.query(PrescriptionItem).filter(
            PrescriptionItem.id == item_id,
            PrescriptionItem.prescription_id == rx_id,
            ~PrescriptionItem.is_deleted,
        ).first()
        if not rx or not item:
            return None
        if not rx.substitution_allowed or not item.substitution_allowed:
            raise PharmacyAuthorizationBlocked("substitution_not_allowed")
        new_drug = self.get_drug(new_drug_id)
        original_drug = self.get_drug(item.drug_catalog_id) if item.drug_catalog_id else None
        if not new_drug or not original_drug:
            return None
        original_generic = (original_drug.generic_name or "").strip().casefold()
        new_generic = (new_drug.generic_name or "").strip().casefold()
        if not original_generic or original_generic != new_generic:
            raise PharmacyAuthorizationBlocked("non_equivalent_substitution")
        item.substituted_from_drug_id = item.drug_catalog_id
        item.substitution_reason = reason.strip()
        item.substituted_by = str(self.user_id) if self.user_id is not None else None
        item.substituted_at = datetime.now(UTC)
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

    def create_pos_sale(self, data: dict[str, Any], request_id: str | None = None) -> PharmacySale:
        """Create an institution-scoped POS sale as one atomic database unit.

        The method validates all lines and FEFO allocations before mutating stock.
        It then writes the commercial sale, billing projection, stock movements,
        and durable EHR MedicationDispense records when a citizen/patient context
        is supplied. Payment remains synthetic and never stores card credentials.
        """
        if self.lab_id is None:
            raise ValueError("institutional pharmacy context is required")

        idempotency_key = str(data.get("idempotency_key") or "").strip() or None
        if idempotency_key:
            previous = self.db.query(PharmacySale).filter(
                PharmacySale.lab_id == self.lab_id,
                PharmacySale.idempotency_key == idempotency_key,
                ~PharmacySale.is_deleted,
            ).first()
            if previous is not None:
                return previous

        raw_lines = data.get("lines") or []
        if not raw_lines:
            raise ValueError("at least one sale line is required")

        issue_invoice = bool(data.get("issue_invoice", True))
        billing_patient_id = data.get("billing_patient_id")
        if issue_invoice and billing_patient_id is None:
            raise ValueError("billing_patient_id is required when issuing an invoice")

        today = date.today()
        allocations: list[dict[str, Any]] = []
        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        cost_total = Decimal("0.00")
        requested_patient_id = data.get("patient_id")
        requested_citizen_id = data.get("citizen_id")

        for raw_line in raw_lines:
            quantity = int(raw_line.get("quantity", 0))
            if quantity <= 0:
                raise ValueError("sale quantity must be positive")

            drug_id = raw_line.get("drug_catalog_id")
            barcode = str(raw_line.get("barcode") or "").strip() or None
            if drug_id is None and barcode:
                drug = self.db.query(DrugCatalog).filter(
                    DrugCatalog.barcode_gs1 == barcode,
                    ~DrugCatalog.is_deleted,
                    DrugCatalog.lab_id == self.lab_id,
                ).first()
                drug_id = drug.id if drug else None
            drug = self.get_drug(str(drug_id)) if drug_id is not None else None
            if drug is None or not drug.is_active:
                raise ValueError("drug not found or inactive")

            stock_query = self.db.query(StockLevel, DrugBatch).join(
                DrugBatch, DrugBatch.id == StockLevel.batch_id,
            ).filter(
                StockLevel.lab_id == self.lab_id,
                StockLevel.drug_catalog_id == drug.id,
                ~StockLevel.is_deleted,
                DrugBatch.lab_id == self.lab_id,
                ~DrugBatch.is_deleted,
                DrugBatch.is_quarantined.is_(False),
                DrugBatch.expiry_date >= today,
                StockLevel.available_quantity > 0,
            )
            requested_batch_id = raw_line.get("batch_id")
            if requested_batch_id:
                stock_query = stock_query.filter(StockLevel.batch_id == str(requested_batch_id))
            stock_rows = stock_query.order_by(DrugBatch.expiry_date.asc(), DrugBatch.id.asc()).with_for_update().all()
            remaining = quantity
            unit_price_override = raw_line.get("unit_price")
            line_discount = Decimal(str(raw_line.get("discount", "0"))).quantize(Decimal("0.01"))
            if line_discount < 0:
                raise ValueError("line discount cannot be negative")

            for stock, batch in stock_rows:
                if remaining <= 0:
                    break
                allocated = min(remaining, int(stock.available_quantity))
                unit_price = Decimal(str(unit_price_override if unit_price_override is not None else (batch.selling_price or "0"))).quantize(Decimal("0.01"))
                unit_cost = Decimal(str(batch.cost_price or "0")).quantize(Decimal("0.01"))
                allocated_discount = (line_discount * Decimal(allocated) / Decimal(quantity)).quantize(Decimal("0.01"))
                line_total = (unit_price * Decimal(allocated) - allocated_discount).quantize(Decimal("0.01"))
                line_cost = (unit_cost * Decimal(allocated)).quantize(Decimal("0.01"))
                if unit_price < 0 or unit_cost < 0 or line_total < 0:
                    raise ValueError("invalid price or discount")
                allocations.append({
                    "drug": drug,
                    "batch": batch,
                    "stock": stock,
                    "quantity": allocated,
                    "barcode": barcode or drug.barcode_gs1,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                    "discount": allocated_discount,
                    "line_total": line_total,
                    "line_cost": line_cost,
                    "prescription_id": raw_line.get("prescription_id"),
                    "quantity_unit": raw_line.get("quantity_unit") or "unit",
                    "days_supply": raw_line.get("days_supply"),
                    "dosage_instruction": raw_line.get("dosage_instruction"),
                    "route": raw_line.get("route"),
                    "frequency": raw_line.get("frequency"),
                })
                remaining -= allocated

            if remaining > 0:
                raise ValueError("insufficient non-expired stock")

        if not allocations:
            raise ValueError("no stock allocation available")

        subtotal = sum((item["unit_price"] * Decimal(item["quantity"]) for item in allocations), Decimal("0.00")).quantize(Decimal("0.01"))
        discount_total = sum((item["discount"] for item in allocations), Decimal("0.00")).quantize(Decimal("0.01"))
        total_amount = (subtotal - discount_total).quantize(Decimal("0.01"))
        cost_total = sum((item["line_cost"] for item in allocations), Decimal("0.00")).quantize(Decimal("0.01"))
        if total_amount < 0:
            raise ValueError("sale total cannot be negative")

        sale = PharmacySale(
            lab_id=self.lab_id,
            patient_id=requested_patient_id,
            citizen_id=requested_citizen_id,
            billing_patient_id=billing_patient_id,
            encounter_id=data.get("encounter_id"),
            sale_number=f"GULA-POS-{datetime.now(UTC):%y%m%d%H%M%S}-{uuid4().hex[:6].upper()}",
            status="completed",
            currency=str(data.get("currency") or "IQD"),
            subtotal=subtotal,
            discount=discount_total,
            total_amount=total_amount,
            cost_amount=cost_total,
            gross_profit=(total_amount - cost_total).quantize(Decimal("0.01")),
            payment_status="unpaid" if total_amount > 0 else "paid",
            payment_method=str(data.get("payment_method") or "synthetic_settlement"),
            idempotency_key=idempotency_key,
            created_by=self.user_id,
            updated_by=self.user_id,
            metadata_={"synthetic": True, "source": "pharmacy_pos", "request_id": request_id},
        )
        self.db.add(sale)
        self.db.flush()

        invoice = None
        if issue_invoice:
            billing_lines = [
                {
                    "service_code": f"PHARM-{item['drug'].code}",
                    "description": item["drug"].name_ar or item["drug"].name,
                    "quantity": item["quantity"],
                    "unit_amount": item["unit_price"],
                }
                for item in allocations
            ]
            invoice = BillingService(self.db).create_invoice(
                lab_id=self.lab_id,
                patient_id=int(str(billing_patient_id)),
                encounter_ref=str(data.get("encounter_ref") or sale.sale_number),
                lines=billing_lines,
                covered_amount=Decimal(str(data.get("covered_amount", "0"))),
                due_at=None,
                idempotency_key=f"pharmacy:{self.lab_id}:{idempotency_key}" if idempotency_key else None,
                actor_user_id=self.user_id,
                request_id=request_id,
            )
            sale.billing_invoice_id = invoice.id

        dispense_rows: list[tuple[PharmacySaleLine, MedicationDispense | None]] = []
        for line_number, item in enumerate(allocations, start=1):
            stock = item["stock"]
            batch = item["batch"]
            drug = item["drug"]
            stock.quantity -= item["quantity"]
            stock.available_quantity = stock.quantity - stock.reserved_quantity
            batch.quantity_remaining -= item["quantity"]

            sale_line = PharmacySaleLine(
                lab_id=self.lab_id,
                sale_id=sale.id,
                drug_catalog_id=drug.id,
                batch_id=batch.id,
                prescription_id=item["prescription_id"],
                line_number=line_number,
                barcode=item["barcode"],
                medication_name=drug.name,
                medication_name_ar=drug.name_ar,
                quantity=item["quantity"],
                quantity_unit=item["quantity_unit"],
                lot_number=batch.batch_number,
                expiry_date=batch.expiry_date,
                unit_price=item["unit_price"],
                unit_cost=item["unit_cost"],
                discount=item["discount"],
                line_total=item["line_total"],
                line_cost=item["line_cost"],
                created_by=self.user_id,
                updated_by=self.user_id,
                metadata_={"synthetic": True},
            )
            self.db.add(sale_line)
            self.db.flush()

            movement = StockMovement(
                lab_id=self.lab_id,
                drug_catalog_id=drug.id,
                batch_id=batch.id,
                warehouse_id=stock.warehouse_id,
                store_id=stock.store_id,
                movement_type=StockMovementType.DISPENSED,
                quantity=item["quantity"],
                reference_type="pharmacy_sale",
                reference_id=sale.id,
                performed_by=str(self.user_id) if self.user_id else None,
                notes="POS sale; FEFO allocation",
            )
            self.db.add(movement)

            record_patient_id = requested_patient_id or requested_citizen_id
            dispense = None
            if record_patient_id:
                dispense = MedicationDispense(
                    patient_id=str(record_patient_id),
                    citizen_id=str(requested_citizen_id) if requested_citizen_id else None,
                    medication_request_id=None,
                    medication_code=drug.code,
                    medication_code_system="GULA-PHARMACY",
                    medication_name=drug.name,
                    medication_name_ar=drug.name_ar,
                    medication_brand=drug.brand_name,
                    medication_form=str(drug.form.value if hasattr(drug.form, "value") else drug.form or ""),
                    status="completed",
                    category="outpatient",
                    quantity=item["quantity"],
                    quantity_unit=item["quantity_unit"],
                    days_supply=item["days_supply"],
                    dosage_instruction=item["dosage_instruction"],
                    route=item["route"],
                    frequency=item["frequency"],
                    dispensed_at=datetime.now(UTC),
                    prepared_at=datetime.now(UTC),
                    metadata_={
                        "source": "pharmacy_pos",
                        "synthetic": True,
                        "pharmacy_sale_id": sale.id,
                        "pharmacy_sale_number": sale.sale_number,
                        "billing_invoice_id": invoice.id if invoice else None,
                        "lot_number": batch.batch_number,
                        "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                    },
                )
                self.db.add(dispense)
                self.db.flush()
                sale_line.medication_dispense_id = dispense.id
            dispense_rows.append((sale_line, dispense))

        self.db.flush()
        if invoice is not None and total_amount > 0:
            BillingService(self.db).simulate_settlement(
                invoice_id=invoice.id,
                lab_id=self.lab_id,
                actor_user_id=self.user_id,
                request_id=request_id,
            )
            sale.payment_status = "paid"
        self._audit(
            "pharmacy.pos.sale.create",
            "pharmacy_sale",
            sale.id,
            f"Created {sale.sale_number} with {len(dispense_rows)} allocated lines",
        )
        self.db.flush()
        return sale

    def get_pos_sale(self, sale_id: str) -> PharmacySale | None:
        query = self.db.query(PharmacySale).filter(
            PharmacySale.id == sale_id,
            ~PharmacySale.is_deleted,
        )
        if self.lab_id:
            query = query.filter(PharmacySale.lab_id == self.lab_id)
        return cast(PharmacySale | None, query.first())

    def list_pos_sales(self, *, citizen_id: str | None = None, skip: int = 0, limit: int = 50) -> list[PharmacySale]:
        query = self.db.query(PharmacySale).filter(~PharmacySale.is_deleted)
        if self.lab_id:
            query = query.filter(PharmacySale.lab_id == self.lab_id)
        if citizen_id:
            query = query.filter(PharmacySale.citizen_id == citizen_id)
        return cast(list[PharmacySale], query.order_by(PharmacySale.sold_at.desc()).offset(skip).limit(limit).all())

    def get_pos_summary(self, days: int = 30) -> dict[str, Any]:
        if days < 1 or days > 3650:
            raise ValueError("days must be between 1 and 3650")
        cutoff = datetime.now(UTC) - timedelta(days=days)
        query = self.db.query(
            func.count(PharmacySale.id),
            func.coalesce(func.sum(PharmacySale.total_amount), 0),
            func.coalesce(func.sum(PharmacySale.cost_amount), 0),
            func.coalesce(func.sum(PharmacySale.gross_profit), 0),
        ).filter(
            PharmacySale.sold_at >= cutoff,
            PharmacySale.status == "completed",
            ~PharmacySale.is_deleted,
        )
        if self.lab_id:
            query = query.filter(PharmacySale.lab_id == self.lab_id)
        sale_count, sales_total, cost_total, profit_total = query.one()

        units_query = self.db.query(func.coalesce(func.sum(PharmacySaleLine.quantity), 0)).join(
            PharmacySale, PharmacySale.id == PharmacySaleLine.sale_id,
        ).filter(
            PharmacySale.sold_at >= cutoff,
            PharmacySale.status == "completed",
            ~PharmacySale.is_deleted,
            ~PharmacySaleLine.is_deleted,
        )
        if self.lab_id:
            units_query = units_query.filter(PharmacySale.lab_id == self.lab_id)
        units_sold = int(units_query.scalar() or 0)

        recent_sales = self.db.query(
            PharmacySaleLine.drug_catalog_id,
            func.max(PharmacySale.sold_at).label("last_sold_at"),
        ).join(
            PharmacySale, PharmacySale.id == PharmacySaleLine.sale_id,
        ).filter(
            PharmacySale.status == "completed",
            ~PharmacySale.is_deleted,
            ~PharmacySaleLine.is_deleted,
        )
        if self.lab_id:
            recent_sales = recent_sales.filter(PharmacySale.lab_id == self.lab_id)
        last_sale_by_drug = dict(recent_sales.group_by(PharmacySaleLine.drug_catalog_id).all())

        stagnant: list[dict[str, Any]] = []
        stock_query = self.db.query(StockLevel).filter(~StockLevel.is_deleted, StockLevel.available_quantity > 0)
        if self.lab_id:
            stock_query = stock_query.filter(StockLevel.lab_id == self.lab_id)
        for stock in stock_query.all():
            last_sold_at = last_sale_by_drug.get(stock.drug_catalog_id)
            if last_sold_at is not None and last_sold_at.tzinfo is None:
                last_sold_at = last_sold_at.replace(tzinfo=UTC)
            if last_sold_at is None or last_sold_at < cutoff:
                drug = self.db.query(DrugCatalog).filter(DrugCatalog.id == stock.drug_catalog_id).first()
                stagnant.append({
                    "drug_id": stock.drug_catalog_id,
                    "drug_name": drug.name if drug else "Unknown",
                    "available_quantity": stock.available_quantity,
                    "last_sold_at": last_sold_at.isoformat() if last_sold_at else None,
                })

        alerts = self.get_stock_alerts()
        return {
            "period_days": days,
            "sale_count": int(sale_count or 0),
            "units_sold": units_sold,
            "sales_total": str(Decimal(str(sales_total or 0)).quantize(Decimal("0.01"))),
            "cost_total": str(Decimal(str(cost_total or 0)).quantize(Decimal("0.01"))),
            "gross_profit": str(Decimal(str(profit_total or 0)).quantize(Decimal("0.01"))),
            "low_stock_count": len(alerts["low_stock"]),
            "expiring_soon_count": len(alerts["expiring_soon"]),
            "stagnant_items": stagnant[:100],
            "synthetic": True,
        }

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
