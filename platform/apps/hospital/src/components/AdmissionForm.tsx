import { useState } from 'react';
import { Input, Select, Button, useRTL } from '@gula/ui-platform';

interface AdmissionFormProps {
  onClose: () => void;
}

export function AdmissionForm({ onClose }: AdmissionFormProps) {
  const { isRtl } = useRTL();
  const [formData, setFormData] = useState({
    patientName: '',
    patientNameAr: '',
    gender: '',
    dateOfBirth: '',
    phone: '',
    nationalId: '',
    department: '',
    ward: '',
    diagnosis: '',
    diagnosisAr: '',
    referringDoctor: '',
    referringDoctorAr: '',
    insuranceProvider: '',
    insuranceNumber: '',
    emergencyContact: '',
    emergencyPhone: '',
    notes: '',
  });

  const updateField = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onClose();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-3">
          {isRtl ? 'معلومات المريض' : 'Patient Information'}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label={isRtl ? 'اسم المريض (عربي)' : 'Patient Name (Arabic)'}
            value={formData.patientNameAr}
            onChange={e => updateField('patientNameAr', e.target.value)}
            required
          />
          <Input
            label={isRtl ? 'اسم المريض (إنجليزي)' : 'Patient Name (English)'}
            value={formData.patientName}
            onChange={e => updateField('patientName', e.target.value)}
          />
          <Select
            label={isRtl ? 'الجنس' : 'Gender'}
            value={formData.gender}
            onChange={e => updateField('gender', e.target.value)}
            options={[
              { value: '', label: isRtl ? 'اختر...' : 'Select...' },
              { value: 'male', label: isRtl ? 'ذكر' : 'Male' },
              { value: 'female', label: isRtl ? 'أنثى' : 'Female' },
            ]}
            required
          />
          <Input
            label={isRtl ? 'تاريخ الميلاد' : 'Date of Birth'}
            type="date"
            value={formData.dateOfBirth}
            onChange={e => updateField('dateOfBirth', e.target.value)}
            required
          />
          <Input
            label={isRtl ? 'رقم الهاتف' : 'Phone'}
            type="tel"
            value={formData.phone}
            onChange={e => updateField('phone', e.target.value)}
            required
          />
          <Input
            label={isRtl ? 'الرقم الوطني' : 'National ID'}
            value={formData.nationalId}
            onChange={e => updateField('nationalId', e.target.value)}
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-3">
          {isRtl ? 'معلومات الاستقبال' : 'Admission Information'}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label={isRtl ? 'القسم' : 'Department'}
            value={formData.department}
            onChange={e => updateField('department', e.target.value)}
            options={[
              { value: '', label: isRtl ? 'اختر...' : 'Select...' },
              { value: 'ER', label: isRtl ? 'الطوارئ' : 'Emergency' },
              { value: 'Internal Medicine', label: isRtl ? 'الباطنية' : 'Internal Medicine' },
              { value: 'Surgery', label: isRtl ? 'الجراحة' : 'Surgery' },
              { value: 'Pediatrics', label: isRtl ? 'طب الأطفال' : 'Pediatrics' },
              { value: 'ICU', label: isRtl ? 'العناية المركزة' : 'ICU' },
              { value: 'Maternity', label: isRtl ? 'النسائية' : 'Maternity' },
              { value: 'Orthopedics', label: isRtl ? 'العظام' : 'Orthopedics' },
            ]}
            required
          />
          <Input
            label={isRtl ? 'الجناح' : 'Ward'}
            value={formData.ward}
            onChange={e => updateField('ward', e.target.value)}
            placeholder={isRtl ? 'مثال: الجناح الغربي - 2' : 'e.g. Ward West-2'}
          />
          <Input
            label={isRtl ? 'التشخيص (عربي)' : 'Diagnosis (Arabic)'}
            value={formData.diagnosisAr}
            onChange={e => updateField('diagnosisAr', e.target.value)}
            required
          />
          <Input
            label={isRtl ? 'التشخيص (إنجليزي)' : 'Diagnosis (English)'}
            value={formData.diagnosis}
            onChange={e => updateField('diagnosis', e.target.value)}
          />
          <Input
            label={isRtl ? 'الطبيب المحول' : 'Referring Doctor'}
            value={formData.referringDoctorAr}
            onChange={e => updateField('referringDoctorAr', e.target.value)}
          />
          <Input
            label={isRtl ? 'الطبيب المحول (إنجليزي)' : 'Referring Doctor (English)'}
            value={formData.referringDoctor}
            onChange={e => updateField('referringDoctor', e.target.value)}
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-3">
          {isRtl ? 'معلومات إضافية' : 'Additional Information'}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label={isRtl ? 'شركة التأمين' : 'Insurance Provider'}
            value={formData.insuranceProvider}
            onChange={e => updateField('insuranceProvider', e.target.value)}
          />
          <Input
            label={isRtl ? 'رقم التأمين' : 'Insurance Number'}
            value={formData.insuranceNumber}
            onChange={e => updateField('insuranceNumber', e.target.value)}
          />
          <Input
            label={isRtl ? 'جهة اتصال طارئة' : 'Emergency Contact'}
            value={formData.emergencyContact}
            onChange={e => updateField('emergencyContact', e.target.value)}
            required
          />
          <Input
            label={isRtl ? 'هاتف الطوارئ' : 'Emergency Phone'}
            type="tel"
            value={formData.emergencyPhone}
            onChange={e => updateField('emergencyPhone', e.target.value)}
            required
          />
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            {isRtl ? 'ملاحظات' : 'Notes'}
          </label>
          <textarea
            value={formData.notes}
            onChange={e => updateField('notes', e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm text-neutral-900 dark:text-neutral-50 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder={isRtl ? 'أي ملاحظات إضافية...' : 'Any additional notes...'}
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <Button type="button" variant="outline" onClick={onClose}>
          {isRtl ? 'إلغاء' : 'Cancel'}
        </Button>
        <Button type="submit">
          {isRtl ? 'تسجيل الاستقبال' : 'Submit Admission'}
        </Button>
      </div>
    </form>
  );
}
