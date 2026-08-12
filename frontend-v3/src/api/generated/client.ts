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

// ── auth ──

export const authApi = {
  login: (data: unknown) =>
    api.post(`/login`, data).then(r => r.data),
  register: (data: unknown) =>
    api.post(`/register`, data).then(r => r.data),
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
  updateAuthority: (data: unknown, params: Record<string, string | number>) =>
    api.put(`/niam/governance/authorities/${params.authority_id}`, data).then(r => r.data),
  createCouncil: (data: unknown) =>
    api.post(`/niam/governance/councils`, data).then(r => r.data),
  getCouncils: () =>
    api.get(`/niam/governance/councils`).then(r => r.data),
  submitPolicy: (data: unknown) =>
    api.post(`/niam/governance/policies/submit`, data).then(r => r.data),
  approvePolicy: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/policies/${params.workflow_id}/approve`, data).then(r => r.data),
  submitAppeal: (data: unknown) =>
    api.post(`/niam/governance/appeals`, data).then(r => r.data),
  reviewAppeal: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/appeals/${params.appeal_id}/review`, data).then(r => r.data),
  suspendIdentity: (data: unknown) =>
    api.post(`/niam/governance/suspensions`, data).then(r => r.data),
  liftSuspension: (data: unknown, params: Record<string, string | number>) =>
    api.post(`/niam/governance/suspensions/${params.suspension_id}/lift`, data).then(r => r.data),
  restoreIdentity: (data: unknown) =>
    api.post(`/niam/governance/restorations`, data).then(r => r.data),
  registerEntity: (data: unknown) =>
    api.post(`/niam/governance/registries`, data).then(r => r.data),
  getRegistry: (params: Record<string, string | number>) =>
    api.get(`/niam/governance/registries/${params.registry_type}`).then(r => r.data),
  createReviewBoard: (data: unknown) =>
    api.post(`/niam/governance/review-board`, data).then(r => r.data),
  getReviewBoard: (params: Record<string, string | number>) =>
    api.get(`/niam/governance/review-board/${params.board_id}`).then(r => r.data),
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
    api.post(`/niam/trust/trust-anchors`, data).then(r => r.data),
  listAnchors: () =>
    api.get(`/niam/trust/trust-anchors`).then(r => r.data),
  evaluateTrust: (data: unknown) =>
    api.post(`/niam/trust/evaluate`, data).then(r => r.data),
  submitProofing: (data: unknown) =>
    api.post(`/niam/trust/identity-proofing`, data).then(r => r.data),
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
export function useGovernanceUpdateAuthority() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variables: { data: unknown; params: Record<string, string | number> }) => governanceApi.updateAuthority(variables.data, variables.params),
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
export function useGovernanceRestoreIdentity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => governanceApi.restoreIdentity(data),
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
export function useGovernanceGetReviewBoard(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['governance', 'getReviewBoard', params],
    queryFn: ({ queryKey: [, , p] }) => governanceApi.getReviewBoard(p as Record<string, string | number>),
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
