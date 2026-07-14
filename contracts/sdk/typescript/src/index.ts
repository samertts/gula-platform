import type { GulaClientConfig } from './client';
import { GulaClient } from './client';
export { GulaClient };
export type { GulaClientConfig };

export { SyncEngine } from './sync';
export type { SyncMutation, SyncOptions, SyncConflictStrategy } from './sync';

export {
  GulaError,
  AuthenticationError,
  PermissionError,
  NotFoundError,
  ConflictError,
  RateLimitError,
  ValidationError,
  ServerError,
  errorFromStatus,
} from './errors';

export {
  LabTypes, LabRoles, PlatformRoles, GenderValues,
  SampleStatus, ResultStatus, ClaimStatus, NotificationChannel,
  EdgeRoleMode, EdgeDeviceStatus, TaskStatus, EdgeTaskPriority,
  PrivacyLevel, ModelStatus, ModelRuntime, MpiMatchMethod,
  ResolveDecision, FeedbackSignal, SubscriptionTier, OrderPriority,
  QcLevel, AbnormalityDirection, GovernanceNodeType, ConsentScope,
  DeploymentMode, SecurityLevel, BillingCycle, HealthGrade,
} from './enums';

export type {
  LabType, LabRole, PlatformRole, Gender, SampleStatus as SampleStatusType,
  ResultStatus as ResultStatusType, ClaimStatus as ClaimStatusType,
  NotificationChannel as NotificationChannelType, EdgeRoleMode as EdgeRoleModeType,
  EdgeDeviceStatus as EdgeDeviceStatusType, TaskStatus as TaskStatusType,
  EdgeTaskPriority as EdgeTaskPriorityType, PrivacyLevel as PrivacyLevelType,
  ModelStatus as ModelStatusType, ModelRuntime as ModelRuntimeType,
  MpiMatchMethod as MpiMatchMethodType, ResolveDecision as ResolveDecisionType,
  FeedbackSignal as FeedbackSignalType,
  SubscriptionTier as SubscriptionTierType, OrderPriority as OrderPriorityType,
  QcLevel as QcLevelType, AbnormalityDirection as AbnormalityDirectionType,
  GovernanceNodeType as GovernanceNodeTypeType, ConsentScope as ConsentScopeType,
  DeploymentMode as DeploymentModeType, SecurityLevel as SecurityLevelType,
  BillingCycle as BillingCycleType, HealthGrade as HealthGradeType,
} from './enums';

export type {
  PaginationMeta, ListResponse, ApiError, QueryParams, PaginationParams,
  LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
  ChangePasswordRequest, LabRegisterRequest, CitizenRegisterRequest,
  StaffRegisterRequest, DoctorRegisterRequest, DeviceTokenRequest,
  CitizenLoginRequest, NationalIdRequest, CreateLabRequest, CreateUserRequest,
  ChangeRoleRequest, KillSwitchRequest, LinkIdentityRequest,
  UserBrief, PatientCreate, PatientUpdate, PatientResponse,
  PatientHistory, ScanRequest, ConvertGuestRequest,
  LabUpdate, LabResponse, CreateEmployeeRequest, UpdateEmployeeRequest,
  LabUserResponse, LabWorkHours, LabHoliday, LabSettings, LabDepartment,
  ResultItem, CreateOrderRequest, OrderResponse, ResultItemResponse,
  AnalyzeRequest, AnalyzeResponse, InterpretationResult, CriticalFlag,
  BatchOrderItem, BatchResultItem, BatchOrderRequest, BatchOrderResponse,
  TestResultCreate, TestResultRead, TestResultBrief, TestResultForCitizen,
  TestResultValidateRequest, DeviceResult, DeviceSubmission,
  DeviceSubmissionResponse, SuggestRequest, RejectRequest,
  ChatRequest, ChatResponse, ResultAmendment,
  SampleCreate, SampleUpdate, SampleResponse, SampleTransferRequest,
  GrantRequest, GrantResponse, RevokeRequest, RevokeResponse,
  CheckResponse, ConsentRecord,
  ClaimItemCreate, ClaimCreate, ClaimItemResponse, ClaimResponse,
  RegisterDeviceRequest, RegisterDeviceResponse, DeviceSummary,
  DeviceDetail, TaskSubmitRequest, TaskSummary, TaskDetail,
  PolicyView, PolicyUpdate, HeartbeatRequest, HeartbeatResponse,
  TaskResultRequest, ModelRegisterRequest, ModelInfo,
  ModelStatusUpdate, ModelAssignRequest, EdgeSite,
  CitizenResponse, MergeRequest, MergeResponse,
  PendingReviewItem, PendingReviewPage, ResolveDecisionBody,
  RetrievalRefIn, InteractionIn, InteractionOut, FeedbackIn, UnresolvedIn,
  NodeCreate, GovernanceNode, DelegationCreate, ActingAppoint,
  WorkerCreate, HealthcareWorker, LabRegister, GovernanceLab,
  SpecimenRegisterRequest, SpecimenTransitionRequest,
  LimsOrderCreateRequest, LimsResultCreateRequest, ResultValidateRequest,
  IQCRunRequest, InstrumentCreateRequest, InstrumentResponse,
  MaintenanceRecordRequest, CalibrationRecordRequest,
  InventoryRequest, InventoryItem, ReportGenerateRequest,
  DeviceMessageRequest, ASTMResultResponse, QCProgram,
  UpgradeRequestBody, DemandSignalBody, SetTierBody,
  FeatureFlagBody, TierInfo, TierUsage,
  QCSubmit, QCBatchSubmit, QCRecord, QCRule, LeveyJenningsData, LeveyJenningsPoint,
  NotifyRequest, NotificationRecord, NotificationPreferences,
  TaskPayload, TaskResult,
  DashboardSummary, StatsResponse, RevenueStats,
  PatientDemographics, TestPopularity, PeakHours,
  CriticalAlert, ComplianceRecord, Regulation, ComplianceReport,
  InsuranceRecord, InsuranceProvider,
  Integration, BatchOperation,
  FhirPatient, FhirPractitioner, FhirOrganization,
  FhirObservation, FhirDiagnosticReport, FhirSpecimen,
  FhirServiceRequest, FhirDevice, FhirEncounter, FhirBundle,
  FhirBundleEntry, FhirResource, FhirIdentifier, FhirHumanName,
  FhirContactPoint, FhirAddress, FhirCodeableConcept, FhirCoding,
  FhirReference, FhirQuantity, FhirReferenceRange, FhirSimpleQuantity,
  FhirPeriod, FhirAttachment, FhirQualification, FhirMeta,
  FhirEncounterParticipant, FhirSpecimenCollection,
  HealthStatus, HealthDeep, HealthComponent,
  OutboxEvent,
} from './types';

