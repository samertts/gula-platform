import React, { useState } from 'react'
import DrugSearch from '../components/DrugSearch'
import InteractionAlert from '../components/InteractionAlert'
import { checkInteractions } from '../services/interactions'
import type { DrugInfo } from '../services/interactions'
import type { InteractionCheckResult } from '../services/interactions'

export default function Interactions() {
  const [selectedDrugs, setSelectedDrugs] = useState<DrugInfo[]>([])
  const [patientId, setPatientId] = useState('')
  const [patientName, setPatientName] = useState('')
  const [allergies, setAllergies] = useState('')
  const [result, setResult] = useState<InteractionCheckResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'check' | 'info' | 'allergies'>('check')

  function handleAddDrug(drug: DrugInfo) {
    setSelectedDrugs((prev) => [...prev, drug])
    setResult(null)
    setError('')
  }

  function handleRemoveDrug(drugCode: string) {
    setSelectedDrugs((prev) => prev.filter((d) => d.drug_code !== drugCode))
    setResult(null)
  }

  async function handleCheck() {
    if (selectedDrugs.length < 2) {
      setError('يرجى إضافة دوائين على الأقل لفحص التفاعلات')
      return
    }

    setLoading(true)
    setError('')
    try {
      const allergyList = allergies
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean)
      const data = await checkInteractions(
        selectedDrugs.map((d) => d.drug_code),
        patientId || undefined,
        allergyList.length > 0 ? allergyList : undefined,
      )
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل فحص التفاعلات')
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setSelectedDrugs([])
    setResult(null)
    setError('')
    setPatientId('')
    setPatientName('')
    setAllergies('')
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">فحص التفاعلات الدوائية</h1>
          <p className="page-subtitle">
            فحص التفاعلات بين الأدوية والحساسية والغذاء
          </p>
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'check' ? 'active' : ''}`}
          onClick={() => setActiveTab('check')}
        >
          🔍 فحص التفاعلات
        </button>
        <button
          className={`tab ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          ℹ️ معلومات دوائية
        </button>
        <button
          className={`tab ${activeTab === 'allergies' ? 'active' : ''}`}
          onClick={() => setActiveTab('allergies')}
        >
          ⚠️ تسجيل حساسية
        </button>
      </div>

      {activeTab === 'check' && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">إضافة أدوية</h3>
              <span className="badge badge-info">{selectedDrugs.length} دواء</span>
            </div>

            <DrugSearch onSelect={handleAddDrug} placeholder="ابحث وأضف دواء..." />

            {selectedDrugs.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                {selectedDrugs.map((drug) => (
                  <div
                    key={drug.drug_code}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.5rem 0.75rem',
                      background: 'var(--bg-primary)',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <span
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        background: 'var(--accent-primary)',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {selectedDrugs.indexOf(drug) + 1}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                        {drug.drug_name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {drug.generic_name} - {drug.drug_class}
                      </div>
                    </div>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleRemoveDrug(drug.drug_code)}
                      aria-label={`إزالة ${drug.drug_name}`}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label className="form-label">معرف المريض (اختياري)</label>
                <input
                  type="text"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  placeholder="رقم الملف"
                  aria-label="معرف المريض"
                />
              </div>
              <div className="form-group">
                <label className="form-label">حساسية دوائية (اختياري)</label>
                <input
                  type="text"
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
                  placeholder="بنسلين, أسبرين, ..."
                  aria-label="الحساسية الدوائية"
                />
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  افصل بين المواد بفاصلة
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
              <button
                className="btn btn-primary"
                onClick={handleCheck}
                disabled={loading || selectedDrugs.length < 2}
              >
                {loading ? <><span className="spinner" /> فحص...</> : '🔍 فحص التفاعلات'}
              </button>
              <button className="btn btn-ghost" onClick={handleClear}>
                مسح
              </button>
            </div>

            {error && (
              <div className="alert alert-danger" role="alert" style={{ marginTop: '1rem' }}>
                ⚠️ {error}
              </div>
            )}
          </div>

          <div>
            {result ? (
              <InteractionAlert
                interactions={result.interactions}
                allergies={result.allergies}
                foodInteractions={result.food_interactions}
                duplicateTherapy={result.duplicate_therapy}
                riskScore={result.risk_score}
              />
            ) : (
              <div className="card">
                <div className="empty-state">
                  <div className="empty-icon">💊</div>
                  <h3>قم بإضافة دوائين أو أكثر</h3>
                  <p>سيتم عرض نتائج فحص التفاعلات هنا</p>
                </div>
              </div>
            )}

            {result && result.interactions.length === 0 && result.allergies.length === 0 && (
              <div className="card">
                <div className="alert alert-success" role="alert">
                  ✅ لا توجد تفاعلات دوائية بين الأدوية المختارة
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'info' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">ℹ️</div>
            <h3>معلومات دوائية</h3>
            <p>ابحث عن معلومات تفصيلية عن أي دواء</p>
          </div>
          <DrugSearch onSelect={() => {}} placeholder="ابحث عن معلومات دواء..." />
        </div>
      )}

      {activeTab === 'allergies' && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">⚠️</div>
            <h3>تسجيل حساسية دوائية</h3>
            <p>هذه الخدمة ستتيح تسجيل الحساسية الدوائية للمرضى</p>
          </div>
          <div className="form-group">
            <label className="form-label">رقم الملف</label>
            <input type="text" placeholder="أدخل رقم ملف المريض" />
          </div>
          <DrugSearch onSelect={() => {}} placeholder="اختر الدواء المسبب للحساسية..." />
          <div className="form-group" style={{ marginTop: '1rem' }}>
            <label className="form-label">نوع التفاعل</label>
            <select>
              <option value="">اختر نوع التفاعل...</option>
              <option value="طفح جلدي">طفح جلدي</option>
              <option value="حكة">حكة</option>
              <option value="تورم">تورم</option>
              <option value="ضيق تنفس">ضيق تنفس</option>
              <option value="صدمة تحسسية">صدمة تحسسية</option>
              <option value="غثيان">غثيان</option>
              <option value="صداع">صداع</option>
            </select>
          </div>
          <button className="btn btn-primary">تسجيل الحساسية</button>
        </div>
      )}
    </div>
  )
}
