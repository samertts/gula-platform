import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SpeechRecognitionState, useSpeechToText } from '../speech/SpeechRecognitionProvider';
import type { VoiceTextMode } from '../speech/types';

export interface VoiceInputOverlayProps {
  existingText: string;
  onApplyDraft: (text: string, mode: VoiceTextMode) => void;
}

function formatDuration(durationMs: number): string {
  const totalSeconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

export function VoiceInputOverlay({ existingText, onApplyDraft }: VoiceInputOverlayProps) {
  const { snapshot, stop, cancel, retry, reset } = useSpeechToText();
  const [mode, setMode] = useState<VoiceTextMode>('append');
  const active = snapshot.state === SpeechRecognitionState.LISTENING || snapshot.state === SpeechRecognitionState.PROCESSING;
  const completed = snapshot.state === SpeechRecognitionState.COMPLETED;
  const hasDraft = Boolean(snapshot.finalText.trim());
  const shouldShow = active || completed || snapshot.state === SpeechRecognitionState.ERROR || snapshot.state === SpeechRecognitionState.DENIED || snapshot.state === SpeechRecognitionState.UNAVAILABLE;

  const statusText = useMemo(() => {
    switch (snapshot.state) {
      case SpeechRecognitionState.LISTENING: return 'يستمع الآن — تحدث بوضوح';
      case SpeechRecognitionState.PROCESSING: return 'يعالج النتيجة النهائية';
      case SpeechRecognitionState.FINALIZING: return 'ينهي تحويل الكلام إلى نص';
      case SpeechRecognitionState.COMPLETED: return 'المسودة جاهزة للمراجعة';
      case SpeechRecognitionState.DENIED: return 'الإذن مرفوض — استخدم الإدخال اليدوي';
      case SpeechRecognitionState.UNAVAILABLE: return 'التعرف الصوتي غير متاح على هذا الجهاز';
      case SpeechRecognitionState.ERROR: return snapshot.error?.message ?? 'حدث خطأ؛ يمكنك المحاولة مرة أخرى';
      default: return '';
    }
  }, [snapshot.state, snapshot.error?.message]);

  if (!shouldShow) return null;

  return (
    <View style={styles.container} accessibilityLiveRegion="polite">
      <View style={styles.header}>
        <View style={styles.statusRow}>
          {active && <View style={styles.pulse} />}
          <Text style={styles.status}>{statusText}</Text>
        </View>
        <Text style={styles.duration}>{formatDuration(snapshot.durationMs)}</Text>
      </View>

      <View style={styles.transcriptBox}>
        <Text style={styles.caption}>النص المرحلي</Text>
        <Text style={styles.interim}>{snapshot.interimText || '—'}</Text>
        <Text style={styles.caption}>النص النهائي</Text>
        <Text style={styles.finalText}>{snapshot.finalText || '—'}</Text>
      </View>

      {active && (
        <Pressable accessibilityRole="button" onPress={stop} style={[styles.action, styles.stopAction]}>
          <Text style={styles.actionText}>إيقاف والحصول على النتيجة</Text>
        </Pressable>
      )}

      {hasDraft && completed && (
        <>
          <Text style={styles.reviewNotice}>راجع النص طبياً قبل إدخاله في الحقل. لن يتم تعديل السجل السريري تلقائياً.</Text>
          <View style={styles.modeRow}>
            {(['append', 'replace'] as const).map((candidate) => (
              <Pressable
                key={candidate}
                accessibilityRole="radio"
                accessibilityState={{ selected: mode === candidate }}
                onPress={() => setMode(candidate)}
                style={[styles.modeButton, mode === candidate && styles.modeSelected]}
              >
                <Text style={[styles.modeText, mode === candidate && styles.modeTextSelected]}>
                  {candidate === 'append' ? 'إلحاق بالنص الموجود' : 'استبدال بعد التأكيد'}
                </Text>
              </Pressable>
            ))}
          </View>
          <Pressable accessibilityRole="button" onPress={() => onApplyDraft(existingText, mode)} style={styles.applyAction}>
            <Text style={styles.actionText}>إضافة إلى مسودة المراجعة</Text>
          </Pressable>
        </>
      )}

      <View style={styles.secondaryRow}>
        <Pressable accessibilityRole="button" onPress={cancel} style={styles.secondaryAction}>
          <Text style={styles.secondaryText}>إلغاء ومسح</Text>
        </Pressable>
        {(snapshot.state === SpeechRecognitionState.ERROR || snapshot.state === SpeechRecognitionState.DENIED) && (
          <Pressable accessibilityRole="button" onPress={() => void retry()} style={styles.secondaryAction}>
            <Text style={styles.secondaryText}>إعادة المحاولة</Text>
          </Pressable>
        )}
        {completed && (
          <Pressable accessibilityRole="button" onPress={reset} style={styles.secondaryAction}>
            <Text style={styles.secondaryText}>جلسة جديدة</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 12, padding: 16, borderRadius: 16, backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#d0d5dd' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  statusRow: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  pulse: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#b42318', marginEnd: 8 },
  status: { color: '#101828', fontWeight: '700', flexShrink: 1 },
  duration: { color: '#475467', fontVariant: ['tabular-nums'] },
  transcriptBox: { padding: 12, borderRadius: 12, backgroundColor: '#ffffff', marginBottom: 12 },
  caption: { color: '#667085', fontSize: 12, fontWeight: '700', marginTop: 4 },
  interim: { color: '#667085', minHeight: 24, marginBottom: 8 },
  finalText: { color: '#101828', minHeight: 24, lineHeight: 22 },
  reviewNotice: { color: '#7a271a', fontSize: 12, lineHeight: 18, marginBottom: 10 },
  modeRow: { flexDirection: 'row', gap: 8, marginBottom: 10 },
  modeButton: { flex: 1, borderWidth: 1, borderColor: '#d0d5dd', borderRadius: 10, padding: 10, backgroundColor: '#ffffff' },
  modeSelected: { borderColor: '#1769aa', backgroundColor: '#eff8ff' },
  modeText: { textAlign: 'center', color: '#344054', fontSize: 12 },
  modeTextSelected: { color: '#175cd3', fontWeight: '700' },
  action: { minHeight: 44, borderRadius: 10, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 12 },
  stopAction: { backgroundColor: '#b42318' },
  applyAction: { backgroundColor: '#1769aa', marginTop: 4 },
  actionText: { color: '#ffffff', fontWeight: '700' },
  secondaryRow: { flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginTop: 12 },
  secondaryAction: { paddingVertical: 8, paddingHorizontal: 10 },
  secondaryText: { color: '#175cd3', fontWeight: '600' },
});
