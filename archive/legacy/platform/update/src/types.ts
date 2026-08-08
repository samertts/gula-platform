export enum UpdateChannel {
  Stable = 'stable',
  Beta = 'beta',
  Canary = 'canary',
  Alpha = 'alpha',
}

export enum UpdateStatus {
  Idle = 'idle',
  Checking = 'checking',
  Available = 'available',
  Downloading = 'downloading',
  Downloaded = 'downloaded',
  Installing = 'installing',
  Installed = 'installed',
  Error = 'error',
  RolledBack = 'rolledBack',
}

export enum UpdatePriority {
  Low = 'low',
  Normal = 'normal',
  High = 'high',
  Critical = 'critical',
}

export enum PlatformType {
  Desktop = 'desktop',
  Android = 'android',
  iOS = 'ios',
  PWA = 'pwa',
}

export interface AppVersion {
  appName: string;
  version: string;
  buildNumber: string;
  platform: PlatformType;
  releaseDate: string;
  minAppVersion?: string;
  channel: UpdateChannel;
}

export interface UpdatePackage {
  id: string;
  appName: string;
  version: string;
  buildNumber: string;
  platform: PlatformType;
  channel: UpdateChannel;
  size: number;
  checksum: string;
  checksumAlgorithm: 'sha256' | 'sha512';
  signature: string;
  signerCertificate: string;
  downloadUrl: string;
  releaseNotes: string;
  releaseDate: string;
  priority: UpdatePriority;
  minAppVersion: string;
  requires: string[];
  isDelta: boolean;
  deltaBaseVersion?: string;
  metadata: Record<string, string>;
}

export interface UpdateCheckResult {
  available: boolean;
  currentVersion: string;
  latestVersion: string | null;
  package: UpdatePackage | null;
  forced: boolean;
  releaseNotes: string[];
  error: string | null;
}

export interface DownloadProgress {
  bytesDownloaded: number;
  totalBytes: number;
  percentage: number;
  speed: number;
  estimatedSecondsRemaining: number;
}

export interface InstallProgress {
  phase: 'extracting' | 'verifying' | 'applying' | 'cleaning';
  percentage: number;
  message: string;
}

export interface UpdateError {
  code: UpdateErrorCode;
  message: string;
  details: string | null;
  recoverable: boolean;
}

export enum UpdateErrorCode {
  NetworkError = 'NETWORK_ERROR',
  ChecksumMismatch = 'CHECKSUM_MISMATCH',
  SignatureInvalid = 'SIGNATURE_INVALID',
  IncompatibleVersion = 'INCOMPATIBLE_VERSION',
  InsufficientStorage = 'INSUFFICIENT_STORAGE',
  DownloadFailed = 'DOWNLOAD_FAILED',
  InstallFailed = 'INSTALL_FAILED',
  RollbackFailed = 'ROLLBACK_FAILED',
  ValidationFailed = 'VALIDATION_FAILED',
  PermissionDenied = 'PERMISSION_DENIED',
  Unknown = 'UNKNOWN',
}

export interface ScheduledUpdate {
  id: string;
  packageId: string;
  scheduledFor: string;
  status: 'pending' | 'installing' | 'completed' | 'failed' | 'cancelled';
  maintenanceWindow: MaintenanceWindow | null;
  retryCount: number;
  maxRetries: number;
  lastError: string | null;
}

export interface MaintenanceWindow {
  startTime: string;
  endTime: string;
  timezone: string;
  daysOfWeek: number[];
}

export interface ReleaseNotes {
  version: string;
  title: string;
  body: string;
  features: string[];
  bugFixes: string[];
  security: string[];
  breakingChanges: string[];
  date: string;
  author: string;
}

export interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  rolloutPercentage: number;
  conditions: FlagCondition[];
  metadata: Record<string, string>;
}

export interface FlagCondition {
  type: 'user' | 'group' | 'lab' | 'region' | 'version' | 'platform' | 'random';
  operator: 'eq' | 'neq' | 'in' | 'nin' | 'gte' | 'lte' | 'contains';
  value: string | string[] | number;
}

export interface VersionCompatibility {
  compatible: boolean;
  currentVersion: string;
  requiredVersion: string;
  reason: string | null;
  dependencies: DependencyCompatibility[];
}

export interface DependencyCompatibility {
  name: string;
  currentVersion: string;
  requiredVersion: string;
  compatible: boolean;
}

export interface UpdateScheduleConfig {
  checkInterval: number;
  backgroundDownload: boolean;
  autoInstall: boolean;
  maintenanceWindow: MaintenanceWindow | null;
  bandwidthLimit: number | null;
  offlineMode: 'delay' | 'skip' | 'queue';
  maxRetries: number;
  retryDelay: number;
}

export interface UpdateEventMap {
  'check:start': { manual: boolean };
  'check:complete': UpdateCheckResult;
  'download:start': UpdatePackage;
  'download:progress': DownloadProgress;
  'download:complete': UpdatePackage;
  'install:start': UpdatePackage;
  'install:progress': InstallProgress;
  'install:complete': UpdatePackage;
  'install:error': UpdateError;
  'rollback:start': { from: string; to: string };
  'rollback:complete': { from: string; to: string };
  'rollback:error': UpdateError;
  'status:change': { from: UpdateStatus; to: UpdateStatus };
  'error': UpdateError;
}

export type UpdateEventListener<K extends keyof UpdateEventMap> = (event: UpdateEventMap[K]) => void;

export interface UpdateState {
  status: UpdateStatus;
  currentVersion: string | null;
  pendingUpdate: UpdatePackage | null;
  downloadProgress: DownloadProgress | null;
  installProgress: InstallProgress | null;
  lastCheckResult: UpdateCheckResult | null;
  lastError: UpdateError | null;
  scheduledUpdates: ScheduledUpdate[];
  checkInterval: number;
  maintenanceWindow: MaintenanceWindow | null;
  channel: UpdateChannel;
}

export interface AppIdentification {
  name: string;
  version: string;
  buildNumber: string;
  platform: PlatformType;
  channel: UpdateChannel;
}
