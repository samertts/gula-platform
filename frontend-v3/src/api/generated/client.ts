// AUTO-GENERATED API CLIENT — DO NOT EDIT
// Generated from backend/ route files
// Run: python scripts/generate_frontend_client.py

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";

// ── adaptive-auth ──

export const adaptive_authApi = {
  evaluateRisk: (data: unknown) =>
    api.post(`/niam/adaptive-auth/evaluate`, data).then(r => r.data),
  getRiskHistory: (params: Record<string, string | number>) =>
    api.get(`/niam/adaptive-auth/risk-history/${params.account_id}`).then(r => r.data),
  createMfaChallenge: (data: unknown) =>
    api.post(`/niam/adaptive-auth/mfa/challenge`, data).then(r => r.data),
  verifyMfa: (data: unknown) =>
    api.post(`/niam/adaptive-auth/mfa/verify`, data).then(r => r.data),
  listRiskPolicies: () =>
    api.get(`/niam/adaptive-auth/policies`).then(r => r.data),
  createSessionPolicy: (data: unknown) =>
    api.post(`/niam/adaptive-auth/session-policies`, data).then(r => r.data),
  getActiveSessionCount: (params: Record<string, string | number>) =>
    api.get(`/niam/adaptive-auth/active-sessions/${params.account_id}`).then(r => r.data),
};

// ── admin ──

export const adminApi = {
  createPortal: (data: unknown) =>
    api.post(`/niam/admin/portals`, data).then(r => r.data),
  listOrgPortals: (params: Record<string, string | number>) =>
    api.get(`/niam/admin/portals/organization/${params.org_id}`).then(r => r.data),
  createSubscription: (data: unknown) =>
    api.post(`/niam/admin/subscriptions`, data).then(r => r.data),
  getSubscription: (params: Record<string, string | number>) =>
    api.get(`/niam/admin/subscriptions/${params.org_id}`).then(r => r.data),
  getAuditLog: (params: Record<string, string | number>) =>
    api.get(`/niam/admin/audit-log/${params.org_id}`).then(r => r.data),
  createFhirConnection: (data: unknown) =>
    api.post(`/niam/admin/fhir-connections`, data).then(r => r.data),
  listFhirConnections: (params: Record<string, string | number>) =>
    api.get(`/niam/admin/fhir-connections/organization/${params.org_id}`).then(r => r.data),
};

// ── ai_fabric ──

export const ai_fabricApi = {
  fabricHealth: () =>
    api.get(`/ai/fabric/health`).then(r => r.data),
  fabricChat: (data: unknown) =>
    api.post(`/ai/fabric/chat`, data).then(r => r.data),
  fabricEmbed: (data: unknown) =>
    api.post(`/ai/fabric/embed`, data).then(r => r.data),
  listProviders: () =>
    api.get(`/ai/fabric/gateway/providers`).then(r => r.data),
  gatewayCost: () =>
    api.get(`/ai/fabric/gateway/cost`).then(r => r.data),
  localAiStatus: () =>
    api.get(`/ai/fabric/local-ai/status`).then(r => r.data),
  ragQuery: (data: unknown) =>
    api.post(`/ai/fabric/rag/query`, data).then(r => r.data),
  ragIndex: (data: unknown) =>
    api.post(`/ai/fabric/rag/index`, data).then(r => r.data),
  kgEntity: () =>
    api.get(`/ai/fabric/knowledge-graph/entity`).then(r => r.data),
  kgRelated: () =>
    api.get(`/ai/fabric/knowledge-graph/related`).then(r => r.data),
};

// ── auth ──

export const authApi = {
  login: (data: unknown) =>
    api.post(`/login`, data).then(r => r.data),
  register: (data: unknown) =>
    api.post(`/register`, data).then(r => r.data),
};

// ── biomedical.api ──

export const biomedical_apiApi = {
  listDevices: () =>
    api.get(`/biomedical/devices`).then(r => r.data),
  getDevice: (params: Record<string, string | number>) =>
    api.get(`/biomedical/devices/${params.device_id}`).then(r => r.data),
  updateDeviceStatus: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/biomedical/devices/${params.device_id}/status`, data).then(r => r.data),
  devicesDueForPm: () =>
    api.get(`/biomedical/devices/due/pm`).then(r => r.data),
  devicesDueForCalibration: () =>
    api.get(`/biomedical/devices/due/calibration`).then(r => r.data),
  createWorkOrder: () =>
    api.get(`/biomedical/devices/due/calibration`).then(r => r.data),
  listWorkOrders: () =>
    api.get(`/biomedical/work-orders`).then(r => r.data),
  getWorkOrder: (params: Record<string, string | number>) =>
    api.get(`/biomedical/work-orders/${params.wo_id}`).then(r => r.data),
  completeWorkOrder: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/biomedical/work-orders/${params.wo_id}/complete`, data).then(r => r.data),
  recordCalibration: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/biomedical/work-orders/${params.wo_id}/complete`, data).then(r => r.data),
};

// ── blood_bank.api ──

export const blood_bank_apiApi = {
  listDonors: () =>
    api.get(`/blood-bank/donors`).then(r => r.data),
  getDonor: (params: Record<string, string | number>) =>
    api.get(`/blood-bank/donors/${params.donor_id}`).then(r => r.data),
  deferDonor: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/blood-bank/donors/${params.donor_id}/defer`, data).then(r => r.data),
  registerDonation: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/blood-bank/donors/${params.donor_id}/defer`, data).then(r => r.data),
  completeDonation: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/blood-bank/donations/${params.donation_id}/complete`, data).then(r => r.data),
  processComponent: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/blood-bank/donations/${params.donation_id}/complete`, data).then(r => r.data),
  getInventory: () =>
    api.get(`/blood-bank/inventory`).then(r => r.data),
  getCriticalInventory: () =>
    api.get(`/blood-bank/inventory/critical`).then(r => r.data),
  issueUnits: (data: unknown) =>
    api.post(`/blood-bank/inventory/issue`, data).then(r => r.data),
  performCrossmatch: (data: unknown) =>
    api.post(`/blood-bank/inventory/issue`, data).then(r => r.data),
};

// ── capabilities.clinical_foundation ──

export const capabilities_clinical_foundationApi = {
  listClinicalFoundation: () =>
    api.get(`/clinical-foundation/`).then(r => r.data),
  getClinicalFoundation: (params: Record<string, string | number>) =>
    api.get(`/clinical-foundation/${params.id}`).then(r => r.data),
  createClinicalFoundation: (data: unknown) =>
    api.post(`/clinical-foundation/`, data).then(r => r.data),
  updateClinicalFoundation: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/clinical-foundation/${params.id}`, data).then(r => r.data),
  deleteClinicalFoundation: (params: Record<string, string | number>) =>
    api.delete(`/clinical-foundation/${params.id}`).then(r => r.data),
};

// ── capabilities.document_management ──

export const capabilities_document_managementApi = {
  listDocumentManagement: () =>
    api.get(`/document-management/`).then(r => r.data),
  getDocumentManagement: (params: Record<string, string | number>) =>
    api.get(`/document-management/${params.id}`).then(r => r.data),
  createDocumentManagement: (data: unknown) =>
    api.post(`/document-management/`, data).then(r => r.data),
  updateDocumentManagement: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/document-management/${params.id}`, data).then(r => r.data),
  deleteDocumentManagement: (params: Record<string, string | number>) =>
    api.delete(`/document-management/${params.id}`).then(r => r.data),
};

// ── capabilities.encounter_management ──

export const capabilities_encounter_managementApi = {
  listEncounterManagement: () =>
    api.get(`/encounter-management/`).then(r => r.data),
  getEncounterManagement: (params: Record<string, string | number>) =>
    api.get(`/encounter-management/${params.id}`).then(r => r.data),
  createEncounterManagement: (data: unknown) =>
    api.post(`/encounter-management/`, data).then(r => r.data),
  updateEncounterManagement: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/encounter-management/${params.id}`, data).then(r => r.data),
  deleteEncounterManagement: (params: Record<string, string | number>) =>
    api.delete(`/encounter-management/${params.id}`).then(r => r.data),
};

// ── capabilities.fhir_interoperability ──

export const capabilities_fhir_interoperabilityApi = {
  listFhirInteroperability: () =>
    api.get(`/fhir-interoperability/`).then(r => r.data),
  getFhirInteroperability: (params: Record<string, string | number>) =>
    api.get(`/fhir-interoperability/${params.id}`).then(r => r.data),
  createFhirInteroperability: (data: unknown) =>
    api.post(`/fhir-interoperability/`, data).then(r => r.data),
  updateFhirInteroperability: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/fhir-interoperability/${params.id}`, data).then(r => r.data),
  deleteFhirInteroperability: (params: Record<string, string | number>) =>
    api.delete(`/fhir-interoperability/${params.id}`).then(r => r.data),
};

// ── capabilities.healthcare_consent ──

export const capabilities_healthcare_consentApi = {
  listHealthcareConsent: () =>
    api.get(`/healthcare-consent/`).then(r => r.data),
  getHealthcareConsent: (params: Record<string, string | number>) =>
    api.get(`/healthcare-consent/${params.id}`).then(r => r.data),
  createHealthcareConsent: (data: unknown) =>
    api.post(`/healthcare-consent/`, data).then(r => r.data),
  updateHealthcareConsent: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/healthcare-consent/${params.id}`, data).then(r => r.data),
  deleteHealthcareConsent: (params: Record<string, string | number>) =>
    api.delete(`/healthcare-consent/${params.id}`).then(r => r.data),
};

// ── capabilities.provider_management ──

export const capabilities_provider_managementApi = {
  listProviderManagement: () =>
    api.get(`/provider-management/`).then(r => r.data),
  getProviderManagement: (params: Record<string, string | number>) =>
    api.get(`/provider-management/${params.id}`).then(r => r.data),
  createProviderManagement: (data: unknown) =>
    api.post(`/provider-management/`, data).then(r => r.data),
  updateProviderManagement: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/provider-management/${params.id}`, data).then(r => r.data),
  deleteProviderManagement: (params: Record<string, string | number>) =>
    api.delete(`/provider-management/${params.id}`).then(r => r.data),
};

// ── capabilities.reporting_service ──

export const capabilities_reporting_serviceApi = {
  listReportingService: () =>
    api.get(`/reporting-service/`).then(r => r.data),
  getReportingService: (params: Record<string, string | number>) =>
    api.get(`/reporting-service/${params.id}`).then(r => r.data),
  createReportingService: (data: unknown) =>
    api.post(`/reporting-service/`, data).then(r => r.data),
  updateReportingService: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/reporting-service/${params.id}`, data).then(r => r.data),
  deleteReportingService: (params: Record<string, string | number>) =>
    api.delete(`/reporting-service/${params.id}`).then(r => r.data),
};

// ── capabilities.search_service ──

export const capabilities_search_serviceApi = {
  listSearchService: () =>
    api.get(`/search-service/`).then(r => r.data),
  getSearchService: (params: Record<string, string | number>) =>
    api.get(`/search-service/${params.id}`).then(r => r.data),
  createSearchService: (data: unknown) =>
    api.post(`/search-service/`, data).then(r => r.data),
  updateSearchService: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/search-service/${params.id}`, data).then(r => r.data),
  deleteSearchService: (params: Record<string, string | number>) =>
    api.delete(`/search-service/${params.id}`).then(r => r.data),
};

// ── capabilities.storage_service ──

export const capabilities_storage_serviceApi = {
  listStorageService: () =>
    api.get(`/storage-service/`).then(r => r.data),
  getStorageService: (params: Record<string, string | number>) =>
    api.get(`/storage-service/${params.id}`).then(r => r.data),
  createStorageService: (data: unknown) =>
    api.post(`/storage-service/`, data).then(r => r.data),
  updateStorageService: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/storage-service/${params.id}`, data).then(r => r.data),
  deleteStorageService: (params: Record<string, string | number>) =>
    api.delete(`/storage-service/${params.id}`).then(r => r.data),
};

// ── capabilities.workflow_engine ──

export const capabilities_workflow_engineApi = {
  listWorkflowEngine: () =>
    api.get(`/workflow-engine/`).then(r => r.data),
  getWorkflowEngine: (params: Record<string, string | number>) =>
    api.get(`/workflow-engine/${params.id}`).then(r => r.data),
  createWorkflowEngine: (data: unknown) =>
    api.post(`/workflow-engine/`, data).then(r => r.data),
  updateWorkflowEngine: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/workflow-engine/${params.id}`, data).then(r => r.data),
  deleteWorkflowEngine: (params: Record<string, string | number>) =>
    api.delete(`/workflow-engine/${params.id}`).then(r => r.data),
};

// ── certificates ──

export const certificatesApi = {
  issueCertificate: (data: unknown) =>
    api.post(`/niam/certificates/issue`, data).then(r => r.data),
  revokeCertificate: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/certificates/${params.certificate_id}/revoke`, data).then(r => r.data),
  getCertificate: (params: Record<string, string | number>) =>
    api.get(`/niam/certificates/${params.thumbprint}`).then(r => r.data),
  listOrgCertificates: (params: Record<string, string | number>) =>
    api.get(`/niam/certificates/organization/${params.org_id}`).then(r => r.data),
  listExpiring: () =>
    api.get(`/niam/certificates/expiring`).then(r => r.data),
  registerCa: (data: unknown) =>
    api.post(`/niam/certificates/authorities`, data).then(r => r.data),
  listCas: () =>
    api.get(`/niam/certificates/authorities`).then(r => r.data),
  generateApiKey: (data: unknown) =>
    api.post(`/niam/certificates/api-keys`, data).then(r => r.data),
  listOrgApiKeys: (params: Record<string, string | number>) =>
    api.get(`/niam/certificates/api-keys/organization/${params.org_id}`).then(r => r.data),
};

// ── certification ──

