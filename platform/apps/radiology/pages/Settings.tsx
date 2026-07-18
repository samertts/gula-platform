import { useState, useCallback } from 'react'

type UserPreferences = {
  language: 'ar' | 'en'
  theme: 'dark' | 'light'
  default_view: 'dashboard' | 'worklist' | 'reports'
  items_per_page: number
  auto_refresh_seconds: number
  default_modality: string
  show_ai_annotations: boolean
  show_dicom_overlays: boolean
  enable_keyboard_shortcuts: boolean
  default_window_width: number
  default_window_center: number
  measurement_unit: 'metric' | 'imperial'
  report_font_size: 'small' | 'medium' | 'large'
  signature_on_report: boolean
  notify_on_critical: boolean
  notify_on_new_study: boolean
  email_notifications: boolean
  sms_notifications: boolean
}

const DEFAULT_PREFERENCES: UserPreferences = {
  language: 'ar',
  theme: 'dark',
  default_view: 'worklist',
  items_per_page: 25,
  auto_refresh_seconds: 30,
  default_modality: 'CT',
  show_ai_annotations: true,
  show_dicom_overlays: true,
  enable_keyboard_shortcuts: true,
  default_window_width: 256,
  default_window_center: 128,
  measurement_unit: 'metric',
  report_font_size: 'medium',
  signature_on_report: true,
  notify_on_critical: true,
  notify_on_new_study: false,
  email_notifications: true,
  sms_notifications: false
}

type Shortcut = {
  key: string
  label: string
  description: string
  category: 'viewer' | 'navigation' | 'reporting'
}

const SHORTCUTS: Shortcut[] = [
  { key: 'W', label: 'W', description: 'أداة النافذة/المستوى', category: 'viewer' },
  { key: 'P', label: 'P', description: 'أداة التحريك', category: 'viewer' },
  { key: 'Z', label: 'Z', description: 'أداة التكبير', category: 'viewer' },
  { key: 'M', label: 'M', description: 'أداة القياس', category: 'viewer' },
  { key: 'R', label: 'R', description: 'تدوير الصورة', category: 'viewer' },
  { key: 'I', label: 'I', description: 'عكس الألوان', category: 'viewer' },
  { key: '←', label: '→', description: 'الصورة السابقة/التالية', category: 'viewer' },
  { key: 'Ctrl+S', label: 'Ctrl+S', description: 'حفظ التقرير', category: 'reporting' },
  { key: 'Ctrl+Enter', label: 'Ctrl+Enter', description: 'تقديم التقرير', category: 'reporting' },
  { key: 'F', label: 'F', description: 'شاشة كاملة', category: 'viewer' },
  { key: '?', label: '?', description: 'عرض اختصارات لوحة المفاتيح', category: 'viewer' }
]

