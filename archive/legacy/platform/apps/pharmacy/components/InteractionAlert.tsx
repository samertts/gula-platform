import React from 'react'
import type { DrugInteraction, DrugAllergy, DrugFoodInteraction } from '../services/interactions'

interface InteractionAlertProps {
  interactions: DrugInteraction[]
  allergies: DrugAllergy[]
  foodInteractions: DrugFoodInteraction[]
  duplicateTherapy: string[]
  riskScore: number
  onAcknowledge?: () => void
  onCancel?: () => void
}

const severityColors: Record<string, string> = {
  contraindicated: 'var(--accent-danger)',
  severe: '#f97316',
  moderate: 'var(--accent-warning)',
  minor: 'var(--accent-info)',
}

const severityLabels: Record<string, string> = {
  contraindicated: 'ممنوع الاستخدام المشترك',
  severe: 'شديد',
  moderate: 'متوسط',
  minor: 'بسيط',
}

export default function InteractionAlert({
  interactions,
  allergies,
  foodInteractions,
  duplicateTherapy,
  riskScore,
  onAcknowledge,
  onCancel,
}: InteractionAlertProps) {
  const hasCritical = interactions.some(
    (i) => i.severity === 'contraindicated' || i.severity === 'severe',
  )
  const hasAllergies = allergies.length > 0

  const alertType = hasCritical || hasAllergies ? 'danger' : riskScore > 5 ? 'warning' : 'info'
  const alertTitle =
    alertType === 'danger'
      ? 'تحذير: تفاعلات دوائية خطيرة'
      : alertType === 'warning'
        ? 'تنبيه: تفاعلات دوائية محتملة'
        : 'معلومات: لا توجد تفاعلات خطيرة'

  return (
    <div
      className={`alert alert-${alertType}`}
      role="alert"
      style={{ flexDirection: 'column', alignItems: 'stretch' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}>
        <span>{alertType === 'danger' ? '⚠️' : alertType === 'warning' ? '⚡' : 'ℹ️'}</span>
        <span>{alertTitle}</span>
        {riskScore > 0 && (
          <span
            style={{
              marginRight: 'auto',
              fontSize: '0.75rem',
              opacity: 0.8,
            }}
          >
            درجة الخطورة: {riskScore}
          </span>
        )}
      </div>

      {interactions.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <strong style={{ fontSize: '0.8rem' }}>تفاعلات دواء-دواء:</strong>
          {interactions.map((interaction) => (
            <div
              key={interaction.id}
              style={{
                marginTop: '0.5rem',
                padding: '0.5rem',
                background: 'rgba(0,0,0,0.2)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div className="interaction-level">
                <span
                  className={`severity-dot severity-${interaction.severity}`}
                  style={{ display: 'inline-block' }}
                />
                <strong>
                  {interaction.drug_a_name} + {interaction.drug_b_name}
                </strong>
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: severityColors[interaction.severity],
                    fontWeight: 600,
                    marginRight: 'auto',
                  }}
                >
                  {severityLabels[interaction.severity]}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem', opacity: 0.9 }}>
                {interaction.effect}
              </p>
              <p style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--accent-info)' }}>
                التوصية: {interaction.recommendation}
              </p>
            </div>
          ))}
        </div>
      )}

      {allergies.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <strong style={{ fontSize: '0.8rem', color: 'var(--accent-danger)' }}>
            تحذيرات الحساسية:
          </strong>
          {allergies.map((allergy, idx) => (
            <div
              key={idx}
              style={{
                marginTop: '0.5rem',
                padding: '0.5rem',
                background: 'rgba(239,68,68,0.1)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(239,68,68,0.3)',
              }}
            >
              <strong>{allergy.drug_name}</strong> - {allergy.allergen}
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                التفاعل: {allergy.reaction} ( severity: {allergy.severity})
              </p>
            </div>
          ))}
        </div>
      )}

      {foodInteractions.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <strong style={{ fontSize: '0.8rem' }}>تفاعلات دواء-غذاء:</strong>
          {foodInteractions.map((fi, idx) => (
            <div
              key={idx}
              style={{
                marginTop: '0.5rem',
                padding: '0.5rem',
                background: 'rgba(0,0,0,0.2)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <strong>{fi.drug_name}</strong> ← {fi.food}
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem', opacity: 0.9 }}>
                {fi.effect}
              </p>
              <p style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--accent-info)' }}>
                {fi.recommendation}
              </p>
            </div>
          ))}
        </div>
      )}

      {duplicateTherapy.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <strong style={{ fontSize: '0.8rem', color: 'var(--accent-warning)' }}>
            علاج مكرر:
          </strong>
          <ul style={{ fontSize: '0.8rem', marginRight: '1rem', marginTop: '0.25rem' }}>
            {duplicateTherapy.map((d, idx) => (
              <li key={idx}>{d}</li>
            ))}
          </ul>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginTop: '1rem',
          justifyContent: 'flex-end',
        }}
      >
        {onCancel && (
          <button className="btn btn-secondary" onClick={onCancel}>
            إلغاء الصرف
          </button>
        )}
        {onAcknowledge && (
          <button
            className={`btn ${hasCritical || hasAllergies ? 'btn-danger' : 'btn-primary'}`}
            onClick={onAcknowledge}
          >
            {hasCritical || hasAllergies ? 'تجاوز التحذير' : 'متابعة الصرف'}
          </button>
        )}
      </div>
    </div>
  )
}