export const certificationApi = {
  evaluateModule: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/certification/evaluate/${params.module_path}`, data).then(r => r.data),
  getCertificationLevel: (params: Record<string, string | number>) =>
    api.get(`/certification/level/${params.module_path}`).then(r => r.data),
  getReport: (params: Record<string, string | number>) =>
    api.get(`/certification/report/${params.module_path}`).then(r => r.data),
  getAllMetrics: () =>
    api.get(`/certification/metrics`).then(r => r.data),
  getMetricsByCategory: (params: Record<string, string | number>) =>
    api.get(`/certification/metrics/${params.category}`).then(r => r.data),
  checkReleaseGates: (data: unknown) =>
    api.post(`/certification/release/check`, data).then(r => r.data),
  validateRelease: (data: unknown) =>
    api.post(`/certification/release/validate`, data).then(r => r.data),
  listDimensions: () =>
    api.get(`/certification/dimensions`).then(r => r.data),
  getDimensionChecks: (params: Record<string, string | number>) =>
    api.get(`/certification/dimensions/${params.dimension}/checks`).then(r => r.data),
};

// ── citizen_platform ──

export const citizen_platformApi = {
  getDashboard: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/dashboard/${params.citizen_id}`).then(r => r.data),
  getProfile: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/profile/${params.citizen_id}`).then(r => r.data),
  getHealthSummary: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/health-summary/${params.citizen_id}`).then(r => r.data),
  listAppointments: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/appointments/${params.citizen_id}`).then(r => r.data),
  bookAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/citizen-platform/appointments/${params.citizen_id}`, data).then(r => r.data),
  listMedications: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/medications/${params.citizen_id}`).then(r => r.data),
  listLabResults: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/lab-results/${params.citizen_id}`).then(r => r.data),
  listRadiologyStudies: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/radiology/${params.citizen_id}`).then(r => r.data),
  getFamily: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/family/${params.citizen_id}`).then(r => r.data),
  getVaccinations: (params: Record<string, string | number>) =>
    api.get(`/citizen-platform/vaccinations/${params.citizen_id}`).then(r => r.data),
};

// ── command_center.api ──

export const command_center_apiApi = {
  listEmergencies: () =>
    api.get(`/command-center/emergencies`).then(r => r.data),
  getEmergency: (params: Record<string, string | number>) =>
    api.get(`/command-center/emergencies/${params.emergency_id}`).then(r => r.data),
  resolveEmergency: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/command-center/emergencies/${params.emergency_id}/resolve`, data).then(r => r.data),
  requestResource: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/command-center/emergencies/${params.emergency_id}/resolve`, data).then(r => r.data),
  listResourceRequests: () =>
    api.get(`/command-center/resource-requests`).then(r => r.data),
  fulfillResource: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/command-center/resource-requests/${params.request_id}/fulfill`, data).then(r => r.data),
  publishSituationReport: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/command-center/resource-requests/${params.request_id}/fulfill`, data).then(r => r.data),
  listSituationReports: () =>
    api.get(`/command-center/situation-reports`).then(r => r.data),
  completeAfterAction: () =>
    api.get(`/command-center/situation-reports`).then(r => r.data),
  listAfterActionReports: () =>
    api.get(`/command-center/after-action-reports`).then(r => r.data),
};

// ── command_intelligence ──

export const command_intelligenceApi = {
  getSituationRoom: () =>
    api.get(`/intelligence/situation-room`).then(r => r.data),
  getKpis: () =>
    api.get(`/intelligence/kpis`).then(r => r.data),
  getKpiTrend: (params: Record<string, string | number>) =>
    api.get(`/intelligence/kpis/${params.kpi_name}/trend`).then(r => r.data),
  getIncidents: () =>
    api.get(`/intelligence/incidents`).then(r => r.data),
  reportIncident: () =>
    api.get(`/intelligence/incidents`).then(r => r.data),
  getCapacity: () =>
    api.get(`/intelligence/capacity`).then(r => r.data),
  createRecommendation: () =>
    api.get(`/intelligence/capacity`).then(r => r.data),
  executiveDashboard: () =>
    api.get(`/intelligence/executive-dashboard`).then(r => r.data),
  regionalDashboard: (params: Record<string, string | number>) =>
    api.get(`/intelligence/regional/${params.region}/dashboard`).then(r => r.data),
};

// ── compliance ──

export const complianceApi = {
  registerFramework: (data: unknown) =>
    api.post(`/niam/compliance/frameworks`, data).then(r => r.data),
  listFrameworks: () =>
    api.get(`/niam/compliance/frameworks`).then(r => r.data),
  getFramework: (params: Record<string, string | number>) =>
    api.get(`/niam/compliance/frameworks/${params.framework_id}`).then(r => r.data),
  runCheck: (data: unknown) =>
    api.post(`/niam/compliance/checks`, data).then(r => r.data),
  listChecks: (params: Record<string, string | number>) =>
    api.get(`/niam/compliance/checks/${params.target_type}/${params.target_id}`).then(r => r.data),
  generateReport: (data: unknown) =>
    api.post(`/niam/compliance/reports`, data).then(r => r.data),
  getReport: (params: Record<string, string | number>) =>
    api.get(`/niam/compliance/reports/${params.report_id}`).then(r => r.data),
  getOrgComplianceStatus: (params: Record<string, string | number>) =>
    api.get(`/niam/compliance/status/${params.org_id}`).then(r => r.data),
};

// ── control_plane ──

export const control_planeApi = {
  listComponents: () =>
    api.get(`/control-plane/registry/components`).then(r => r.data),
  registerComponent: () =>
    api.get(`/control-plane/registry/components`).then(r => r.data),
  updateComponent: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/control-plane/registry/components/${params.name}`, data).then(r => r.data),
  unregisterComponent: (params: Record<string, string | number>) =>
    api.delete(`/control-plane/registry/components/${params.name}`).then(r => r.data),
  getTopology: () =>
    api.get(`/control-plane/registry/topology`).then(r => r.data),
  controlPlaneHealth: () =>
    api.get(`/control-plane/health`).then(r => r.data),
  getConfig: (params: Record<string, string | number>) =>
    api.get(`/control-plane/config/${params.scope}/${params.component}`).then(r => r.data),
  setConfig: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/control-plane/config/${params.scope}/${params.component}`, data).then(r => r.data),
  reloadConfig: (data: unknown) =>
    api.post(`/control-plane/config/reload`, data).then(r => r.data),
  listPolicies: () =>
    api.get(`/control-plane/policies`).then(r => r.data),
};

// ── critical_care.api ──

export const critical_care_apiApi = {
  listAdmissions: () =>
    api.get(`/critical-care/admissions`).then(r => r.data),
  getAdmission: (params: Record<string, string | number>) =>
    api.get(`/critical-care/admissions/${params.admission_id}`).then(r => r.data),
  dischargePatient: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/critical-care/admissions/${params.admission_id}/discharge`, data).then(r => r.data),
  registerBed: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/critical-care/admissions/${params.admission_id}/discharge`, data).then(r => r.data),
  getBedAvailability: () =>
    api.get(`/critical-care/beds/availability`).then(r => r.data),
  recordVitals: () =>
    api.get(`/critical-care/beds/availability`).then(r => r.data),
  getVitals: (params: Record<string, string | number>) =>
    api.get(`/critical-care/vitals/${params.patient_id}`).then(r => r.data),
  setVentilator: (params: Record<string, string | number>) =>
    api.get(`/critical-care/vitals/${params.patient_id}`).then(r => r.data),
  getVentilatorSettings: (params: Record<string, string | number>) =>
    api.get(`/critical-care/ventilator/${params.patient_id}`).then(r => r.data),
  calculateEws: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/critical-care/ews/${params.patient_id}`, data).then(r => r.data),
};

// ── ems.api ──

export const ems_apiApi = {
  listIncidents: () =>
    api.get(`/ems/incidents`).then(r => r.data),
  getIncident: (params: Record<string, string | number>) =>
    api.get(`/ems/incidents/${params.incident_id}`).then(r => r.data),
  updateIncidentStatus: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/incidents/${params.incident_id}/status`, data).then(r => r.data),
  dispatchIncident: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/incidents/${params.incident_id}/status`, data).then(r => r.data),
  registerAmbulance: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/incidents/${params.incident_id}/status`, data).then(r => r.data),
  listAmbulances: () =>
    api.get(`/ems/ambulances`).then(r => r.data),
  getAmbulance: (params: Record<string, string | number>) =>
    api.get(`/ems/ambulances/${params.ambulance_id}`).then(r => r.data),
  updateAmbulanceLocation: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/ambulances/${params.ambulance_id}/location`, data).then(r => r.data),
  updateAmbulanceStatus: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/ambulances/${params.ambulance_id}/status`, data).then(r => r.data),
  registerCrew: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/ems/ambulances/${params.ambulance_id}/status`, data).then(r => r.data),
};

// ── federation ──

export const federationApi = {
  registerProvider: (data: unknown) =>
    api.post(`/niam/federation/providers`, data).then(r => r.data),
  listProviders: () =>
    api.get(`/niam/federation/providers`).then(r => r.data),
  getProvider: (params: Record<string, string | number>) =>
    api.get(`/niam/federation/providers/${params.provider_id}`).then(r => r.data),
  linkIdentity: (data: unknown) =>
    api.post(`/niam/federation/identities/link`, data).then(r => r.data),
  getPersonIdentities: (params: Record<string, string | number>) =>
    api.get(`/niam/federation/identities/${params.person_id}`).then(r => r.data),
  establishTrust: (data: unknown) =>
    api.post(`/niam/federation/trust`, data).then(r => r.data),
  getTrustRelationships: (params: Record<string, string | number>) =>
    api.get(`/niam/federation/trust/${params.org_id}`).then(r => r.data),
  createAgreement: (data: unknown) =>
    api.post(`/niam/federation/agreements`, data).then(r => r.data),
  listAgreements: () =>
    api.get(`/niam/federation/agreements`).then(r => r.data),
};

// ── governance ──

export const governanceApi = {
  getAuthorities: () =>
    api.get(`/niam/governance/authorities`).then(r => r.data),
  createAuthority: (data: unknown) =>
    api.post(`/niam/governance/authorities`, data).then(r => r.data),
  getAuthority: (params: Record<string, string | number>) =>
    api.get(`/niam/governance/authorities/${params.authority_id}`).then(r => r.data),
  activateAuthority: (params: Record<string, string | number>) =>
    api.post(`/niam/governance/authorities/${params.authority_id}/activate`).then(r => r.data),
  suspendAuthority: (params: Record<string, string | number>) =>
    api.post(`/niam/governance/authorities/${params.authority_id}/suspend`).then(r => r.data),
  createCouncil: (data: unknown) =>
    api.post(`/niam/governance/councils`, data).then(r => r.data),
  getCouncils: () =>
    api.get(`/niam/governance/councils`).then(r => r.data),
  submitPolicy: (data: unknown) =>
    api.post(`/niam/governance/policy-approvals`, data).then(r => r.data),
  approvePolicy: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/policy-approvals/${params.workflow_id}/approve`, data).then(r => r.data),
  submitAppeal: (data: unknown) =>
    api.post(`/niam/governance/appeals`, data).then(r => r.data),
  reviewAppeal: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/appeals/${params.appeal_id}/decide`, data).then(r => r.data),
  suspendIdentity: (data: unknown) =>
    api.post(`/niam/governance/suspensions`, data).then(r => r.data),
  liftSuspension: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/suspensions/${params.suspension_id}/lift`, data).then(r => r.data),
  registerEntity: (data: unknown) =>
    api.post(`/niam/governance/registry`, data).then(r => r.data),
  getRegistry: (params: Record<string, string | number>) =>
    api.get(`/niam/governance/registry/${params.person_id}`).then(r => r.data),
  createReviewBoard: (data: unknown) =>
    api.post(`/niam/governance/review-boards`, data).then(r => r.data),
};

// ── health_data ──

export const health_dataApi = {
  listCatalog: () =>
    api.get(`/health-data/catalog`).then(r => r.data),
  getDatasetMetadata: (params: Record<string, string | number>) =>
    api.get(`/health-data/catalog/${params.dataset}`).then(r => r.data),
  getLineage: (params: Record<string, string | number>) =>
    api.get(`/health-data/lineage/${params.entity_type}/${params.entity_id}`).then(r => r.data),
  listPolicies: () =>
    api.get(`/health-data/governance/policies`).then(r => r.data),
  createPolicy: (data: unknown) =>
    api.post(`/health-data/governance/policies`, data).then(r => r.data),
  getQualityMetrics: () =>
    api.get(`/health-data/quality/metrics`).then(r => r.data),
  triggerIngestion: (data: unknown) =>
    api.post(`/health-data/ingest`, data).then(r => r.data),
  queryEventStore: () =>
    api.get(`/health-data/event-store/events`).then(r => r.data),
  runWarehouseQuery: () =>
    api.get(`/health-data/warehouse/query`).then(r => r.data),
  mapFhirPatient: (data: unknown) =>
    api.post(`/health-data/canonical/map-patient`, data).then(r => r.data),
};

// ── integration ──

export const integrationApi = {
  listGateways: () =>
    api.get(`/integration/gateways`).then(r => r.data),
  getGateway: (params: Record<string, string | number>) =>
    api.get(`/integration/gateway/${params.protocol}`).then(r => r.data),
  sendViaGateway: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/gateway/${params.protocol}/send`, data).then(r => r.data),
  receiveViaGateway: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/gateway/${params.protocol}/receive`, data).then(r => r.data),
  apiCatalog: () =>
    api.get(`/integration/catalog`).then(r => r.data),
  listIntegrationConnectors: () =>
    api.get(`/integration/connectors`).then(r => r.data),
  standardsConformance: () =>
    api.get(`/integration/standards`).then(r => r.data),
  runTransformation: (data: unknown) =>
    api.post(`/integration/transform`, data).then(r => r.data),
  integrationHealthDashboard: () =>
    api.get(`/integration/monitoring/dashboard`).then(r => r.data),
  runIntegrationTests: (data: unknown) =>
    api.post(`/integration/test/run`, data).then(r => r.data),
};

// ── integration.connectors ──

export const integration_connectorsApi = {
  connectorsStatus: () =>
    api.get(`/integration/connectors/status`).then(r => r.data),
  getConnector: (params: Record<string, string | number>) =>
    api.get(`/integration/connectors/${params.name}`).then(r => r.data),
  connectConnector: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/connectors/${params.name}/connect`, data).then(r => r.data),
  disconnectConnector: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/connectors/${params.name}/disconnect`, data).then(r => r.data),
  connectorHealth: (params: Record<string, string | number>) =>
    api.get(`/integration/connectors/${params.name}/health`).then(r => r.data),
  sendThroughConnector: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/connectors/${params.name}/send`, data).then(r => r.data),
  configureConnector: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/integration/connectors/${params.name}/configure`, data).then(r => r.data),
};

// ── kernel ──

export const kernelApi = {
  kernelStatus: () =>
    api.get(`/kernel/status`).then(r => r.data),
  kernelServices: () =>
    api.get(`/kernel/services`).then(r => r.data),
  kernelCapabilities: () =>
    api.get(`/kernel/capabilities`).then(r => r.data),
  kernelPlugins: () =>
    api.get(`/kernel/plugins`).then(r => r.data),
  kernelModules: () =>
    api.get(`/kernel/modules`).then(r => r.data),
  kernelConfig: () =>
    api.get(`/kernel/config`).then(r => r.data),
  kernelOutbox: () =>
    api.get(`/kernel/events/outbox`).then(r => r.data),
  kernelDeadLetterQueue: () =>
    api.get(`/kernel/events/dlq`).then(r => r.data),
  kernelTenants: () =>
    api.get(`/kernel/tenants`).then(r => r.data),
  kernelLocks: () =>
    api.get(`/kernel/locks`).then(r => r.data),
};