export function Settings() {
  const [prefs, setPrefs] = useState<UserPreferences>(() => {
    try {
      const stored = localStorage.getItem('gula_radiology_preferences')
      return stored ? { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) } : DEFAULT_PREFERENCES
    } catch {
      return DEFAULT_PREFERENCES
    }
  })
  const [saved, setSaved] = useState(false)
  const [activeSection, setActiveSection] = useState<'preferences' | 'shortcuts'>('preferences')

  const savePreferences = useCallback((newPrefs: UserPreferences) => {
    setPrefs(newPrefs)
    localStorage.setItem('gula_radiology_preferences', JSON.stringify(newPrefs))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)

    // Apply theme
    document.documentElement.setAttribute('data-theme', newPrefs.theme)
  }, [])

  const updatePreference = useCallback(<K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    const newPrefs = { ...prefs, [key]: value }
    savePreferences(newPrefs)
  }, [prefs, savePreferences])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>الإعدادات</h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
          تخصيص إعدادات المستخدم وتفضيلات النظام
        </p>
      </div>

      {/* Save notification */}
      {saved && (
        <div style={{
          padding: 12,
          backgroundColor: 'rgba(34,197,94,0.1)',
          border: '1px solid var(--border-success)',
          borderRadius: 8,
          color: 'var(--text-success)',
          fontSize: '0.875rem',
          textAlign: 'center'
        }}>
          ✅ تم حفظ الإعدادات بنجاح
        </div>
      )}

      {/* Sections */}
      <div className="tabs">
        <button className={`tab ${activeSection === 'preferences' ? 'active' : ''}`} onClick={() => setActiveSection('preferences')}>
          🎨 التفضيلات
        </button>
        <button className={`tab ${activeSection === 'shortcuts' ? 'active' : ''}`} onClick={() => setActiveSection('shortcuts')}>
          ⌨️ اختصارات لوحة المفاتيح
        </button>
      </div>

      {activeSection === 'preferences' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">تفضيلات المستخدم</h2>
            <button className="btn btn-sm btn-secondary" onClick={() => savePreferences(DEFAULT_PREFERENCES)}>
              استعادة الإعدادات الافتراضية
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Appearance */}
            <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
              <legend style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
                المظهر
              </legend>
              <div className="grid grid-2">
                <div className="input-group">
                  <label className="input-label">السمة</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      className={`btn ${prefs.theme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => updatePreference('theme', 'dark')}
                      style={{ flex: 1 }}
                    >
                      🌙 داكن
                    </button>
                    <button
                      className={`btn ${prefs.theme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => updatePreference('theme', 'light')}
                      style={{ flex: 1 }}
                    >
                      ☀️ فاتح
                    </button>
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">اللغة</label>
                  <select
                    className="select"
                    value={prefs.language}
                    onChange={e => updatePreference('language', e.target.value as 'ar' | 'en')}
                  >
                    <option value="ar">العربية</option>
                    <option value="en">English</option>
                  </select>
                </div>
              </div>
            </fieldset>

            {/* Viewer */}
            <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
              <legend style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
                عارض الصور
              </legend>
              <div className="grid grid-2">
                <div className="input-group">
                  <label className="input-label">عرض النافذة الافتراضي (WW)</label>
                  <input
                    type="number"
                    className="input"
                    value={prefs.default_window_width}
                    onChange={e => updatePreference('default_window_width', Number(e.target.value))}
                    min={1}
                    max={4096}
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">مستوى النافذة الافتراضي (WC)</label>
                  <input
                    type="number"
                    className="input"
                    value={prefs.default_window_center}
                    onChange={e => updatePreference('default_window_center', Number(e.target.value))}
                    min={-1024}
                    max={4096}
                  />
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.show_ai_annotations}
                    onChange={e => updatePreference('show_ai_annotations', e.target.checked)}
                  />
                  إظهار تعليقات الذكاء الاصطناعي
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.show_dicom_overlays}
                    onChange={e => updatePreference('show_dicom_overlays', e.target.checked)}
                  />
                  إظهار بيانات DICOM على الصورة
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.enable_keyboard_shortcuts}
                    onChange={e => updatePreference('enable_keyboard_shortcuts', e.target.checked)}
                  />
                  تفعيل اختصارات لوحة المفاتيح
                </label>
              </div>
            </fieldset>

            {/* Worklist */}
            <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
              <legend style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
                قائمة العمل
              </legend>
              <div className="grid grid-2">
                <div className="input-group">
                  <label className="input-label">الصفحة الافتراضية</label>
                  <select
                    className="select"
                    value={prefs.default_view}
                    onChange={e => updatePreference('default_view', e.target.value as UserPreferences['default_view'])}
                  >
                    <option value="dashboard">لوحة التحكم</option>
                    <option value="worklist">قائمة العمل</option>
                    <option value="reports">التقارير</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">عدد العناصر في الصفحة</label>
                  <select
                    className="select"
                    value={prefs.items_per_page}
                    onChange={e => updatePreference('items_per_page', Number(e.target.value))}
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">التحديث التلقائي (ثانية)</label>
                  <input
                    type="number"
                    className="input"
                    value={prefs.auto_refresh_seconds}
                    onChange={e => updatePreference('auto_refresh_seconds', Number(e.target.value))}
                    min={5}
                    max={300}
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">الجهاز الافتراضي</label>
                  <select
                    className="select"
                    value={prefs.default_modality}
                    onChange={e => updatePreference('default_modality', e.target.value)}
                  >
                    {['CT', 'MR', 'US', 'XA', 'CR', 'DX', 'MG', 'NM', 'PT'].map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>
            </fieldset>

            {/* Reporting */}
            <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
              <legend style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
                التقارير
              </legend>
              <div className="grid grid-2">
                <div className="input-group">
                  <label className="input-label">حجم الخط في التقرير</label>
                  <select
                    className="select"
                    value={prefs.report_font_size}
                    onChange={e => updatePreference('report_font_size', e.target.value as UserPreferences['report_font_size'])}
                  >
                    <option value="small">صغير</option>
                    <option value="medium">متوسط</option>
                    <option value="large">كبير</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">وحدة القياس</label>
                  <select
                    className="select"
                    value={prefs.measurement_unit}
                    onChange={e => updatePreference('measurement_unit', e.target.value as 'metric' | 'imperial')}
                  >
                    <option value="metric">متري (سم، مم)</option>
                    <option value="imperial">إمبراطوري (إنش)</option>
                  </select>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.signature_on_report}
                    onChange={e => updatePreference('signature_on_report', e.target.checked)}
                  />
                  إضافة توقيع إلكتروني للتقرير
                </label>
              </div>
            </fieldset>

            {/* Notifications */}
            <fieldset style={{ border: '1px solid var(--border-primary)', borderRadius: 8, padding: 16 }}>
              <legend style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 8px', color: 'var(--text-secondary)' }}>
                الإشعارات
              </legend>
              <div className="grid grid-2">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.notify_on_critical}
                    onChange={e => updatePreference('notify_on_critical', e.target.checked)}
                  />
                  إشعار عند وجود نتائج حرجة
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.notify_on_new_study}
                    onChange={e => updatePreference('notify_on_new_study', e.target.checked)}
                  />
                  إشعار عند وصول دراسة جديدة
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.email_notifications}
                    onChange={e => updatePreference('email_notifications', e.target.checked)}
                  />
                  إشعارات البريد الإلكتروني
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={prefs.sms_notifications}
                    onChange={e => updatePreference('sms_notifications', e.target.checked)}
                  />
                  إشعارات الرسائل النصية
                </label>
              </div>
            </fieldset>
          </div>
        </div>
      )}

      {activeSection === 'shortcuts' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">اختصارات لوحة المفاتيح</h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
              اضغط ? في عارض الصور لعرض الاختصارات
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {(['viewer', 'navigation', 'reporting'] as const).map(category => {
              const catShortcuts = SHORTCUTS.filter(s => s.category === category)
              const catLabels: Record<string, string> = {
                viewer: 'عارض الصور',
                navigation: 'التنقل',
                reporting: 'التقارير'
              }
              return (
                <div key={category}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                    {catLabels[category]}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {catShortcuts.map(shortcut => (
                      <div key={shortcut.key} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 16,
                        padding: '8px 12px',
                        backgroundColor: 'var(--bg-tertiary)',
                        borderRadius: 6
                      }}>
                        <kbd style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4px 10px',
                          backgroundColor: 'var(--bg-card)',
                          border: '1px solid var(--border-primary)',
                          borderRadius: 4,
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          minWidth: 60,
                          boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                        }}>
                          {shortcut.label}
                        </kbd>
                        <span style={{ fontSize: '0.85rem' }}>{shortcut.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
