import { LucideIcon } from 'lucide-react';

export type UserRole = 
  | 'physician' 
  | 'technician' 
  | 'admin' 
  | 'master_admin'
  | 'citizen' 
  | 'regulator' 
  | 'researcher' 
  | 'lab_admin' 
  | 'pathologist'
  | 'ministry_admin'
  | 'ministry_analyst'
  | 'ministry_inspector'
  | 'auditor'
  | 'integration_service';

export type UserWing = 'doctor' | 'lab' | 'citizen' | 'admin' | 'researcher' | 'regulator' | 'ministry' | 'system';

export type PermissionAction = 'read' | 'create' | 'update' | 'delete' | 'validate' | 'release' | 'audit' | 'manage';
export type PermissionResource = 'patient' | 'lab_test' | 'lab_result' | 'consent' | 'user' | 'system_config' | 'inventory' | 'audit_log' | 'infrastructure' | 'architecture' | 'integration' | 'research';
export type PermissionScope = 'own' | 'assigned' | 'entity' | 'global';

export interface Permission {
  resource: PermissionResource;
  action: PermissionAction;
  scope: PermissionScope;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  userEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  changes?: {
    before: any;
    after: any;
  };
  metadata: {
    ip: string;
    userAgent: string;
    severity: 'info' | 'warning' | 'critical';
  };
}

export interface Task {
  id: string;
  title: string;
  type: 'diagnostic' | 'validation' | 'inventory_check' | 'audit_review' | 'manual_review';
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'on_hold';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignedTo?: string;
  entityId: string; // Lab ID or Clinic ID
  relatedResourceId: string; // Patient ID or Sample ID
  slaDeadline: string;
  createdAt: string;
  updatedAt: string;
}

export interface Tenant {
  id: string;
  name: string;
  type: 'hospital' | 'lab' | 'clinic';
  status: 'active' | 'suspended';
  apiKey?: string;
}

export interface Consent {
  id: string;
  patientId: string;
  grantedTo: string;
  accessLevel: 'full' | 'redacted' | 'emergency';
  expiresAt: string;
  createdAt: string;
}

export type OrderStatus = 'pending' | 'received' | 'processing' | 'completed' | 'released';
export type Priority = 'routine' | 'urgent' | 'stat';

export interface ModuleMetadata {
  id: string;
  labelKey: string;
  icon: string;
  path: string;
  wing: UserWing;
  roles: UserRole[];
}

export type VerificationLevel = 'Level_1' | 'Level_2' | 'Level_3'; // Basic, Documented, Verified/Biometric
export type PermissionType = 'read_vitals' | 'read_labs' | 'read_history' | 'read_imaging' | 'write_order' | 'emergency';
export type ConsentDuration = '1_day' | '1_week' | '1_month' | 'permanent';

export interface AuditRecord {
  timestamp: any;
  actorId: string;
  action: string;
  previousValue?: any;
  newValue?: any;
  ipAddress?: string;
  reason?: string;
}

export interface PatientRecord {
  id: string;
  nationalId: string;
  name: string;
  age: number;
  gender: string;
  bloodType: string;
  identityVerified: boolean;
  verificationLevel: VerificationLevel;
  verificationStatus: 'unverified' | 'pending' | 'verified' | 'rejected';
  qrCode?: string;
  lastVisit?: string;
  status: 'active' | 'archived' | 'critical';
  phone: string;
  email: string;
  dob: string;
  auditTrail?: AuditRecord[];
}

export interface MedicalHistoryItem {
  id: string;
  patientId: string;
  date: string;
  type: 'diagnosis' | 'lab' | 'imaging' | 'prescription';
  description: string;
  provider: string;
  documents?: string[];
  title: string;
}

export interface LabSample {
  id: string;
  patientId: string;
  testType: string;
  status: OrderStatus;
  priority: Priority;
  receivedAt: string;
  processedAt?: string;
  technicianId?: string;
  deviceId?: string;
}

export interface ClinicalOrder {
  id: string;
  patientId: string;
  physicianId: string;
  tests: string[];
  status: 'ordered' | 'sampling' | 'processing' | 'completed';
  createdAt: string;
  aiNotes?: string;
}

export interface HealthInsight {
  id: string;
  patientId: string;
  type: 'warning' | 'info' | 'critical';
  title: string;
  content: string;
  actionRequired?: string;
  generatedAt: any;
}

export interface LabTestResult {
  id: string;
  testName: string;
  value: string;
  unit: string;
  range: string;
  flag?: 'H' | 'L' | 'N' | 'C';
  status: OrderStatus;
  labId: string;
  labName: string;
  verifiedBy?: string;
  verifiedAt?: any;
  trend?: { date: string; value: number }[];
}

export interface ConsentRecord {
  id: string;
  citizenId: string;
  providerId: string;
  providerName?: string;
  scope: 'full' | 'limited' | 'emergency';
  permissions: PermissionType[];
  grantedAt: string;
  expiresAt?: string;
  duration: ConsentDuration;
  status: 'active' | 'revoked' | 'expired';
  purposeOfUse: 'clinical' | 'research' | 'emergency';
}

export type EventType = 
  | 'critical_alert' 
  | 'expiring_reagent' 
  | 'consent_granted' 
  | 'consent_revoked' 
  | 'lab_result_ready'
  | 'inventory_low'
  | 'system_update';

export interface GulaEvent {
  id: string;
  type: EventType;
  recipientId: string; // User ID or 'all'
  senderId?: string;
  wing: UserWing | 'system';
  title?: string;
  message?: string;
  read: boolean;
  priority: Priority;
  payload?: any;
  createdAt: any;
}

export interface UserProfile {
  uid: string;
  role: UserRole;
  wing: UserWing;
  email: string;
  name: string;
  displayName?: string;
  nationalId?: string;
  licenseNumber?: string;
  specialization?: string;
  workplace?: string;
  verified: boolean;
  identityLevel?: number;
  createdAt: string;
}
