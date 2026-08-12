export type VoiceDictationLanguage = 'ar-IQ' | 'ar-SA' | 'en-US';

export interface VoiceDictationResult {
  transcript: string;
  isFinal: boolean;
  confidence: number;
  alternatives?: string[];
}

export interface VoiceDictationSession {
  id: string;
  isActive: boolean;
  isPaused: boolean;
  language: VoiceDictationLanguage;
  startTime: number;
  accumulatedText: string;
  interimText: string;
}

export type VoiceEventCallback = {
  onResult?: (result: VoiceDictationResult) => void;
  onError?: (error: string) => void;
  onEnd?: () => void;
  onStart?: () => void;
  onPause?: () => void;
  onResume?: () => void;
};

type RecognitionInstance = {
  start: () => void;
  stop: () => void;
  abort: () => void;
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: ((() => void) | null);
  onstart: ((() => void) | null);
};

export class VoiceDictationEngine {
  private recognition: RecognitionInstance | null = null;
  private session: VoiceDictationSession | null = null;
  private callbacks: VoiceEventCallback = {};
  private isSupported: boolean = false;

  constructor() {
    this.isSupported = this.checkSupport();
  }

  private checkSupport(): boolean {
    return !!(
      (typeof window !== 'undefined') &&
      (window.SpeechRecognition || window.webkitSpeechRecognition)
    );
  }

  get supported(): boolean {
    return this.isSupported;
  }

  get currentSession(): VoiceDictationSession | null {
    return this.session;
  }

  start(language: VoiceDictationLanguage = 'ar-IQ', callbacks: VoiceEventCallback = {}): VoiceDictationSession | null {
    if (!this.isSupported) {
      callbacks.onError?.('Voice dictation is not supported in this browser');
      return null;
    }

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognitionAPI();
    this.recognition = recognition;
    this.callbacks = callbacks;

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';
      let lastConfidence = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
          lastConfidence = result[0].confidence;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      if (finalTranscript && this.session) {
        this.session.accumulatedText += finalTranscript;
        const result: VoiceDictationResult = {
          transcript: finalTranscript,
          isFinal: true,
          confidence: lastConfidence,
        };
        this.callbacks.onResult?.(result);
      }

      if (interimTranscript && this.session) {
        this.session.interimText = interimTranscript;
        const result: VoiceDictationResult = {
          transcript: interimTranscript,
          isFinal: false,
          confidence: 0,
        };
        this.callbacks.onResult?.(result);
      }
    };

    recognition.onerror = (event: any) => {
      const errorMessages: Record<string, string> = {
        'no-speech': 'لم يتم اكتشاف أي كلام',
        'aborted': 'تم إلغاء الإملاء',
        'audio-capture': 'تعذر الوصول إلى الميكروفون',
        'network': 'فشل الاتصال بخدمة التعرف على الكلام',
        'not-allowed': 'لم يتم منح الإذن للوصول إلى الميكروفون',
        'service-not-allowed': 'خدمة التعرف على الكلام غير متاحة',
        'bad-grammar': 'خطأ في قواعد اللغة',
        'language-not-supported': 'اللغة غير مدعومة',
      };
      this.callbacks.onError?.(errorMessages[event.error] || event.error);
    };

    recognition.onend = () => {
      if (this.session) {
        this.session.isActive = false;
      }
      this.callbacks.onEnd?.();
    };

    recognition.onstart = () => {
      this.callbacks.onStart?.();
    };

    try {
      recognition.start();
    } catch (error) {
      this.callbacks.onError?.(`Failed to start: ${error}`);
      return null;
    }

    this.session = {
      id: `voice-${Date.now()}`,
      isActive: true,
      isPaused: false,
      language,
      startTime: Date.now(),
      accumulatedText: '',
      interimText: '',
    };

    return this.session;
  }

  stop(): string {
    if (this.recognition && this.session?.isActive) {
      this.recognition.stop();
    }
    const text = this.session?.accumulatedText || '';
    this.session = null;
    this.recognition = null;
    return text;
  }

  pause(): void {
    if (this.recognition && this.session) {
      this.recognition.stop();
      this.session.isPaused = true;
      this.callbacks.onPause?.();
    }
  }

  resume(): void {
    if (!this.isSupported || !this.session) return;

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    const session = this.session;
    const recognition = new SpeechRecognitionAPI();
    this.recognition = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = session.language;

    recognition.onresult = (event: any) => { /* same as start */ };
    recognition.onerror = (event: any) => { /* same as start */ };
    recognition.onend = () => { /* same as start */ };
    recognition.onstart = () => { /* same as start */ };

    try {
      recognition.start();
      session.isPaused = false;
      this.callbacks.onResume?.();
    } catch (error) {
      this.callbacks.onError?.(`Failed to resume: ${error}`);
    }
  }

  cancel(): void {
    if (this.recognition) {
      this.recognition.abort();
    }
    this.session = null;
    this.recognition = null;
  }
}

export function createVoiceEngine(): VoiceDictationEngine {
  return new VoiceDictationEngine();
}