// ── lifecycle ──

export const lifecycleApi = {
  startRegistration: (data: unknown) =>
    api.post(`/niam/lifecycle/enterprise/register`, data).then(r => r.data),
  validateLicense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/enterprise/${params.reg_id}/validate-license`, data).then(r => r.data),
  approveRegistration: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/enterprise/${params.reg_id}/approve`, data).then(r => r.data),
  rejectRegistration: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/enterprise/${params.reg_id}/reject`, data).then(r => r.data),
  getEnterpriseStatus: (params: Record<string, string | number>) =>
    api.get(`/niam/lifecycle/enterprise/${params.org_id}`).then(r => r.data),
  requestEmployee: (data: unknown) =>
    api.post(`/niam/lifecycle/workforce/request`, data).then(r => r.data),
  approveRequest: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/workforce/${params.request_id}/approve`, data).then(r => r.data),
  createAppointment: (data: unknown) =>
    api.post(`/niam/lifecycle/government/appointments`, data).then(r => r.data),
  approveAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/government/appointments/${params.appointment_id}/approve`, data).then(r => r.data),
  promoteEmployee: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/government/appointments/${params.appointment_id}/promote`, data).then(r => r.data),
  registerCitizen: (data: unknown) =>
    api.post(`/niam/lifecycle/citizen/register`, data).then(r => r.data),
  verifyCitizenOtp: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/citizen/${params.citizen_id}/verify-otp`, data).then(r => r.data),
  issueHealthId: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/citizen/${params.citizen_id}/issue-health-id`, data).then(r => r.data),
  deactivateCitizen: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/lifecycle/citizen/${params.citizen_id}/deactivate`, data).then(r => r.data),
  getCitizenStatus: (params: Record<string, string | number>) =>
    api.get(`/niam/lifecycle/citizen/${params.person_id}`).then(r => r.data),
  createGuardianship: (data: unknown) =>
    api.post(`/niam/lifecycle/guardians`, data).then(r => r.data),
  getDependents: (params: Record<string, string | number>) =>
    api.get(`/niam/lifecycle/guardians/dependents/${params.guardian_person_id}`).then(r => r.data),
};

// ── lifecycle_platform.api ──

export const lifecycle_platform_apiApi = {
  listComponents: () =>
    api.get(`/lifecycle/components`).then(r => r.data),
  getComponent: (params: Record<string, string | number>) =>
    api.get(`/lifecycle/components/${params.component_id}`).then(r => r.data),
  findComponent: (params: Record<string, string | number>) =>
    api.get(`/lifecycle/components/name/${params.name}`).then(r => r.data),
  updateComponentStage: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/lifecycle/components/${params.component_id}/stage`, data).then(r => r.data),
  createRelease: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/lifecycle/components/${params.component_id}/stage`, data).then(r => r.data),
  listReleases: () =>
    api.get(`/lifecycle/releases`).then(r => r.data),
  getRelease: (params: Record<string, string | number>) =>
    api.get(`/lifecycle/releases/${params.release_id}`).then(r => r.data),
  approveRelease: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/lifecycle/releases/${params.release_id}/approve`, data).then(r => r.data),
  recordCompatibility: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/lifecycle/releases/${params.release_id}/approve`, data).then(r => r.data),
  checkCompatibility: () =>
    api.get(`/lifecycle/compatibility/check`).then(r => r.data),
};

// ── national.background_platform.api ──

export const national_background_platform_apiApi = {
  listJobs: () =>
    api.get(`/national/jobs/`).then(r => r.data),
  getJob: (params: Record<string, string | number>) =>
    api.get(`/national/jobs/${params.job_id}`).then(r => r.data),
  updateJob: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/jobs/${params.job_id}`, data).then(r => r.data),
  deleteJob: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/jobs/${params.job_id}`, data).then(r => r.data),
  executeJobNow: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/jobs/${params.job_id}/execute`, data).then(r => r.data),
  cancelJob: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/jobs/${params.job_id}/cancel`, data).then(r => r.data),
  pauseJob: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/jobs/${params.job_id}/pause`, data).then(r => r.data),
  resumeJob: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/jobs/${params.job_id}/resume`, data).then(r => r.data),
  getExecutionHistory: (params: Record<string, string | number>) =>
    api.get(`/national/jobs/${params.job_id}/executions`).then(r => r.data),
  getSchedules: (params: Record<string, string | number>) =>
    api.get(`/national/jobs/${params.job_id}/schedules`).then(r => r.data),
};

// ── national.document_platform.api ──

export const national_document_platform_apiApi = {
  listDocuments: () =>
    api.get(`/national/documents/`).then(r => r.data),
  getDocument: (params: Record<string, string | number>) =>
    api.get(`/national/documents/${params.document_id}`).then(r => r.data),
  updateDocument: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/documents/${params.document_id}`, data).then(r => r.data),
  deleteDocument: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/documents/${params.document_id}`, data).then(r => r.data),
  createVersion: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/documents/${params.document_id}`, data).then(r => r.data),
  listVersions: (params: Record<string, string | number>) =>
    api.get(`/national/documents/${params.document_id}/versions`).then(r => r.data),
  signDocument: (params: Record<string, string | number>) =>
    api.get(`/national/documents/${params.document_id}/versions`).then(r => r.data),
  listSignatures: (params: Record<string, string | number>) =>
    api.get(`/national/documents/${params.document_id}/signatures`).then(r => r.data),
  verifyDocument: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/documents/${params.document_id}/verify`, data).then(r => r.data),
  generateQrCode: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/documents/${params.document_id}/verify`, data).then(r => r.data),
};

// ── national.ecosystem ──

export const national_ecosystemApi = {
  registerConnector: (data: unknown) =>
    api.post(`/ecosystem/connectors/register`, data).then(r => r.data),
  listConnectors: () =>
    api.get(`/ecosystem/connectors`).then(r => r.data),
  connectorHealth: (params: Record<string, string | number>) =>
    api.get(`/ecosystem/connectors/${params.name}/health`).then(r => r.data),
  unregisterConnector: (params: Record<string, string | number>) =>
    api.delete(`/ecosystem/connectors/${params.name}`).then(r => r.data),
  connectorSend: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/ecosystem/connectors/${params.name}/send`, data).then(r => r.data),
  connectorReceive: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/ecosystem/connectors/${params.name}/receive`, data).then(r => r.data),
  transformData: (data: unknown) =>
    api.post(`/ecosystem/transform`, data).then(r => r.data),
  listSchemas: () =>
    api.get(`/ecosystem/schemas`).then(r => r.data),
  registerSchema: (data: unknown) =>
    api.post(`/ecosystem/schemas`, data).then(r => r.data),
  validateAgainstSchema: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/ecosystem/schemas/${params.schema_name}/validate`, data).then(r => r.data),
};

// ── national.ecosystem.gateway ──

export const national_ecosystem_gatewayApi = {
  routeRequest: (data: unknown) =>
    api.post(`/gateway/route`, data).then(r => r.data),
  gatewayStatus: () =>
    api.get(`/gateway/status`).then(r => r.data),
  listPolicies: () =>
    api.get(`/gateway/policies`).then(r => r.data),
  createPolicy: (data: unknown) =>
    api.post(`/gateway/policies`, data).then(r => r.data),
  updatePolicy: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/gateway/policies/${params.policy_id}`, data).then(r => r.data),
  deletePolicy: (params: Record<string, string | number>) =>
    api.delete(`/gateway/policies/${params.policy_id}`).then(r => r.data),
  listApiCatalog: () =>
    api.get(`/gateway/catalog`).then(r => r.data),
  registerApi: (data: unknown) =>
    api.post(`/gateway/catalog`, data).then(r => r.data),
};

// ── national.notification_platform.api ──

export const national_notification_platform_apiApi = {
  listNotifications: () =>
    api.get(`/national/notifications/`).then(r => r.data),
  getDashboard: () =>
    api.get(`/national/notifications/dashboard`).then(r => r.data),
  getNotification: (params: Record<string, string | number>) =>
    api.get(`/national/notifications/${params.notification_id}`).then(r => r.data),
  cancelNotification: (params: Record<string, string | number>) =>
    api.get(`/national/notifications/${params.notification_id}`).then(r => r.data),
  createTemplate: (params: Record<string, string | number>) =>
    api.get(`/national/notifications/${params.notification_id}`).then(r => r.data),
  listTemplates: () =>
    api.get(`/national/notifications/templates`).then(r => r.data),
  getTemplate: (params: Record<string, string | number>) =>
    api.get(`/national/notifications/templates/${params.template_id}`).then(r => r.data),
  updateTemplate: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/notifications/templates/${params.template_id}`, data).then(r => r.data),
  deleteTemplate: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/notifications/templates/${params.template_id}`, data).then(r => r.data),
  renderTemplate: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/notifications/templates/${params.template_id}/render`, data).then(r => r.data),
};

// ── national.observability.api ──

export const national_observability_apiApi = {
  queryMetrics: () =>
    api.get(`/national/observability/metrics/query`).then(r => r.data),
  recordTraces: () =>
    api.get(`/national/observability/metrics/query`).then(r => r.data),
  getTrace: (params: Record<string, string | number>) =>
    api.get(`/national/observability/traces/${params.trace_id}`).then(r => r.data),
  searchTraces: () =>
    api.get(`/national/observability/traces/search`).then(r => r.data),
  runHealthCheck: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/observability/health/checks/${params.name}`, data).then(r => r.data),
  listHealthChecks: () =>
    api.get(`/national/observability/health/checks`).then(r => r.data),
  healthStatus: () =>
    api.get(`/national/observability/health/status`).then(r => r.data),
  health: () =>
    api.get(`/national/observability/health`).then(r => r.data),
  createAlertRule: () =>
    api.get(`/national/observability/health`).then(r => r.data),
  listAlertRules: () =>
    api.get(`/national/observability/alerts/rules`).then(r => r.data),
};

// ── national.rules_engine.api ──

export const national_rules_engine_apiApi = {
  evaluateRules: (data: unknown) =>
    api.post(`/national/rules/evaluate`, data).then(r => r.data),
  simulateRule: (data: unknown) =>
    api.post(`/national/rules/simulate`, data).then(r => r.data),
  createRule: (data: unknown) =>
    api.post(`/national/rules/simulate`, data).then(r => r.data),
  listRules: () =>
    api.get(`/national/rules/`).then(r => r.data),
  getRule: (params: Record<string, string | number>) =>
    api.get(`/national/rules/${params.rule_id}`).then(r => r.data),
  updateRule: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/rules/${params.rule_id}`, data).then(r => r.data),
  deleteRule: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/rules/${params.rule_id}`, data).then(r => r.data),
  activateRule: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/rules/${params.rule_id}/activate`, data).then(r => r.data),
  deactivateRule: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/rules/${params.rule_id}/deactivate`, data).then(r => r.data),
  createRuleVersion: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/rules/${params.rule_id}/version`, data).then(r => r.data),
};

// ── national.scheduling_platform.api ──

export const national_scheduling_platform_apiApi = {
  listAppointments: () =>
    api.get(`/national/scheduling/appointments`).then(r => r.data),
  getAppointment: (params: Record<string, string | number>) =>
    api.get(`/national/scheduling/appointments/${params.appointment_id}`).then(r => r.data),
  updateAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/scheduling/appointments/${params.appointment_id}`, data).then(r => r.data),
  cancelAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/scheduling/appointments/${params.appointment_id}`, data).then(r => r.data),
  completeAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/scheduling/appointments/${params.appointment_id}/complete`, data).then(r => r.data),
  markNoShow: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/scheduling/appointments/${params.appointment_id}/no-show`, data).then(r => r.data),
  rescheduleAppointment: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/scheduling/appointments/${params.appointment_id}/reschedule`, data).then(r => r.data),
  checkAvailability: (data: unknown) =>
    api.post(`/national/scheduling/availability/check`, data).then(r => r.data),
  findAvailableSlots: () =>
    api.get(`/national/scheduling/availability/slots`).then(r => r.data),
  createResource: () =>
    api.get(`/national/scheduling/availability/slots`).then(r => r.data),
};

// ── national.search_platform.api ──

export const national_search_platform_apiApi = {
  searchPost: (data: unknown) =>
    api.post(`/national/search/search`, data).then(r => r.data),
  searchGet: () =>
    api.get(`/national/search/search`).then(r => r.data),
  fhirSearch: (data: unknown) =>
    api.post(`/national/search/fhir/search`, data).then(r => r.data),
  suggest: () =>
    api.get(`/national/search/suggest`).then(r => r.data),
  getFacets: () =>
    api.get(`/national/search/facets`).then(r => r.data),
  saveSearch: () =>
    api.get(`/national/search/facets`).then(r => r.data),
  listSavedSearches: () =>
    api.get(`/national/search/saved`).then(r => r.data),
  getSavedSearch: (params: Record<string, string | number>) =>
    api.get(`/national/search/saved/${params.search_id}`).then(r => r.data),
  deleteSavedSearch: (params: Record<string, string | number>) =>
    api.get(`/national/search/saved/${params.search_id}`).then(r => r.data),
  rebuildIndex: (data: unknown) =>
    api.post(`/national/search/index/rebuild`, data).then(r => r.data),
};

// ── national.task_engine.api ──

export const national_task_engine_apiApi = {
  createTask: (data: unknown) =>
    api.post(`/national/tasks/`, data).then(r => r.data),
  bulkCreate: (data: unknown) =>
    api.post(`/national/tasks/bulk`, data).then(r => r.data),
  listTasks: () =>
    api.get(`/national/tasks/`).then(r => r.data),
  getDashboard: () =>
    api.get(`/national/tasks/dashboard`).then(r => r.data),
  getTask: (params: Record<string, string | number>) =>
    api.get(`/national/tasks/${params.task_id}`).then(r => r.data),
  updateTask: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/national/tasks/${params.task_id}`, data).then(r => r.data),
  deleteTask: (params: Record<string, string | number>) =>
    api.delete(`/national/tasks/${params.task_id}`).then(r => r.data),
  assignTask: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/tasks/${params.task_id}/assign`, data).then(r => r.data),
  startTask: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/tasks/${params.task_id}/start`, data).then(r => r.data),
  completeTask: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/national/tasks/${params.task_id}/complete`, data).then(r => r.data),
};


// ── notifications ──

