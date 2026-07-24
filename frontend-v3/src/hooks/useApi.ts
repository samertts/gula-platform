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
import { queryKeys } from "./queryKeys";
import type { LoginRequest } from "@/types/api";
import type {
  Patient, LabOrder, Sample, Lab, CriticalAlert, QualityControl, LabResult,
  DashboardData, StatsSummary, TrendData,
  SubscriptionTier, SubscriptionInfo, User, AuditLog, AIProviderStatus,
} from "@/types";

// ── Auth ──
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
export function useDashboard(opts?: UseQueryOptions<DashboardData>) {
  return useQuery({ queryKey: queryKeys.dashboard.all, queryFn: () => dashboardApi.dashboard(), ...opts });
}

// ── Patients ──
export function usePatients(params?: { search?: string; skip?: number; limit?: number }, opts?: UseQueryOptions<Patient[]>) {
  return useQuery({ queryKey: queryKeys.patients.list(params), queryFn: () => patientsApi.list(params), ...opts });
}
export function usePatient(id: number, opts?: UseQueryOptions<Patient>) {
  return useQuery({ queryKey: queryKeys.patients.detail(id), queryFn: () => patientsApi.get(id), enabled: !!id, ...opts });
}
export function useCreatePatient(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (d) => patientsApi.create(d),
    onMutate: async () => { await qc.cancelQueries({ queryKey: queryKeys.patients.all }); },
    onError: (_err, _vars, _ctx) => { qc.invalidateQueries({ queryKey: queryKeys.patients.all }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.patients.all }),
    ...opts,
  });
}
export function useUpdatePatient(opts?: UseMutationOptions<unknown, Error, { id: number; data: Record<string, unknown> }>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => patientsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.patients.all }),
    ...opts,
  });
}

// ── Orders ──
export function useOrders(params?: { skip?: number; limit?: number; search?: string }, opts?: UseQueryOptions<LabOrder[]>) {
  return useQuery({ queryKey: queryKeys.orders.list(params), queryFn: () => ordersApi.list(params), ...opts });
}
export function useOrder(id: number, opts?: UseQueryOptions<LabOrder>) {
  return useQuery({ queryKey: queryKeys.orders.detail(id), queryFn: () => ordersApi.get(id), enabled: !!id, ...opts });
}
export function useCreateOrder(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (d) => ordersApi.create(d),
    onMutate: async () => { await qc.cancelQueries({ queryKey: queryKeys.orders.all }); },
    onError: () => { qc.invalidateQueries({ queryKey: queryKeys.orders.all }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.orders.all }),
    ...opts,
  });
}
export function useCancelOrder(opts?: UseMutationOptions<unknown, Error, number>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => ordersApi.cancel(id),
    onMutate: async () => { await qc.cancelQueries({ queryKey: queryKeys.orders.all }); },
    onError: () => { qc.invalidateQueries({ queryKey: queryKeys.orders.all }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.orders.all }),
    ...opts,
  });
}

// ── Results ──
export function useResults(params?: Record<string, unknown>, opts?: UseQueryOptions<LabResult[]>) {
  return useQuery({ queryKey: queryKeys.results.list(params), queryFn: () => resultsApi.list(params), ...opts });
}
export function useCreateResult(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (d) => resultsApi.create(d),
    onMutate: async () => { await qc.cancelQueries({ queryKey: queryKeys.results.all }); },
    onError: () => { qc.invalidateQueries({ queryKey: queryKeys.results.all }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.results.all }),
    ...opts,
  });
}

// ── Samples ──
export function useSamples(params?: { status?: string; skip?: number; limit?: number }, opts?: UseQueryOptions<{ total: number; samples: Sample[] }>) {
  return useQuery({ queryKey: queryKeys.samples.list(params), queryFn: () => samplesApi.list(params), ...opts });
}
export function useSample(barcode: string, opts?: UseQueryOptions<Sample>) {
  return useQuery({ queryKey: queryKeys.samples.detail(barcode), queryFn: () => samplesApi.get(barcode), enabled: !!barcode, ...opts });
}
export function useCreateSample(opts?: UseMutationOptions<unknown, Error, Record<string, unknown>>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (d) => samplesApi.create(d),
    onMutate: async () => { await qc.cancelQueries({ queryKey: queryKeys.samples.all }); },
    onError: () => { qc.invalidateQueries({ queryKey: queryKeys.samples.all }); },
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.samples.all }),
    ...opts,
  });
}

