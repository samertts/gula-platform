import {
  ExpoSpeechRecognitionModule,
  type ExpoSpeechRecognitionErrorEvent,
  type ExpoSpeechRecognitionResultEvent,
} from 'expo-speech-recognition';
import { AppState, Platform, type AppStateStatus } from 'react-native';
import {
  SUPPORTED_LOCALE_CANDIDATES,
  SpeechPermissionState,
  SpeechRecognitionState,
  type SpeechCapabilities,
  type SpeechError,
  type SpeechLocale,
  type SpeechServiceListener,
  type SpeechSnapshot,
  type SpeechStartOptions,
} from './types';

const SESSION_TIMEOUT_MS = 120_000;

const TRANSITIONS: Record<string, readonly string[]> = {
  IDLE: ['REQUESTING_PERMISSION', 'READY', 'UNAVAILABLE', 'ERROR'],
  REQUESTING_PERMISSION: ['READY', 'DENIED', 'UNAVAILABLE', 'ERROR', 'CANCELLED'],
  READY: ['LISTENING', 'REQUESTING_PERMISSION', 'CANCELLED', 'UNAVAILABLE', 'ERROR'],
  LISTENING: ['PROCESSING', 'FINALIZING', 'CANCELLED', 'ERROR'],
  PROCESSING: ['FINALIZING', 'COMPLETED', 'CANCELLED', 'ERROR'],
  FINALIZING: ['COMPLETED', 'CANCELLED', 'ERROR'],
  COMPLETED: ['READY', 'REQUESTING_PERMISSION', 'CANCELLED'],
  DENIED: ['REQUESTING_PERMISSION', 'READY', 'CANCELLED'],
  UNAVAILABLE: ['READY', 'REQUESTING_PERMISSION', 'CANCELLED'],
  ERROR: ['READY', 'REQUESTING_PERMISSION', 'CANCELLED'],
  CANCELLED: ['READY', 'REQUESTING_PERMISSION', 'CANCELLED'],
};

const ERROR_MESSAGES: Record<string, { code: SpeechError['code']; message: string; recoverable: boolean }> = {
  'not-allowed': { code: 'permission-denied', message: 'لم يتم منح إذن الميكروفون أو التعرف على الكلام.', recoverable: false },
  'service-not-allowed': { code: 'recognition-unavailable', message: 'خدمة التعرف على الكلام غير متاحة على هذا الجهاز.', recoverable: true },
  network: { code: 'network-failure', message: 'تعذر الاتصال بخدمة التعرف على الكلام. يمكنك استخدام الإدخال اليدوي.', recoverable: true },
  'no-speech': { code: 'no-speech', message: 'لم يتم اكتشاف كلام. حاول مرة أخرى.', recoverable: true },
  'speech-timeout': { code: 'timeout', message: 'انتهت مهلة الإملاء دون نتيجة نهائية.', recoverable: true },
  'audio-capture': { code: 'microphone-unavailable', message: 'تعذر الوصول إلى الميكروفون أو حدث تغيير في مسار الصوت.', recoverable: true },
  interrupted: { code: 'audio-interruption', message: 'تمت مقاطعة جلسة الصوت. لم يتم حفظ التسجيل.', recoverable: true },
  busy: { code: 'service-busy', message: 'خدمة التعرف مشغولة. انتظر قليلاً ثم حاول مرة أخرى.', recoverable: true },
  'language-not-supported': { code: 'language-unavailable', message: 'اللغة المختارة غير مدعومة فعلياً على هذا الجهاز.', recoverable: true },
  aborted: { code: 'unknown', message: 'تم إلغاء جلسة الإملاء.', recoverable: true },
};

function createError(nativeCode: string, nativeMessage?: string): SpeechError {
  const mapped = ERROR_MESSAGES[nativeCode] ?? {
    code: 'unknown' as const,
    message: 'حدث خطأ غير متوقع في خدمة التعرف على الكلام.',
    recoverable: true,
  };
  return {
    code: mapped.code,
    message: nativeMessage && mapped.code === 'unknown' ? `${mapped.message} (${nativeMessage})` : mapped.message,
    recoverable: mapped.recoverable,
  };
}

function normalizeLocale(locale: string): SpeechLocale | null {
  const exact = SUPPORTED_LOCALE_CANDIDATES.find((candidate) => candidate === locale);
  if (exact) return exact;
  const base = locale.split('-')[0];
  const compatible = SUPPORTED_LOCALE_CANDIDATES.find((candidate) => candidate === base);
  return compatible ?? null;
}

function joinClinicalText(previous: string, next: string): string {
  const left = previous.trim();
  const right = next.trim();
  if (!left) return right;
  if (!right) return left;
  return `${left} ${right}`;
}

