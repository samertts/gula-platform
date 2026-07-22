import { useQuery, useMutation, useQueryClient, type UseQueryOptions, type UseMutationOptions } from "@tanstack/react-query";
import {
  authApi, dashboardApi, patientsApi, ordersApi, resultsApi,
  samplesApi, labsApi, adminApi, criticalAlertsApi,
  qcApi, tiersApi,
  aiApi, aiPlatformApi, statsApi, healthApi, securityApi, complianceApi,
  mfaApi, serviceAccountsApi, ehrApi, careContinuumApi,
  clinicalFullApi, clinicalDocumentationApi, clinicalOrdersApi,
  clinicalQualityApi, hospitalApi, nationalDataApi, nationalStreamingApi,
  edgeApi, consentApi, claimsApi, integrationsApi, optimizerApi,
  financialApi, kernelRuntimeApi,
} from "@/api/endpoints";
import type { LoginRequest } from "@/types/api";
import type {
  Patient, LabOrder, Sample, Lab, CriticalAlert, QualityControl, LabResult,
  DashboardData, StatsSummary, TrendData,
  SubscriptionTier, SubscriptionInfo, User, AuditLog, AIProviderStatus,
} from "@/types";

// ── Helpers ──
function qk(...parts: unknown[]) {
  return parts.map(p => String(p ?? ""));
}

// ── Auth ──
export const authKeys = { all: ["auth"] as const };
export function useLogin(opts?: UseMutationOptions<unknown, Error, LoginRequest>) {
  return useMutation({ mutationFn: (d) => authApi.login(d), ...opts });
}
export function useLogout(opts?: UseMutationOptions<unknown, Error, void>) {
  return useMutation({ mutationFn: () => authApi.logout(), ...opts });
}
export function useChangePassword(opts?: UseMutationOptions<unknown, Error, { current_password: string; new_password: string }>) {
  return useMutation({ mutationFn: (d) => authApi.changePassword(d.current_password, d.new_password), ...opts });
}

// ── Dashboard ──
export const dashboardKeys = { all: ["dashboard"] as const };
export function useDashboard(opts?: UseQueryOptions<DashboardData>) {
  return useQuery({ queryKey: qk("dashboard"), queryFn: () => dashboardApi.dashboard(), ...opts });
}

// ── Patients ──
export const patientKeys = { all: ["patients"], list: (p?: Record<string, unknown>) => ["patients", "list", p], detail: (id: number) => ["patients", id] as const };
export function usePatients(params?: { search?: string; skip?: number; limit?: number }, opts?: UseQueryOptions<Patient[]>) {
  return useQuery({ queryKey: qk("patients", "list", JSON.stringify(params)), queryFn: () => patientsApi.list(params), ...opts });
}
export function usePatient(id: number, opts?: UseQueryOptions<Patient>) {
  return useQuery({ queryKey: qk("patients", id), queryFn: () => patientsApi.get(id), enabled: !!id, ...opts });
}
export function useCreatePatient(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (d) => patientsApi.create(d), onSuccess: () => qc.invalidateQueries({ queryKey: ["patients"] }), ...opts });
}
export function useUpdatePatient(opts?: UseMutationOptions<unknown, Error, { id: number; data: Record<string, unknown> }>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, data }) => patientsApi.update(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ["patients"] }), ...opts });
}

// ── Orders ──
export const orderKeys = { all: ["orders"], list: (p?: Record<string, unknown>) => ["orders", "list", p], detail: (id: number) => ["orders", id] as const };
export function useOrders(params?: { skip?: number; limit?: number; search?: string }, opts?: UseQueryOptions<LabOrder[]>) {
  return useQuery({ queryKey: qk("orders", "list", JSON.stringify(params)), queryFn: () => ordersApi.list(params), ...opts });
}
export function useOrder(id: number, opts?: UseQueryOptions<LabOrder>) {
  return useQuery({ queryKey: qk("orders", id), queryFn: () => ordersApi.get(id), enabled: !!id, ...opts });
}
export function useCreateOrder(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (d) => ordersApi.create(d), onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }), ...opts });
}
export function useCancelOrder(opts?: UseMutationOptions<unknown, Error, number>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id) => ordersApi.cancel(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }), ...opts });
}

