// Design System Tokens
export { colors } from './design-system/tokens/colors';
export { semanticColors } from './design-system/tokens/colors';
export { getColor, getSemantic } from './design-system/tokens/colors';
export type { ColorFamily, ColorShade, ThemeMode, SemanticToken } from './design-system/tokens/colors';

export { fontFamilies, typeScale } from './design-system/tokens/typography';
export { getFontFamily, getTypeScale } from './design-system/tokens/typography';
export type { FontCategory, TypeScaleCategory, TypeScaleSize } from './design-system/tokens/typography';

export { spacing, borderRadius, shadows } from './design-system/tokens/spacing';
export type { SpacingKey, BorderRadiusKey } from './design-system/tokens/spacing';

export { breakpoints, getBreakpointValue, getMediaQuery, containerMaxWidths } from './design-system/tokens/breakpoints';
export type { BreakpointKey, BreakpointDirection } from './design-system/tokens/breakpoints';

// Theme System
export { createTheme, applyThemeToDocument } from './theme/theme';
export type { GulaTheme } from './theme/theme';
export { ThemeProvider } from './theme/ThemeProvider';
export { ThemeContext } from './theme/ThemeProvider';
export type { ThemeContextValue, ThemeProviderProps } from './theme/ThemeProvider';
export { useTheme } from './theme/useTheme';

// Components
export { Button } from './components/Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './components/Button';

export { Card, CardHeader, CardBody, CardFooter } from './components/Card';
export type { CardProps, CardHeaderProps, CardBodyProps, CardFooterProps } from './components/Card';

export { Input } from './components/Input';
export type { InputProps, InputVariant } from './components/Input';

export { Select } from './components/Select';
export type { SelectProps, SelectOption } from './components/Select';

export { Modal } from './components/Modal';
export type { ModalProps, ModalSize } from './components/Modal';

export { Table } from './components/Table';
export type { TableProps, Column } from './components/Table';

export { Badge } from './components/Badge';
export type { BadgeProps, BadgeVariant, BadgeSize } from './components/Badge';

export { Alert } from './components/Alert';
export type { AlertProps, AlertVariant } from './components/Alert';

export { Tabs } from './components/Tabs';
export type { TabsProps, Tab } from './components/Tabs';

export { Sidebar } from './components/Sidebar';
export type { SidebarProps, SidebarItem, SidebarSection } from './components/Sidebar';

export { Header } from './components/Header';
export type { HeaderProps, HeaderBreadcrumb } from './components/Header';

export { Layout, LayoutContent, LayoutSplit } from './components/Layout';
export type { LayoutProps, LayoutContentProps, LayoutSplitProps } from './components/Layout';

export { DataTable } from './components/DataTable';
export type { DataTableProps, DataTableColumn, DataTableAction } from './components/DataTable';

export { SearchInput } from './components/SearchInput';
export type { SearchInputProps } from './components/SearchInput';

export { Pagination } from './components/Pagination';
export type { PaginationProps } from './components/Pagination';

export { StatusIndicator } from './components/StatusIndicator';
export type { StatusIndicatorProps, StatusType } from './components/StatusIndicator';

export { LoadingSpinner, LoadingOverlay } from './components/LoadingSpinner';
export type { LoadingSpinnerProps, LoadingOverlayProps, SpinnerSize } from './components/LoadingSpinner';

export { EmptyState } from './components/EmptyState';
export type { EmptyStateProps, EmptyStateAction } from './components/EmptyState';

export { ErrorBoundary } from './components/ErrorBoundary';
export type { ErrorBoundaryProps } from './components/ErrorBoundary';

export { ProtectedRoute } from './components/ProtectedRoute';
export type { ProtectedRouteProps, AuthState } from './components/ProtectedRoute';

// Hooks
export { useRTL, getDir, isArabicLang } from './hooks/useRTL';
export type { RTLResult } from './hooks/useRTL';

export { useLocalization } from './hooks/useLocalization';
export type { LocalizationResult, Locale } from './hooks/useLocalization';

export { useMediaQuery, useBreakpoint } from './hooks/useMediaQuery';
export type { MediaQueryResult } from './hooks/useMediaQuery';

export { useDebounce, useDebouncedCallback } from './hooks/useDebounce';

export { useOffline } from './hooks/useOffline';
export type { OfflineResult } from './hooks/useOffline';

export { usePWA } from './hooks/usePWA';
export type { PWAResult, BeforeInstallPromptEvent } from './hooks/usePWA';

export { useNotification } from './hooks/useNotification';
export type { NotificationResult, Toast, NotificationType } from './hooks/useNotification';

export { usePagination } from './hooks/usePagination';
export type { PaginationResult, PaginationState } from './hooks/usePagination';

// Utils
export { cn } from './utils/cn';
export {
  isSensitiveQueueKey,
  sanitizeQueueHeaders,
  inspectQueuePayload,
  inspectQueueRecord,
  purgeLegacyWorkboxQueue,
} from './utils/offlineQueueSecurity';
export type { SanitizedHeaders, QueueSecurityCheck } from './utils/offlineQueueSecurity';
export {
  createQueueEnvelope,
  serializeQueueBody,
  parseQueueBody,
  buildQueueRequestInit,
  classifyQueueResponse,
  nextQueueEnvelopeState,
} from './utils/offlineQueueContract';
export type {
  OfflineQueueEnvelope,
  QueueEnvelopeInput,
  QueueResponseDisposition,
  QueueState,
} from './utils/offlineQueueContract';

export {
  formatDate, formatDateTime, formatRelativeTime,
  formatNumber, formatCurrency, formatPercentage,
  formatPhone, formatNationalId, truncate,
} from './utils/format';

export {
  validateIraqiNationalId, validatePhone, validateEmail,
  validateRequired, validateMinLength, validateMaxLength,
  validatePassword, validateBloodType, validateLabTestName,
} from './utils/validation';
export type { ValidationResult } from './utils/validation';

export { setItem, getItem, removeItem, clearAll, getKeys, exists, storage } from './utils/storage';

export {
  APP_NAME, APP_VERSION, COMPANY_NAME,
  WINGS, ROLES, ORDER_STATUSES, PRIORITIES,
  SAMPLE_STATUSES, BLOOD_TYPES, GENDERS,
  CONSENT_DURATIONS, CONSENT_SCOPES, VERIFICATION_LEVELS,
  EVENT_TYPES, LANGUAGES, RTL_LANGUAGES,
  ROUTES, STORAGE_KEYS, PAGINATION, DEBOUNCE,
} from './utils/constants';
export type {
  Wing, Role, OrderStatus, Priority,
  SampleStatus, BloodType, Gender,
  ConsentDuration, ConsentScope, VerificationLevel,
  EventType, LanguageCode,
} from './utils/constants';

// i18n
export { I18nProvider, I18nContext } from './i18n/I18nProvider';
export type { I18nContextValue, I18nProviderProps } from './i18n/I18nProvider';
export { useTranslation, t, tpl, getDirection } from './i18n/useTranslation';
export type { TranslationKey } from './i18n/useTranslation';
export { setLocale, getCurrentLocale } from './i18n/i18n';

// Icons
export * from './icons/index.tsx';
