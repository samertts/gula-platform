from __future__ import annotations

import logging
from typing import Any

from app.citizen_platform.accessibility import AccessibilityService
from app.citizen_platform.appointments import (
    AppointmentService,
)
from app.citizen_platform.certificates import (
    HealthCertificateService,
)
from app.citizen_platform.emergency import (
    EmergencyAccessService,
)
from app.citizen_platform.family import FamilyAccountService
from app.citizen_platform.identity import (
    HealthIdentityService,
)
from app.citizen_platform.laboratory import CitizenLabService
from app.citizen_platform.medications import (
    MedicationService,
)
from app.citizen_platform.notifications import CitizenNotificationService
from app.citizen_platform.offline import CitizenOfflineService
from app.citizen_platform.phr import PHRService
from app.citizen_platform.preventive import (
    VaccinationService,
)
from app.citizen_platform.privacy import (
    ConsentEngine,
)
from app.citizen_platform.radiology import CitizenRadiologyService
from app.citizen_platform.telemedicine import TelemedicineService

logger = logging.getLogger("gula.citizen.sdk")


class CitizenSDK:
    def __init__(
        self,
        identity: HealthIdentityService,
        appointments: AppointmentService,
        medications: MedicationService,
        laboratory: CitizenLabService,
        radiology: CitizenRadiologyService,
        family: FamilyAccountService,
        preventive: VaccinationService,
        telemedicine: TelemedicineService,
        phr: PHRService,
        notifications: CitizenNotificationService,
        emergency: EmergencyAccessService,
        offline: CitizenOfflineService,
        accessibility: AccessibilityService,
        privacy: ConsentEngine,
        certificates: HealthCertificateService,
    ) -> None:
        self.identity = identity
        self.appointments = appointments
        self.medications = medications
        self.laboratory = laboratory
        self.radiology = radiology
        self.family = family
        self.preventive = preventive
        self.telemedicine = telemedicine
        self.phr = phr
        self.notifications = notifications
        self.emergency = emergency
        self.offline = offline
        self.accessibility = accessibility
        self.privacy = privacy
        self.certificates = certificates

    async def get_citizen_overview(self, citizen_id: str) -> dict[str, Any]:
        return {
            "appointments": {
                "upcoming": len(
                    await self.appointments.list_appointments(citizen_id, status="booked"),
                ),
            },
            "medications": {
                "active": len(self.medications.get_active_medications(citizen_id)),
            },
            "laboratory": {
                "recent_results": len(self.laboratory.get_results(citizen_id, limit=5)),
            },
            "radiology": {
                "recent_studies": len(self.radiology.get_studies(citizen_id, limit=5)),
            },
            "family": {
                "members": len(self.family.get_family_members(citizen_id)),
            },
            "notifications": {
                "unread": self.notifications.get_unread_count(citizen_id),
            },
            "certificates": {
                "active": len(self.certificates.get_certificates(citizen_id, status="active")),
            },
        }


class MobileAPI:
    def __init__(self, sdk: CitizenSDK) -> None:
        self._sdk = sdk

    async def get_dashboard(self, citizen_id: str) -> dict[str, Any]:
        return await self._sdk.get_citizen_overview(citizen_id)

    async def get_profile(self, citizen_id: str) -> dict[str, Any]:
        return {
            "citizen_id": citizen_id,
            "family": [m.full_name for m in self._sdk.family.get_family_members(citizen_id)],
            "emergency_contacts": [
                {"name": c.name, "phone": c.phone}
                for c in self._sdk.emergency.get_contacts(citizen_id)
            ],
            "active_consents": len(self._sdk.privacy.get_active_consents(citizen_id)),
        }

    async def get_health_summary(self, citizen_id: str) -> dict[str, Any]:
        return {
            "medications": [
                {
                    "name": m.medication_name,
                    "dosage": m.dosage_text,
                    "status": m.status,
                }
                for m in self._sdk.medications.get_active_medications(citizen_id)
            ],
            "lab_results": [
                {
                    "test": r.test_name,
                    "value": r.value,
                    "flag": r.flag,
                }
                for r in self._sdk.laboratory.get_results(citizen_id, limit=10)
            ],
            "vaccinations": [
                {
                    "vaccine": v.vaccine_name,
                    "date": v.date_administered,
                    "status": v.status,
                }
                for v in self._sdk.preventive.get_vaccination_history(citizen_id)
            ],
        }

    async def get_notifications(self, citizen_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": n.id,
                "title": n.title,
                "title_ar": n.title_ar,
                "message": n.message,
                "message_ar": n.message_ar,
                "type": n.alert_type,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in self._sdk.notifications.get_notifications(citizen_id)
        ]

    def get_app_config(self, citizen_id: str) -> dict[str, Any]:
        prefs = self._sdk.accessibility.get_preferences(citizen_id)
        return {
            "language": prefs.language,
            "font_size": prefs.font_size,
            "high_contrast": prefs.high_contrast,
            "reduced_motion": prefs.reduced_motion,
            "text_to_speech": prefs.text_to_speech,
        }