// ── Labs ──
export function useMyLab(opts?: UseQueryOptions<Lab>) {
  return useQuery({ queryKey: queryKeys.labs.me, queryFn: () => labsApi.me(), ...opts });
}
export function useLabEmployees(opts?: UseQueryOptions<{ employees: unknown[] }>) {
  return useQuery({ queryKey: queryKeys.labs.employees, queryFn: () => labsApi.employees(), ...opts });
}

// ── Admin ──
export function useAdminLabs(params?: { skip?: number; limit?: number }, opts?: UseQueryOptions<{ total: number; labs: Lab[] }>) {
  return useQuery({ queryKey: queryKeys.admin.labs(params), queryFn: () => adminApi.labs(params), ...opts });
}
export function useAdminUsers(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; users: User[] }>) {
  return useQuery({ queryKey: queryKeys.admin.users(params), queryFn: () => adminApi.users(params as { role?: string; lab_id?: number; skip?: number; limit?: number }), ...opts });
}
export function useAdminAuditLogs(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; logs: AuditLog[] }>) {
  return useQuery({ queryKey: queryKeys.admin.auditLogs(params), queryFn: () => adminApi.auditLogs(params as { action?: string; user_id?: number; skip?: number; limit?: number }), ...opts });
}

// ── Critical Alerts ──
export function useCriticalAlerts(params?: { hours?: number; acknowledged?: boolean }, opts?: UseQueryOptions<CriticalAlert[]>) {
  return useQuery({ queryKey: queryKeys.criticalAlerts.list(params), queryFn: () => criticalAlertsApi.list(params), ...opts });
}

// ── Quality Control ──
export function useQcResults(params?: Record<string, unknown>, opts?: UseQueryOptions<{ total: number; qc_results: QualityControl[] }>) {
  return useQuery({ queryKey: queryKeys.qc.list(params), queryFn: () => qcApi.list(params as { test_code?: string; status?: string; days?: number; skip?: number; limit?: number }), ...opts });
}

// ── Stats ──
export function useStatsSummary(opts?: UseQueryOptions<StatsSummary>) {
  return useQuery({ queryKey: queryKeys.stats.summary, queryFn: () => statsApi.summary(), ...opts });
}
export function useDailyTrends(params?: { days?: number }, opts?: UseQueryOptions<TrendData>) {
  return useQuery({ queryKey: queryKeys.stats.dailyTrends(params), queryFn: () => statsApi.dailyTrends(params), ...opts });
}

// ── Tiers ──
export function useTiers(opts?: UseQueryOptions<{ tiers: SubscriptionTier[] }>) {
  return useQuery({ queryKey: queryKeys.tiers.all, queryFn: () => tiersApi.list(), ...opts });
}
export function useMyTier(opts?: UseQueryOptions<SubscriptionInfo>) {
  return useQuery({ queryKey: queryKeys.tiers.my, queryFn: () => tiersApi.my(), ...opts });
}

// ── AI ──
export function useAiPendingApprovals(opts?: UseQueryOptions<{ pending: number }>) {
  return useQuery({ queryKey: queryKeys.ai.pending, queryFn: () => aiApi.pending() as unknown as Promise<{ pending: number }>, ...opts });
}
export function useAiProviders(opts?: UseQueryOptions<AIProviderStatus>) {
  return useQuery({ queryKey: queryKeys.ai.providers, queryFn: () => aiApi.providers(), ...opts });
}

// ── AI Platform v2 ──
export function useAiPlatformMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.aiPlatform.metrics, queryFn: () => aiPlatformApi.metrics(), ...opts });
}
export function useAiGovernanceModels(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.aiPlatform.governance.models, queryFn: () => aiPlatformApi.governanceModels(), ...opts });
}
export function useAiGovernancePrompts(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.aiPlatform.governance.prompts, queryFn: () => aiPlatformApi.governancePrompts(), ...opts });
}
export function useAiAgentTools(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.aiPlatform.agents.tools, queryFn: () => aiPlatformApi.agentTools(), ...opts });
}
export function useAiKnowledgeGraphInfo(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.aiPlatform.knowledgeGraph.info, queryFn: () => aiPlatformApi.knowledgeGraphInfo(), ...opts });
}