// ── Results ──
export const resultKeys = { all: ["results"] as const };
export function useResults(params?: Record<string, unknown>, opts?: UseQueryOptions<LabResult[]>) {
  return useQuery({ queryKey: qk("results", JSON.stringify(params)), queryFn: () => resultsApi.list(params), ...opts });
}
export function useCreateResult(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (d) => resultsApi.create(d), onSuccess: () => qc.invalidateQueries({ queryKey: ["results"] }), ...opts });
}

// ── Samples ──
export const sampleKeys = { all: ["samples"] as const };
export function useSamples(params?: { status?: string; skip?: number; limit?: number }, opts?: UseQueryOptions<{ total: number; samples: Sample[] }>) {
  return useQuery({ queryKey: qk("samples", JSON.stringify(params)), queryFn: () => samplesApi.list(params), ...opts });
}
export function useSample(barcode: string, opts?: UseQueryOptions<Sample>) {
  return useQuery({ queryKey: qk("samples", barcode), queryFn: () => samplesApi.get(barcode), enabled: !!barcode, ...opts });
}
export function useCreateSample(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (d) => samplesApi.create(d), onSuccess: () => qc.invalidateQueries({ queryKey: ["samples"] }), ...opts });
}

// ── Labs ──
export const labKeys = { all: ["labs"], me: ["labs", "me"] as const };
export function useMyLab(opts?: UseQueryOptions<Lab>) {
  return useQuery({ queryKey: qk("labs", "me"), queryFn: () => labsApi.me(), ...opts });
}
export function useLabEmployees(opts?: UseQueryOptions<{ employees: unknown[] }>) {
  return useQuery({ queryKey: qk("labs", "employees"), queryFn: () => labsApi.employees(), ...opts });
}

// ── Admin ──
export function useAdminLabs(params?: { skip?: number; limit?: number }, opts?: UseQueryOptions<{ total: number; labs: Lab[] }>) {
  return useQuery({ queryKey: qk("admin", "labs", JSON.stringify(params)), queryFn: () => adminApi.labs(params), ...opts });
}
export function useAdminUsers(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; users: User[] }>) {
  return useQuery({ queryKey: qk("admin", "users", JSON.stringify(params)), queryFn: () => adminApi.users(params as { role?: string; lab_id?: number; skip?: number; limit?: number }), ...opts });
}
export function useAdminAuditLogs(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; logs: AuditLog[] }>) {
  return useQuery({ queryKey: qk("admin", "audit-logs", JSON.stringify(params)), queryFn: () => adminApi.auditLogs(params as { action?: string; user_id?: number; skip?: number; limit?: number }), ...opts });
}

// ── Critical Alerts ──
export function useCriticalAlerts(params?: { hours?: number; acknowledged?: boolean }, opts?: UseQueryOptions<CriticalAlert[]>) {
  return useQuery({ queryKey: qk("critical-alerts", JSON.stringify(params)), queryFn: () => criticalAlertsApi.list(params), ...opts });
}

// ── Quality Control ──
export function useQcResults(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; qc_results: QualityControl[] }>) {
  return useQuery({ queryKey: qk("qc", JSON.stringify(params)), queryFn: () => qcApi.list(params as { test_code?: string; status?: string; days?: number; skip?: number; limit?: number }), ...opts });
}

// ── Stats ──
export function useStatsSummary(opts?: UseQueryOptions<StatsSummary>) {
  return useQuery({ queryKey: qk("stats", "summary"), queryFn: () => statsApi.summary(), ...opts });
}
export function useDailyTrends(params?: { days?: number }, opts?: UseQueryOptions<TrendData>) {
  return useQuery({ queryKey: qk("stats", "trends", "daily", JSON.stringify(params)), queryFn: () => statsApi.dailyTrends(params), ...opts });
}