export const notificationsApi = {
  sendNotification: (data: unknown) =>
    api.post(`/niam/notifications/send`, data).then(r => r.data),
  createTemplate: (data: unknown) =>
    api.post(`/niam/notifications/templates`, data).then(r => r.data),
  listTemplates: () =>
    api.get(`/niam/notifications/templates`).then(r => r.data),
  getQueue: (params: Record<string, string | number>) =>
    api.get(`/niam/notifications/queue/${params.recipient_id}`).then(r => r.data),
  markNotificationRead: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/notifications/queue/${params.queue_id}/read`, data).then(r => r.data),
  markNotificationSent: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/notifications/queue/${params.queue_id}/sent`, data).then(r => r.data),
  markNotificationDelivered: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/notifications/queue/${params.queue_id}/delivered`, data).then(r => r.data),
  getPreferences: (params: Record<string, string | number>) =>
    api.get(`/niam/notifications/preferences/${params.recipient_id}`).then(r => r.data),
  updatePreferences: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/niam/notifications/preferences/${params.recipient_id}`, data).then(r => r.data),
};

// ── patients ──

export const patientsApi = {
  listPatients: () =>
    api.get(`/patients`).then(r => r.data),
  createPatient: (data: unknown) =>
    api.post(`/patients`, data).then(r => r.data),
  getPatient: (params: Record<string, string | number>) =>
    api.get(`/patients/${params.patient_id}`).then(r => r.data),
};

// ── pharmacy ──

export const pharmacyApi = {
  getDispenseQueue: () =>
    api.get(`/pharmacy/dispense-queue`).then(r => r.data),
  prepareDispense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/prepare`, data).then(r => r.data),
  verifyDispense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/verify`, data).then(r => r.data),
  completeDispense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/dispense`, data).then(r => r.data),
  partialDispense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/partial`, data).then(r => r.data),
  cancelDispense: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/cancel`, data).then(r => r.data),
  createDispenseRecord: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/cancel`, data).then(r => r.data),
  getDispenseRecords: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/cancel`, data).then(r => r.data),
  checkInteractions: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/pharmacy/dispense-queue/${params.queue_id}/cancel`, data).then(r => r.data),
  checkContraindications: (data: unknown) =>
    api.post(`/pharmacy/clinical/contraindications/check`, data).then(r => r.data),
};

// ── pilot_platform.api ──

export const pilot_platform_apiApi = {
  listPilots: () =>
    api.get(`/pilot-platform/pilots`).then(r => r.data),
  getPilot: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/pilots/${params.pilot_id}`).then(r => r.data),
  advancePhase: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/pilot-platform/pilots/${params.pilot_id}/phase`, data).then(r => r.data),
  enrollFacility: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/pilot-platform/pilots/${params.pilot_id}/phase`, data).then(r => r.data),
  listPilotFacilities: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/pilots/${params.pilot_id}/facilities`).then(r => r.data),
  assessReadiness: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/pilots/${params.pilot_id}/facilities`).then(r => r.data),
  getFacilityReadiness: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/facilities/${params.facility_id}/readiness`).then(r => r.data),
  decideGate: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/facilities/${params.facility_id}/readiness`).then(r => r.data),
  listGates: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/pilots/${params.pilot_id}/gates`).then(r => r.data),
  recordDeployment: (params: Record<string, string | number>) =>
    api.get(`/pilot-platform/pilots/${params.pilot_id}/gates`).then(r => r.data),
};

// ── platform ──

export const platformApi = {
  platformHealth: () =>
    api.get(`/platform/health`).then(r => r.data),
  platformModules: () =>
    api.get(`/platform/modules`).then(r => r.data),
  platformCapabilities: () =>
    api.get(`/platform/capabilities`).then(r => r.data),
};

// ── public_health.api ──

export const public_health_apiApi = {
  listCases: () =>
    api.get(`/public-health/disease-cases`).then(r => r.data),
  getCase: (params: Record<string, string | number>) =>
    api.get(`/public-health/disease-cases/${params.case_id}`).then(r => r.data),
  getCaseStats: () =>
    api.get(`/public-health/disease-cases/stats`).then(r => r.data),
  raiseAlert: () =>
    api.get(`/public-health/disease-cases/stats`).then(r => r.data),
  listAlerts: () =>
    api.get(`/public-health/outbreak-alerts`).then(r => r.data),
  getAlert: (params: Record<string, string | number>) =>
    api.get(`/public-health/outbreak-alerts/${params.alert_id}`).then(r => r.data),
  updateAlertStatus: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/public-health/outbreak-alerts/${params.alert_id}/status`, data).then(r => r.data),
  recordSignal: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/public-health/outbreak-alerts/${params.alert_id}/status`, data).then(r => r.data),
  listSignals: () =>
    api.get(`/public-health/surveillance-signals`).then(r => r.data),
  analyzeSurveillance: (data: unknown) =>
    api.post(`/public-health/analyze`, data).then(r => r.data),
};

// ── trust ──

export const trustApi = {
  createFramework: (data: unknown) =>
    api.post(`/niam/trust/frameworks`, data).then(r => r.data),
  listFrameworks: () =>
    api.get(`/niam/trust/frameworks`).then(r => r.data),
  getFramework: (params: Record<string, string | number>) =>
    api.get(`/niam/trust/frameworks/${params.framework_id}`).then(r => r.data),
  createProfile: (data: unknown) =>
    api.post(`/niam/trust/assurance-profiles`, data).then(r => r.data),
  listProfiles: () =>
    api.get(`/niam/trust/assurance-profiles`).then(r => r.data),
  registerAnchor: (data: unknown) =>
    api.post(`/niam/trust/anchors`, data).then(r => r.data),
  listAnchors: () =>
    api.get(`/niam/trust/anchors`).then(r => r.data),
  evaluateTrust: (data: unknown) =>
    api.post(`/niam/trust/evaluations`, data).then(r => r.data),
  submitProofing: (data: unknown) =>
    api.post(`/niam/trust/proofing`, data).then(r => r.data),
};

// ── workflows ──

export const workflowsApi = {
  createDefinition: (data: unknown) =>
    api.post(`/niam/workflows/definitions`, data).then(r => r.data),
  listDefinitions: () =>
    api.get(`/niam/workflows/definitions`).then(r => r.data),
  getDefinition: (params: Record<string, string | number>) =>
    api.get(`/niam/workflows/definitions/${params.def_id}`).then(r => r.data),
  startInstance: (data: unknown) =>
    api.post(`/niam/workflows/instances`, data).then(r => r.data),
  getInstance: (params: Record<string, string | number>) =>
    api.get(`/niam/workflows/instances/${params.instance_id}`).then(r => r.data),
  submitApproval: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/workflows/instances/${params.instance_id}/approve`, data).then(r => r.data),
  cancelInstance: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/workflows/instances/${params.instance_id}/cancel`, data).then(r => r.data),
  getPendingApprovals: (params: Record<string, string | number>) =>
    api.get(`/niam/workflows/approvals/pending/${params.approver_id}`).then(r => r.data),
};

// ── React Query Hooks ──