export class SpeechRecognitionService {
  private state: SpeechRecognitionState = SpeechRecognitionState.IDLE;
  private permission: SpeechPermissionState = SpeechPermissionState.UNKNOWN;
  private locale: SpeechLocale = 'ar-IQ';
  private interimText = '';
  private finalText = '';
  private durationMs = 0;
  private error: SpeechError | null = null;
  private capabilities: SpeechCapabilities | null = null;
  private startedAt = 0;
  private timeoutHandle: ReturnType<typeof setTimeout> | null = null;
  private lastFinalText = '';
  private readonly listeners = new Set<SpeechServiceListener>();
  private nativeSubscriptions: Array<{ remove: () => void }> = [];
  private disposed = false;
  private appStateSubscription: { remove: () => void } | null = null;

  constructor() {
    this.appStateSubscription = AppState.addEventListener('change', (nextState: AppStateStatus) => {
      if (nextState !== 'active' && this.state === SpeechRecognitionState.LISTENING) {
        this.cancel();
      }
    });
  }

  getSnapshot(): SpeechSnapshot {
    return {
      state: this.state,
      permission: this.permission,
      locale: this.locale,
      interimText: this.interimText,
      finalText: this.finalText,
      durationMs: this.durationMs,
      error: this.error,
      capabilities: this.capabilities,
    };
  }

  subscribe(listener: SpeechServiceListener): () => void {
    this.listeners.add(listener);
    listener(this.getSnapshot());
    return () => this.listeners.delete(listener);
  }

  async refreshCapabilities(): Promise<SpeechCapabilities> {
    try {
      const recognitionAvailable = ExpoSpeechRecognitionModule.isRecognitionAvailable();
      const onDeviceAvailable = ExpoSpeechRecognitionModule.supportsOnDeviceRecognition();
      const microphonePermission = await ExpoSpeechRecognitionModule.getMicrophonePermissionsAsync();
      const recognitionServices = ExpoSpeechRecognitionModule.getSpeechRecognitionServices();
      const defaultService = ExpoSpeechRecognitionModule.getDefaultRecognitionService();
      const locales = await ExpoSpeechRecognitionModule.getSupportedLocales({
        androidRecognitionServicePackage: defaultService.packageName || undefined,
      });
      const supportedLocales = locales.locales.filter((candidate) => normalizeLocale(candidate) !== null);
      const installedLocales = locales.installedLocales.filter((candidate) => normalizeLocale(candidate) !== null);
      this.capabilities = {
        recognitionAvailable,
        onDeviceAvailable,
        microphoneAvailable: microphonePermission.granted || microphonePermission.canAskAgain,
        supportedLocales,
        installedLocales,
        recognitionServices,
        developmentBuildRequired: false,
      };
      if (!recognitionAvailable) this.transition(SpeechRecognitionState.UNAVAILABLE);
      else if (this.state === SpeechRecognitionState.IDLE || this.state === SpeechRecognitionState.UNAVAILABLE) {
        this.transition(SpeechRecognitionState.READY);
      }
    } catch {
      this.capabilities = {
        recognitionAvailable: false,
        onDeviceAvailable: false,
        microphoneAvailable: false,
        supportedLocales: [],
        installedLocales: [],
        recognitionServices: [],
        developmentBuildRequired: true,
      };
      this.fail({
        code: 'native-module-unavailable',
        message: 'التعرف الصوتي غير متاح في هذا التشغيل. استخدم Development Build بدلاً من Expo Go، أو استخدم الإدخال اليدوي.',
        recoverable: true,
      });
    }
    this.emit();
    return this.capabilities;
  }

  async requestPermissions(): Promise<SpeechPermissionState> {
    if (this.disposed) return SpeechPermissionState.UNAVAILABLE;
    this.transition(SpeechRecognitionState.REQUESTING_PERMISSION);
    this.permission = SpeechPermissionState.REQUESTING;
    this.error = null;
    this.emit();
    try {
      const result = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
      if (result.granted) {
        this.permission = SpeechPermissionState.GRANTED;
        if (!this.capabilities) await this.refreshCapabilities();
        if (this.capabilities?.recognitionAvailable) this.transition(SpeechRecognitionState.READY);
        else this.transition(SpeechRecognitionState.UNAVAILABLE);
      } else {
        this.permission = result.canAskAgain ? SpeechPermissionState.DENIED : SpeechPermissionState.BLOCKED;
        this.transition(SpeechRecognitionState.DENIED);
      }
    } catch {
      this.permission = SpeechPermissionState.UNAVAILABLE;
      this.fail({
        code: 'native-module-unavailable',
        message: 'تعذر فحص صلاحيات التعرف الصوتي. يمكنك متابعة العمل بالإدخال اليدوي.',
        recoverable: true,
      });
    }
    this.emit();
    return this.permission;
  }

