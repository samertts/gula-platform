# كتالوج مسارات وإجراءات واجهة GULA v3

> أُنشئ آليًا من مسارات الواجهة وملفات الصفحات. «مرجع API محلي» دليل فهرسة فقط؛ لا يثبت بمفرده أن مسار الخلفية منفذ أو أن التفويض الخادمي يتحقق منه.

**عدد المسارات المفهرسة:** 77

| المسار | المكوّن | الملف | مراجع API محلية | مؤشرات الحالة | الإجراءات المرئية | التصنيف الأولي |
|---|---|---|---|---|---|---|
| `admin/audit` | `AdminAuditPage` | `pages/admin/AdminPages.tsx` | adminApi.labs، adminApi.users، adminApi.auditLogs | isLoading، error، Loading | أزرار: 2؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `admin/labs` | `AdminLabsPage` | `pages/admin/AdminPages.tsx` | adminApi.labs، adminApi.users، adminApi.auditLogs | isLoading، error، Loading | أزرار: 2؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `admin/users` | `AdminUsersPage` | `pages/admin/AdminPages.tsx` | adminApi.labs، adminApi.users، adminApi.auditLogs | isLoading، error، Loading | أزرار: 2؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `ai` | `AIPage` | `pages/ai/AIPage.tsx` | aiApi.pending | isLoading، error، EmptyState، Loading | أزرار: 3؛ onClick: 3؛ mutations: 0 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `ai-fabric` | `AiFabricPageLazy` | `pages/ai-fabric/AiFabricPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `ai-platform` | `AiPlatformPage` | `pages/ai-platform/AiPlatformPage.tsx` | aiPlatformApi.metrics، aiPlatformApi.governanceModels، aiPlatformApi.governancePrompts، aiPlatformApi.search، aiPlatformApi.ragQuery، aiPlatformApi.knowledgeGraphInfo، aiPlatformApi.knowledgeGraphSearch، aiPlatformApi.agentTools، aiPlatformApi.agentExecute، aiPlatformApi.createSession، aiPlatformApi.sessionMessage | isLoading، error، EmptyState، Loading | أزرار: 7؛ onClick: 2؛ mutations: 0 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `alerts` | `CriticalAlertsPage` | `pages/alerts/CriticalAlertsPage.tsx` | criticalAlertsApi.list | isLoading، error، EmptyState، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `biomedical` | `BiomedicalApiPageLazy` | `pages/biomedical/BiomedicalApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `blood-bank` | `BloodBankApiPageLazy` | `pages/blood-bank/BloodBankApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/clinical-foundation` | `CapabilitiesClinicalFoundationPageLazy` | `pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/document-management` | `CapabilitiesDocumentManagementPageLazy` | `pages/capabilities/document-management/CapabilitiesDocumentManagementPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/encounter-management` | `CapabilitiesEncounterManagementPageLazy` | `pages/capabilities/encounter-management/CapabilitiesEncounterManagementPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/healthcare-consent` | `CapabilitiesHealthcareConsentPageLazy` | `pages/capabilities/healthcare-consent/CapabilitiesHealthcareConsentPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/provider-management` | `CapabilitiesProviderManagementPageLazy` | `pages/capabilities/provider-management/CapabilitiesProviderManagementPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/reporting-service` | `CapabilitiesReportingServicePageLazy` | `pages/capabilities/reporting-service/CapabilitiesReportingServicePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/search-service` | `CapabilitiesSearchServicePageLazy` | `pages/capabilities/search-service/CapabilitiesSearchServicePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/storage-service` | `CapabilitiesStorageServicePageLazy` | `pages/capabilities/storage-service/CapabilitiesStorageServicePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `capabilities/workflow-engine` | `CapabilitiesWorkflowEnginePageLazy` | `pages/capabilities/workflow-engine/CapabilitiesWorkflowEnginePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `certification` | `CertificationPageLazy` | `pages/certification/CertificationPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `citizen` | `CitizenWorkspacePageLazy` | `pages/citizen-platform/CitizenWorkspacePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `citizen-platform` | `CitizenPlatformPageLazy` | `pages/citizen-platform/CitizenPlatformPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `command-center` | `CommandCenterApiPageLazy` | `pages/command-center/CommandCenterApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `command-intelligence` | `CommandIntelligencePageLazy` | `pages/command-intelligence/CommandIntelligencePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `compliance` | `CompliancePage` | `pages/compliance/CompliancePage.tsx` | complianceApi.systemStatus | isLoading، error، Loading | أزرار: 3؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `control-plane` | `ControlPlanePageLazy` | `pages/control-plane/ControlPlanePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `critical-care` | `CriticalCareApiPageLazy` | `pages/critical-care/CriticalCareApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `dashboard` | `DashboardPage` | `pages/dashboard/DashboardPage.tsx` | dashboardApi.demo | isLoading، isError، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `edge` | `EdgePage` | `pages/edge/EdgePage.tsx` | edgeApi.listDevices، edgeApi.quarantineDevice، edgeApi.revokeDevice، edgeApi.reinstateDevice، edgeApi.listTasks، edgeApi.fleetSummary | isLoading، error، EmptyState، Loading | أزرار: 6؛ onClick: 7؛ mutations: 4 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `ems` | `EmsApiPageLazy` | `pages/ems/EmsApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `fhir` | `FhirPage` | `pages/fhir/FhirPage.tsx` | — | — | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `financial` | `FinancialPage` | `pages/financial/FinancialPage.tsx` | financialApi.billingStatus، financialApi.billingRates، financialApi.listInvoices، financialApi.listPayments، financialApi.listTransactions | isLoading، error، EmptyState، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `health-data` | `HealthDataPageLazy` | `pages/health-data/HealthDataPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `hospital` | `HospitalPage` | `pages/hospital/HospitalPage.tsx` | hospitalApi.list، hospitalApi.create، hospitalApi.listDepartments، hospitalApi.listUnits، hospitalApi.createDepartment، hospitalApi.occupancy | isLoading، error، EmptyState، Loading | أزرار: 8؛ onClick: 8؛ mutations: 3 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `identity` | `IdentityPage` | `pages/identity/IdentityPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `integration` | `IntegrationPageLazy` | `pages/integration/IntegrationPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `integration/connectors` | `IntegrationConnectorsPageLazy` | `pages/integration/connectors/IntegrationConnectorsPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `kernel` | `KernelPageLazy` | `pages/kernel/KernelPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `labs` | `LabsPage` | `pages/labs/LabsPage.tsx` | adminApi.labs | isLoading، Loading | أزرار: 1؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `lifecycle-platform` | `LifecyclePlatformApiPageLazy` | `pages/lifecycle-platform/LifecyclePlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `login` | `LoginPage` | `pages/auth/LoginPage.tsx` | — | error، Loading | أزرار: 4؛ onClick: 3؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national-data` | `NationalDataPage` | `pages/national-data/NationalDataPage.tsx` | nationalDataApi.listGoldenRecords، nationalDataApi.listDataCatalog، nationalDataApi.listDeidentificationJobs، nationalDataApi.recordDataQualityCheck | isLoading، error، EmptyState، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `national/background-platform` | `NationalBackgroundPlatformApiPageLazy` | `pages/national/background-platform/NationalBackgroundPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/document-platform` | `NationalDocumentPlatformApiPageLazy` | `pages/national/document-platform/NationalDocumentPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/ecosystem` | `NationalEcosystemPageLazy` | `pages/national/ecosystem/NationalEcosystemPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/ecosystem/gateway` | `NationalEcosystemGatewayPageLazy` | `pages/national/ecosystem/gateway/NationalEcosystemGatewayPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/notification-platform` | `NationalNotificationPlatformApiPageLazy` | `pages/national/notification-platform/NationalNotificationPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/observability` | `NationalObservabilityApiPageLazy` | `pages/national/observability/NationalObservabilityApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/rules-engine` | `NationalRulesEngineApiPageLazy` | `pages/national/rules-engine/NationalRulesEngineApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/scheduling-platform` | `NationalSchedulingPlatformApiPageLazy` | `pages/national/scheduling-platform/NationalSchedulingPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/search-platform` | `NationalSearchPlatformApiPageLazy` | `pages/national/search-platform/NationalSearchPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/task-engine` | `NationalTaskEngineApiPageLazy` | `pages/national/task-engine/NationalTaskEngineApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `national/workflow-runtime` | `NationalWorkflowRuntimeApiPageLazy` | `pages/national/workflow-runtime/NationalWorkflowRuntimeApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/adaptive-auth` | `NiamAdaptiveAuthPage` | `pages/niam/AdaptiveAuthPage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/certificates` | `NiamCertificatesPage` | `pages/niam/CertificatesPage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/federation` | `NiamFederationPage` | `pages/niam/FederationPage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/governance` | `NiamGovernancePage` | `pages/niam/GovernancePage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/lifecycle` | `NiamLifecyclePage` | `pages/niam/LifecyclePage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/trust` | `NiamTrustPage` | `pages/niam/TrustPage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `niam/workflows` | `NiamWorkflowsPage` | `pages/niam/WorkflowsPage.tsx` | — | isLoading، Loading | أزرار: 3؛ onClick: 2؛ mutations: 2 | إجراءات مرئية بلا مرجع API محلي واضح |
| `notifications` | `NotificationsPage` | `pages/notifications/NotificationsPage.tsx` | notificationsApi.send، notificationsApi.history | isLoading، error، Loading | أزرار: 4؛ onClick: 4؛ mutations: 2 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `orders` | `OrdersPage` | `pages/orders/OrdersPage.tsx` | — | isLoading، error، EmptyState، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `patient-card` | `PatientCardPage` | `pages/patient-card/PatientCardPage.tsx` | patientCardApi.get | isLoading، error، EmptyState، Loading | أزرار: 2؛ onClick: 2؛ mutations: 0 | يتطلب تحققًا يدويًا من معالجات الإجراءات |
| `patients` | `PatientsPage` | `pages/patients/PatientsPage.tsx` | — | isLoading، error، EmptyState، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `pharmacy` | `PharmacyPageLazy` | `pages/pharmacy/PharmacyPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `pilot-platform` | `PilotPlatformApiPageLazy` | `pages/pilot-platform/PilotPlatformApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `platform` | `PlatformPageLazy` | `pages/platform/PlatformPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `profile` | `ProfilePage` | `pages/profile/ProfilePage.tsx` | — | — | أزرار: 1؛ onClick: 0؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `public-health` | `PublicHealthApiPageLazy` | `pages/public-health/PublicHealthApiPage.tsx` | — | isLoading، Loading | أزرار: 1؛ onClick: 1؛ mutations: 0 | إجراءات مرئية بلا مرجع API محلي واضح |
| `qc` | `QCPage` | `pages/qc/QCPage.tsx` | qcApi.list | isLoading، error، EmptyState، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `register` | `RegisterPage` | `pages/auth/RegisterPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `reports` | `ReportsPage` | `pages/reports/ReportsPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `results` | `ResultsPage` | `pages/results/ResultsPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `samples` | `SamplesPage` | `pages/samples/SamplesPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `security` | `SecurityPage` | `pages/security/SecurityPage.tsx` | securityApi.status | isLoading، error، Loading | أزرار: 2؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `settings` | `SettingsPage` | `pages/settings/SettingsPage.tsx` | — | — | أزرار: 0؛ onClick: 0؛ mutations: 0 | سطح قالب أو عرض ساكن محتمل |
| `stats` | `StatsPage` | `pages/stats/StatsPage.tsx` | statsApi.summary | isLoading، error، Loading | أزرار: 0؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |
| `tiers` | `TiersPage` | `pages/tiers/TiersPage.tsx` | tiersApi.list، tiersApi.my | isLoading، Loading | أزرار: 1؛ onClick: 0؛ mutations: 0 | يحتاج مواءمة مع عقد الخلفية |

## حدود الكتالوج

يسجل الكتالوج استدعاءات تحمل لاحقة `Api` ومعالجات وأزرارًا في ملف الصفحة نفسه. ولا يكشف الاستدعاءات المارة عبر مكوّنات فرعية أو hooks، لذلك تراجع الأسطح المصنفة عالية المخاطر يدويًا مقابل عقد الخلفية وسجل الصلاحيات قبل تغيير سلوك المستخدم.
