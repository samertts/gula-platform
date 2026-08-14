from fastapi import APIRouter

from .advance_directive import router as advance_directive_router
from .cds import router as cds_router
from .citizen import router as citizen_router
from .consent import router as consent_router
from .encounter import router as encounter_router
from .family import router as family_router
from .fhir import router as fhir_router
from .health_card import router as health_card_router
from .identity import router as identity_router
from .interop import router as interop_router
from .medication_catalog import router as medication_catalog_router
from .observation import router as observation_router
from .reference import router as reference_router
from .referral import router as referral_router
from .security import router as security_router
from .vital_signs import router as vital_signs_router

national_router = APIRouter(prefix="/national", tags=["National Healthcare Domain"])
national_router.include_router(advance_directive_router)
national_router.include_router(cds_router)
national_router.include_router(citizen_router)
national_router.include_router(consent_router)
national_router.include_router(encounter_router)
national_router.include_router(family_router)
national_router.include_router(fhir_router)
national_router.include_router(health_card_router)
national_router.include_router(identity_router)
national_router.include_router(interop_router)
national_router.include_router(medication_catalog_router)
national_router.include_router(observation_router)
national_router.include_router(reference_router)
national_router.include_router(referral_router)
national_router.include_router(security_router)
national_router.include_router(vital_signs_router)
