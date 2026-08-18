import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import { SpeechRecognitionService } from './SpeechRecognitionService';
import {
  SpeechPermissionState,
  SpeechRecognitionState,
  type SpeechLocale,
  type SpeechSnapshot,
  type SpeechStartOptions,
  type VoiceTextMode,
} from './types';

export interface SpeechToTextContextValue {
  snapshot: SpeechSnapshot;
  start: (options?: SpeechStartOptions) => Promise<boolean>;
  stop: () => void;
  cancel: () => void;
  retry: () => Promise<boolean>;
  reset: () => void;
  resetSession: () => void;
  setLocale: (locale: SpeechLocale) => void;
  applyToText: (existingText: string, mode: VoiceTextMode) => string;
  refreshCapabilities: () => Promise<void>;
}

const SpeechToTextContext = createContext<SpeechToTextContextValue | null>(null);

export interface SpeechRecognitionProviderProps extends PropsWithChildren {
  sessionKey: string;
  initialLocale?: SpeechLocale;
}

function joinText(existingText: string, draftText: string, mode: VoiceTextMode): string {
  if (mode === 'replace') return draftText.trim();
  const left = existingText.trim();
  const right = draftText.trim();
  if (!left) return right;
  if (!right) return left;
  return `${left} ${right}`;
}

export function SpeechRecognitionProvider({
  children,
  sessionKey,
  initialLocale = 'ar',
}: SpeechRecognitionProviderProps) {
  const [service] = useState(() => new SpeechRecognitionService());
  const [snapshot, setSnapshot] = useState<SpeechSnapshot>(() => service.getSnapshot());

  useEffect(() => {
    service.subscribe(setSnapshot);
    void service.refreshCapabilities();
    return () => service.dispose();
  }, [service]);

  useEffect(() => {
    service.resetSession();
    service.setLocale(initialLocale);
  }, [service, sessionKey, initialLocale]);

  const start = useCallback((options?: SpeechStartOptions) => service.start(options), [service]);
  const stop = useCallback(() => service.stop(), [service]);
  const cancel = useCallback(() => service.cancel(), [service]);
  const reset = useCallback(() => service.reset(), [service]);
  const resetSession = useCallback(() => {
    service.cancel();
    service.reset();
  }, [service]);
  const setLocale = useCallback((locale: SpeechLocale) => service.setLocale(locale), [service]);
  const retry = useCallback(() => {
    service.reset();
    return service.start();
  }, [service]);
  const refreshCapabilities = useCallback(async () => {
    await service.refreshCapabilities();
  }, [service]);
  const applyToText = useCallback((existingText: string, mode: VoiceTextMode) => joinText(existingText, snapshot.finalText, mode), [snapshot.finalText]);

  const value = useMemo<SpeechToTextContextValue>(() => ({
    snapshot,
    start,
    stop,
    cancel,
    retry,
    reset,
    resetSession,
    setLocale,
    applyToText,
    refreshCapabilities,
  }), [snapshot, start, stop, cancel, retry, reset, resetSession, setLocale, applyToText, refreshCapabilities]);

  return <SpeechToTextContext.Provider value={value}>{children}</SpeechToTextContext.Provider>;
}

export function useSpeechToText(): SpeechToTextContextValue {
  const context = useContext(SpeechToTextContext);
  if (!context) throw new Error('useSpeechToText must be used inside SpeechRecognitionProvider');
  return context;
}

export { SpeechPermissionState, SpeechRecognitionState };