  setLocale(locale: SpeechLocale): void {
    if (this.state === SpeechRecognitionState.LISTENING || this.state === SpeechRecognitionState.PROCESSING) return;
    this.locale = locale;
    this.emit();
  }

  async start(options: SpeechStartOptions = {}): Promise<boolean> {
    if (this.disposed || this.state === SpeechRecognitionState.LISTENING) return false;
    if (!this.capabilities) await this.refreshCapabilities();
    if (!this.capabilities?.recognitionAvailable) {
      this.transition(SpeechRecognitionState.UNAVAILABLE);
      this.emit();
      return false;
    }
    if (this.permission !== SpeechPermissionState.GRANTED) {
      const permission = await this.requestPermissions();
      if (permission !== SpeechPermissionState.GRANTED) return false;
    }

    const selectedLocale = options.locale ?? this.locale;
    const actualLocale = this.resolveSupportedLocale(selectedLocale);
    if (!actualLocale) {
      this.fail({ code: 'language-unavailable', message: 'اللغة المختارة غير مثبتة أو غير مدعومة على هذا الجهاز.', recoverable: true });
      return false;
    }

    const requiresOnDeviceRecognition = options.requiresOnDeviceRecognition ?? Boolean(this.capabilities.onDeviceAvailable);
    if (requiresOnDeviceRecognition && !this.capabilities.onDeviceAvailable) {
      this.fail({ code: 'on-device-unavailable', message: 'التعرف على الكلام محلياً غير متاح لهذه اللغة أو لهذا الجهاز. استخدم الإدخال اليدوي.', recoverable: true });
      return false;
    }

    this.locale = actualLocale;
    this.error = null;
    this.interimText = '';
    this.finalText = '';
    this.durationMs = 0;
    this.lastFinalText = '';
    this.startedAt = Date.now();
    this.removeNativeSubscriptions();
    this.installNativeSubscriptions();
    this.transition(SpeechRecognitionState.LISTENING);
    this.emit();
    this.timeoutHandle = setTimeout(() => {
      if (this.state === SpeechRecognitionState.LISTENING) {
        this.stop();
        this.fail({ code: 'timeout', message: 'انتهت مدة الإملاء القصوى. راجع المسودة قبل الحفظ.', recoverable: true });
      }
    }, SESSION_TIMEOUT_MS);

    try {
      const contextualStringsSupported = Platform.OS === 'ios' || (Platform.OS === 'android' && Number(Platform.Version) >= 33);
      const punctuationSupported = Platform.OS === 'ios' || (Platform.OS === 'android' && Number(Platform.Version) >= 33);
      ExpoSpeechRecognitionModule.start({
        lang: actualLocale,
        interimResults: true,
        maxAlternatives: 1,
        continuous: false,
        requiresOnDeviceRecognition,
        addsPunctuation: punctuationSupported && (options.addsPunctuation ?? true),
        contextualStrings: contextualStringsSupported ? options.contextualStrings : undefined,
        recordingOptions: { persist: false },
        iosTaskHint: 'dictation',
      });
      return true;
    } catch {
      this.fail({ code: 'unknown', message: 'تعذر بدء التعرف على الكلام. يمكنك استخدام الإدخال اليدوي.', recoverable: true });
      this.removeNativeSubscriptions();
      return false;
    }
  }

  stop(): void {
    if (this.state !== SpeechRecognitionState.LISTENING && this.state !== SpeechRecognitionState.PROCESSING) return;
    this.clearTimeout();
    this.transition(SpeechRecognitionState.PROCESSING);
    this.emit();
    try {
      ExpoSpeechRecognitionModule.stop();
    } catch {
      this.fail({ code: 'unknown', message: 'تعذر إيقاف جلسة الإملاء بأمان.', recoverable: true });
    }
  }

  cancel(): void {
    this.clearTimeout();
    try {
      if (this.state === SpeechRecognitionState.LISTENING || this.state === SpeechRecognitionState.PROCESSING) {
        ExpoSpeechRecognitionModule.abort();
      }
    } catch {
      // Cancellation is best-effort; never expose audio or transcript in logs.
    }
    this.removeNativeSubscriptions();
    this.interimText = '';
    this.finalText = '';
    this.durationMs = 0;
    this.lastFinalText = '';
    this.error = null;
    if (this.state !== SpeechRecognitionState.IDLE) this.transition(SpeechRecognitionState.CANCELLED);
    this.emit();
  }