import { AuthAPI } from './api/auth';
import { PatientsAPI } from './api/patients';
import { LabsAPI } from './api/labs';
import { OrdersAPI } from './api/orders';
import { ResultsAPI } from './api/results';
import { SamplesAPI } from './api/samples';
import { AdminAPI } from './api/admin';
import { ComplianceAPI } from './api/compliance';
import { ClaimsAPI } from './api/claims';
import { ConsentAPI } from './api/consent';
import { EdgeAPI } from './api/edge';
import { MPIAPI } from './api/mpi';
import { NotificationsAPI } from './api/notifications';
import { QualityControlAPI } from './api/quality-control';
import { AIAPI } from './api/ai';
import { StatsAPI } from './api/stats';
import { GovernanceAPI } from './api/governance';
import { LIMSAPI } from './api/lims';
import { FHIRAPI } from './api/fhir';

export { AuthAPI, PatientsAPI, LabsAPI, OrdersAPI, ResultsAPI, SamplesAPI,
  AdminAPI, ComplianceAPI, ClaimsAPI, ConsentAPI, EdgeAPI, MPIAPI,
  NotificationsAPI, QualityControlAPI, AIAPI, StatsAPI, GovernanceAPI,
  LIMSAPI, FHIRAPI };

export class GulaPlatform {
  public readonly auth: AuthAPI;
  public readonly patients: PatientsAPI;
  public readonly labs: LabsAPI;
  public readonly orders: OrdersAPI;
  public readonly results: ResultsAPI;
  public readonly samples: SamplesAPI;
  public readonly admin: AdminAPI;
  public readonly compliance: ComplianceAPI;
  public readonly claims: ClaimsAPI;
  public readonly consent: ConsentAPI;
  public readonly edge: EdgeAPI;
  public readonly mpi: MPIAPI;
  public readonly notifications: NotificationsAPI;
  public readonly qualityControl: QualityControlAPI;
  public readonly ai: AIAPI;
  public readonly stats: StatsAPI;
  public readonly governance: GovernanceAPI;
  public readonly lims: LIMSAPI;
  public readonly fhir: FHIRAPI;

  constructor(public readonly client: GulaClient) {
    this.auth = new AuthAPI(client);
    this.patients = new PatientsAPI(client);
    this.labs = new LabsAPI(client);
    this.orders = new OrdersAPI(client);
    this.results = new ResultsAPI(client);
    this.samples = new SamplesAPI(client);
    this.admin = new AdminAPI(client);
    this.compliance = new ComplianceAPI(client);
    this.claims = new ClaimsAPI(client);
    this.consent = new ConsentAPI(client);
    this.edge = new EdgeAPI(client);
    this.mpi = new MPIAPI(client);
    this.notifications = new NotificationsAPI(client);
    this.qualityControl = new QualityControlAPI(client);
    this.ai = new AIAPI(client);
    this.stats = new StatsAPI(client);
    this.governance = new GovernanceAPI(client);
    this.lims = new LIMSAPI(client);
    this.fhir = new FHIRAPI(client);
  }
}

export default GulaPlatform;
