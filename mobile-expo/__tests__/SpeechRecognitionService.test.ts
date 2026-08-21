import { AppState } from 'react-native';
import { ExpoSpeechRecognitionModule } from 'expo-speech-recognition';
import { SpeechRecognitionService } from '../src/speech/SpeechRecognitionService';
import {
  SUPPORTED_LOCALE_CANDIDATES,
  SpeechPermissionState,
  SpeechRecognitionState,
} from '../src/speech/types';

jest.mock('expo-speech-recognition', () => {
  const listeners = new Map();
  return {
    ExpoSpeechRecognitionModule: {
      isRecognitionAvailable: jest.fn(() => true),
      supportsOnDeviceRecognition: jest.fn(() => true),
      supportsRecording: jest.fn(() => false),
      getSpeechRecognitionServices: jest.fn(() => ['com.google.android.as']),
      getDefaultRecognitionService: jest.fn(() => ({ packageName: 'com.google.android.as' })),
      getSupportedLocales: jest.fn(async () => ({ locales: ['ar-IQ', 'en-US'], installedLocales: ['ar-IQ'] })),
      getMicrophonePermissionsAsync: jest.fn(async () => ({ granted: false, canAskAgain: true })),
      requestPermissionsAsync: jest.fn(async () => ({ granted: true, canAskAgain: true })),
      start: jest.fn(),
      stop: jest.fn(),
      abort: jest.fn(),
      addListener: jest.fn((eventName, listener) => {
        listeners.set(eventName, listener);
        return { remove: () => listeners.delete(eventName) };
      }),
      __emit: (...args: any[]) => {
        const eventName = args[0];
        const event = args[1] ?? null;
        listeners.get(eventName)?.(event);
      },
    },
  };
});

const native = ExpoSpeechRecognitionModule as typeof ExpoSpeechRecognitionModule & {
  __emit: (eventName: string, event?: unknown) => void;
};

describe('SpeechRecognitionService', () => {
  afterEach(() => jest.clearAllMocks());

  it('requests permission and exposes only verified locales', async () => {
    const service = new SpeechRecognitionService();
    await service.refreshCapabilities();
    const permission = await service.requestPermissions();

    expect(permission).toBe(SpeechPermissionState.GRANTED);
    expect(service.getSnapshot().state).toBe(SpeechRecognitionState.READY);
    expect(SUPPORTED_LOCALE_CANDIDATES).toEqual(['ar', 'en-US', 'ku', 'tk', 'syr']);
    expect(service.getSnapshot().capabilities?.supportedLocales).toEqual(['ar-IQ', 'en-US']);
    service.dispose();
  });

  it('starts without audio persistence and completes through final review state', async () => {
    const service = new SpeechRecognitionService();
    await service.refreshCapabilities();
    await service.requestPermissions();
    const started = await service.start({ locale: 'ar' });

    expect(started).toBe(true);
    expect(native.start).toHaveBeenCalledWith(expect.objectContaining({
      lang: 'ar',
      interimResults: true,
      continuous: false,
      recordingOptions: { persist: false },
      requiresOnDeviceRecognition: true,
    }));
    expect(service.getSnapshot().state).toBe(SpeechRecognitionState.LISTENING);

    native.__emit('result', { isFinal: false, results: [{ transcript: 'مريض', confidence: 0.8 }] });
    expect(service.getSnapshot().interimText).toBe('مريض');

    native.__emit('result', { isFinal: true, results: [{ transcript: 'مريض يعاني من', confidence: 0.8 }] });
    native.__emit('end');
    expect(service.getSnapshot().state).toBe(SpeechRecognitionState.COMPLETED);
    expect(service.getSnapshot().finalText).toBe('مريض يعاني من');
    expect(service.getSnapshot().error).toBeNull();
    service.dispose();
  });

  it('uses the selected locale when start is called without an override', async () => {
    const service = new SpeechRecognitionService();
    await service.refreshCapabilities();
    await service.requestPermissions();
    service.setLocale('en-US');

    await service.start();

    expect(native.start).toHaveBeenCalledWith(expect.objectContaining({ lang: 'en-US' }));
    service.cancel();
    service.dispose();
  });

  it('cancels on lifecycle interruption and clears transcript', async () => {
    const service = new SpeechRecognitionService();
    await service.refreshCapabilities();
    await service.requestPermissions();
    await service.start({ locale: 'ar' });
    native.__emit('result', { isFinal: false, results: [{ transcript: 'نص حساس', confidence: 0.5 }] });

    const appStateHandler = (AppState.addEventListener as jest.Mock).mock.calls[0]?.[1] as (state: 'background') => void;
    appStateHandler('background');

    expect(native.abort).toHaveBeenCalled();
    expect(service.getSnapshot().state).toBe(SpeechRecognitionState.CANCELLED);
    expect(service.getSnapshot().interimText).toBe('');
    expect(service.getSnapshot().finalText).toBe('');
    service.dispose();
  });
});