// ── Compliance ──
export function useComplianceStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.compliance.status, queryFn: () => complianceApi.systemStatus(), ...opts });
}
export function useSecurityReport(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.compliance.securityReport, queryFn: () => complianceApi.securityReport(), ...opts });
}
export function useFhirPatient(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.fhir.patient(patientId), queryFn: () => complianceApi.fhirPatient(patientId), enabled: !!patientId, ...opts });
}

// ── Hospital ──
export function useHospitals(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.hospital.list(params), queryFn: () => hospitalApi.list(params), ...opts });
}
export function useHospitalDepartments(hospitalId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.hospital.departments(hospitalId), queryFn: () => hospitalApi.listDepartments(hospitalId), enabled: !!hospitalId, ...opts });
}
export function useHospitalOccupancy(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.hospital.occupancy(params), queryFn: () => hospitalApi.occupancy(params), ...opts });
}
export function useHospitalAppointments(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.hospital.appointments(params), queryFn: () => hospitalApi.listAppointments(params), ...opts });
}
export function useHospitalEquipment(hospitalId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.hospital.equipment(hospitalId), queryFn: () => hospitalApi.listEquipment(hospitalId), enabled: !!hospitalId, ...opts });
}

// ── Edge ──
export function useEdgeDevices(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.edge.devices(params), queryFn: () => edgeApi.listDevices(params), ...opts });
}
export function useEdgeTasks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.edge.tasks(params), queryFn: () => edgeApi.listTasks(params), ...opts });
}
export function useEdgeFleetSummary(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.edge.fleetSummary, queryFn: () => edgeApi.fleetSummary(), ...opts });
}

// ── Financial ──
export function useFinancialInvoices(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.financial.invoices(params), queryFn: () => financialApi.listInvoices(params), ...opts });
}
export function useFinancialPayments(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.financial.payments(params), queryFn: () => financialApi.listPayments(params), ...opts });
}
export function useFinancialTransactions(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.financial.transactions(params), queryFn: () => financialApi.listTransactions(params), ...opts });
}
export function useFinancialBillingStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.financial.billingStatus, queryFn: () => financialApi.billingStatus(), ...opts });
}

// ── National Data ──
export function useGoldenRecords(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.nationalData.goldenRecords(params), queryFn: () => nationalDataApi.listGoldenRecords(params), ...opts });
}
export function useDataCatalog(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.nationalData.dataCatalog(params), queryFn: () => nationalDataApi.listDataCatalog(params), ...opts });
}
export function useDeidentificationJobs(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.nationalData.deidentificationJobs(params), queryFn: () => nationalDataApi.listDeidentificationJobs(params), ...opts });
}

// ── Health ──
export function useHealthCheck(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.health.basic, queryFn: () => healthApi.health(), ...opts });
}
export function useDeepHealth(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.health.deep, queryFn: () => healthApi.deep(), ...opts });
}

// ── MFA ──
export function useMfaStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.mfa.status, queryFn: () => mfaApi.status(), ...opts });
}
export function useMfaDevices(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.mfa.devices, queryFn: () => mfaApi.devices(), ...opts });
}

// ── Security ──
export function useSecurityStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.security.status, queryFn: () => securityApi.status(), ...opts });
}

// ── EHR ──
export function usePatientEhr(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.patient(patientId), queryFn: () => ehrApi.getPatientEhr(patientId), enabled: !!patientId, ...opts });
}
export function usePatientSummary(patientId: number, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.summary(patientId), queryFn: () => ehrApi.getPatientSummary(patientId), enabled: !!patientId, ...opts });
}
export function useClinicalNotes(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.clinicalNotes(params), queryFn: () => ehrApi.listClinicalNotes(params), ...opts });
}
export function useAllergies(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.allergies(params), queryFn: () => ehrApi.listAllergies(params), ...opts });
}
export function useMedications(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.medications(params), queryFn: () => ehrApi.listMedicationStatements(params), ...opts });
}
export function useCarePlans(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.carePlans(params), queryFn: () => ehrApi.listCarePlans(params), ...opts });
}
export function useConditions(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.conditions(params), queryFn: () => ehrApi.listConditions(params), ...opts });
}
export function useImmunizations(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.ehr.immunizations(params), queryFn: () => ehrApi.listImmunizations(params), ...opts });
}

// ── Care Continuum ──
export function useReferrals(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.careContinuum.referrals(params), queryFn: () => careContinuumApi.listReferrals(params), ...opts });
}
export function useCareJourneys(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.careContinuum.careJourneys(params), queryFn: () => careContinuumApi.listCareJourneys(params), ...opts });
}
export function usePatientTasks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.careContinuum.patientTasks(params), queryFn: () => careContinuumApi.listPatientTasks(params), ...opts });
}
export function useHealthPrograms(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.careContinuum.healthPrograms(params), queryFn: () => careContinuumApi.listHealthPrograms(params), ...opts });
}

