import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { VoiceInputButton } from './src/components/VoiceInputButton';
import { VoiceInputOverlay } from './src/components/VoiceInputOverlay';
import { SpeechRecognitionProvider, useSpeechToText } from './src/speech/SpeechRecognitionProvider';
import type { VoiceTextMode } from './src/speech/types';

const CLINICAL_CONTEXTUAL_STRINGS = [
  'ضغط الدم', 'السكري', 'الحمى', 'ألم الصدر', 'ضيق النفس', 'النبض', 'الأكسجين',
  'تحليل الدم', 'صورة الدم الكاملة', 'الكرياتينين', 'الهيموغلوبين', 'المزرعة',
  'باراسيتامول', 'أموكسيسيلين', 'الجرعة', 'الوصفة', 'التشخيص', 'التاريخ المرضي',
  'CBC', 'ECG', 'SpO2', 'BP', 'HR', 'HbA1c',
];

function VoiceDraftScreen() {
  const { applyToText, snapshot } = useSpeechToText();
  const [draftText, setDraftText] = useState('');
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const applyVoiceDraft = (existingText: string, mode: VoiceTextMode) => {
    setDraftText(applyToText(existingText, mode));
    setSavedAt(null);
  };

  const saveReviewedDraft = () => {
    if (!draftText.trim()) return;
    // This screen intentionally saves only the reviewed draft in local component state.
    // A production submit must call the authenticated GULA API with version checks and audit metadata.
    setSavedAt(new Date().toISOString());
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Text style={styles.eyebrow}>GULA MOBILE · SDK 54</Text>
          <Text style={styles.title}>مسودة إملاء سريري آمنة</Text>
          <Text style={styles.subtitle}>
            الصوت يحوّل إلى نص فقط بعد ضغطك الصريح على الميكروفون. راجع النص قبل إدخاله أو حفظه.
          </Text>

          <View style={styles.card}>
            <Text style={styles.label}>الملاحظة السريرية — مسودة قابلة للمراجعة</Text>
            <TextInput
              accessibilityLabel="حقل الملاحظة السريرية"
              multiline
              textAlign="right"
              value={draftText}
              onChangeText={(value) => {
                setDraftText(value);
                setSavedAt(null);
              }}
              placeholder="اكتب يدوياً أو استخدم الإملاء الصوتي..."
              placeholderTextColor="#98a2b3"
              style={styles.input}
            />
            <VoiceInputButton contextualStrings={CLINICAL_CONTEXTUAL_STRINGS} />
            <VoiceInputOverlay existingText={draftText} onApplyDraft={applyVoiceDraft} />
          </View>

          <View style={styles.reviewCard}>
            <Text style={styles.reviewTitle}>مراجعة بشرية إلزامية</Text>
            <Text style={styles.reviewText}>
              لا يغير الإملاء الصوتي تشخيصاً أو دواءً أو نتيجة تحليل مباشرة. لا يتم إرسال أي صوت إلى الخادم، ولا يحفظ التطبيق التسجيل الصوتي.
            </Text>
            <Text style={styles.meta}>الحالة: {snapshot.state}</Text>
            <Text style={styles.meta}>اللغة: {snapshot.locale}</Text>
            <Text style={styles.meta}>النص النهائي: {snapshot.finalText ? 'متاح للمراجعة' : 'لا توجد نتيجة بعد'}</Text>
            <Text style={styles.meta}>التعرف المحلي: {snapshot.capabilities?.onDeviceAvailable ? 'متاح حسب الجهاز' : 'غير مؤكد — لا ندّعي وضع Offline'}</Text>
            <Text style={styles.meta}>صلاحية الميكروفون: {snapshot.permission}</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="حفظ المسودة بعد المراجعة"
              disabled={!draftText.trim()}
              onPress={saveReviewedDraft}
              style={[styles.saveButton, !draftText.trim() && styles.saveDisabled]}
            >
              <Text style={styles.saveButtonText}>حفظ المسودة بعد المراجعة</Text>
            </Pressable>
            {savedAt && <Text style={styles.success}>تم اعتماد المسودة محلياً للمراجعة اللاحقة: {new Date(savedAt).toLocaleTimeString('ar-IQ')}</Text>}
          </View>

          <Text style={styles.manualFallback}>إذا لم تتوفر الخدمة أو رفضت الصلاحية، يبقى الإدخال اليدوي متاحاً دون تعطيل التطبيق.</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SpeechRecognitionProvider sessionKey="authenticated-user-session" initialLocale="ar-IQ">
      <VoiceDraftScreen />
    </SpeechRecognitionProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f2f4f7' },
  flex: { flex: 1 },
  content: { padding: 20, gap: 16 },
  eyebrow: { color: '#175cd3', fontSize: 12, fontWeight: '800', letterSpacing: 1 },
  title: { color: '#101828', fontSize: 28, fontWeight: '800', textAlign: 'right' },
  subtitle: { color: '#475467', fontSize: 15, lineHeight: 23, textAlign: 'right' },
  card: { backgroundColor: '#ffffff', borderRadius: 18, padding: 16, gap: 12, borderWidth: 1, borderColor: '#eaecf0' },
  label: { color: '#344054', fontSize: 15, fontWeight: '700', textAlign: 'right' },
  input: { minHeight: 150, borderWidth: 1, borderColor: '#d0d5dd', borderRadius: 12, padding: 14, color: '#101828', fontSize: 16, lineHeight: 25, textAlignVertical: 'top' },
  reviewCard: { backgroundColor: '#fffaeb', borderRadius: 18, padding: 16, borderWidth: 1, borderColor: '#fedf89', gap: 8 },
  reviewTitle: { color: '#7a271a', fontSize: 16, fontWeight: '800', textAlign: 'right' },
  reviewText: { color: '#93370d', fontSize: 13, lineHeight: 20, textAlign: 'right' },
  meta: { color: '#7a271a', fontSize: 12, textAlign: 'right' },
  saveButton: { minHeight: 46, borderRadius: 10, backgroundColor: '#1769aa', alignItems: 'center', justifyContent: 'center', marginTop: 4 },
  saveButtonText: { color: '#ffffff', fontWeight: '800', paddingVertical: 12, paddingHorizontal: 20 },
  saveDisabled: { opacity: 0.45 },
  success: { color: '#027a48', fontSize: 12, textAlign: 'right' },
  manualFallback: { color: '#667085', fontSize: 12, lineHeight: 19, textAlign: 'right', paddingBottom: 20 },
});
