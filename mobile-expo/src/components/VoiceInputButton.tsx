import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import { SpeechRecognitionState, useSpeechToText } from '../speech/SpeechRecognitionProvider';

export interface VoiceInputButtonProps {
  label?: string;
  disabled?: boolean;
  contextualStrings?: string[];
}

export function VoiceInputButton({ label = 'إملاء صوتي', disabled = false, contextualStrings }: VoiceInputButtonProps) {
  const { snapshot, start, stop, cancel } = useSpeechToText();
  const isListening = snapshot.state === SpeechRecognitionState.LISTENING || snapshot.state === SpeechRecognitionState.PROCESSING;
  const unavailable = snapshot.state === SpeechRecognitionState.UNAVAILABLE || snapshot.state === SpeechRecognitionState.DENIED;
  const busy = snapshot.state === SpeechRecognitionState.REQUESTING_PERMISSION || snapshot.state === SpeechRecognitionState.FINALIZING;

  const handlePress = () => {
    if (disabled || busy || unavailable) return;
    if (isListening) {
      stop();
      return;
    }
    if (snapshot.state === SpeechRecognitionState.ERROR || snapshot.state === SpeechRecognitionState.CANCELLED || snapshot.state === SpeechRecognitionState.COMPLETED) {
      void start({ contextualStrings });
      return;
    }
    void start({ contextualStrings });
  };

  const handleLongPress = () => {
    if (isListening) cancel();
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={isListening ? 'إيقاف الإملاء الصوتي' : label}
      accessibilityHint={unavailable ? 'التعرف الصوتي غير متاح؛ استخدم الإدخال اليدوي' : undefined}
      disabled={disabled || busy || unavailable}
      onPress={handlePress}
      onLongPress={handleLongPress}
      style={({ pressed }) => [styles.button, isListening && styles.active, unavailable && styles.disabled, pressed && styles.pressed]}
    >
      {busy ? <ActivityIndicator color="#ffffff" /> : <Text style={styles.icon}>{isListening ? '■' : '●'}</Text>}
      <Text style={styles.label}>{isListening ? 'إيقاف' : label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#1769aa',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  active: { backgroundColor: '#b42318' },
  disabled: { backgroundColor: '#98a2b3' },
  pressed: { opacity: 0.78 },
  icon: { color: '#ffffff', fontSize: 16, fontWeight: '700' },
  label: { color: '#ffffff', fontSize: 15, fontWeight: '700' },
});
