export const SpeechRecognitionState = {
  IDLE: 'IDLE',
  REQUESTING_PERMISSION: 'REQUESTING_PERMISSION',
  READY: 'READY',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING',
  FINALIZING: 'FINALIZING',
  COMPLETED: 'COMPLETED',
  DENIED: 'DENIED',
  UNAVAILABLE: 'UNAVAILABLE',
  ERROR: 'ERROR',
  CANCELLED: 'CANCELLED',
} as const;

export type SpeechRecognitionState =
  (typeof SpeechRecognitionState)[keyof typeof SpeechRecognitionState];

export const SpeechPermissionState = {
  UNKNOWN: 'UNKNOWN',
  REQUESTING: 'REQUESTING',
  GRANTED: 'GRANTED',
  DENIED: 'DENIED',
  BLOCKED: 'BLOCKED',
  UNAVAILABLE: 'UNAVAILABLE',
} as const;

export type SpeechPermissionState =
  (typeof SpeechPermissionState)[keyof typeof SpeechPermissionState];

export const SUPPORTED_LOCALE_CANDIDATES = [
  'ar',
  'en-US',
  'ku',
  'tk',
  'syr',
] as const;

export type SpeechLocale = (typeof SUPPORTED_LOCALE_CANDIDATES)[number];

export type VoiceTextMode = 'append' | 'replace';

export type SpeechErrorCode =
  | 'permission-denied'
  | 'recognition-unavailable'
  | 'network-failure'
  | 'on-device-unavailable'
  | 'timeout'
  | 'no-speech'
  | 'audio-interruption'
  | 'service-busy'
  | 'language-unavailable'
  | 'microphone-unavailable'
  | 'native-module-unavailable'
  | 'unknown';

export interface SpeechError {
  code: SpeechErrorCode;
  message: string;
  recoverable: boolean;
}

export interface SpeechCapabilities {
  recognitionAvailable: boolean;
  onDeviceAvailable: boolean;
  microphoneAvailable: boolean;
  supportedLocales: string[];
  installedLocales: string[];
  recognitionServices: string[];
  developmentBuildRequired: boolean;
}

export interface SpeechResult {
  text: string;
  isFinal: boolean;
  confidence: number;
}

export interface SpeechSnapshot {
  state: SpeechRecognitionState;
  permission: SpeechPermissionState;
  locale: SpeechLocale;
  interimText: string;
  finalText: string;
  durationMs: number;
  error: SpeechError | null;
  capabilities: SpeechCapabilities | null;
}

export interface SpeechStartOptions {
  locale?: SpeechLocale;
  requiresOnDeviceRecognition?: boolean;
  addsPunctuation?: boolean;
  contextualStrings?: string[];
}

export interface SpeechServiceListener {
  (snapshot: SpeechSnapshot): void;
}