// ── Clinical ──
export function useClinicalGuidelines(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.guidelines(params), queryFn: () => clinicalFullApi.listGuidelines(params), ...opts });
}
export function useClinicalProtocols(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.protocols(params), queryFn: () => clinicalFullApi.listProtocols(params), ...opts });
}
export function useClinicalPathways(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.pathways(params), queryFn: () => clinicalFullApi.listPathways(params), ...opts });
}
export function useClinicalAlerts(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.alerts(params), queryFn: () => clinicalFullApi.listAlerts(params), ...opts });
}
export function useQualityIndicators(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.qualityIndicators(params), queryFn: () => clinicalFullApi.listQualityIndicators(), ...opts });
}
export function useResearchRegistries(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.registries(params), queryFn: () => clinicalFullApi.listRegistries(params), ...opts });
}

// ── Clinical Documentation ──
export function useDocumentationList(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.documentation(params), queryFn: () => clinicalDocumentationApi.list(params), ...opts });
}
export function useDocumentationTemplates(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.documentationTemplates(params), queryFn: () => clinicalDocumentationApi.listTemplates(params), ...opts });
}

// ── Clinical Orders ──
export function useClinicalOrderList(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.orders(params), queryFn: () => clinicalOrdersApi.list(params), ...opts });
}
export function useClinicalOrderTemplates(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.orderTemplates(params), queryFn: () => clinicalOrdersApi.listTemplates(params), ...opts });
}
export function useRecurringOrders(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.recurringOrders(params), queryFn: () => clinicalOrdersApi.listRecurring(params), ...opts });
}

// ── Clinical Quality ──
export function useQualityKpis(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.kpis(params), queryFn: () => clinicalQualityApi.kpis(params), ...opts });
}
export function useQualityComplianceDashboard(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.complianceDashboard(params), queryFn: () => clinicalQualityApi.complianceDashboard(params), ...opts });
}
export function useQualityBenchmarks(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.clinical.benchmarks(params), queryFn: () => clinicalQualityApi.benchmarks(params), ...opts });
}

// ── National Streaming ──
export function useCdcFeed(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.nationalData.streaming.cdc(params), queryFn: () => nationalStreamingApi.getCdcFeed(params), ...opts });
}

// ── Optimizer ──
export function useOptimizerMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.optimizer.metrics, queryFn: () => optimizerApi.metrics(), ...opts });
}
export function useOptimizerAnalysis(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.optimizer.analyze, queryFn: () => optimizerApi.analyze(), ...opts });
}

// ── Kernel Runtime ──
export function useKernelHealth(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.kernel.health, queryFn: () => kernelRuntimeApi.health(), ...opts });
}
export function useKernelMetrics(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.kernel.metrics, queryFn: () => kernelRuntimeApi.metrics(), ...opts });
}
export function useKernelResources(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.kernel.resources, queryFn: () => kernelRuntimeApi.resources(), ...opts });
}
export function useKernelSlowQueries(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.kernel.slowQueries, queryFn: () => kernelRuntimeApi.slowQueries(), ...opts });
}
export function useKernelAiModels(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.kernel.aiModels, queryFn: () => kernelRuntimeApi.aiModels(), ...opts });
}

// ── Integrations ──
export function useIntegrationStatus(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.integrations.status, queryFn: () => integrationsApi.status(), ...opts });
}

// ── Consent ──
export function useConsentCheck(params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.consent.check(params), queryFn: () => consentApi.check(params), ...opts });
}

// ── Claims ──
export function useClaim(claimId: string, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.claims.detail(claimId), queryFn: () => claimsApi.get(claimId), enabled: !!claimId, ...opts });
}

// ── Service Accounts ──
export function useServiceAccounts(opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.serviceAccounts.all, queryFn: () => serviceAccountsApi.list(), ...opts });
}

// ── Events / Real-time ──
export function useEventStream(endpoint: string, params?: Record<string, unknown>, opts?: UseQueryOptions<Record<string, unknown>>) {
  return useQuery({ queryKey: queryKeys.events.stream(endpoint, params), queryFn: () => kernelRuntimeApi.validationReport(), ...opts });
}
