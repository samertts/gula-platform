import { useState } from 'react';
import { Card, CardHeader, CardBody, Tabs, LayoutContent, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { VoiceInput } from '../components/VoiceInput';

export function VoiceDictation() {
  const { isRtl } = useRTL();
  const [activeTab, setActiveTab] = useState('dictation');
  const [clinicalNotes, setClinicalNotes] = useState<string[]>([]);
  const [prescriptionText, setPrescriptionText] = useState('');

  const handleNoteResult = (text: string) => {
    if (text.trim()) {
      setClinicalNotes(prev => [...prev, text]);
    }
  };

  const handlePrescriptionResult = (text: string) => {
    setPrescriptionText(prev => prev + ' ' + text);
  };

  const tabs = [
    { id: 'dictation', label: isRtl ? 'الإملاء' : 'Dictation' },
    { id: 'notes', label: isRtl ? 'الملاحظات' : 'Notes' },
  ];

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الإملاء الصوتي' : 'Voice Dictation'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'تحويل الكلام إلى نص - يدعم العربية والإنكليزية' : 'Speech-to-text - Supports Arabic and English'}
          </p>
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === 'dictation' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <VoiceInput
              onResult={handleNoteResult}
              label={isRtl ? 'ملاحظة سريرية' : 'Clinical Note'}
              labelAr="ملاحظة سريرية"
              placeholderAr="تحدث للإملاء... انقر على الميكروفون للبدء"
              placeholder="Speak to dictate... Click the microphone to start"
            />
            <VoiceInput
              onResult={handlePrescriptionResult}
              label={isRtl ? 'وصفة طبية' : 'Prescription'}
              labelAr="وصفة طبية"
              placeholderAr="تحدث لكتابة الوصفة..."
              placeholder="Speak to write a prescription..."
              language="en-US"
            />
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="space-y-4">
            {prescriptionText && (
              <Card>
                <CardHeader title={isRtl ? 'الوصفة الطبية' : 'Prescription'} />
                <CardBody>
                  <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700">
                    <p className="text-sm whitespace-pre-wrap">{prescriptionText}</p>
                  </div>
                </CardBody>
              </Card>
            )}

            <Card>
              <CardHeader
                title={isRtl ? 'الملاحظات السريرية' : 'Clinical Notes'}
                subtitle={`${clinicalNotes.length} ${isRtl ? 'ملاحظة' : 'notes'}`}
              />
              <CardBody>
                {clinicalNotes.length === 0 ? (
                  <p className="text-sm text-neutral-500 text-center py-8">
                    {isRtl ? 'لا توجد ملاحظات بعد. استخدم الإملاء الصوتي لإنشاء ملاحظات.' : 'No notes yet. Use voice dictation to create notes.'}
                  </p>
                ) : (
                  <div className="space-y-3">
                    {clinicalNotes.map((note, i) => (
                      <div key={i} className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="info" size="xs">{isRtl ? 'ملاحظة' : 'Note'} {i + 1}</Badge>
                          <span className="text-xs text-neutral-400">
                            {new Date().toLocaleTimeString(isRtl ? 'ar-IQ' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{note}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>
        )}
      </div>
    </LayoutContent>
  );
}