export function useAdaptive_authEvaluateRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adaptive_authApi.evaluateRisk(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adaptive_auth'] }),
  });
}
export function useAdaptive_authGetRiskHistory(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['adaptive_auth', 'getRiskHistory', params],
    queryFn: ({ queryKey: [, , p] }) => adaptive_authApi.getRiskHistory(p as Record<string, string | number>),
  });
}
export function useAdaptive_authCreateMfaChallenge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adaptive_authApi.createMfaChallenge(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adaptive_auth'] }),
  });
}
export function useAdaptive_authVerifyMfa() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adaptive_authApi.verifyMfa(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adaptive_auth'] }),
  });
}
export function useAdaptive_authListRiskPolicies() {
  return useQuery({
    queryKey: ['adaptive_auth', 'listRiskPolicies'],
    queryFn: () => adaptive_authApi.listRiskPolicies(),
  });
}
export function useAdaptive_authCreateSessionPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adaptive_authApi.createSessionPolicy(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adaptive_auth'] }),
  });
}
export function useAdaptive_authGetActiveSessionCount(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['adaptive_auth', 'getActiveSessionCount', params],
    queryFn: ({ queryKey: [, , p] }) => adaptive_authApi.getActiveSessionCount(p as Record<string, string | number>),
  });
}
export function useAdminCreatePortal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adminApi.createPortal(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin'] }),
  });
}
export function useAdminListOrgPortals(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['admin', 'listOrgPortals', params],
    queryFn: ({ queryKey: [, , p] }) => adminApi.listOrgPortals(p as Record<string, string | number>),
  });
}
export function useAdminCreateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adminApi.createSubscription(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin'] }),
  });
}
export function useAdminGetSubscription(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['admin', 'getSubscription', params],
    queryFn: ({ queryKey: [, , p] }) => adminApi.getSubscription(p as Record<string, string | number>),
  });
}
export function useAdminGetAuditLog(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['admin', 'getAuditLog', params],
    queryFn: ({ queryKey: [, , p] }) => adminApi.getAuditLog(p as Record<string, string | number>),
  });
}
export function useAdminCreateFhirConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => adminApi.createFhirConnection(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin'] }),
  });
}
export function useAdminListFhirConnections(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['admin', 'listFhirConnections', params],
    queryFn: ({ queryKey: [, , p] }) => adminApi.listFhirConnections(p as Record<string, string | number>),
  });
}
export function useAi_fabricFabricHealth() {
  return useQuery({
    queryKey: ['ai_fabric', 'fabricHealth'],
    queryFn: () => ai_fabricApi.fabricHealth(),
  });
}
export function useAi_fabricFabricChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => ai_fabricApi.fabricChat(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai_fabric'] }),
  });
}
export function useAi_fabricFabricEmbed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => ai_fabricApi.fabricEmbed(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai_fabric'] }),
  });
}
export function useAi_fabricListProviders() {
  return useQuery({
    queryKey: ['ai_fabric', 'listProviders'],
    queryFn: () => ai_fabricApi.listProviders(),
  });
}
export function useAi_fabricGatewayCost() {
  return useQuery({
    queryKey: ['ai_fabric', 'gatewayCost'],
    queryFn: () => ai_fabricApi.gatewayCost(),
  });
}
export function useAi_fabricLocalAiStatus() {
  return useQuery({
    queryKey: ['ai_fabric', 'localAiStatus'],
    queryFn: () => ai_fabricApi.localAiStatus(),
  });
}
export function useAi_fabricRagQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => ai_fabricApi.ragQuery(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai_fabric'] }),
  });
}
export function useAi_fabricRagIndex() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => ai_fabricApi.ragIndex(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai_fabric'] }),
  });
}
export function useAi_fabricKgEntity() {
  return useQuery({
    queryKey: ['ai_fabric', 'kgEntity'],
    queryFn: () => ai_fabricApi.kgEntity(),
  });
}
export function useAi_fabricKgRelated() {
  return useQuery({
    queryKey: ['ai_fabric', 'kgRelated'],
    queryFn: () => ai_fabricApi.kgRelated(),
  });
}
export function useAuthLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => authApi.login(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth'] }),
  });
}
export function useAuthRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => authApi.register(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth'] }),
  });
}
export function useBiomedical_apiListDevices() {
  return useQuery({
    queryKey: ['biomedical_api', 'listDevices'],
    queryFn: () => biomedical_apiApi.listDevices(),
  });
}
export function useBiomedical_apiGetDevice(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['biomedical_api', 'getDevice', params],
    queryFn: ({ queryKey: [, , p] }) => biomedical_apiApi.getDevice(p as Record<string, string | number>),
  });
}
export function useBiomedical_apiUpdateDeviceStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => biomedical_apiApi.updateDeviceStatus(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['biomedical_api'] }),
  });
}
export function useBiomedical_apiDevicesDueForPm() {
  return useQuery({
    queryKey: ['biomedical_api', 'devicesDueForPm'],
    queryFn: () => biomedical_apiApi.devicesDueForPm(),
  });
}
export function useBiomedical_apiDevicesDueForCalibration() {
  return useQuery({
    queryKey: ['biomedical_api', 'devicesDueForCalibration'],
    queryFn: () => biomedical_apiApi.devicesDueForCalibration(),
  });
}
export function useBiomedical_apiCreateWorkOrder() {
  return useQuery({
    queryKey: ['biomedical_api', 'createWorkOrder'],
    queryFn: () => biomedical_apiApi.createWorkOrder(),
  });
}
export function useBiomedical_apiListWorkOrders() {
  return useQuery({
    queryKey: ['biomedical_api', 'listWorkOrders'],
    queryFn: () => biomedical_apiApi.listWorkOrders(),
  });
}
export function useBiomedical_apiGetWorkOrder(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['biomedical_api', 'getWorkOrder', params],
    queryFn: ({ queryKey: [, , p] }) => biomedical_apiApi.getWorkOrder(p as Record<string, string | number>),
  });
}
export function useBiomedical_apiCompleteWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => biomedical_apiApi.completeWorkOrder(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['biomedical_api'] }),
  });
}
export function useBiomedical_apiRecordCalibration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => biomedical_apiApi.recordCalibration(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['biomedical_api'] }),
  });
}
export function useBlood_bank_apiListDonors() {
  return useQuery({
    queryKey: ['blood_bank_api', 'listDonors'],
    queryFn: () => blood_bank_apiApi.listDonors(),
  });
}
export function useBlood_bank_apiGetDonor(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['blood_bank_api', 'getDonor', params],
    queryFn: ({ queryKey: [, , p] }) => blood_bank_apiApi.getDonor(p as Record<string, string | number>),
  });
}
export function useBlood_bank_apiDeferDonor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => blood_bank_apiApi.deferDonor(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useBlood_bank_apiRegisterDonation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => blood_bank_apiApi.registerDonation(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useBlood_bank_apiCompleteDonation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => blood_bank_apiApi.completeDonation(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useBlood_bank_apiProcessComponent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => blood_bank_apiApi.processComponent(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useBlood_bank_apiGetInventory() {
  return useQuery({
    queryKey: ['blood_bank_api', 'getInventory'],
    queryFn: () => blood_bank_apiApi.getInventory(),
  });
}
export function useBlood_bank_apiGetCriticalInventory() {
  return useQuery({
    queryKey: ['blood_bank_api', 'getCriticalInventory'],
    queryFn: () => blood_bank_apiApi.getCriticalInventory(),
  });
}
export function useBlood_bank_apiIssueUnits() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => blood_bank_apiApi.issueUnits(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useBlood_bank_apiPerformCrossmatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => blood_bank_apiApi.performCrossmatch(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['blood_bank_api'] }),
  });
}
export function useCapabilities_clinical_foundationListClinicalFoundation() {
  return useQuery({
    queryKey: ['capabilities_clinical_foundation', 'listClinicalFoundation'],
    queryFn: () => capabilities_clinical_foundationApi.listClinicalFoundation(),
  });
}
export function useCapabilities_clinical_foundationGetClinicalFoundation(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_clinical_foundation', 'getClinicalFoundation', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_clinical_foundationApi.getClinicalFoundation(p as Record<string, string | number>),
  });
}
export function useCapabilities_clinical_foundationCreateClinicalFoundation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_clinical_foundationApi.createClinicalFoundation(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_clinical_foundation'] }),
  });
}
export function useCapabilities_clinical_foundationUpdateClinicalFoundation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_clinical_foundationApi.updateClinicalFoundation(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_clinical_foundation'] }),
  });
}
export function useCapabilities_clinical_foundationDeleteClinicalFoundation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_clinical_foundationApi.deleteClinicalFoundation(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_clinical_foundation'] }),
  });
}
export function useCapabilities_document_managementListDocumentManagement() {
  return useQuery({
    queryKey: ['capabilities_document_management', 'listDocumentManagement'],
    queryFn: () => capabilities_document_managementApi.listDocumentManagement(),
  });
}
export function useCapabilities_document_managementGetDocumentManagement(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_document_management', 'getDocumentManagement', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_document_managementApi.getDocumentManagement(p as Record<string, string | number>),
  });
}
export function useCapabilities_document_managementCreateDocumentManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_document_managementApi.createDocumentManagement(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_document_management'] }),
  });
}
export function useCapabilities_document_managementUpdateDocumentManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_document_managementApi.updateDocumentManagement(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_document_management'] }),
  });
}
export function useCapabilities_document_managementDeleteDocumentManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_document_managementApi.deleteDocumentManagement(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_document_management'] }),
  });
}
export function useCapabilities_encounter_managementListEncounterManagement() {
  return useQuery({
    queryKey: ['capabilities_encounter_management', 'listEncounterManagement'],
    queryFn: () => capabilities_encounter_managementApi.listEncounterManagement(),
  });
}
export function useCapabilities_encounter_managementGetEncounterManagement(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_encounter_management', 'getEncounterManagement', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_encounter_managementApi.getEncounterManagement(p as Record<string, string | number>),
  });
}
export function useCapabilities_encounter_managementCreateEncounterManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_encounter_managementApi.createEncounterManagement(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_encounter_management'] }),
  });
}
export function useCapabilities_encounter_managementUpdateEncounterManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_encounter_managementApi.updateEncounterManagement(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_encounter_management'] }),
  });
}
export function useCapabilities_encounter_managementDeleteEncounterManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_encounter_managementApi.deleteEncounterManagement(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_encounter_management'] }),
  });
}
export function useCapabilities_fhir_interoperabilityListFhirInteroperability() {
  return useQuery({
    queryKey: ['capabilities_fhir_interoperability', 'listFhirInteroperability'],
    queryFn: () => capabilities_fhir_interoperabilityApi.listFhirInteroperability(),
  });
}
export function useCapabilities_fhir_interoperabilityGetFhirInteroperability(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_fhir_interoperability', 'getFhirInteroperability', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_fhir_interoperabilityApi.getFhirInteroperability(p as Record<string, string | number>),
  });
}
export function useCapabilities_fhir_interoperabilityCreateFhirInteroperability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_fhir_interoperabilityApi.createFhirInteroperability(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_fhir_interoperability'] }),
  });
}
export function useCapabilities_fhir_interoperabilityUpdateFhirInteroperability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_fhir_interoperabilityApi.updateFhirInteroperability(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_fhir_interoperability'] }),
  });
}
export function useCapabilities_fhir_interoperabilityDeleteFhirInteroperability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_fhir_interoperabilityApi.deleteFhirInteroperability(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_fhir_interoperability'] }),
  });
}
export function useCapabilities_healthcare_consentListHealthcareConsent() {
  return useQuery({
    queryKey: ['capabilities_healthcare_consent', 'listHealthcareConsent'],
    queryFn: () => capabilities_healthcare_consentApi.listHealthcareConsent(),
  });
}
export function useCapabilities_healthcare_consentGetHealthcareConsent(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_healthcare_consent', 'getHealthcareConsent', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_healthcare_consentApi.getHealthcareConsent(p as Record<string, string | number>),
  });
}
export function useCapabilities_healthcare_consentCreateHealthcareConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_healthcare_consentApi.createHealthcareConsent(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_healthcare_consent'] }),
  });
}
export function useCapabilities_healthcare_consentUpdateHealthcareConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_healthcare_consentApi.updateHealthcareConsent(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_healthcare_consent'] }),
  });
}
export function useCapabilities_healthcare_consentDeleteHealthcareConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_healthcare_consentApi.deleteHealthcareConsent(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_healthcare_consent'] }),
  });
}
export function useCapabilities_provider_managementListProviderManagement() {
  return useQuery({
    queryKey: ['capabilities_provider_management', 'listProviderManagement'],
    queryFn: () => capabilities_provider_managementApi.listProviderManagement(),
  });
}
export function useCapabilities_provider_managementGetProviderManagement(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_provider_management', 'getProviderManagement', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_provider_managementApi.getProviderManagement(p as Record<string, string | number>),
  });
}
export function useCapabilities_provider_managementCreateProviderManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_provider_managementApi.createProviderManagement(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_provider_management'] }),
  });
}
export function useCapabilities_provider_managementUpdateProviderManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_provider_managementApi.updateProviderManagement(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_provider_management'] }),
  });
}
export function useCapabilities_provider_managementDeleteProviderManagement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_provider_managementApi.deleteProviderManagement(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_provider_management'] }),
  });
}
export function useCapabilities_reporting_serviceListReportingService() {
  return useQuery({
    queryKey: ['capabilities_reporting_service', 'listReportingService'],
    queryFn: () => capabilities_reporting_serviceApi.listReportingService(),
  });
}
export function useCapabilities_reporting_serviceGetReportingService(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_reporting_service', 'getReportingService', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_reporting_serviceApi.getReportingService(p as Record<string, string | number>),
  });
}
export function useCapabilities_reporting_serviceCreateReportingService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_reporting_serviceApi.createReportingService(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_reporting_service'] }),
  });
}
export function useCapabilities_reporting_serviceUpdateReportingService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_reporting_serviceApi.updateReportingService(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_reporting_service'] }),
  });
}
export function useCapabilities_reporting_serviceDeleteReportingService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_reporting_serviceApi.deleteReportingService(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_reporting_service'] }),
  });
}
export function useCapabilities_search_serviceListSearchService() {
  return useQuery({
    queryKey: ['capabilities_search_service', 'listSearchService'],
    queryFn: () => capabilities_search_serviceApi.listSearchService(),
  });
}
export function useCapabilities_search_serviceGetSearchService(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_search_service', 'getSearchService', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_search_serviceApi.getSearchService(p as Record<string, string | number>),
  });
}
export function useCapabilities_search_serviceCreateSearchService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_search_serviceApi.createSearchService(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_search_service'] }),
  });
}
export function useCapabilities_search_serviceUpdateSearchService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_search_serviceApi.updateSearchService(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_search_service'] }),
  });
}
export function useCapabilities_search_serviceDeleteSearchService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_search_serviceApi.deleteSearchService(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_search_service'] }),
  });
}
export function useCapabilities_storage_serviceListStorageService() {
  return useQuery({
    queryKey: ['capabilities_storage_service', 'listStorageService'],
    queryFn: () => capabilities_storage_serviceApi.listStorageService(),
  });
}
export function useCapabilities_storage_serviceGetStorageService(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_storage_service', 'getStorageService', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_storage_serviceApi.getStorageService(p as Record<string, string | number>),
  });
}
export function useCapabilities_storage_serviceCreateStorageService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_storage_serviceApi.createStorageService(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_storage_service'] }),
  });
}
export function useCapabilities_storage_serviceUpdateStorageService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_storage_serviceApi.updateStorageService(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_storage_service'] }),
  });
}
export function useCapabilities_storage_serviceDeleteStorageService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_storage_serviceApi.deleteStorageService(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_storage_service'] }),
  });
}
export function useCapabilities_workflow_engineListWorkflowEngine() {
  return useQuery({
    queryKey: ['capabilities_workflow_engine', 'listWorkflowEngine'],
    queryFn: () => capabilities_workflow_engineApi.listWorkflowEngine(),
  });
}
export function useCapabilities_workflow_engineGetWorkflowEngine(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['capabilities_workflow_engine', 'getWorkflowEngine', params],
    queryFn: ({ queryKey: [, , p] }) => capabilities_workflow_engineApi.getWorkflowEngine(p as Record<string, string | number>),
  });
}
export function useCapabilities_workflow_engineCreateWorkflowEngine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => capabilities_workflow_engineApi.createWorkflowEngine(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_workflow_engine'] }),
  });
}
export function useCapabilities_workflow_engineUpdateWorkflowEngine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => capabilities_workflow_engineApi.updateWorkflowEngine(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_workflow_engine'] }),
  });
}
export function useCapabilities_workflow_engineDeleteWorkflowEngine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => capabilities_workflow_engineApi.deleteWorkflowEngine(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['capabilities_workflow_engine'] }),
  });
}
export function useCertificatesIssueCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => certificatesApi.issueCertificate(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certificates'] }),
  });
}
export function useCertificatesRevokeCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => certificatesApi.revokeCertificate(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certificates'] }),
  });
}
export function useCertificatesGetCertificate(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certificates', 'getCertificate', params],
    queryFn: ({ queryKey: [, , p] }) => certificatesApi.getCertificate(p as Record<string, string | number>),
  });
}
export function useCertificatesListOrgCertificates(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certificates', 'listOrgCertificates', params],
    queryFn: ({ queryKey: [, , p] }) => certificatesApi.listOrgCertificates(p as Record<string, string | number>),
  });
}
export function useCertificatesListExpiring() {
  return useQuery({
    queryKey: ['certificates', 'listExpiring'],
    queryFn: () => certificatesApi.listExpiring(),
  });
}
export function useCertificatesRegisterCa() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => certificatesApi.registerCa(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certificates'] }),
  });
}
export function useCertificatesListCas() {
  return useQuery({
    queryKey: ['certificates', 'listCas'],
    queryFn: () => certificatesApi.listCas(),
  });
}
export function useCertificatesGenerateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => certificatesApi.generateApiKey(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certificates'] }),
  });
}
export function useCertificatesListOrgApiKeys(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certificates', 'listOrgApiKeys', params],
    queryFn: ({ queryKey: [, , p] }) => certificatesApi.listOrgApiKeys(p as Record<string, string | number>),
  });
}
export function useCertificationEvaluateModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => certificationApi.evaluateModule(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certification'] }),
  });
}
export function useCertificationGetCertificationLevel(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certification', 'getCertificationLevel', params],
    queryFn: ({ queryKey: [, , p] }) => certificationApi.getCertificationLevel(p as Record<string, string | number>),
  });
}
export function useCertificationGetReport(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certification', 'getReport', params],
    queryFn: ({ queryKey: [, , p] }) => certificationApi.getReport(p as Record<string, string | number>),
  });
}
export function useCertificationGetAllMetrics() {
  return useQuery({
    queryKey: ['certification', 'getAllMetrics'],
    queryFn: () => certificationApi.getAllMetrics(),
  });
}
export function useCertificationGetMetricsByCategory(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certification', 'getMetricsByCategory', params],
    queryFn: ({ queryKey: [, , p] }) => certificationApi.getMetricsByCategory(p as Record<string, string | number>),
  });
}
export function useCertificationCheckReleaseGates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => certificationApi.checkReleaseGates(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certification'] }),
  });
}
export function useCertificationValidateRelease() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => certificationApi.validateRelease(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['certification'] }),
  });
}
export function useCertificationListDimensions() {
  return useQuery({
    queryKey: ['certification', 'listDimensions'],
    queryFn: () => certificationApi.listDimensions(),
  });
}
export function useCertificationGetDimensionChecks(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['certification', 'getDimensionChecks', params],
    queryFn: ({ queryKey: [, , p] }) => certificationApi.getDimensionChecks(p as Record<string, string | number>),
  });
}
export function useCitizen_platformGetDashboard(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'getDashboard', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.getDashboard(p as Record<string, string | number>),
  });
}
export function useCitizen_platformGetProfile(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'getProfile', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.getProfile(p as Record<string, string | number>),
  });
}
export function useCitizen_platformGetHealthSummary(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'getHealthSummary', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.getHealthSummary(p as Record<string, string | number>),
  });
}
export function useCitizen_platformListAppointments(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'listAppointments', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.listAppointments(p as Record<string, string | number>),
  });
}
export function useCitizen_platformBookAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => citizen_platformApi.bookAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['citizen_platform'] }),
  });
}
export function useCitizen_platformListMedications(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'listMedications', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.listMedications(p as Record<string, string | number>),
  });
}
export function useCitizen_platformListLabResults(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'listLabResults', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.listLabResults(p as Record<string, string | number>),
  });
}
export function useCitizen_platformListRadiologyStudies(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'listRadiologyStudies', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.listRadiologyStudies(p as Record<string, string | number>),
  });
}
export function useCitizen_platformGetFamily(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'getFamily', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.getFamily(p as Record<string, string | number>),
  });
}
export function useCitizen_platformGetVaccinations(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['citizen_platform', 'getVaccinations', params],
    queryFn: ({ queryKey: [, , p] }) => citizen_platformApi.getVaccinations(p as Record<string, string | number>),
  });
}
export function useCommand_center_apiListEmergencies() {
  return useQuery({
    queryKey: ['command_center_api', 'listEmergencies'],
    queryFn: () => command_center_apiApi.listEmergencies(),
  });
}
export function useCommand_center_apiGetEmergency(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['command_center_api', 'getEmergency', params],
    queryFn: ({ queryKey: [, , p] }) => command_center_apiApi.getEmergency(p as Record<string, string | number>),
  });
}
export function useCommand_center_apiResolveEmergency() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => command_center_apiApi.resolveEmergency(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['command_center_api'] }),
  });
}
export function useCommand_center_apiRequestResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => command_center_apiApi.requestResource(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['command_center_api'] }),
  });
}
export function useCommand_center_apiListResourceRequests() {
  return useQuery({
    queryKey: ['command_center_api', 'listResourceRequests'],
    queryFn: () => command_center_apiApi.listResourceRequests(),
  });
}
export function useCommand_center_apiFulfillResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => command_center_apiApi.fulfillResource(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['command_center_api'] }),
  });
}
export function useCommand_center_apiPublishSituationReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => command_center_apiApi.publishSituationReport(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['command_center_api'] }),
  });
}
export function useCommand_center_apiListSituationReports() {
  return useQuery({
    queryKey: ['command_center_api', 'listSituationReports'],
    queryFn: () => command_center_apiApi.listSituationReports(),
  });
}
export function useCommand_center_apiCompleteAfterAction() {
  return useQuery({
    queryKey: ['command_center_api', 'completeAfterAction'],
    queryFn: () => command_center_apiApi.completeAfterAction(),
  });
}
export function useCommand_center_apiListAfterActionReports() {
  return useQuery({
    queryKey: ['command_center_api', 'listAfterActionReports'],
    queryFn: () => command_center_apiApi.listAfterActionReports(),
  });
}
export function useCommand_intelligenceGetSituationRoom() {
  return useQuery({
    queryKey: ['command_intelligence', 'getSituationRoom'],
    queryFn: () => command_intelligenceApi.getSituationRoom(),
  });
}
export function useCommand_intelligenceGetKpis() {
  return useQuery({
    queryKey: ['command_intelligence', 'getKpis'],
    queryFn: () => command_intelligenceApi.getKpis(),
  });
}
export function useCommand_intelligenceGetKpiTrend(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['command_intelligence', 'getKpiTrend', params],
    queryFn: ({ queryKey: [, , p] }) => command_intelligenceApi.getKpiTrend(p as Record<string, string | number>),
  });
}
export function useCommand_intelligenceGetIncidents() {
  return useQuery({
    queryKey: ['command_intelligence', 'getIncidents'],
    queryFn: () => command_intelligenceApi.getIncidents(),
  });
}
export function useCommand_intelligenceReportIncident() {
  return useQuery({
    queryKey: ['command_intelligence', 'reportIncident'],
    queryFn: () => command_intelligenceApi.reportIncident(),
  });
}
export function useCommand_intelligenceGetCapacity() {
  return useQuery({
    queryKey: ['command_intelligence', 'getCapacity'],
    queryFn: () => command_intelligenceApi.getCapacity(),
  });
}
export function useCommand_intelligenceCreateRecommendation() {
  return useQuery({
    queryKey: ['command_intelligence', 'createRecommendation'],
    queryFn: () => command_intelligenceApi.createRecommendation(),
  });
}
export function useCommand_intelligenceExecutiveDashboard() {
  return useQuery({
    queryKey: ['command_intelligence', 'executiveDashboard'],
    queryFn: () => command_intelligenceApi.executiveDashboard(),
  });
}
export function useCommand_intelligenceRegionalDashboard(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['command_intelligence', 'regionalDashboard', params],
    queryFn: ({ queryKey: [, , p] }) => command_intelligenceApi.regionalDashboard(p as Record<string, string | number>),
  });
}
export function useComplianceRegisterFramework() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => complianceApi.registerFramework(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['compliance'] }),
  });
}
export function useComplianceListFrameworks() {
  return useQuery({
    queryKey: ['compliance', 'listFrameworks'],
    queryFn: () => complianceApi.listFrameworks(),
  });
}
export function useComplianceGetFramework(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['compliance', 'getFramework', params],
    queryFn: ({ queryKey: [, , p] }) => complianceApi.getFramework(p as Record<string, string | number>),
  });
}
export function useComplianceRunCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => complianceApi.runCheck(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['compliance'] }),
  });
}
export function useComplianceListChecks(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['compliance', 'listChecks', params],
    queryFn: ({ queryKey: [, , p] }) => complianceApi.listChecks(p as Record<string, string | number>),
  });
}
export function useComplianceGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => complianceApi.generateReport(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['compliance'] }),
  });
}
export function useComplianceGetReport(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['compliance', 'getReport', params],
    queryFn: ({ queryKey: [, , p] }) => complianceApi.getReport(p as Record<string, string | number>),
  });
}
export function useComplianceGetOrgComplianceStatus(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['compliance', 'getOrgComplianceStatus', params],
    queryFn: ({ queryKey: [, , p] }) => complianceApi.getOrgComplianceStatus(p as Record<string, string | number>),
  });
}
export function useControl_planeListComponents() {
  return useQuery({
    queryKey: ['control_plane', 'listComponents'],
    queryFn: () => control_planeApi.listComponents(),
  });
}
export function useControl_planeRegisterComponent() {
  return useQuery({
    queryKey: ['control_plane', 'registerComponent'],
    queryFn: () => control_planeApi.registerComponent(),
  });
}
export function useControl_planeUpdateComponent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => control_planeApi.updateComponent(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['control_plane'] }),
  });
}
export function useControl_planeUnregisterComponent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => control_planeApi.unregisterComponent(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['control_plane'] }),
  });
}
export function useControl_planeGetTopology() {
  return useQuery({
    queryKey: ['control_plane', 'getTopology'],
    queryFn: () => control_planeApi.getTopology(),
  });
}
export function useControl_planeControlPlaneHealth() {
  return useQuery({
    queryKey: ['control_plane', 'controlPlaneHealth'],
    queryFn: () => control_planeApi.controlPlaneHealth(),
  });
}
export function useControl_planeGetConfig(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['control_plane', 'getConfig', params],
    queryFn: ({ queryKey: [, , p] }) => control_planeApi.getConfig(p as Record<string, string | number>),
  });
}
export function useControl_planeSetConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => control_planeApi.setConfig(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['control_plane'] }),
  });
}
export function useControl_planeReloadConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => control_planeApi.reloadConfig(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['control_plane'] }),
  });
}
export function useControl_planeListPolicies() {
  return useQuery({
    queryKey: ['control_plane', 'listPolicies'],
    queryFn: () => control_planeApi.listPolicies(),
  });
}
export function useCritical_care_apiListAdmissions() {
  return useQuery({
    queryKey: ['critical_care_api', 'listAdmissions'],
    queryFn: () => critical_care_apiApi.listAdmissions(),
  });
}
export function useCritical_care_apiGetAdmission(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['critical_care_api', 'getAdmission', params],
    queryFn: ({ queryKey: [, , p] }) => critical_care_apiApi.getAdmission(p as Record<string, string | number>),
  });
}
export function useCritical_care_apiDischargePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => critical_care_apiApi.dischargePatient(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['critical_care_api'] }),
  });
}
export function useCritical_care_apiRegisterBed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => critical_care_apiApi.registerBed(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['critical_care_api'] }),
  });
}
export function useCritical_care_apiGetBedAvailability() {
  return useQuery({
    queryKey: ['critical_care_api', 'getBedAvailability'],
    queryFn: () => critical_care_apiApi.getBedAvailability(),
  });
}
export function useCritical_care_apiRecordVitals() {
  return useQuery({
    queryKey: ['critical_care_api', 'recordVitals'],
    queryFn: () => critical_care_apiApi.recordVitals(),
  });
}
export function useCritical_care_apiGetVitals(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['critical_care_api', 'getVitals', params],
    queryFn: ({ queryKey: [, , p] }) => critical_care_apiApi.getVitals(p as Record<string, string | number>),
  });
}
export function useCritical_care_apiSetVentilator(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['critical_care_api', 'setVentilator', params],
    queryFn: ({ queryKey: [, , p] }) => critical_care_apiApi.setVentilator(p as Record<string, string | number>),
  });
}
export function useCritical_care_apiGetVentilatorSettings(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['critical_care_api', 'getVentilatorSettings', params],
    queryFn: ({ queryKey: [, , p] }) => critical_care_apiApi.getVentilatorSettings(p as Record<string, string | number>),
  });
}
export function useCritical_care_apiCalculateEws() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => critical_care_apiApi.calculateEws(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['critical_care_api'] }),
  });
}
export function useEms_apiListIncidents() {
  return useQuery({
    queryKey: ['ems_api', 'listIncidents'],
    queryFn: () => ems_apiApi.listIncidents(),
  });
}
export function useEms_apiGetIncident(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['ems_api', 'getIncident', params],
    queryFn: ({ queryKey: [, , p] }) => ems_apiApi.getIncident(p as Record<string, string | number>),
  });
}
export function useEms_apiUpdateIncidentStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.updateIncidentStatus(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useEms_apiDispatchIncident() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.dispatchIncident(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useEms_apiRegisterAmbulance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.registerAmbulance(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useEms_apiListAmbulances() {
  return useQuery({
    queryKey: ['ems_api', 'listAmbulances'],
    queryFn: () => ems_apiApi.listAmbulances(),
  });
}
export function useEms_apiGetAmbulance(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['ems_api', 'getAmbulance', params],
    queryFn: ({ queryKey: [, , p] }) => ems_apiApi.getAmbulance(p as Record<string, string | number>),
  });
}
export function useEms_apiUpdateAmbulanceLocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.updateAmbulanceLocation(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useEms_apiUpdateAmbulanceStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.updateAmbulanceStatus(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useEms_apiRegisterCrew() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => ems_apiApi.registerCrew(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ems_api'] }),
  });
}
export function useFederationRegisterProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => federationApi.registerProvider(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['federation'] }),
  });
}
export function useFederationListProviders() {
  return useQuery({
    queryKey: ['federation', 'listProviders'],
    queryFn: () => federationApi.listProviders(),
  });
}
export function useFederationGetProvider(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['federation', 'getProvider', params],
    queryFn: ({ queryKey: [, , p] }) => federationApi.getProvider(p as Record<string, string | number>),
  });
}
export function useFederationLinkIdentity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => federationApi.linkIdentity(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['federation'] }),
  });
}
export function useFederationGetPersonIdentities(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['federation', 'getPersonIdentities', params],
    queryFn: ({ queryKey: [, , p] }) => federationApi.getPersonIdentities(p as Record<string, string | number>),
  });
}
export function useFederationEstablishTrust() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => federationApi.establishTrust(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['federation'] }),
  });
}
export function useFederationGetTrustRelationships(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['federation', 'getTrustRelationships', params],
    queryFn: ({ queryKey: [, , p] }) => federationApi.getTrustRelationships(p as Record<string, string | number>),
  });
}
export function useFederationCreateAgreement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => federationApi.createAgreement(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['federation'] }),
  });
}
export function useFederationListAgreements() {
  return useQuery({
    queryKey: ['federation', 'listAgreements'],
    queryFn: () => federationApi.listAgreements(),
  });
}
export function useGovernanceGetAuthorities() {
  return useQuery({
    queryKey: ['governance', 'getAuthorities'],
    queryFn: () => governanceApi.getAuthorities(),
  });
}
export function useGovernanceCreateAuthority() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.createAuthority(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceCreateCouncil() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.createCouncil(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceGetCouncils() {
  return useQuery({
    queryKey: ['governance', 'getCouncils'],
    queryFn: () => governanceApi.getCouncils(),
  });
}
export function useGovernanceSubmitPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.submitPolicy(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceApprovePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => governanceApi.approvePolicy(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceSubmitAppeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.submitAppeal(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceReviewAppeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => governanceApi.reviewAppeal(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceSuspendIdentity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.suspendIdentity(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceLiftSuspension() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => governanceApi.liftSuspension(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceRegisterEntity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.registerEntity(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useGovernanceGetRegistry(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['governance', 'getRegistry', params],
    queryFn: ({ queryKey: [, , p] }) => governanceApi.getRegistry(p as Record<string, string | number>),
  });
}
export function useGovernanceCreateReviewBoard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.createReviewBoard(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance'] }),
  });
}
export function useHealth_dataListCatalog() {
  return useQuery({
    queryKey: ['health_data', 'listCatalog'],
    queryFn: () => health_dataApi.listCatalog(),
  });
}
export function useHealth_dataGetDatasetMetadata(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['health_data', 'getDatasetMetadata', params],
    queryFn: ({ queryKey: [, , p] }) => health_dataApi.getDatasetMetadata(p as Record<string, string | number>),
  });
}
export function useHealth_dataGetLineage(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['health_data', 'getLineage', params],
    queryFn: ({ queryKey: [, , p] }) => health_dataApi.getLineage(p as Record<string, string | number>),
  });
}
export function useHealth_dataListPolicies() {
  return useQuery({
    queryKey: ['health_data', 'listPolicies'],
    queryFn: () => health_dataApi.listPolicies(),
  });
}
export function useHealth_dataCreatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => health_dataApi.createPolicy(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health_data'] }),
  });
}
export function useHealth_dataGetQualityMetrics() {
  return useQuery({
    queryKey: ['health_data', 'getQualityMetrics'],
    queryFn: () => health_dataApi.getQualityMetrics(),
  });
}
export function useHealth_dataTriggerIngestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => health_dataApi.triggerIngestion(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health_data'] }),
  });
}
export function useHealth_dataQueryEventStore() {
  return useQuery({
    queryKey: ['health_data', 'queryEventStore'],
    queryFn: () => health_dataApi.queryEventStore(),
  });
}
export function useHealth_dataRunWarehouseQuery() {
  return useQuery({
    queryKey: ['health_data', 'runWarehouseQuery'],
    queryFn: () => health_dataApi.runWarehouseQuery(),
  });
}
export function useHealth_dataMapFhirPatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => health_dataApi.mapFhirPatient(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['health_data'] }),
  });
}
export function useIntegrationListGateways() {
  return useQuery({
    queryKey: ['integration', 'listGateways'],
    queryFn: () => integrationApi.listGateways(),
  });
}
export function useIntegrationGetGateway(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['integration', 'getGateway', params],
    queryFn: ({ queryKey: [, , p] }) => integrationApi.getGateway(p as Record<string, string | number>),
  });
}
export function useIntegrationSendViaGateway() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integrationApi.sendViaGateway(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration'] }),
  });
}
export function useIntegrationReceiveViaGateway() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integrationApi.receiveViaGateway(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration'] }),
  });
}
export function useIntegrationApiCatalog() {
  return useQuery({
    queryKey: ['integration', 'apiCatalog'],
    queryFn: () => integrationApi.apiCatalog(),
  });
}
export function useIntegrationListIntegrationConnectors() {
  return useQuery({
    queryKey: ['integration', 'listIntegrationConnectors'],
    queryFn: () => integrationApi.listIntegrationConnectors(),
  });
}
export function useIntegrationStandardsConformance() {
  return useQuery({
    queryKey: ['integration', 'standardsConformance'],
    queryFn: () => integrationApi.standardsConformance(),
  });
}
export function useIntegrationRunTransformation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => integrationApi.runTransformation(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration'] }),
  });
}
export function useIntegrationIntegrationHealthDashboard() {
  return useQuery({
    queryKey: ['integration', 'integrationHealthDashboard'],
    queryFn: () => integrationApi.integrationHealthDashboard(),
  });
}
export function useIntegrationRunIntegrationTests() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => integrationApi.runIntegrationTests(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration'] }),
  });
}
export function useIntegration_connectorsConnectorsStatus() {
  return useQuery({
    queryKey: ['integration_connectors', 'connectorsStatus'],
    queryFn: () => integration_connectorsApi.connectorsStatus(),
  });
}
export function useIntegration_connectorsGetConnector(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['integration_connectors', 'getConnector', params],
    queryFn: ({ queryKey: [, , p] }) => integration_connectorsApi.getConnector(p as Record<string, string | number>),
  });
}
export function useIntegration_connectorsConnectConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integration_connectorsApi.connectConnector(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration_connectors'] }),
  });
}
export function useIntegration_connectorsDisconnectConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integration_connectorsApi.disconnectConnector(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration_connectors'] }),
  });
}
export function useIntegration_connectorsConnectorHealth(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['integration_connectors', 'connectorHealth', params],
    queryFn: ({ queryKey: [, , p] }) => integration_connectorsApi.connectorHealth(p as Record<string, string | number>),
  });
}
export function useIntegration_connectorsSendThroughConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integration_connectorsApi.sendThroughConnector(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration_connectors'] }),
  });
}
export function useIntegration_connectorsConfigureConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => integration_connectorsApi.configureConnector(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration_connectors'] }),
  });
}
export function useKernelKernelStatus() {
  return useQuery({
    queryKey: ['kernel', 'kernelStatus'],
    queryFn: () => kernelApi.kernelStatus(),
  });
}
export function useKernelKernelServices() {
  return useQuery({
    queryKey: ['kernel', 'kernelServices'],
    queryFn: () => kernelApi.kernelServices(),
  });
}
export function useKernelKernelCapabilities() {
  return useQuery({
    queryKey: ['kernel', 'kernelCapabilities'],
    queryFn: () => kernelApi.kernelCapabilities(),
  });
}
export function useKernelKernelPlugins() {
  return useQuery({
    queryKey: ['kernel', 'kernelPlugins'],
    queryFn: () => kernelApi.kernelPlugins(),
  });
}
export function useKernelKernelModules() {
  return useQuery({
    queryKey: ['kernel', 'kernelModules'],
    queryFn: () => kernelApi.kernelModules(),
  });
}
export function useKernelKernelConfig() {
  return useQuery({
    queryKey: ['kernel', 'kernelConfig'],
    queryFn: () => kernelApi.kernelConfig(),
  });
}
export function useKernelKernelOutbox() {
  return useQuery({
    queryKey: ['kernel', 'kernelOutbox'],
    queryFn: () => kernelApi.kernelOutbox(),
  });
}
export function useKernelKernelDeadLetterQueue() {
  return useQuery({
    queryKey: ['kernel', 'kernelDeadLetterQueue'],
    queryFn: () => kernelApi.kernelDeadLetterQueue(),
  });
}
export function useKernelKernelTenants() {
  return useQuery({
    queryKey: ['kernel', 'kernelTenants'],
    queryFn: () => kernelApi.kernelTenants(),
  });
}
export function useKernelKernelLocks() {
  return useQuery({
    queryKey: ['kernel', 'kernelLocks'],
    queryFn: () => kernelApi.kernelLocks(),
  });
}
export function useLifecycleStartRegistration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => lifecycleApi.startRegistration(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleValidateLicense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.validateLicense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleApproveRegistration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.approveRegistration(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleRejectRegistration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.rejectRegistration(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleGetEnterpriseStatus(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle', 'getEnterpriseStatus', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycleApi.getEnterpriseStatus(p as Record<string, string | number>),
  });
}
export function useLifecycleRequestEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => lifecycleApi.requestEmployee(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleApproveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.approveRequest(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleCreateAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => lifecycleApi.createAppointment(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleApproveAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.approveAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecyclePromoteEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.promoteEmployee(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleRegisterCitizen() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => lifecycleApi.registerCitizen(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleVerifyCitizenOtp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.verifyCitizenOtp(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleIssueHealthId() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.issueHealthId(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleDeactivateCitizen() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycleApi.deactivateCitizen(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleGetCitizenStatus(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle', 'getCitizenStatus', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycleApi.getCitizenStatus(p as Record<string, string | number>),
  });
}
export function useLifecycleCreateGuardianship() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => lifecycleApi.createGuardianship(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle'] }),
  });
}
export function useLifecycleGetDependents(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle', 'getDependents', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycleApi.getDependents(p as Record<string, string | number>),
  });
}
export function useLifecycle_platform_apiListComponents() {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'listComponents'],
    queryFn: () => lifecycle_platform_apiApi.listComponents(),
  });
}
export function useLifecycle_platform_apiGetComponent(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'getComponent', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycle_platform_apiApi.getComponent(p as Record<string, string | number>),
  });
}
export function useLifecycle_platform_apiFindComponent(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'findComponent', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycle_platform_apiApi.findComponent(p as Record<string, string | number>),
  });
}
export function useLifecycle_platform_apiUpdateComponentStage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycle_platform_apiApi.updateComponentStage(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle_platform_api'] }),
  });
}
export function useLifecycle_platform_apiCreateRelease() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycle_platform_apiApi.createRelease(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle_platform_api'] }),
  });
}
export function useLifecycle_platform_apiListReleases() {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'listReleases'],
    queryFn: () => lifecycle_platform_apiApi.listReleases(),
  });
}
export function useLifecycle_platform_apiGetRelease(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'getRelease', params],
    queryFn: ({ queryKey: [, , p] }) => lifecycle_platform_apiApi.getRelease(p as Record<string, string | number>),
  });
}
export function useLifecycle_platform_apiApproveRelease() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycle_platform_apiApi.approveRelease(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle_platform_api'] }),
  });
}
export function useLifecycle_platform_apiRecordCompatibility() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => lifecycle_platform_apiApi.recordCompatibility(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lifecycle_platform_api'] }),
  });
}
export function useLifecycle_platform_apiCheckCompatibility() {
  return useQuery({
    queryKey: ['lifecycle_platform_api', 'checkCompatibility'],
    queryFn: () => lifecycle_platform_apiApi.checkCompatibility(),
  });
}
export function useNational_background_platform_apiListJobs() {
  return useQuery({
    queryKey: ['national_background_platform_api', 'listJobs'],
    queryFn: () => national_background_platform_apiApi.listJobs(),
  });
}
export function useNational_background_platform_apiGetJob(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_background_platform_api', 'getJob', params],
    queryFn: ({ queryKey: [, , p] }) => national_background_platform_apiApi.getJob(p as Record<string, string | number>),
  });
}
export function useNational_background_platform_apiUpdateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.updateJob(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.deleteJob(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiExecuteJobNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.executeJobNow(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.cancelJob(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiPauseJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.pauseJob(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiResumeJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_background_platform_apiApi.resumeJob(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_background_platform_api'] }),
  });
}
export function useNational_background_platform_apiGetExecutionHistory(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_background_platform_api', 'getExecutionHistory', params],
    queryFn: ({ queryKey: [, , p] }) => national_background_platform_apiApi.getExecutionHistory(p as Record<string, string | number>),
  });
}
export function useNational_background_platform_apiGetSchedules(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_background_platform_api', 'getSchedules', params],
    queryFn: ({ queryKey: [, , p] }) => national_background_platform_apiApi.getSchedules(p as Record<string, string | number>),
  });
}
export function useNational_document_platform_apiListDocuments() {
  return useQuery({
    queryKey: ['national_document_platform_api', 'listDocuments'],
    queryFn: () => national_document_platform_apiApi.listDocuments(),
  });
}
export function useNational_document_platform_apiGetDocument(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_document_platform_api', 'getDocument', params],
    queryFn: ({ queryKey: [, , p] }) => national_document_platform_apiApi.getDocument(p as Record<string, string | number>),
  });
}
export function useNational_document_platform_apiUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_document_platform_apiApi.updateDocument(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_document_platform_api'] }),
  });
}
export function useNational_document_platform_apiDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_document_platform_apiApi.deleteDocument(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_document_platform_api'] }),
  });
}
export function useNational_document_platform_apiCreateVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_document_platform_apiApi.createVersion(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_document_platform_api'] }),
  });
}
export function useNational_document_platform_apiListVersions(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_document_platform_api', 'listVersions', params],
    queryFn: ({ queryKey: [, , p] }) => national_document_platform_apiApi.listVersions(p as Record<string, string | number>),
  });
}
export function useNational_document_platform_apiSignDocument(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_document_platform_api', 'signDocument', params],
    queryFn: ({ queryKey: [, , p] }) => national_document_platform_apiApi.signDocument(p as Record<string, string | number>),
  });
}
export function useNational_document_platform_apiListSignatures(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_document_platform_api', 'listSignatures', params],
    queryFn: ({ queryKey: [, , p] }) => national_document_platform_apiApi.listSignatures(p as Record<string, string | number>),
  });
}
export function useNational_document_platform_apiVerifyDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_document_platform_apiApi.verifyDocument(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_document_platform_api'] }),
  });
}
export function useNational_document_platform_apiGenerateQrCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_document_platform_apiApi.generateQrCode(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_document_platform_api'] }),
  });
}
export function useNational_ecosystemRegisterConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystemApi.registerConnector(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemListConnectors() {
  return useQuery({
    queryKey: ['national_ecosystem', 'listConnectors'],
    queryFn: () => national_ecosystemApi.listConnectors(),
  });
}
export function useNational_ecosystemConnectorHealth(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_ecosystem', 'connectorHealth', params],
    queryFn: ({ queryKey: [, , p] }) => national_ecosystemApi.connectorHealth(p as Record<string, string | number>),
  });
}
export function useNational_ecosystemUnregisterConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => national_ecosystemApi.unregisterConnector(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemConnectorSend() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_ecosystemApi.connectorSend(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemConnectorReceive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_ecosystemApi.connectorReceive(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemTransformData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystemApi.transformData(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemListSchemas() {
  return useQuery({
    queryKey: ['national_ecosystem', 'listSchemas'],
    queryFn: () => national_ecosystemApi.listSchemas(),
  });
}
export function useNational_ecosystemRegisterSchema() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystemApi.registerSchema(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystemValidateAgainstSchema() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_ecosystemApi.validateAgainstSchema(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem'] }),
  });
}
export function useNational_ecosystem_gatewayRouteRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystem_gatewayApi.routeRequest(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem_gateway'] }),
  });
}
export function useNational_ecosystem_gatewayGatewayStatus() {
  return useQuery({
    queryKey: ['national_ecosystem_gateway', 'gatewayStatus'],
    queryFn: () => national_ecosystem_gatewayApi.gatewayStatus(),
  });
}
export function useNational_ecosystem_gatewayListPolicies() {
  return useQuery({
    queryKey: ['national_ecosystem_gateway', 'listPolicies'],
    queryFn: () => national_ecosystem_gatewayApi.listPolicies(),
  });
}
export function useNational_ecosystem_gatewayCreatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystem_gatewayApi.createPolicy(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem_gateway'] }),
  });
}
export function useNational_ecosystem_gatewayUpdatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_ecosystem_gatewayApi.updatePolicy(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem_gateway'] }),
  });
}
export function useNational_ecosystem_gatewayDeletePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => national_ecosystem_gatewayApi.deletePolicy(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem_gateway'] }),
  });
}
export function useNational_ecosystem_gatewayListApiCatalog() {
  return useQuery({
    queryKey: ['national_ecosystem_gateway', 'listApiCatalog'],
    queryFn: () => national_ecosystem_gatewayApi.listApiCatalog(),
  });
}
export function useNational_ecosystem_gatewayRegisterApi() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_ecosystem_gatewayApi.registerApi(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_ecosystem_gateway'] }),
  });
}
export function useNational_notification_platform_apiListNotifications() {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'listNotifications'],
    queryFn: () => national_notification_platform_apiApi.listNotifications(),
  });
}
export function useNational_notification_platform_apiGetDashboard() {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'getDashboard'],
    queryFn: () => national_notification_platform_apiApi.getDashboard(),
  });
}
export function useNational_notification_platform_apiGetNotification(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'getNotification', params],
    queryFn: ({ queryKey: [, , p] }) => national_notification_platform_apiApi.getNotification(p as Record<string, string | number>),
  });
}
export function useNational_notification_platform_apiCancelNotification(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'cancelNotification', params],
    queryFn: ({ queryKey: [, , p] }) => national_notification_platform_apiApi.cancelNotification(p as Record<string, string | number>),
  });
}
export function useNational_notification_platform_apiCreateTemplate(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'createTemplate', params],
    queryFn: ({ queryKey: [, , p] }) => national_notification_platform_apiApi.createTemplate(p as Record<string, string | number>),
  });
}
export function useNational_notification_platform_apiListTemplates() {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'listTemplates'],
    queryFn: () => national_notification_platform_apiApi.listTemplates(),
  });
}
export function useNational_notification_platform_apiGetTemplate(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_notification_platform_api', 'getTemplate', params],
    queryFn: ({ queryKey: [, , p] }) => national_notification_platform_apiApi.getTemplate(p as Record<string, string | number>),
  });
}
export function useNational_notification_platform_apiUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_notification_platform_apiApi.updateTemplate(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_notification_platform_api'] }),
  });
}
export function useNational_notification_platform_apiDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_notification_platform_apiApi.deleteTemplate(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_notification_platform_api'] }),
  });
}
export function useNational_notification_platform_apiRenderTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_notification_platform_apiApi.renderTemplate(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_notification_platform_api'] }),
  });
}
export function useNational_observability_apiQueryMetrics() {
  return useQuery({
    queryKey: ['national_observability_api', 'queryMetrics'],
    queryFn: () => national_observability_apiApi.queryMetrics(),
  });
}
export function useNational_observability_apiRecordTraces() {
  return useQuery({
    queryKey: ['national_observability_api', 'recordTraces'],
    queryFn: () => national_observability_apiApi.recordTraces(),
  });
}
export function useNational_observability_apiGetTrace(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_observability_api', 'getTrace', params],
    queryFn: ({ queryKey: [, , p] }) => national_observability_apiApi.getTrace(p as Record<string, string | number>),
  });
}
export function useNational_observability_apiSearchTraces() {
  return useQuery({
    queryKey: ['national_observability_api', 'searchTraces'],
    queryFn: () => national_observability_apiApi.searchTraces(),
  });
}
export function useNational_observability_apiRunHealthCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_observability_apiApi.runHealthCheck(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_observability_api'] }),
  });
}
export function useNational_observability_apiListHealthChecks() {
  return useQuery({
    queryKey: ['national_observability_api', 'listHealthChecks'],
    queryFn: () => national_observability_apiApi.listHealthChecks(),
  });
}
export function useNational_observability_apiHealthStatus() {
  return useQuery({
    queryKey: ['national_observability_api', 'healthStatus'],
    queryFn: () => national_observability_apiApi.healthStatus(),
  });
}
export function useNational_observability_apiHealth() {
  return useQuery({
    queryKey: ['national_observability_api', 'health'],
    queryFn: () => national_observability_apiApi.health(),
  });
}
export function useNational_observability_apiCreateAlertRule() {
  return useQuery({
    queryKey: ['national_observability_api', 'createAlertRule'],
    queryFn: () => national_observability_apiApi.createAlertRule(),
  });
}
export function useNational_observability_apiListAlertRules() {
  return useQuery({
    queryKey: ['national_observability_api', 'listAlertRules'],
    queryFn: () => national_observability_apiApi.listAlertRules(),
  });
}
export function useNational_rules_engine_apiEvaluateRules() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_rules_engine_apiApi.evaluateRules(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiSimulateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_rules_engine_apiApi.simulateRule(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiCreateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_rules_engine_apiApi.createRule(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiListRules() {
  return useQuery({
    queryKey: ['national_rules_engine_api', 'listRules'],
    queryFn: () => national_rules_engine_apiApi.listRules(),
  });
}
export function useNational_rules_engine_apiGetRule(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_rules_engine_api', 'getRule', params],
    queryFn: ({ queryKey: [, , p] }) => national_rules_engine_apiApi.getRule(p as Record<string, string | number>),
  });
}
export function useNational_rules_engine_apiUpdateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_rules_engine_apiApi.updateRule(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiDeleteRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_rules_engine_apiApi.deleteRule(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiActivateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_rules_engine_apiApi.activateRule(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiDeactivateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_rules_engine_apiApi.deactivateRule(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_rules_engine_apiCreateRuleVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_rules_engine_apiApi.createRuleVersion(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_rules_engine_api'] }),
  });
}
export function useNational_scheduling_platform_apiListAppointments() {
  return useQuery({
    queryKey: ['national_scheduling_platform_api', 'listAppointments'],
    queryFn: () => national_scheduling_platform_apiApi.listAppointments(),
  });
}
export function useNational_scheduling_platform_apiGetAppointment(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_scheduling_platform_api', 'getAppointment', params],
    queryFn: ({ queryKey: [, , p] }) => national_scheduling_platform_apiApi.getAppointment(p as Record<string, string | number>),
  });
}
export function useNational_scheduling_platform_apiUpdateAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_scheduling_platform_apiApi.updateAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiCancelAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_scheduling_platform_apiApi.cancelAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiCompleteAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_scheduling_platform_apiApi.completeAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiMarkNoShow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_scheduling_platform_apiApi.markNoShow(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiRescheduleAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_scheduling_platform_apiApi.rescheduleAppointment(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiCheckAvailability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_scheduling_platform_apiApi.checkAvailability(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_scheduling_platform_api'] }),
  });
}
export function useNational_scheduling_platform_apiFindAvailableSlots() {
  return useQuery({
    queryKey: ['national_scheduling_platform_api', 'findAvailableSlots'],
    queryFn: () => national_scheduling_platform_apiApi.findAvailableSlots(),
  });
}
export function useNational_scheduling_platform_apiCreateResource() {
  return useQuery({
    queryKey: ['national_scheduling_platform_api', 'createResource'],
    queryFn: () => national_scheduling_platform_apiApi.createResource(),
  });
}
export function useNational_search_platform_apiSearchPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_search_platform_apiApi.searchPost(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_search_platform_api'] }),
  });
}
export function useNational_search_platform_apiSearchGet() {
  return useQuery({
    queryKey: ['national_search_platform_api', 'searchGet'],
    queryFn: () => national_search_platform_apiApi.searchGet(),
  });
}
export function useNational_search_platform_apiFhirSearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_search_platform_apiApi.fhirSearch(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_search_platform_api'] }),
  });
}
export function useNational_search_platform_apiSuggest() {
  return useQuery({
    queryKey: ['national_search_platform_api', 'suggest'],
    queryFn: () => national_search_platform_apiApi.suggest(),
  });
}
export function useNational_search_platform_apiGetFacets() {
  return useQuery({
    queryKey: ['national_search_platform_api', 'getFacets'],
    queryFn: () => national_search_platform_apiApi.getFacets(),
  });
}
export function useNational_search_platform_apiSaveSearch() {
  return useQuery({
    queryKey: ['national_search_platform_api', 'saveSearch'],
    queryFn: () => national_search_platform_apiApi.saveSearch(),
  });
}
export function useNational_search_platform_apiListSavedSearches() {
  return useQuery({
    queryKey: ['national_search_platform_api', 'listSavedSearches'],
    queryFn: () => national_search_platform_apiApi.listSavedSearches(),
  });
}
export function useNational_search_platform_apiGetSavedSearch(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_search_platform_api', 'getSavedSearch', params],
    queryFn: ({ queryKey: [, , p] }) => national_search_platform_apiApi.getSavedSearch(p as Record<string, string | number>),
  });
}
export function useNational_search_platform_apiDeleteSavedSearch(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_search_platform_api', 'deleteSavedSearch', params],
    queryFn: ({ queryKey: [, , p] }) => national_search_platform_apiApi.deleteSavedSearch(p as Record<string, string | number>),
  });
}
export function useNational_search_platform_apiRebuildIndex() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_search_platform_apiApi.rebuildIndex(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_search_platform_api'] }),
  });
}
export function useNational_task_engine_apiCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_task_engine_apiApi.createTask(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiBulkCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => national_task_engine_apiApi.bulkCreate(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiListTasks() {
  return useQuery({
    queryKey: ['national_task_engine_api', 'listTasks'],
    queryFn: () => national_task_engine_apiApi.listTasks(),
  });
}
export function useNational_task_engine_apiGetDashboard() {
  return useQuery({
    queryKey: ['national_task_engine_api', 'getDashboard'],
    queryFn: () => national_task_engine_apiApi.getDashboard(),
  });
}
export function useNational_task_engine_apiGetTask(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['national_task_engine_api', 'getTask', params],
    queryFn: ({ queryKey: [, , p] }) => national_task_engine_apiApi.getTask(p as Record<string, string | number>),
  });
}
export function useNational_task_engine_apiUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_task_engine_apiApi.updateTask(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: Record<string, string | number>) => national_task_engine_apiApi.deleteTask(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiAssignTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_task_engine_apiApi.assignTask(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiStartTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_task_engine_apiApi.startTask(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNational_task_engine_apiCompleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => national_task_engine_apiApi.completeTask(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['national_task_engine_api'] }),
  });
}
export function useNotificationsSendNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => notificationsApi.sendNotification(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function useNotificationsCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => notificationsApi.createTemplate(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function useNotificationsListTemplates() {
  return useQuery({
    queryKey: ['notifications', 'listTemplates'],
    queryFn: () => notificationsApi.listTemplates(),
  });
}
export function useNotificationsGetQueue(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['notifications', 'getQueue', params],
    queryFn: ({ queryKey: [, , p] }) => notificationsApi.getQueue(p as Record<string, string | number>),
  });
}
export function useNotificationsMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => notificationsApi.markNotificationRead(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function useNotificationsMarkNotificationSent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => notificationsApi.markNotificationSent(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function useNotificationsMarkNotificationDelivered() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => notificationsApi.markNotificationDelivered(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function useNotificationsGetPreferences(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['notifications', 'getPreferences', params],
    queryFn: ({ queryKey: [, , p] }) => notificationsApi.getPreferences(p as Record<string, string | number>),
  });
}
export function useNotificationsUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => notificationsApi.updatePreferences(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
export function usePatientsListPatients() {
  return useQuery({
    queryKey: ['patients', 'listPatients'],
    queryFn: () => patientsApi.listPatients(),
  });
}
export function usePatientsCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => patientsApi.createPatient(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['patients'] }),
  });
}
export function usePatientsGetPatient(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['patients', 'getPatient', params],
    queryFn: ({ queryKey: [, , p] }) => patientsApi.getPatient(p as Record<string, string | number>),
  });
}
export function usePharmacyGetDispenseQueue() {
  return useQuery({
    queryKey: ['pharmacy', 'getDispenseQueue'],
    queryFn: () => pharmacyApi.getDispenseQueue(),
  });
}
export function usePharmacyPrepareDispense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.prepareDispense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyVerifyDispense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.verifyDispense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyCompleteDispense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.completeDispense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyPartialDispense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.partialDispense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyCancelDispense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.cancelDispense(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyCreateDispenseRecord() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.createDispenseRecord(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyGetDispenseRecords() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.getDispenseRecords(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyCheckInteractions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pharmacyApi.checkInteractions(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePharmacyCheckContraindications() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => pharmacyApi.checkContraindications(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pharmacy'] }),
  });
}
export function usePilot_platform_apiListPilots() {
  return useQuery({
    queryKey: ['pilot_platform_api', 'listPilots'],
    queryFn: () => pilot_platform_apiApi.listPilots(),
  });
}
export function usePilot_platform_apiGetPilot(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'getPilot', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.getPilot(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiAdvancePhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pilot_platform_apiApi.advancePhase(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pilot_platform_api'] }),
  });
}
export function usePilot_platform_apiEnrollFacility() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => pilot_platform_apiApi.enrollFacility(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pilot_platform_api'] }),
  });
}
export function usePilot_platform_apiListPilotFacilities(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'listPilotFacilities', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.listPilotFacilities(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiAssessReadiness(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'assessReadiness', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.assessReadiness(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiGetFacilityReadiness(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'getFacilityReadiness', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.getFacilityReadiness(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiDecideGate(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'decideGate', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.decideGate(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiListGates(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'listGates', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.listGates(p as Record<string, string | number>),
  });
}
export function usePilot_platform_apiRecordDeployment(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['pilot_platform_api', 'recordDeployment', params],
    queryFn: ({ queryKey: [, , p] }) => pilot_platform_apiApi.recordDeployment(p as Record<string, string | number>),
  });
}
export function usePlatformPlatformHealth() {
  return useQuery({
    queryKey: ['platform', 'platformHealth'],
    queryFn: () => platformApi.platformHealth(),
  });
}
export function usePlatformPlatformModules() {
  return useQuery({
    queryKey: ['platform', 'platformModules'],
    queryFn: () => platformApi.platformModules(),
  });
}
export function usePlatformPlatformCapabilities() {
  return useQuery({
    queryKey: ['platform', 'platformCapabilities'],
    queryFn: () => platformApi.platformCapabilities(),
  });
}
export function usePublic_health_apiListCases() {
  return useQuery({
    queryKey: ['public_health_api', 'listCases'],
    queryFn: () => public_health_apiApi.listCases(),
  });
}
export function usePublic_health_apiGetCase(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['public_health_api', 'getCase', params],
    queryFn: ({ queryKey: [, , p] }) => public_health_apiApi.getCase(p as Record<string, string | number>),
  });
}
export function usePublic_health_apiGetCaseStats() {
  return useQuery({
    queryKey: ['public_health_api', 'getCaseStats'],
    queryFn: () => public_health_apiApi.getCaseStats(),
  });
}
export function usePublic_health_apiRaiseAlert() {
  return useQuery({
    queryKey: ['public_health_api', 'raiseAlert'],
    queryFn: () => public_health_apiApi.raiseAlert(),
  });
}
export function usePublic_health_apiListAlerts() {
  return useQuery({
    queryKey: ['public_health_api', 'listAlerts'],
    queryFn: () => public_health_apiApi.listAlerts(),
  });
}
export function usePublic_health_apiGetAlert(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['public_health_api', 'getAlert', params],
    queryFn: ({ queryKey: [, , p] }) => public_health_apiApi.getAlert(p as Record<string, string | number>),
  });
}
export function usePublic_health_apiUpdateAlertStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => public_health_apiApi.updateAlertStatus(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['public_health_api'] }),
  });
}
export function usePublic_health_apiRecordSignal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => public_health_apiApi.recordSignal(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['public_health_api'] }),
  });
}
export function usePublic_health_apiListSignals() {
  return useQuery({
    queryKey: ['public_health_api', 'listSignals'],
    queryFn: () => public_health_apiApi.listSignals(),
  });
}
export function usePublic_health_apiAnalyzeSurveillance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => public_health_apiApi.analyzeSurveillance(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['public_health_api'] }),
  });
}
export function useTrustCreateFramework() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => trustApi.createFramework(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trust'] }),
  });
}
export function useTrustListFrameworks() {
  return useQuery({
    queryKey: ['trust', 'listFrameworks'],
    queryFn: () => trustApi.listFrameworks(),
  });
}
export function useTrustGetFramework(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['trust', 'getFramework', params],
    queryFn: ({ queryKey: [, , p] }) => trustApi.getFramework(p as Record<string, string | number>),
  });
}
export function useTrustCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => trustApi.createProfile(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trust'] }),
  });
}
export function useTrustListProfiles() {
  return useQuery({
    queryKey: ['trust', 'listProfiles'],
    queryFn: () => trustApi.listProfiles(),
  });
}
export function useTrustRegisterAnchor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => trustApi.registerAnchor(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trust'] }),
  });
}
export function useTrustListAnchors() {
  return useQuery({
    queryKey: ['trust', 'listAnchors'],
    queryFn: () => trustApi.listAnchors(),
  });
}
export function useTrustEvaluateTrust() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => trustApi.evaluateTrust(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trust'] }),
  });
}
export function useTrustSubmitProofing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => trustApi.submitProofing(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trust'] }),
  });
}
export function useWorkflowsCreateDefinition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => workflowsApi.createDefinition(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });
}
export function useWorkflowsListDefinitions() {
  return useQuery({
    queryKey: ['workflows', 'listDefinitions'],
    queryFn: () => workflowsApi.listDefinitions(),
  });
}
export function useWorkflowsGetDefinition(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['workflows', 'getDefinition', params],
    queryFn: ({ queryKey: [, , p] }) => workflowsApi.getDefinition(p as Record<string, string | number>),
  });
}
export function useWorkflowsStartInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => workflowsApi.startInstance(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });
}
export function useWorkflowsGetInstance(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['workflows', 'getInstance', params],
    queryFn: ({ queryKey: [, , p] }) => workflowsApi.getInstance(p as Record<string, string | number>),
  });
}
export function useWorkflowsSubmitApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => workflowsApi.submitApproval(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });
}
export function useWorkflowsCancelInstance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => workflowsApi.cancelInstance(variables.data, variables.params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });
}
export function useWorkflowsGetPendingApprovals(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['workflows', 'getPendingApprovals', params],
    queryFn: ({ queryKey: [, , p] }) => workflowsApi.getPendingApprovals(p as Record<string, string | number>),
  });
}
