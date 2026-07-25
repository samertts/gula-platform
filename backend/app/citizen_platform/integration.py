from __future__ import annotations

import logging
from typing import Any

from app.citizen_platform.accessibility import AccessibilityService, LocalizationService
from app.citizen_platform.appointments import (
    AppointmentService,
)
from app.citizen_platform.certificates import (
    HealthCertificateService,
    InsuranceInfoService,
    MedicalLeaveService,
    ReferralService,
)
from app.citizen_platform.emergency import (
    CriticalInfoService,
    EmergencyAccessService,
    EmergencyContactService,
)
from app.citizen_platform.family import FamilyAccountService
from app.citizen_platform.identity import (
    HealthIdentityService,
)
from app.citizen_platform.laboratory import CitizenLabService
from app.citizen_platform.medications import (
    MedicationService,
)
from app.citizen_platform.notifications import AlertService, CitizenNotificationService
from app.citizen_platform.offline import CitizenOfflineService, OfflineSyncEngine
from app.citizen_platform.phr import DocumentUploader, PHRService, StorageService
from app.citizen_platform.preventive import (
    HealthCampaignService,
    RiskAssessment,
    ScreeningService,
    VaccinationService,
)
from app.citizen_platform.privacy import (
    AccessLogs,
    ConsentEngine,
    DataSharingControls,
    EmergencyBreakGlass,
    PrivacyDashboard,
)
from app.citizen_platform.radiology import CitizenRadiologyService
from app.citizen_platform.sdk import CitizenSDK, MobileAPI
from app.citizen_platform.telemedicine import FollowUpService, SecureMessaging, TelemedicineService
from app.national.scheduling_platform import SchedulingPlatformService
from app.national.services.citizen_service import CitizenService as NationalCitizenService
from app.platform.documents import DocumentService as PlatformDocumentService
from app.platform.i18n import TranslationService
from app.platform.notifications import NotificationService as PlatformNotificationService
from app.platform.sync import SyncService as PlatformSyncService

logger = logging.getLogger("gula.citizen.integration")


class CitizenPlatform:
    def __init__(self) -> None:
        self.sdk: CitizenSDK | None = None
        self.mobile_api: MobileAPI | None = None
        self._initialized = False

    def initialize(
        self,
        citizen_service: NationalCitizenService | None = None,
        scheduling_service: Any = None,
        encryption_key: str = "",
        hmac_key: str = "",
    ) -> None:
        if self._initialized:
            logger.warning("CitizenPlatform already initialized")
            return

        platform_docs = PlatformDocumentService()
        platform_notifications = PlatformNotificationService()
        platform_sync = PlatformSyncService()
        translation = TranslationService()
        access_logs = AccessLogs()

        identity = HealthIdentityService(
            citizen_service=citizen_service
            or NationalCitizenService.__new__(NationalCitizenService),
            encryption_key=encryption_key,
            hmac_key=hmac_key,
        )

        appointments = AppointmentService(
            scheduling_service=scheduling_service
            or SchedulingPlatformService.__new__(SchedulingPlatformService),
        )

        medications = MedicationService()
        laboratory = CitizenLabService()
        radiology = CitizenRadiologyService()
        family = FamilyAccountService()
        vaccinations = VaccinationService()
        ScreeningService()
        HealthCampaignService()
        RiskAssessment()
        telemedicine = TelemedicineService()
        SecureMessaging()
        FollowUpService()

        phr = PHRService(document_service=platform_docs)
        DocumentUploader(document_service=platform_docs)
        StorageService()

        notifications = CitizenNotificationService(notification_service=platform_notifications)
        AlertService(notification_service=notifications)

        emergency_access = EmergencyAccessService()
        EmergencyContactService()
        CriticalInfoService()

        offline = CitizenOfflineService(sync_service=platform_sync)
        OfflineSyncEngine(platform_sync=platform_sync)

        accessibility = AccessibilityService()
        LocalizationService(translation_service=translation)

        consent_engine = ConsentEngine()
        PrivacyDashboard(consent_engine=consent_engine)
        DataSharingControls(consent_engine=consent_engine)
        EmergencyBreakGlass(access_logs=access_logs)

        certificates = HealthCertificateService()
        MedicalLeaveService()
        ReferralService()
        InsuranceInfoService()

        self.sdk = CitizenSDK(
            identity=identity,
            appointments=appointments,
            medications=medications,
            laboratory=laboratory,
            radiology=radiology,
            family=family,
            preventive=vaccinations,
            telemedicine=telemedicine,
            phr=phr,
            notifications=notifications,
            emergency=emergency_access,
            offline=offline,
            accessibility=accessibility,
            privacy=consent_engine,
            certificates=certificates,
        )

        self.mobile_api = MobileAPI(sdk=self.sdk)
        self._initialized = True
        logger.info("CitizenPlatform initialized successfully")


_platform: CitizenPlatform | None = None


def get_platform() -> CitizenPlatform:
    global _platform
    if _platform is None:
        _platform = CitizenPlatform()
    return _platform


def get_sdk() -> CitizenSDK:
    platform = get_platform()
    if platform.sdk is None:
        platform.initialize()
    assert platform.sdk is not None
    return platform.sdk


def get_mobile_api() -> MobileAPI:
    platform = get_platform()
    if platform.mobile_api is None:
        platform.initialize()
    assert platform.mobile_api is not None
    return platform.mobile_api


__all__ = [
    "CitizenPlatform",
    "get_mobile_api",
    "get_platform",
    "get_sdk",
]