// ── Tiers ──
export function useTiers(opts?: UseQueryOptions<{ tiers: SubscriptionTier[] }>) {
  return useQuery({ queryKey: qk("tiers"), queryFn: () => tiersApi.list(), ...opts });
}
export function useMyTier(opts?: UseQueryOptions<SubscriptionInfo>) {
  return useQuery({ queryKey: qk("tiers", "my"), queryFn: () => tiersApi.my(), ...opts });
}

// ── AI ──
export function useAiPendingApprovals(opts?: UseQueryOptions<{ pending: number }>) {
  return useQuery({ queryKey: qk("ai", "pending"), queryFn: () => aiApi.pending(), ...opts });
}
export function useAiProviders(opts?: UseQueryOptions<AIProviderStatus>) {
  return useQuery({ queryKey: qk("ai", "providers"), queryFn: () => aiApi.providers(), ...opts });
}

// ── AI Platform v2 ──
export function useAiPlatformMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ai-platform", "metrics"), queryFn: () => aiPlatformApi.metrics(), ...opts });
}
export function useAiGovernanceModels(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ai-platform", "governance", "models"), queryFn: () => aiPlatformApi.governanceModels(), ...opts });
}
export function useAiGovernancePrompts(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ai-platform", "governance", "prompts"), queryFn: () => aiPlatformApi.governancePrompts(), ...opts });
}
export function useAiAgentTools(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ai-platform", "agents", "tools"), queryFn: () => aiPlatformApi.agentTools(), ...opts });
}
export function useAiKnowledgeGraphInfo(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ai-platform", "knowledge-graph", "info"), queryFn: () => aiPlatformApi.knowledgeGraphInfo(), ...opts });
}

// ── Compliance ──
export function useComplianceStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("compliance", "status"), queryFn: () => complianceApi.systemStatus(), ...opts });
}
export function useSecurityReport(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("compliance", "security-report"), queryFn: () => complianceApi.securityReport(), ...opts });
}
export function useFhirPatient(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("fhir", "patient", patientId), queryFn: () => complianceApi.fhirPatient(patientId), enabled: !!patientId, ...opts });
}

// ── Hospital ──
export function useHospitals(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("hospital", JSON.stringify(params)), queryFn: () => hospitalApi.list(params), ...opts });
}
export function useHospitalDepartments(hospitalId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("hospital", hospitalId, "departments"), queryFn: () => hospitalApi.listDepartments(hospitalId), enabled: !!hospitalId, ...opts });
}
export function useHospitalOccupancy(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("hospital", "occupancy", JSON.stringify(params)), queryFn: () => hospitalApi.occupancy(params), ...opts });
}
export function useHospitalAppointments(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("hospital", "appointments", JSON.stringify(params)), queryFn: () => hospitalApi.listAppointments(params), ...opts });
}
export function useHospitalEquipment(hospitalId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("hospital", hospitalId, "equipment"), queryFn: () => hospitalApi.listEquipment(hospitalId), enabled: !!hospitalId, ...opts });
}

// ── Edge ──
export function useEdgeDevices(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("edge", "devices", JSON.stringify(params)), queryFn: () => edgeApi.listDevices(params), ...opts });
}
export function useEdgeTasks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("edge", "tasks", JSON.stringify(params)), queryFn: () => edgeApi.listTasks(params), ...opts });
}
export function useEdgeFleetSummary(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("edge", "fleet", "summary"), queryFn: () => edgeApi.fleetSummary(), ...opts });
}

