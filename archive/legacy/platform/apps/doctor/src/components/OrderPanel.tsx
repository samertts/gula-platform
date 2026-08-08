import { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Input, Select, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { OrderCategory, OrderPriority } from '../services/orders';

interface OrderPanelProps {
  patientId: string;
  category: OrderCategory;
  onSubmit: (order: OrderFormData) => void;
  onCancel?: () => void;
}

export interface OrderFormData {
  category: OrderCategory;
  priority: OrderPriority;
  description: string;
  descriptionAr: string;
  instructions?: string;
  instructionsAr?: string;
  indications?: string;
  code?: string;
}

const categories: { value: OrderCategory; label: string; labelAr: string }[] = [
  { value: 'medication', label: 'Medication', labelAr: 'دواء' },
  { value: 'lab', label: 'Lab Test', labelAr: 'تحليل مختبر' },
  { value: 'radiology', label: 'Radiology', labelAr: 'أشعة' },
  { value: 'procedure', label: 'Procedure', labelAr: 'إجراء' },
  { value: 'consultation', label: 'Consultation', labelAr: 'استشارة' },
  { value: 'diet', label: 'Diet', labelAr: 'نظام غذائي' },
  { value: 'nursing', label: 'Nursing', labelAr: 'تمريض' },
];

const priorities: { value: OrderPriority; label: string; labelAr: string }[] = [
  { value: 'routine', label: 'Routine', labelAr: 'روتيني' },
  { value: 'urgent', label: 'Urgent', labelAr: 'عاجل' },
  { value: 'stat', label: 'STAT', labelAr: 'فوري' },
  { value: 'asap', label: 'ASAP', labelAr: 'في أقرب وقت' },
];

export function OrderPanel({ category: initialCategory, onSubmit, onCancel }: OrderPanelProps) {
  const { isRtl } = useRTL();
  const [form, setForm] = useState<OrderFormData>({
    category: initialCategory,
    priority: 'routine',
    description: '',
    descriptionAr: '',
    instructions: '',
    instructionsAr: '',
    indications: '',
    code: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Card>
      <CardHeader title={isRtl ? 'طلب جديد' : 'New Order'} />
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={isRtl ? 'الفئة' : 'Category'}
              value={form.category}
              onChange={(v) => setForm(f => ({ ...f, category: v as OrderCategory }))}
              options={categories.map(c => ({ value: c.value, label: isRtl ? c.labelAr : c.label }))}
            />
            <Select
              label={isRtl ? 'الأولوية' : 'Priority'}
              value={form.priority}
              onChange={(v) => setForm(f => ({ ...f, priority: v as OrderPriority }))}
              options={priorities.map(p => ({ value: p.value, label: isRtl ? p.labelAr : p.label }))}
            />
          </div>

          <Input
            label={isRtl ? 'رمز الطلب' : 'Order Code'}
            value={form.code || ''}
            onChange={(e) => setForm(f => ({ ...f, code: e.target.value }))}
            placeholder={isRtl ? 'مثال: LAB-CBC' : 'e.g., LAB-CBC'}
          />

          <Input
            label={isRtl ? 'الوصف (عربي)' : 'Description (Arabic)'}
            value={form.descriptionAr}
            onChange={(e) => setForm(f => ({ ...f, descriptionAr: e.target.value }))}
            required
            placeholder={isRtl ? 'وصف الطلب' : 'Order description'}
          />

          <Input
            label={isRtl ? 'الوصف (إنجليزي)' : 'Description (English)'}
            value={form.description}
            onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
            placeholder="Order description in English"
          />

          <Input
            label={isRtl ? 'التعليمات (عربي)' : 'Instructions (Arabic)'}
            value={form.instructionsAr || ''}
            onChange={(e) => setForm(f => ({ ...f, instructionsAr: e.target.value }))}
          />

          <Input
            label={isRtl ? 'التبرير السريري' : 'Clinical Indications'}
            value={form.indications || ''}
            onChange={(e) => setForm(f => ({ ...f, indications: e.target.value }))}
          />

          <div className="flex gap-3 pt-2">
            <Button type="submit" variant="primary">
              {isRtl ? 'إرسال الطلب' : 'Submit Order'}
            </Button>
            {onCancel && (
              <Button type="button" variant="ghost" onClick={onCancel}>
                {isRtl ? 'إلغاء' : 'Cancel'}
              </Button>
            )}
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
