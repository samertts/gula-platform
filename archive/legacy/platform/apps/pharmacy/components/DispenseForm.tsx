import React, { useState } from 'react'
import type { Prescription, PrescriptionItem } from '../services/dispensing'

interface DispenseFormProps {
  prescription: Prescription
  onSubmit: (data: {
    items: { inventory_id: string; quantity: number; batch_number: string }[]
    notes: string
  }) => void
  onCancel: () => void
  onCheckInteractions: (drugCodes: string[]) => void
}

export default function DispenseForm({
  prescription,
  onSubmit,
  onCancel,
  onCheckInteractions,
}: DispenseFormProps) {
  const [dispenseItems, setDispenseItems] = useState<
    Record<
      string,
      {
        inventoryId: string
        quantity: number
        batchNumber: string
        verified: boolean
      }
    >
  >(
    Object.fromEntries(
      prescription.items.map((item) => [
        item.id,
        {
          inventoryId: '',
          quantity: item.quantity,
          batchNumber: '',
          verified: false,
        },
      ]),
    ),
  )
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  function updateItem(
    itemId: string,
    field: string,
    value: string | number | boolean,
  ) {
    setDispenseItems((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], [field]: value },
    }))
    if (errors[itemId]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[itemId]
        return next
      })
    }
  }

  function validate(): boolean {
    const newErrors: Record<string, string> = {}
    for (const item of prescription.items) {
      const di = dispenseItems[item.id]
      if (!di.inventoryId) {
        newErrors[item.id] = 'يرجى اختيار المخزون'
      }
      if (di.quantity <= 0) {
        newErrors[item.id] = 'الكمية يجب أن تكون أكبر من صفر'
      }
      if (di.quantity > item.quantity - (item.dispensed_quantity || 0)) {
        newErrors[item.id] = 'الكمية تتجاوز المتبقي'
      }
      if (!di.batchNumber) {
        newErrors[item.id] = 'يرجى إدخال رقم الدفعة'
      }
      if (!di.verified) {
        newErrors[item.id] = 'يرجى تأكيد التحقق'
      }
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    onSubmit({
      items: Object.entries(dispenseItems).map(([itemId, di]) => ({
        inventory_id: di.inventoryId,
        quantity: di.quantity,
        batch_number: di.batchNumber,
      })),
      notes,
    })
  }

  function handleInteractionCheck() {
    const codes = prescription.items.map((i) => i.drug_code)
    onCheckInteractions(codes)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-header">
          <h3 className="card-title">بيانات الوصفة</h3>
          <span className="badge badge-info">
            {prescription.prescription_number}
          </span>
        </div>
        <div className="grid-2">
          <div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              المريض
            </p>
            <p style={{ fontWeight: 600 }}>{prescription.patient_name}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              الطبيب
            </p>
            <p style={{ fontWeight: 600 }}>{prescription.doctor_name}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              التاريخ
            </p>
            <p style={{ fontWeight: 600 }}>
              {new Date(prescription.issue_date).toLocaleDateString('ar-IQ')}
            </p>
          </div>
          <div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              المنشأة
            </p>
            <p style={{ fontWeight: 600 }}>{prescription.facility}</p>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <button
          type="button"
          className="btn btn-warning"
          onClick={handleInteractionCheck}
        >
          🔍 فحص التفاعلات الدوائية
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">أدوية الوصفة</h3>
        </div>

        {prescription.items.map((item) => {
          const di = dispenseItems[item.id]
          return (
            <div
              key={item.id}
              style={{
                padding: '1rem',
                border: `1px solid ${errors[item.id] ? 'var(--accent-danger)' : 'var(--border-color)'}`,
                borderRadius: 'var(--radius-md)',
                marginBottom: '0.75rem',
                background: errors[item.id]
                  ? 'rgba(239,68,68,0.05)'
                  : 'transparent',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.75rem',
                }}
              >
                <div>
                  <strong>{item.drug_name}</strong>
                  <span
                    style={{
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      marginRight: '0.5rem',
                    }}
                  >
                    {item.dose} {item.dose_unit} - {item.route}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    الكمية: {item.quantity}
                  </span>
                  {item.is_controlled && (
                    <span className="badge badge-danger">مخدر</span>
                  )}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">رقم الدفعة</label>
                  <input
                    type="text"
                    value={di.batchNumber}
                    onChange={(e) =>
                      updateItem(item.id, 'batchNumber', e.target.value)
                    }
                    placeholder="أدخل رقم الدفعة"
                    aria-label={`رقم الدفعة لـ ${item.drug_name}`}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">الكمية المراد صرفها</label>
                  <input
                    type="number"
                    min={1}
                    max={item.quantity - (item.dispensed_quantity || 0)}
                    value={di.quantity}
                    onChange={(e) =>
                      updateItem(item.id, 'quantity', parseInt(e.target.value) || 0)
                    }
                    aria-label={`الكمية لـ ${item.drug_name}`}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">اختيار من المخزون</label>
                  <select
                    value={di.inventoryId}
                    onChange={(e) =>
                      updateItem(item.id, 'inventoryId', e.target.value)
                    }
                    aria-label={`اختيار المخزون لـ ${item.drug_name}`}
                  >
                    <option value="">اختر...</option>
                    <option value="inv_1">مستودع أ - دفعة B001 (500 متبقي)</option>
                    <option value="inv_2">مستودع ب - دفعة B002 (250 متبقي)</option>
                  </select>
                </div>
                <div
                  className="form-group"
                  style={{
                    display: 'flex',
                    alignItems: 'flex-end',
                    paddingBottom: '0.25rem',
                  }}
                >
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={di.verified}
                      onChange={(e) =>
                        updateItem(item.id, 'verified', e.target.checked)
                      }
                      style={{ width: 'auto' }}
                      aria-label={`تأكيد التحقق من ${item.drug_name}`}
                    />
                    تم التحقق
                  </label>
                </div>
              </div>

              {errors[item.id] && (
                <div
                  className="form-error"
                  role="alert"
                  style={{ marginTop: '0.25rem' }}
                >
                  {errors[item.id]}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="form-group">
        <label className="form-label">ملاحظات الصرف</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          placeholder="ملاحظات إضافية للصرف..."
          aria-label="ملاحظات الصرف"
        />
      </div>

      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          justifyContent: 'flex-end',
          marginTop: '1rem',
        }}
      >
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          إلغاء
        </button>
        <button type="submit" className="btn btn-primary btn-lg">
          تأكيد الصرف
        </button>
      </div>
    </form>
  )
}
