export interface CitizenUser {
  id: string;
  nationalId: string;
  name: string;
  nameEn?: string;
  phone: string;
  email?: string;
  dateOfBirth: string;
  gender: 'male' | 'female';
  bloodType?: string;
  verificationLevel: 'Level_1' | 'Level_2' | 'Level_3';
  identityVerified: boolean;
  photoUrl?: string;
  address?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FamilyMember {
  id: string;
  citizenId: string;
  nationalId: string;
  name: string;
  relationship: 'spouse' | 'child' | 'parent' | 'sibling' | 'other';
  dateOfBirth: string;
  gender: 'male' | 'female';
  bloodType?: string;
  photoUrl?: string;
  canViewRecords: boolean;
  canBookAppointments: boolean;
  createdAt: string;
}

export interface HealthRecord {
  id: string;
  patientId: string;
  type: 'lab_result' | 'radiology' | 'prescription' | 'vaccination' | 'diagnosis' | 'procedure' | 'visit';
  title: string;
  titleEn?: string;
  description?: string;
  provider: string;
  providerId: string;
  facilityName: string;
  date: string;
  createdAt: string;
  attachments?: string[];
  metadata?: Record<string, unknown>;
}

export interface LabResult {
  id: string;
  patientId: string;
  orderId: string;
  labName: string;
  labId: string;
  testName: string;
  testNameEn?: string;
  category: string;
  value: string;
  unit: string;
  referenceRange: string;
  flag: 'H' | 'L' | 'N' | 'C';
  interpretation?: string;
  interpretationEn?: string;
  performedDate: string;
  verifiedDate?: string;
  verifiedBy?: string;
  status: 'pending' | 'completed' | 'verified' | 'amended';
  trend?: { date: string; value: number }[];
}

export interface RadiologyReport {
  id: string;
  patientId: string;
  studyId: string;
  modality: 'X-ray' | 'CT' | 'MRI' | 'Ultrasound' | 'Mammography' | 'PET' | 'Other';
  bodyPart: string;
  bodyPartEn?: string;
  findings: string;
  findingsEn?: string;
  impression: string;
  impressionEn?: string;
  radiologist: string;
  facility: string;
  studyDate: string;
  reportDate: string;
  status: 'preliminary' | 'final' | 'amended';
  imageUrls?: string[];
  pdfUrl?: string;
}

export interface Prescription {
  id: string;
  patientId: string;
  medicationName: string;
  medicationNameEn?: string;
  dosage: string;
  frequency: string;
  route: 'oral' | 'topical' | 'injection' | 'inhalation' | 'other';
  quantity: number;
  refills: number;
  prescribedBy: string;
  prescribedDate: string;
  expiryDate: string;
  status: 'active' | 'completed' | 'cancelled' | 'expired';
  notes?: string;
  pharmacy?: string;
  isControlled: boolean;
}

export interface Vaccination {
  id: string;
  patientId: string;
  vaccineName: string;
  vaccineNameEn?: string;
  doseNumber: number;
  totalDoses: number;
  administeredDate: string;
  administeredBy: string;
  facility: string;
  batchNumber: string;
  nextDoseDate?: string;
  status: 'completed' | 'scheduled' | 'overdue';
  notes?: string;
}

export interface Appointment {
  id: string;
  patientId: string;
  providerId: string;
  providerName: string;
  providerSpecialty?: string;
  facilityName: string;
  facilityId: string;
  type: 'checkup' | 'consultation' | 'followup' | 'emergency' | 'lab_test' | 'vaccination';
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  date: string;
  startTime: string;
  endTime: string;
  notes?: string;
  isVirtual: boolean;
  meetingUrl?: string;
  createdAt: string;
}

export interface Consent {
  id: string;
  citizenId: string;
  providerId: string;
  providerName: string;
  providerType: 'lab' | 'hospital' | 'clinic' | 'pharmacy' | 'research';
  scope: 'full' | 'limited' | 'emergency';
  permissions: ConsentPermission[];
  grantedAt: string;
  expiresAt?: string;
  duration: '1_day' | '1_week' | '1_month' | 'permanent';
  status: 'active' | 'revoked' | 'expired';
  purposeOfUse: 'clinical' | 'research' | 'emergency' | 'administrative';
  revokedAt?: string;
  revocationReason?: string;
}

export type ConsentPermission =
  | 'read_vitals'
  | 'read_labs'
  | 'read_history'
  | 'read_imaging'
  | 'read_prescriptions'
  | 'write_order'
  | 'emergency_access';

export interface Notification {
  id: string;
  userId: string;
  title: string;
  titleEn?: string;
  body: string;
  bodyEn?: string;
  type: 'lab_result' | 'appointment' | 'medication' | 'consent' | 'emergency' | 'system' | 'family';
  priority: 'low' | 'normal' | 'high' | 'critical';
  read: boolean;
  actionable: boolean;
  actionUrl?: string;
  actionLabel?: string;
  actionLabelEn?: string;
  createdAt: string;
}

export interface EmergencyContact {
  id: string;
  name: string;
  nameEn?: string;
  relationship: string;
  phone: string;
  isPrimary: boolean;
}

export interface EmergencyInfo {
  bloodType: string;
  allergies: string[];
  chronicConditions: string[];
  medications: string[];
  emergencyContacts: EmergencyContact[];
  organDonor: boolean;
  preferredHospital?: string;
  notes?: string;
}

export interface PaymentMethod {
  id: string;
  type: 'credit_card' | 'debit_card' | 'bank_transfer' | 'wallet' | 'cash';
  label: string;
  last4?: string;
  expiryDate?: string;
  isDefault: boolean;
  isVerified: boolean;
}

export interface PaymentTransaction {
  id: string;
  patientId: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  type: 'appointment' | 'lab_test' | 'medication' | 'telemedicine' | 'other';
  description: string;
  descriptionEn?: string;
  paymentMethod?: string;
  invoiceUrl?: string;
  createdAt: string;
  completedAt?: string;
}

export interface TelemedicineSession {
  id: string;
  patientId: string;
  providerId: string;
  providerName: string;
  providerSpecialty: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  scheduledDate: string;
  startTime?: string;
  endTime?: string;
  duration?: number;
  meetingUrl: string;
  notes?: string;
  recordingUrl?: string;
}

export interface OfflineQueueItem {
  id?: number;
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
}

export interface SyncStatus {
  lastSync: Date | null;
  pendingItems: number;
  isSyncing: boolean;
  error?: string;
}

export interface HealthScore {
  overall: number;
  physical: number;
  mental: number;
  lifestyle: number;
  lastUpdated: string;
  trends: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type: 'text' | 'report' | 'suggestion' | 'alert';
  metadata?: Record<string, unknown>;
}
