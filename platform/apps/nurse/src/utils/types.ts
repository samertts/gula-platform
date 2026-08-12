export interface Patient {
  id: string;
  mrn: string;
  name: string;
  age: number;
  gender: 'ذكر' | 'أنثى';
  ward: string;
  bed: string;
  diagnosis: string;
  attendingPhysician: string;
  admissionDate: string;
  allergies: string[];
  codeStatus: string;
  isolation: string | null;
  fallRisk: boolean;
}

export interface NursingTask {
  id: string;
  patientId: string;
  patientName: string;
  bed: string;
  type: TaskType;
  description: string;
  priority: Priority;
  status: TaskStatus;
  due: string;
  assignedTo: string;
  createdAt: string;
  notes?: string;
}

export type TaskType =
  | 'medication'
  | 'vitals'
  | 'wound_care'
  | 'catheter'
  | 'dressing'
  | 'observation'
  | 'feeding'
  | 'mobilization'
  | 'education'
  | 'assessment'
  | 'other';

export type Priority = 'low' | 'medium' | 'high' | 'urgent' | 'stat';

export type TaskStatus = 'pending' | 'in-progress' | 'completed' | 'cancelled' | 'delayed';

export interface Medication {
  id: string;
  patientId: string;
  patientName: string;
  bed: string;
  name: string;
  dosage: string;
  route: string;
  frequency: string;
  scheduledTime: string;
  administeredTime?: string;
  administeredBy?: string;
  status: 'scheduled' | 'given' | 'missed' | 'refused' | 'held';
  rightsVerified: FiveRights;
  notes?: string;
}

export interface FiveRights {
  rightPatient: boolean;
  rightMedication: boolean;
  rightDose: boolean;
  rightRoute: boolean;
  rightTime: boolean;
}

export interface VitalSigns {
  id: string;
  patientId: string;
  patientName: string;
  bed: string;
  temperature: number | null;
  heartRate: number | null;
  respiratoryRate: number | null;
  bloodPressureSystolic: number | null;
  bloodPressureDiastolic: number | null;
  oxygenSaturation: number | null;
  bloodGlucose: number | null;
  painScore: number | null;
  consciousness: string;
  recordedAt: string;
  recordedBy: string;
  earlyWarningScore?: number;
  notes?: string;
}

export interface CarePlan {
  id: string;
  patientId: string;
  patientName: string;
  bed: string;
  diagnosis: string;
  goals: CareGoal[];
  interventions: CareIntervention[];
  startDate: string;
  reviewDate: string;
  status: 'active' | 'completed' | 'revised';
  createdBy: string;
}

export interface CareGoal {
  id: string;
  description: string;
  targetDate: string;
  status: 'pending' | 'achieved' | 'revised';
}

export interface CareIntervention {
  id: string;
  description: string;
  frequency: string;
  status: 'active' | 'discontinued';
}

export interface ShiftHandover {
  id: string;
  date: string;
  shift: 'morning' | 'evening' | 'night';
  nurseInCharge: string;
  ward: string;
  totalPatients: number;
  admissions: number;
  discharges: number;
  transfers: number;
  criticalPatients: number;
  pendingTasks: number;
  incidents: string[];
  notes: string;
  handoverTo: string;
  createdAt: string;
}

export interface Admission {
  id: string;
  patientId: string;
  patientName: string;
  mrn: string;
  admissionDate: string;
  ward: string;
  bed: string;
  diagnosis: string;
  referringPhysician: string;
  admissionType: 'emergency' | 'elective' | 'transfer';
  status: 'admitted' | 'discharged' | 'transferred';
  notes?: string;
}

export interface BedAssignment {
  bed: string;
  ward: string;
  patientId: string | null;
  patientName: string | null;
  status: 'occupied' | 'available' | 'cleaning' | 'maintenance';
  isolation: string | null;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  ward: string;
  shift: string;
}

export interface OfflineQueueItem {
  id: string;
  type: 'vitals' | 'medication' | 'task' | 'assessment';
  action: 'create' | 'update';
  payload: unknown;
  createdAt: string;
  synced: boolean;
  schemaVersion?: 1;
  operationId?: string;
  idempotencyKey?: string;
  requestFingerprint?: string;
  expectedVersion?: number;
  state?: 'pending' | 'syncing' | 'synced' | 'conflict' | 'rejected' | 'failed';
  attempt?: number;
  maxAttempts?: number;
  updatedAt?: string;
  lastError?: string;
}
