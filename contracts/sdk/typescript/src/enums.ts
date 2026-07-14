export const LabTypes = {
  PRIVATE: 'private',
  GOVERNMENT: 'government',
  HOSPITAL: 'hospital',
  CLINIC: 'clinic',
} as const;
export type LabType = (typeof LabTypes)[keyof typeof LabTypes];

export const LabRoles = {
  ADMIN: 'admin',
  TECHNICIAN: 'technician',
  DOCTOR: 'doctor',
  RECEPTIONIST: 'receptionist',
  STAFF: 'staff',
} as const;
export type LabRole = (typeof LabRoles)[keyof typeof LabRoles];

export const PlatformRoles = {
  LAB_ADMIN: 'lab_admin',
  TECHNICIAN: 'technician',
  DOCTOR: 'doctor',
  STAFF: 'staff',
  MASTER_ADMIN: 'master_admin',
  MINISTRY_ADMIN: 'ministry_admin',
  PROVINCE_ADMIN: 'province_admin',
  PATIENT: 'patient',
  CITIZEN: 'citizen',
  MONITORING: 'monitoring',
} as const;
export type PlatformRole = (typeof PlatformRoles)[keyof typeof PlatformRoles];

export const GenderValues = {
  MALE: 'male',
  FEMALE: 'female',
  M: 'M',
  F: 'F',
} as const;
export type Gender = (typeof GenderValues)[keyof typeof GenderValues];

export const SampleStatus = {
  COLLECTED: 'collected',
  RECEIVED: 'received',
  PROCESSING: 'processing',
  ANALYZED: 'analyzed',
  REJECTED: 'rejected',
} as const;
export type SampleStatus = (typeof SampleStatus)[keyof typeof SampleStatus];

export const ResultStatus = {
  PENDING: 'pending',
  COMPLETED: 'completed',
  VERIFIED: 'verified',
  REJECTED: 'rejected',
} as const;
export type ResultStatus = (typeof ResultStatus)[keyof typeof ResultStatus];

export const ClaimStatus = {
  DRAFT: 'draft',
  VALIDATED: 'validated',
  SUBMITTED: 'submitted',
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const;
export type ClaimStatus = (typeof ClaimStatus)[keyof typeof ClaimStatus];

export const NotificationChannel = {
  WHATSAPP: 'whatsapp',
  SMS: 'sms',
} as const;
export type NotificationChannel = (typeof NotificationChannel)[keyof typeof NotificationChannel];

export const EdgeRoleMode = {
  PERSONAL: 'personal',
  CLINIC: 'clinic',
  ENTERPRISE: 'enterprise',
} as const;
export type EdgeRoleMode = (typeof EdgeRoleMode)[keyof typeof EdgeRoleMode];

export const EdgeDeviceStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  QUARANTINED: 'quarantined',
  REVOKED: 'revoked',
} as const;
export type EdgeDeviceStatus = (typeof EdgeDeviceStatus)[keyof typeof EdgeDeviceStatus];

export const TaskStatus = {
  PENDING: 'pending',
  RUNNING: 'running',
  DONE: 'done',
  FAILED: 'failed',
  DEAD: 'dead',
} as const;
export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export const EdgeTaskPriority = {
  LOW: 1,
  MEDIUM: 5,
  HIGH: 10,
} as const;
export type EdgeTaskPriority = (typeof EdgeTaskPriority)[keyof typeof EdgeTaskPriority];

export const PrivacyLevel = {
  STANDARD: 'standard',
  SENSITIVE: 'sensitive',
  PHI: 'phi',
} as const;
export type PrivacyLevel = (typeof PrivacyLevel)[keyof typeof PrivacyLevel];

export const ModelStatus = {
  DRAFT: 'draft',
  CANARY: 'canary',
  ACTIVE: 'active',
  RETIRED: 'retired',
  BLOCKED: 'blocked',
} as const;
export type ModelStatus = (typeof ModelStatus)[keyof typeof ModelStatus];

export const ModelRuntime = {
  OLLAMA: 'ollama',
  LLAMACPP: 'llamacpp',
  ONNX: 'onnx',
  CUSTOM: 'custom',
} as const;
export type ModelRuntime = (typeof ModelRuntime)[keyof typeof ModelRuntime];

export const MpiMatchMethod = {
  NID_EXACT: 'nid_exact',
  PROBABILISTIC: 'probabilistic',
  PENDING_REVIEW: 'pending_review',
  NEW: 'new',
} as const;
export type MpiMatchMethod = (typeof MpiMatchMethod)[keyof typeof MpiMatchMethod];

export const ResolveDecision = {
  CONFIRM: 'confirm',
  REJECT: 'reject',
} as const;
export type ResolveDecision = (typeof ResolveDecision)[keyof typeof ResolveDecision];

export const FeedbackSignal = {
  HELPFUL: 'helpful',
  NOT_HELPFUL: 'not_helpful',
  UNCLEAR: 'unclear',
  NEED_DOCTOR: 'need_doctor',
  INCORRECT_INTERPRETATION: 'incorrect_interpretation',
} as const;
export type FeedbackSignal = (typeof FeedbackSignal)[keyof typeof FeedbackSignal];

export const SubscriptionTier = {
  STARTER: 'starter',
  GROWTH: 'growth',
  ENTERPRISE: 'enterprise',
} as const;
export type SubscriptionTier = (typeof SubscriptionTier)[keyof typeof SubscriptionTier];

export const OrderPriority = {
  ROUTINE: 'routine',
  URGENT: 'urgent',
  STAT: 'stat',
} as const;
export type OrderPriority = (typeof OrderPriority)[keyof typeof OrderPriority];

export const QcLevel = {
  LOW: 'low',
  NORMAL: 'normal',
  HIGH: 'high',
} as const;
export type QcLevel = (typeof QcLevel)[keyof typeof QcLevel];

export const AbnormalityDirection = {
  HIGH: 'high',
  LOW: 'low',
  NORMAL: 'normal',
} as const;
export type AbnormalityDirection = (typeof AbnormalityDirection)[keyof typeof AbnormalityDirection];

export const GovernanceNodeType = {
  GOVERNORATE: 'governorate',
  DIRECTORATE: 'directorate',
  PROVINCE: 'province',
  DISTRICT: 'district',
} as const;
export type GovernanceNodeType = (typeof GovernanceNodeType)[keyof typeof GovernanceNodeType];

export const ConsentScope = {
  VIEW_RESULTS: 'view:results',
  VIEW_PROFILE: 'view:profile',
  VIEW_HISTORY: 'view:history',
} as const;
export type ConsentScope = (typeof ConsentScope)[keyof typeof ConsentScope];

export const DeploymentMode = {
  SINGLE: 'single',
  MULTI: 'multi',
} as const;
export type DeploymentMode = (typeof DeploymentMode)[keyof typeof DeploymentMode];

export const SecurityLevel = {
  STANDARD: 'standard',
  ENHANCED: 'enhanced',
} as const;
export type SecurityLevel = (typeof SecurityLevel)[keyof typeof SecurityLevel];

export const BillingCycle = {
  MONTHLY: 'monthly',
  ANNUAL: 'annual',
} as const;
export type BillingCycle = (typeof BillingCycle)[keyof typeof BillingCycle];

export const HealthGrade = {
  GREEN: 'GREEN',
  YELLOW: 'YELLOW',
  RED: 'RED',
} as const;
export type HealthGrade = (typeof HealthGrade)[keyof typeof HealthGrade];
