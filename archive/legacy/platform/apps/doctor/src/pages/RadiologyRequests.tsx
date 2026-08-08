import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, Input, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { OrderPriority } from '../services/orders';

interface RadiologyExam {
  code: string;
  name: string;
  nameAr: string;
  bodyPart: string;
  contrast: boolean;
  preparation: string;
  preparationAr: string;
}

const AVAILABLE_EXAMS: RadiologyExam[] = [
  { code: 'CXR', name: 'Chest X-Ray', nameAr: 'أشعة الصدر', bodyPart: 'Chest', contrast: false, preparation: 'None', preparationAr: 'لا يوجد' },
  { code: 'CT-BRAIN', name: 'CT Brain', nameAr: 'أشعة مقطعية للدماغ', bodyPart: 'Head', contrast: false, preparation: 'None', preparationAr: 'لا يوجد' },
  { code: 'CT-ABD', name: 'CT Abdomen with Contrast', nameAr: 'أشعة مقطعية للبطن مع صبغة', bodyPart: 'Abdomen', contrast: true, preparation: 'Fasting 4 hours', preparationAr: 'صيام 4 ساعات' },
  { code: 'MRI-BRAIN', name: 'MRI Brain', nameAr: 'رنين مغناطيسي للدماغ', bodyPart: 'Head', contrast: false, preparation: 'Remove metal objects', preparationAr: 'إزالة المعادن' },
  { code: 'US-ABD', name: 'Abdominal Ultrasound', nameAr: 'تصوير تلفزيوني للبطن', bodyPart: 'Abdomen', contrast: false, preparation: 'Fasting 6 hours', preparationAr: 'صيام 6 ساعات' },
  { code: 'MAMMO', name: 'Mammogram', nameAr: 'تصوير الثدي الشعاعي', bodyPart: 'Breast', contrast: false, preparation: 'No deodorant', preparationAr: 'بدون مزيل عرق' },
];

export function RadiologyRequests() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [selectedExams, setSelectedExams] = useState<RadiologyExam[]>([]);
  const [priority, setPriority] = useState<OrderPriority>('routine');
  const [clinicalIndication, setClinicalIndication] = useState('');
  const [notes, setNotes] = useState('');

  const toggleExam = (exam: RadiologyExam) => {
    setSelectedExams(prev =>
      prev.find(e => e.code === exam.code)
        ? prev.filter(e => e.code !== exam.code)
        : [...prev, exam],
    );
  };

  const handleSubmit = () => {
    if (selectedExams.length === 0) return;
    navigate(-1);
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'طلب فحوصات أشعة' : 'Radiology Request'}
            </h1>
          </div>
        </div>

        <Card>
          <CardHeader title={isRtl ? 'اختيار الفحص' : 'Select Exam'} />
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {AVAILABLE_EXAMS.map(exam => (
                <button
                  key={exam.code}
                  onClick={() => toggleExam(exam)}
                  className={`p-4 rounded-xl text-right border-2 transition-colors ${
                    selectedExams.find(e => e.code === exam.code)
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950'
                      : 'border-neutral-200 dark:border-neutral-700 hover:border-primary-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center shrink-0">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <circle cx="12" cy="12" r="10" /><path d="M12 6v12M6 12h12" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-sm">{isRtl ? exam.nameAr : exam.name}</p>
                      <p className="text-xs text-neutral-500">{exam.code} | {exam.bodyPart}</p>
                      <div className="flex gap-1 mt-1">
                        {exam.contrast && <Badge variant="warning" size="xs">{isRtl ? 'صبغة' : 'Contrast'}</Badge>}
                        <Badge variant="default" size="xs">{isRtl ? exam.preparationAr : exam.preparation}</Badge>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={isRtl ? 'تفاصيل الطلب' : 'Request Details'} />
          <CardBody>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{isRtl ? 'الأولوية' : 'Priority'}</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value as OrderPriority)}
                  className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
                >
                  <option value="routine">{isRtl ? 'روتيني' : 'Routine'}</option>
                  <option value="urgent">{isRtl ? 'عاجل' : 'Urgent'}</option>
                  <option value="stat">{isRtl ? 'فوري' : 'STAT'}</option>
                </select>
              </div>

              <Input
                label={isRtl ? 'التبرير السريري' : 'Clinical Indication'}
                value={clinicalIndication}
                onChange={e => setClinicalIndication(e.target.value)}
                required
              />

              <Input
                label={isRtl ? 'ملاحظات إضافية' : 'Additional Notes'}
                value={notes}
                onChange={e => setNotes(e.target.value)}
              />

              {selectedExams.length > 0 && (
                <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-900">
                  <p className="font-medium text-sm mb-2">
                    {isRtl ? `الفحوصات المختارة (${selectedExams.length})` : `Selected Exams (${selectedExams.length})`}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedExams.map(e => (
                      <Badge key={e.code} variant="primary">{e.code}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button variant="primary" onClick={handleSubmit} disabled={selectedExams.length === 0}>
                  {isRtl ? 'إرسال الطلب' : 'Submit Request'}
                </Button>
                <Button variant="ghost" onClick={() => navigate(-1)}>
                  {isRtl ? 'إلغاء' : 'Cancel'}
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
