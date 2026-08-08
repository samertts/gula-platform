import { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardHeader, CardBody, Button, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { createVoiceEngine, type VoiceDictationEngine, type VoiceDictationResult, type VoiceDictationLanguage } from '../services/voiceDictation';

interface VoiceInputProps {
  onResult: (text: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  language?: VoiceDictationLanguage;
  placeholder?: string;
  placeholderAr?: string;
  label?: string;
  labelAr?: string;
}

export function VoiceInput({
  onResult,
  onStart,
  onEnd,
  language: initialLanguage = 'ar-IQ',
  placeholder,
  placeholderAr,
  label,
  labelAr,
}: VoiceInputProps) {
  const { isRtl } = useRTL();
  const [engine] = useState<VoiceDictationEngine>(() => createVoiceEngine());
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [finalText, setFinalText] = useState('');
  const [language, setLanguage] = useState<VoiceDictationLanguage>(initialLanguage);
  const [isSupported, setIsSupported] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setIsSupported(engine.supported);
  }, [engine]);

  const handleResult = useCallback((result: VoiceDictationResult) => {
    if (result.isFinal) {
      setFinalText(prev => prev + ' ' + result.transcript);
      setInterimText('');
    } else {
      setInterimText(result.transcript);
    }
  }, []);

  const handleError = useCallback((error: string) => {
    console.warn('[VoiceInput] Error:', error);
    setIsRecording(false);
    setIsPaused(false);
  }, []);

  const handleStart = useCallback(() => {
    setIsRecording(true);
    onStart?.();
  }, [onStart]);

  const handleEnd = useCallback(() => {
    setIsRecording(false);
    setIsPaused(false);
    onEnd?.();
  }, [onEnd]);

  const startRecording = useCallback(() => {
    engine.start(language, {
      onResult: handleResult,
      onError: handleError,
      onStart: handleStart,
      onEnd: handleEnd,
    });
  }, [engine, language, handleResult, handleError, handleStart, handleEnd]);

  const stopRecording = useCallback(() => {
    const text = engine.stop();
    setFinalText(prev => prev + ' ' + text);
    setInterimText('');
    setIsRecording(false);
    setIsPaused(false);
    onResult(finalText + ' ' + text);
  }, [engine, finalText, onResult]);

  const pauseRecording = useCallback(() => {
    engine.pause();
    setIsPaused(true);
  }, [engine]);

  const resumeRecording = useCallback(() => {
    if (!isRecording) {
      startRecording();
    } else {
      engine.resume();
      setIsPaused(false);
    }
  }, [engine, isRecording, startRecording]);

  const clearText = useCallback(() => {
    setFinalText('');
    setInterimText('');
    if (textareaRef.current) {
      textareaRef.current.value = '';
    }
  }, []);

  const acceptText = useCallback(() => {
    onResult(finalText);
  }, [finalText, onResult]);

  const displayText = finalText + (interimText ? ` [${interimText}]` : '');

  if (!isSupported) {
    return (
      <Card>
        <CardBody>
          <div className="p-4 rounded-xl bg-warning-50 dark:bg-warning-950 border border-warning-200 dark:border-warning-900 text-center">
            <p className="text-sm text-warning-700 dark:text-warning-400">
              {isRtl ? 'الإملاء الصوتي غير مدعوم في هذا المتصفح' : 'Voice dictation is not supported in this browser'}
            </p>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title={label || (isRtl ? 'الإملاء الصوتي' : 'Voice Dictation')}
        action={
          <select
            value={language}
            onChange={e => setLanguage(e.target.value as VoiceDictationLanguage)}
            className="text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-transparent px-2 py-1"
          >
            <option value="ar-IQ">العربية (العراق)</option>
            <option value="ar-SA">العربية (السعودية)</option>
            <option value="en-US">English (US)</option>
          </select>
        }
      />
      <CardBody>
        <div className="space-y-4">
          <textarea
            ref={textareaRef}
            value={displayText}
            onChange={e => setFinalText(e.target.value)}
            rows={6}
            className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-3 text-sm resize-y"
            dir={language.startsWith('ar') ? 'rtl' : 'ltr'}
            placeholder={isRtl ? (placeholderAr || 'انقر على الميكروفون وابدأ بالتحدث...') : (placeholder || 'Click the microphone and start speaking...')}
          />

          <div className="flex items-center gap-3">
            {!isRecording ? (
              <Button
                variant="primary"
                onClick={startRecording}
                icon={
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
                    <path d="M19 10v2a7 7 0 01-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                }
              >
                {isRtl ? 'بدء التسجيل' : 'Start Recording'}
              </Button>
            ) : (
              <>
                {isPaused ? (
                  <Button variant="secondary" onClick={resumeRecording}>
                    {isRtl ? 'استئناف' : 'Resume'}
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={pauseRecording}>
                    {isRtl ? 'إيقاف مؤقت' : 'Pause'}
                  </Button>
                )}
                <Button variant="danger" onClick={stopRecording}>
                  {isRtl ? 'إيقاف' : 'Stop'}
                </Button>
              </>
            )}

            <div className="flex-1" />

            {isRecording && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-danger-500 animate-pulse" />
                <span className="text-xs text-danger-600">
                  {isPaused ? (isRtl ? 'متوقف مؤقتاً' : 'Paused') : (isRtl ? 'تسجيل...' : 'Recording...')}
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <Button variant="primary" onClick={acceptText} disabled={!finalText.trim()}>
              {isRtl ? 'قبول النص' : 'Accept Text'}
            </Button>
            <Button variant="ghost" onClick={clearText} disabled={!finalText.trim()}>
              {isRtl ? 'مسح' : 'Clear'}
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