  resetSession(): void {
    this.cancel();
    this.reset();
  }

  reset(): void {
    this.clearTimeout();
    this.removeNativeSubscriptions();
    this.interimText = '';
    this.finalText = '';
    this.durationMs = 0;
    this.lastFinalText = '';
    this.error = null;
    if (this.capabilities?.recognitionAvailable) this.transition(SpeechRecognitionState.READY);
    else this.transition(SpeechRecognitionState.UNAVAILABLE);
    this.emit();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.cancel();
    this.listeners.clear();
    this.appStateSubscription?.remove();
    this.appStateSubscription = null;
  }

  private resolveSupportedLocale(requested: SpeechLocale): SpeechLocale | null {
    const supported = this.capabilities?.supportedLocales ?? [];
    if (supported.length === 0) return null;
    const exact = supported.find((candidate) => candidate.toLowerCase() === requested.toLowerCase());
    if (exact) return normalizeLocale(exact);
    const base = requested.split('-')[0] ?? requested;
    const compatible = supported.find((candidate) => (candidate.split('-')[0] ?? candidate).toLowerCase() === base.toLowerCase());
    return compatible ? normalizeLocale(compatible) : null;
  }

  private installNativeSubscriptions(): void {
    this.nativeSubscriptions = [
      ExpoSpeechRecognitionModule.addListener('start', () => {
        if (this.state === SpeechRecognitionState.LISTENING) this.emit();
      }),
      ExpoSpeechRecognitionModule.addListener('result', (event: ExpoSpeechRecognitionResultEvent) => {
        const result = event.results[0];
        if (!result) return;
        const text = result.transcript.trim();
        if (!text) return;
        if (event.isFinal) {
          if (text !== this.lastFinalText) {
            this.finalText = joinClinicalText(this.finalText, text);
            this.lastFinalText = text;
          }
          this.interimText = '';
          this.transition(SpeechRecognitionState.FINALIZING);
        } else {
          this.interimText = text;
        }
        this.updateDuration();
        this.emit();
      }),
      ExpoSpeechRecognitionModule.addListener('speechend', () => {
        if (this.state === SpeechRecognitionState.LISTENING) this.transition(SpeechRecognitionState.PROCESSING);
        this.emit();
      }),
      ExpoSpeechRecognitionModule.addListener('error', (event: ExpoSpeechRecognitionErrorEvent) => {
        if (event.error === 'aborted' && this.state === SpeechRecognitionState.CANCELLED) return;
        this.fail(createError(event.error, event.message));
      }),
      ExpoSpeechRecognitionModule.addListener('nomatch', () => {
        this.fail({ code: 'no-speech', message: 'لم يتم التعرف على كلام واضح. يمكنك المحاولة مرة أخرى أو الكتابة يدوياً.', recoverable: true });
      }),
      ExpoSpeechRecognitionModule.addListener('end', () => {
        this.updateDuration();
        this.clearTimeout();
        if (this.state === SpeechRecognitionState.FINALIZING || this.state === SpeechRecognitionState.PROCESSING) {
          this.transition(this.finalText ? SpeechRecognitionState.COMPLETED : SpeechRecognitionState.ERROR);
          if (!this.finalText) this.error = createError('no-speech');
        }
        this.removeNativeSubscriptions();
        this.emit();
      }),
    ];
  }

  private removeNativeSubscriptions(): void {
    this.nativeSubscriptions.forEach((subscription) => subscription.remove());
    this.nativeSubscriptions = [];
  }

  private fail(nextError: SpeechError): void {
    this.clearTimeout();
    this.error = nextError;
    this.interimText = '';
    if (this.state !== SpeechRecognitionState.ERROR) this.transition(SpeechRecognitionState.ERROR);
    this.removeNativeSubscriptions();
    this.emit();
  }

  private transition(nextState: SpeechRecognitionState): void {
    if (this.state === nextState) return;
    const allowed = TRANSITIONS[this.state] ?? [];
    if (!allowed.includes(nextState)) {
      this.state = SpeechRecognitionState.ERROR;
      this.error = {
        code: 'unknown',
        message: 'تم رفض انتقال غير صالح في آلة حالات الإملاء الصوتي.',
        recoverable: false,
      };
      return;
    }
    this.state = nextState;
  }

  private updateDuration(): void {
    if (this.startedAt > 0) this.durationMs = Date.now() - this.startedAt;
  }

  private clearTimeout(): void {
    if (this.timeoutHandle) clearTimeout(this.timeoutHandle);
    this.timeoutHandle = null;
  }

  private emit(): void {
    const snapshot = this.getSnapshot();
    this.listeners.forEach((listener) => listener(snapshot));
  }
}
