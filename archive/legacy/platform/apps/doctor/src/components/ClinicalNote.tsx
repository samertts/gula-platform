import { useState } from 'react';
import { Card, CardHeader, CardBody, Input, Button, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface ClinicalNoteData {
  type: 'consultation' | 'follow_up' | 'procedure' | 'discharge_summary' | 'progress_note';
  content: string;
  contentAr: string;
}

interface ClinicalNoteProps {
  onSubmit: (note: ClinicalNoteData) => void;
  initialData?: ClinicalNoteData;
  isSigned?: boolean;
  onSign?: () => void;
}

const noteTypes = [
  { value: 'consultation', label: 'Consultation', labelAr: 'استشارة' },
  { value: 'follow_up', label: 'Follow Up', labelAr: 'متابعة' },
  { value: 'procedure', label: 'Procedure', labelAr: 'إجراء' },
  { value: 'discharge_summary', label: 'Discharge Summary', labelAr: 'ملخص خروج' },
  { value: 'progress_note', label: 'Progress Note', labelAr: 'ملاحظة تقدم' },
];

export function ClinicalNote({ onSubmit, initialData, isSigned, onSign }: ClinicalNoteProps) {
  const { isRtl } = useRTL();
  const [type, setType] = useState(initialData?.type || 'consultation');
  const [content, setContent] = useState(initialData?.content || '');
  const [contentAr, setContentAr] = useState(initialData?.contentAr || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ type, content, contentAr });
    if (!initialData) {
      setContent('');
      setContentAr('');
    }
  };

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'ملاحظة سريرية' : 'Clinical Note'}
        action={isSigned ? <Badge variant="success">{isRtl ? 'موقعة' : 'Signed'}</Badge> : undefined}
      />
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {isRtl ? 'النوع' : 'Type'}
            </label>
            <select
              value={type}
              onChange={e => setType(e.target.value as any)}
              className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
            >
              {noteTypes.map(t => (
                <option key={t.value} value={t.value}>{isRtl ? t.labelAr : t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {isRtl ? 'المحتوى (عربي)' : 'Content (Arabic)'}
            </label>
            <textarea
              value={contentAr}
              onChange={e => setContentAr(e.target.value)}
              rows={6}
              dir="rtl"
              className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm resize-y"
              placeholder={isRtl ? 'اكتب الملاحظة السريرية هنا...' : 'Write the clinical note here...'}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {isRtl ? 'المحتوى (إنجليزي)' : 'Content (English)'}
            </label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              rows={4}
              className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm resize-y"
              placeholder="Write the clinical note in English..."
            />
          </div>

          <div className="flex gap-3">
            <Button type="submit" variant="primary">
              {initialData ? (isRtl ? 'تحديث' : 'Update') : (isRtl ? 'حفظ' : 'Save')}
            </Button>
            {onSign && !isSigned && (
              <Button type="button" variant="secondary" onClick={onSign}>
                {isRtl ? 'توقيع' : 'Sign'}
              </Button>
            )}
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