// ── Financial ──
export function useFinancialInvoices(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("financial", "invoices", JSON.stringify(params)), queryFn: () => financialApi.listInvoices(params), ...opts });
}
export function useFinancialPayments(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("financial", "payments", JSON.stringify(params)), queryFn: () => financialApi.listPayments(params), ...opts });
}
export function useFinancialTransactions(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("financial", "transactions", JSON.stringify(params)), queryFn: () => financialApi.listTransactions(params), ...opts });
}
export function useFinancialBillingStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("financial", "billing", "status"), queryFn: () => financialApi.billingStatus(), ...opts });
}

// ── National Data ──
export function useGoldenRecords(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("national-data", "golden-records", JSON.stringify(params)), queryFn: () => nationalDataApi.listGoldenRecords(params), ...opts });
}
export function useDataCatalog(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("national-data", "data-catalog", JSON.stringify(params)), queryFn: () => nationalDataApi.listDataCatalog(params), ...opts });
}
export function useDeidentificationJobs(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("national-data", "deidentification-jobs", JSON.stringify(params)), queryFn: () => nationalDataApi.listDeidentificationJobs(params), ...opts });
}

// ── Health ──
export function useHealthCheck(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("health"), queryFn: () => healthApi.health(), ...opts });
}
export function useDeepHealth(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("health", "deep"), queryFn: () => healthApi.deep(), ...opts });
}

// ── MFA ──
export function useMfaStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("mfa", "status"), queryFn: () => mfaApi.status(), ...opts });
}
export function useMfaDevices(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("mfa", "devices"), queryFn: () => mfaApi.devices(), ...opts });
}

// ── Security ──
export function useSecurityStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("security", "status"), queryFn: () => securityApi.status(), ...opts });
}

// ── EHR ──
export function usePatientEhr(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "patient", patientId), queryFn: () => ehrApi.getPatientEhr(patientId), enabled: !!patientId, ...opts });
}
export function usePatientSummary(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "patient", patientId, "summary"), queryFn: () => ehrApi.getPatientSummary(patientId), enabled: !!patientId, ...opts });
}
export function useClinicalNotes(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "clinical-notes", JSON.stringify(params)), queryFn: () => ehrApi.listClinicalNotes(params), ...opts });
}
export function useAllergies(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "allergies", JSON.stringify(params)), queryFn: () => ehrApi.listAllergies(params), ...opts });
}
export function useMedications(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "medication-statements", JSON.stringify(params)), queryFn: () => ehrApi.listMedicationStatements(params), ...opts });
}
export function useCarePlans(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "care-plans", JSON.stringify(params)), queryFn: () => ehrApi.listCarePlans(params), ...opts });
}
export function useConditions(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "conditions", JSON.stringify(params)), queryFn: () => ehrApi.listConditions(params), ...opts });
}
export function useImmunizations(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("ehr", "immunizations", JSON.stringify(params)), queryFn: () => ehrApi.listImmunizations(params), ...opts });
}

// ── Care Continuum ──
export function useReferrals(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("care-continuum", "referrals", JSON.stringify(params)), queryFn: () => careContinuumApi.listReferrals(params), ...opts });
}
export function useCareJourneys(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("care-continuum", "care-journeys", JSON.stringify(params)), queryFn: () => careContinuumApi.listCareJourneys(params), ...opts });
}
export function usePatientTasks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("care-continuum", "patient-tasks", JSON.stringify(params)), queryFn: () => careContinuumApi.listPatientTasks(params), ...opts });
}
export function useHealthPrograms(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("care-continuum", "health-programs", JSON.stringify(params)), queryFn: () => careContinuumApi.listHealthPrograms(params), ...opts });
}

// ── Clinical ──
export function useClinicalGuidelines(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "guidelines", JSON.stringify(params)), queryFn: () => clinicalFullApi.listGuidelines(params), ...opts });
}
export function useClinicalProtocols(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "protocols", JSON.stringify(params)), queryFn: () => clinicalFullApi.listProtocols(params), ...opts });
}
export function useClinicalPathways(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "pathways", JSON.stringify(params)), queryFn: () => clinicalFullApi.listPathways(params), ...opts });
}
export function useClinicalAlerts(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "cds", "alerts", JSON.stringify(params)), queryFn: () => clinicalFullApi.listAlerts(params), ...opts });
}
export function useQualityIndicators(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "quality", "indicators", JSON.stringify(params)), queryFn: () => clinicalFullApi.listQualityIndicators(), ...opts });
}
export function useResearchRegistries(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "research", "registries", JSON.stringify(params)), queryFn: () => clinicalFullApi.listRegistries(params), ...opts });
}

