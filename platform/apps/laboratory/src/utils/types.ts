export interface LabUser {
  id: string;
  labId: string;
  name: string;
  email: string;
  role: LabRole;
  specialization?: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
}

export type LabRole = 'technician' | 'senior_technician' | 'pathologist' | 'lab_manager' | 'admin' | 'phlebotomist';

export interface Sample {
  id: string;
  sampleId: string;
  barcode: string;
  patientId: string;
  patientName: string;
  patientPhone?: string;
  specimenType: SpecimenType;
  tests: string[];
  priority: Priority;
  status: SampleStatus;
  collectedAt?: string;
  collectedBy?: string;
  receivedAt?: string;
  receivedBy?: string;
  processedAt?: string;
  analyzedAt?: string;
  verifiedAt?: string;
  verifiedBy?: string;
  rejectedReason?: string;
  volume?: number;
  container?: string;
  storage?: string;
  expiresAt?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export type SpecimenType =
  | 'whole_blood' | 'serum' | 'plasma' | 'urine' | 'stool'
  | 'csf' | 'sputum' | 'swab' | 'tissue' | 'bone_marrow'
  | 'amniotic' | 'pleural' | 'pericardial' | 'peritoneal'
  | 'synovial' | 'saliva' | 'hair' | 'nail' | 'other';

export type SampleStatus =
  | 'ordered' | 'registered' | 'collected' | 'transporting'
  | 'received' | 'accepted' | 'rejected' | 'aliquoted'
  | 'processing' | 'analyzing' | 'analyzed' | 'verified'
  | 'validated' | 'released' | 'archived' | 'disposed';

export type Priority = 'routine' | 'urgent' | 'stat';

export interface TestResult {
  id: string;
  sampleId: string;
  orderId: string;
  testName: string;
  testNameEn?: string;
  category: string;
  value: string;
  numericValue?: number;
  unit: string;
  referenceRange: string;
  referenceLow?: number;
  referenceHigh?: number;
  flag: ResultFlag;
  method?: string;
  instrument?: string;
  performedBy?: string;
  performedAt?: string;
  verifiedBy?: string;
  verifiedAt?: string;
  status: ResultStatus;
  notes?: string;
  version: number;
}

export type ResultFlag = 'normal' | 'high' | 'low' | 'critical_high' | 'critical_low' | 'panic' | 'delta_fail' | 'invalid';

export type ResultStatus = 'pending' | 'in_progress' | 'completed' | 'verified' | 'amended' | 'cancelled';

export interface QCData {
  id: string;
  level: 'L1' | 'L2' | 'L3';
  testName: string;
  mean: number;
  sd: number;
  currentValue: number;
  status: QCStatus;
  history: QCPoint[];
  deviceId?: string;
  lotNumber?: string;
  performedBy?: string;
  performedAt: string;
  westgardViolations?: WestgardRule[];
}

export type QCStatus = 'in_control' | 'warning' | 'out_of_control' | 'not_run';

export type WestgardRule = '1_2s' | '1_3s' | '2_2s' | 'r_4s' | '4_1s' | '10x' | '12x' | '8x';

export interface QCPoint {
  date: string;
  value: number;
  violated?: boolean;
}

export interface Analyzer {
  id: string;
  name: string;
  model: string;
  serialNumber: string;
  manufacturer: string;
  status: AnalyzerStatus;
  tests: string[];
  lastCalibration?: string;
  nextCalibration?: string;
  lastQC?: string;
  connectionType: 'astm' | 'hl7' | 'serial' | 'tcpip' | 'file' | 'manual';
  ipAddress?: string;
  port?: number;
  location?: string;
  isActive: boolean;
  metrics?: AnalyzerMetrics;
  createdAt: string;
}

export type AnalyzerStatus = 'online' | 'offline' | 'maintenance' | 'calibrating' | 'qc_failed' | 'error' | 'disabled';

export interface AnalyzerMetrics {
  uptime: number;
  testsProcessed: number;
  errorRate: number;
  avgTurnaround: number;
  throughput: number;
  lastHourTests: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  nameEn?: string;
  category: 'reagent' | 'consumable' | 'calibrator' | 'control' | 'reference' | 'other';
  sku: string;
  lotNumber?: string;
  batchNumber?: string;
  manufacturer?: string;
  supplier?: string;
  quantity: number;
  unit: string;
  minimumStock: number;
  maximumStock: number;
  location?: string;
  expiryDate?: string;
  receivedDate?: string;
  cost?: number;
  isActive: boolean;
  createdAt: string;
}

export interface AutoverificationRule {
  id: string;
  name: string;
  testName: string;
  conditions: AutoverificationCondition[];
  action: 'auto_verify' | 'flag_review' | 'reject';
  priority: number;
  isActive: boolean;
  createdAt: string;
}

export interface AutoverificationCondition {
  field: 'value' | 'delta' | 'range' | 'qc_status' | 'instrument' | 'time';
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'in';
  value: string | number | string[];
}

export interface AuditEntry {
  id: string;
  action: string;
  entityType: string;
  entityId: string;
  userId: string;
  userName: string;
  details?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  timestamp: string;
}

export interface LabReport {
  id: string;
  name: string;
  type: 'cumulative' | 'daily' | 'weekly' | 'monthly' | 'custom';
  format: 'pdf' | 'csv' | 'excel' | 'html';
  parameters?: Record<string, unknown>;
  generatedAt?: string;
  generatedBy?: string;
  url?: string;
}

export interface MicrobiologyResult {
  id: string;
  sampleId: string;
  organism: string;
  growth: 'heavy' | 'moderate' | 'light' | 'none';
  gramStain?: string;
  morphology?: string;
  sensitivity: SensitivityResult[];
  notes?: string;
  status: 'pending' | 'preliminary' | 'final';
  performedBy?: string;
  performedAt: string;
}

export interface SensitivityResult {
  antibiotic: string;
  sensitivity: 'sensitive' | 'intermediate' | 'resistant' | 'not_tested';
  mic?: number;
  micUnit?: string;
  interpretation?: string;
}

export interface MolecularResult {
  id: string;
  sampleId: string;
  target: string;
  method: 'pcr' | 'rt_pcr' | 'sequencing' | 'genotyping' | 'other';
  result: 'positive' | 'negative' | 'indeterminate' | 'invalid';
  ctValue?: number;
  quantification?: number;
  quantificationUnit?: string;
  gene?: string;
  mutation?: string;
  notes?: string;
  status: 'pending' | 'preliminary' | 'final';
  performedBy?: string;
  performedAt: string;
}

export interface BloodBankResult {
  id: string;
  sampleId: string;
  bloodGroup: string;
  rhType: 'positive' | 'negative';
  antibodyScreen: 'positive' | 'negative' | 'not_done';
  crossmatchType?: 'major' | 'minor' | 'both';
  crossmatchResult?: 'compatible' | 'incompatible' | 'not_done';
  components: BloodComponent[];
  coombsDirect?: 'positive' | 'negative';
  coombsIndirect?: 'positive' | 'negative';
  notes?: string;
  status: 'pending' | 'preliminary' | 'final';
  performedBy?: string;
  performedAt: string;
}

export interface BloodComponent {
  type: string;
  volume: number;
  unit: string;
  expiryDate: string;
  donorId?: string;
}

export interface HistopathologyResult {
  id: string;
  sampleId: string;
  specimenType: string;
  grossDescription: string;
  microscopicDescription: string;
  diagnosis: string;
  diagnosisCode?: string;
  conclusion: string;
  pathologist: string;
  stains: string[];
  images?: string[];
  status: 'pending' | 'preliminary' | 'final';
  performedAt: string;
  verifiedAt?: string;
}

export interface BarcodeLabel {
  sampleId: string;
  patientName: string;
  patientId: string;
  specimenType: string;
  tests: string[];
  collectedAt?: string;
  barcode: string;
  container?: string;
  volume?: number;
  notes?: string;
}
