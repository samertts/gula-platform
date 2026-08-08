import React, { useState, useEffect } from 'react'

interface PharmacySettings {
  pharmacy_name: string
  pharmacy_address: string
  pharmacy_phone: string
  pharmacy_license: string
  pharmacist_in_charge: string
  auto_approve_prescriptions: boolean
  require_barcode_verification: boolean
  require_witness_for_controlled: boolean
  low_stock_threshold: number
  expiry_warning_days: number
  enable_interaction_checking: boolean
  enable_offline_mode: boolean
  auto_sync_interval: number
  language: string
  theme: string
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'general' | 'clinical' | 'inventory' | 'system'>('general')
  const [saved, setSaved] = useState(false)
  const [settings, setSettings] = useState<PharmacySettings>({
    pharmacy_name: 'صيدلية جلا',
    pharmacy_address: 'بغداد، العراق',
    pharmacy_phone: '+964 123 456 789',
    pharmacy_license: 'PH-2024-001',
    pharmacist_in_charge: 'د. أحمد السامرائي',
    auto_approve_prescriptions: false,
    require_barcode_verification: true,
    require_witness_for_controlled: true,
    low_stock_threshold: 10,
    expiry_warning_days: 30,
    enable_interaction_checking: true,
    enable_offline_mode: true,
    auto_sync_interval: 5,
    language: 'ar',
    theme: 'dark',
  })

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
    try {
      localStorage.setItem('pharmacy_settings', JSON.stringify(settings))
    } catch {
      // silent
    }
  }

  function updateField<K extends keyof PharmacySettings>(key: K, value: PharmacySettings[K]) {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">الإعدادات</h1>
          <p className="page-subtitle">إعدادات وتخصيص نظام الصيدلية</p>
        </div>
      </div>

      {saved && (
        <div className="alert alert-success" role="alert">
          ✅ تم حفظ الإعدادات بنجاح
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'general' ? 'active' : ''}`} onClick={() => setActiveTab('general')}>🏢 عام</button>
        <button className={`tab ${activeTab === 'clinical' ? 'active' : ''}`} onClick={() => setActiveTab('clinical')}>🩺 سريري</button>
        <button className={`tab ${activeTab === 'inventory' ? 'active' : ''}`} onClick={() => setActiveTab('inventory')}>📦 مخزون</button>
        <button className={`tab ${activeTab === 'system' ? 'active' : ''}`} onClick={() => setActiveTab('system')}>⚙️ النظام</button>
      </div>

      <form onSubmit={handleSave}>
        {activeTab === 'general' && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">معلومات الصيدلية</h3>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">اسم الصيدلية</label>
                <input type="text" value={settings.pharmacy_name} onChange={(e) => updateField('pharmacy_name', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">رقم الترخيص</label>
                <input type="text" value={settings.pharmacy_license} onChange={(e) => updateField('pharmacy_license', e.target.value)} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">العنوان</label>
                <input type="text" value={settings.pharmacy_address} onChange={(e) => updateField('pharmacy_address', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">الهاتف</label>
                <input type="text" value={settings.pharmacy_phone} onChange={(e) => updateField('pharmacy_phone', e.target.value)} dir="ltr" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">الصيدلي المسؤول</label>
              <input type="text" value={settings.pharmacist_in_charge} onChange={(e) => updateField('pharmacist_in_charge', e.target.value)} />
            </div>
          </div>
        )}

        {activeTab === 'clinical' && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">الإعدادات السريرية</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={settings.auto_approve_prescriptions} onChange={(e) => updateField('auto_approve_prescriptions', e.target.checked)} style={{ width: 'auto' }} />
                <div>
                  <div style={{ fontWeight: 600 }}>موافقة تلقائية على الوصفات</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>اعتماد الوصفات تلقائياً بدون مراجعة يدوية</div>
                </div>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={settings.require_barcode_verification} onChange={(e) => updateField('require_barcode_verification', e.target.checked)} style={{ width: 'auto' }} />
                <div>
                  <div style={{ fontWeight: 600 }}>التحقق بالباركود إلزامي</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>وجوب مسح الباركود قبل صرف أي دواء</div>
                </div>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={settings.require_witness_for_controlled} onChange={(e) => updateField('require_witness_for_controlled', e.target.checked)} style={{ width: 'auto' }} />
                <div>
                  <div style={{ fontWeight: 600 }}>شاهد إلزامي للأدوية المخدرة</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>وجوب توقيع شاهد عند صرف الأدوية المخدرة</div>
                </div>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={settings.enable_interaction_checking} onChange={(e) => updateField('enable_interaction_checking', e.target.checked)} style={{ width: 'auto' }} />
                <div>
                  <div style={{ fontWeight: 600 }}>فحص التفاعلات الدوائية</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>تفعيل الفحص التلقائي للتفاعلات الدوائية عند الصرف</div>
                </div>
              </label>
            </div>
          </div>
        )}

        {activeTab === 'inventory' && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">إعدادات المخزون</h3>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">حد المخزون المنخفض الافتراضي</label>
                <input type="number" min={1} value={settings.low_stock_threshold} onChange={(e) => updateField('low_stock_threshold', parseInt(e.target.value) || 10)} />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>الحد الأدنى للمخزون قبل إصدار تنبيه</div>
              </div>
              <div className="form-group">
                <label className="form-label">أيام التحذير قبل انتهاء الصلاحية</label>
                <input type="number" min={1} value={settings.expiry_warning_days} onChange={(e) => updateField('expiry_warning_days', parseInt(e.target.value) || 30)} />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>عدد الأيام قبل انتهاء الصلاحية لبدء التحذير</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">إعدادات النظام</h3>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">اللغة</label>
                <select value={settings.language} onChange={(e) => updateField('language', e.target.value)}>
                  <option value="ar">العربية</option>
                  <option value="en">English</option>
                  <option value="ku">كوردی</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">المظهر</label>
                <select value={settings.theme} onChange={(e) => updateField('theme', e.target.value)}>
                  <option value="dark">داكن</option>
                  <option value="light">فاتح</option>
                  <option value="system">حسب النظام</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={settings.enable_offline_mode} onChange={(e) => updateField('enable_offline_mode', e.target.checked)} style={{ width: 'auto' }} />
                  <div>
                    <div style={{ fontWeight: 600 }}>وضع عدم الاتصال</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>السماح بالعمل عند انقطاع الإنترنت</div>
                  </div>
                </label>
              </div>
              <div className="form-group">
                <label className="form-label">فترة المزامنة التلقائية (دقائق)</label>
                <input type="number" min={1} max={60} value={settings.auto_sync_interval} onChange={(e) => updateField('auto_sync_interval', parseInt(e.target.value) || 5)} disabled={!settings.enable_offline_mode} />
              </div>
            </div>
            <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>معلومات النظام</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>الإصدار:</span>
                <span>2.1.0</span>
                <span style={{ color: 'var(--text-secondary)' }}>المنصة:</span>
                <span>GULA Pharmacy</span>
                <span style={{ color: 'var(--text-secondary)' }}>حالة التخزين المحلي:</span>
                <span>{typeof Storage !== 'undefined' ? 'متوفر ✅' : 'غير متوفر ❌'}</span>
                <span style={{ color: 'var(--text-secondary)' }}>المتصفح:</span>
                <span>{navigator.userAgent.substring(0, 60)}</span>
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button type="button" className="btn btn-secondary" onClick={() => window.location.reload()}>إعادة تعيين</button>
          <button type="submit" className="btn btn-primary btn-lg">💾 حفظ الإعدادات</button>
        </div>
      </form>
    </div>
  )
}
