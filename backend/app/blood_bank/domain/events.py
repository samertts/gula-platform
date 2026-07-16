from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class DonorRegistered(NationalDomainEvent):
    event_type: str = "bloodbank.donor.registered"
    aggregate_type: str = "BloodDonor"
    donor_id: str = ""
    blood_group: str = ""


@dataclass
class DonorDeferred(NationalDomainEvent):
    event_type: str = "bloodbank.donor.deferred"
    aggregate_type: str = "BloodDonor"
    donor_id: str = ""
    reason: str = ""
    deferral_days: int = 0


@dataclass
class DonationCompleted(NationalDomainEvent):
    event_type: str = "bloodbank.donation.completed"
    aggregate_type: str = "BloodDonation"
    donation_id: str = ""
    donor_id: str = ""
    donation_type: str = ""
    volume_ml: float = 0.0


@dataclass
class ComponentPrepared(NationalDomainEvent):
    event_type: str = "bloodbank.component.prepared"
    aggregate_type: str = "BloodComponent"
    component_id: str = ""
    blood_component: str = ""
    source_donation_id: str = ""


@dataclass
class InventoryUpdated(NationalDomainEvent):
    event_type: str = "bloodbank.inventory.updated"
    aggregate_type: str = "BloodInventory"
    blood_group: str = ""
    component: str = ""
    quantity_change: int = 0


@dataclass
class CrossmatchCompleted(NationalDomainEvent):
    event_type: str = "bloodbank.crossmatch.completed"
    aggregate_type: str = "Crossmatch"
    crossmatch_id: str = ""
    patient_id: str = ""
    result: str = ""


@dataclass
class TransfusionStarted(NationalDomainEvent):
    event_type: str = "bloodbank.transfusion.started"
    aggregate_type: str = "Transfusion"
    transfusion_id: str = ""
    patient_id: str = ""
    unit_id: str = ""


@dataclass
class TransfusionReactionReported(NationalDomainEvent):
    event_type: str = "bloodbank.transfusion.reaction"
    aggregate_type: str = "Transfusion"
    transfusion_id: str = ""
    severity: str = ""
    reaction_type: str = ""


@dataclass
class CriticalStockAlert(NationalDomainEvent):
    event_type: str = "bloodbank.stock.critical_alert"
    aggregate_type: str = "BloodInventory"
    blood_group: str = ""
    component: str = ""
    current_quantity: int = 0


@dataclass
class UnitDiscarded(NationalDomainEvent):
    event_type: str = "bloodbank.unit.discarded"
    aggregate_type: str = "BloodUnit"
    unit_id: str = ""
    reason: str = ""
