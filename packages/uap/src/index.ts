export const UAP_VERSION = '1.0.0';
export const UAP_NAME = '@gula/uap';
export const UAP_BUILD = 'application-platform-v1.0';

export {
  ThemeProvider, ThemeToggle, useTheme,
  Button, IconButton,
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
  Dialog, ConfirmDialog,
  Input, Select, Textarea,
  Table, DataGrid,
  Alert, Badge, Spinner, EmptyState, Skeleton,
  cn, rtl, isRtl,
} from './components';
export type { ButtonProps, ThemeMode } from './components';

export {
  useI18n, setLocale, t,
  useAuth, restoreSession,
  useConfig, hydrateConfig, appConfigSchema,
  usePluginLoader,
  useFeatureFlags,
  ErrorProvider, AppErrorBoundary, useErrorHandler,
  useCrashRecovery, attemptRecovery,
  AppShell, SplashScreen,
  useAppState,
} from './runtime';
export type {
  Locale, TranslationDict,
  AuthUser, AuthStatus, AuthConfig,
  AppConfig,
  PluginManifest, PluginInstance,
  FeatureFlag,
  AppError, ErrorSeverity,
  AppView, NavigationTab, SessionInfo,
} from './runtime';

export {
  DEFAULT_SYNC_CONFIG,
  getStorage, setStorage, IndexedDBBackend,
  useSyncQueue, processSyncQueue, startSyncEngine, stopSyncEngine, initNetworkMonitor,
  defaultConflictResolver,
  compress, decompress, calculateBackoff, batchOperations, generateDeltaPatch,
} from './offline';
export type {
  OfflineEntry, SyncOperation, SyncConflict, SyncConfig, StorageBackend,
  ConflictResolver, ResolutionStrategy,
} from './offline';

export {
  useDeviceRegistry,
  requestCamera, requestGPS, scanBarcode,
  requestBluetooth, requestNFC,
  checkBiometricAvailability, authenticateBiometric,
} from './device';
export type { DeviceInfo } from './device';

export {
  useUpdatePlatform,
  checkVersionCompatibility,
} from './update';
export type { AppVersion, UpdateChannel, UpdateState } from './update';

export {
  useMarketplace,
} from './marketplace';
export type { AppStoreEntry, AppCategory, Extension } from './marketplace';

export {
  useNotificationPlatform, scheduleNotification,
} from './notifications';
export type { Notification, NotificationTemplate, NotificationChannel, NotificationPriority } from './notifications';

export {
  usePrinting,
  generateBarcodeSvg, generateQRSvg, printPDF,
  generateDigitalSignature, addWatermark,
} from './printing';
export type { PrintJob, PrintFormat, PrintOrientation } from './printing';

export {
  useTelemetry, initTelemetry, trackLatency, trackBattery, trackMemory,
} from './telemetry';
export type { Metric, TelemetryEvent, CrashReport, PerformanceMetrics } from './telemetry';

export {
  GulaSDK, createSDK, generateBoilerplate,
} from './sdk';
export type { SDKConfig } from './sdk';

export {
  runQualityGates,
  registerGate,
  securityValidation,
  architectureValidation,
  performanceValidation,
  accessibilityValidation,
  offlineValidation,
  compatibilityValidation,
} from './quality';
export type { QualityGate, QualityReport } from './quality';
