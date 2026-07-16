from backend.app.integration.healthcare.blood_bank import BloodBankIntegration
from backend.app.integration.healthcare.hospitals import HospitalIntegration
from backend.app.integration.healthcare.insurance import InsuranceIntegration
from backend.app.integration.healthcare.laboratories import LaboratoryIntegration
from backend.app.integration.healthcare.pharmacies import PharmacyIntegration
from backend.app.integration.healthcare.primary_care import PrimaryCareIntegration
from backend.app.integration.healthcare.radiology import RadiologyIntegration
from backend.app.integration.healthcare.vaccination import VaccinationIntegration

__all__ = [
    "BloodBankIntegration",
    "HospitalIntegration",
    "InsuranceIntegration",
    "LaboratoryIntegration",
    "PharmacyIntegration",
    "PrimaryCareIntegration",
    "RadiologyIntegration",
    "VaccinationIntegration",
]