// ── Clinical Documentation ──
export function useDocumentationList(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "documentation", JSON.stringify(params)), queryFn: () => clinicalDocumentationApi.list(params), ...opts });
}
export function useDocumentationTemplates(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "documentation", "templates", JSON.stringify(params)), queryFn: () => clinicalDocumentationApi.listTemplates(params), ...opts });
}

// ── Clinical Orders ──
export function useClinicalOrderList(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "orders", JSON.stringify(params)), queryFn: () => clinicalOrdersApi.list(params), ...opts });
}
export function useClinicalOrderTemplates(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "orders", "templates", JSON.stringify(params)), queryFn: () => clinicalOrdersApi.listTemplates(params), ...opts });
}
export function useRecurringOrders(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "orders", "recurring", JSON.stringify(params)), queryFn: () => clinicalOrdersApi.listRecurring(params), ...opts });
}

// ── Clinical Quality ──
export function useQualityKpis(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "quality", "kpis", JSON.stringify(params)), queryFn: () => clinicalQualityApi.kpis(params), ...opts });
}
export function useQualityComplianceDashboard(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "quality", "compliance", JSON.stringify(params)), queryFn: () => clinicalQualityApi.complianceDashboard(params), ...opts });
}
export function useQualityBenchmarks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("clinical", "quality", "benchmarks", JSON.stringify(params)), queryFn: () => clinicalQualityApi.benchmarks(params), ...opts });
}

// ── National Streaming ──
export function useCdcFeed(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("national-data", "streaming", "cdc", JSON.stringify(params)), queryFn: () => nationalStreamingApi.getCdcFeed(params), ...opts });
}

// ── Optimizer ──
export function useOptimizerMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("optimizer", "metrics"), queryFn: () => optimizerApi.metrics(), ...opts });
}
export function useOptimizerAnalysis(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("optimizer", "analyze"), queryFn: () => optimizerApi.analyze(), ...opts });
}

// ── Kernel Runtime ──
export function useKernelHealth(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("kernel", "health"), queryFn: () => kernelRuntimeApi.health(), ...opts });
}
export function useKernelMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("kernel", "metrics"), queryFn: () => kernelRuntimeApi.metrics(), ...opts });
}
export function useKernelResources(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("kernel", "resources"), queryFn: () => kernelRuntimeApi.resources(), ...opts });
}
export function useKernelSlowQueries(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("kernel", "slow-queries"), queryFn: () => kernelRuntimeApi.slowQueries(), ...opts });
}
export function useKernelAiModels(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("kernel", "ai", "models"), queryFn: () => kernelRuntimeApi.aiModels(), ...opts });
}

// ── Integrations ──
export function useIntegrationStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("integrations", "status"), queryFn: () => integrationsApi.status(), ...opts });
}

// ── Consent ──
export function useConsentCheck(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("consent", "check", JSON.stringify(params)), queryFn: () => consentApi.check(params), ...opts });
}

// ── Claims ──
export function useClaim(claimId: string, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("claims", claimId), queryFn: () => claimsApi.get(claimId), enabled: !!claimId, ...opts });
}

// ── Service Accounts ──
export function useServiceAccounts(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("service-accounts"), queryFn: () => serviceAccountsApi.list(), ...opts });
}

// ── Events / Real-time ──
export function useEventStream(endpoint: string, params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: qk("events", endpoint, JSON.stringify(params)), queryFn: () => kernelRuntimeApi.validationReport(), ...opts });
}
