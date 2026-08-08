import { useState } from 'react'
import type { Modality } from '@services/dicom'

type UserRole = 'radiologist' | 'technician' | 'admin' | 'scheduler' | 'viewer'

type RadUser = {
  id: string
  username: string
  full_name: string
  email: string
  role: UserRole
  specialization?: string
  license_number?: string
  is_active: boolean
  last_login?: string
  created_at: string
}

type DicomNode = {
  id: string
  name: string
  host: string
  port: number
  ae_title: string
  type: 'PACS' | 'MWL' | 'MPPS' | 'STORAGE'
  modality?: Modality
  is_connected: boolean
  last_heartbeat?: string
}

type SystemSetting = {
  key: string
  label: string
  value: string
  category: 'general' | 'dicom' | 'worklist' | 'reporting' | 'integrations'
  description: string
}

const USERS: RadUser[] = [
  { id: 'u1', username: 'drahmed', full_name: 'د. أحمد محمد', email: 'ahmed@gula.health', role: 'radiologist', specialization: 'أشعة تشخيصية', license_number: 'LIC-001', is_active: true, last_login: '2026-07-16 08:30', created_at: '2025-06-01' },
  { id: 'u2', username: 'saraali', full_name: 'د. سارة علي', email: 'sara@gula.health', role: 'radiologist', specialization: 'أشعة تداخلية', license_number: 'LIC-002', is_active: true, last_login: '2026-07-15 14:00', created_at: '2025-06-15' },
  { id: 'u3', username: 'tech_khalid', full_name: 'خالد عمر', email: 'khalid@gula.health', role: 'technician', is_active: true, last_login: '2026-07-16 07:45', created_at: '2025-07-01' },
  { id: 'u4', username: 'admin_noor', full_name: 'نور حسن', email: 'noor@gula.health', role: 'admin', is_active: true, last_login: '2026-07-16 09:00', created_at: '2025-05-01' }
]

const DICOM_NODES: DicomNode[] = [
  { id: 'n1', name: 'PACS الرئيسي', host: 'pacs.gula.local', port: 11112, ae_title: 'GULA_PACS', type: 'PACS', is_connected: true, last_heartbeat: '2026-07-16 09:15' },
  { id: 'n2', name: 'MWL - CT 1', host: 'ct1.gula.local', port: 11113, ae_title: 'CT1_MWL', type: 'MWL', modality: 'CT', is_connected: true, last_heartbeat: '2026-07-16 09:14' },
  { id: 'n3', name: 'MWL - MRI 1', host: 'mri1.gula.local', port: 11114, ae_title: 'MRI1_MWL', type: 'MWL', modality: 'MR', is_connected: false, last_heartbeat: '2026-07-15 22:00' },
  { id: 'n4', name: 'تخزين احتياطي', host: 'storage.gula.local', port: 11115, ae_title: 'GULA_STORE', type: 'STORAGE', is_connected: true, last_heartbeat: '2026-07-16 09:10' }
]

const SETTINGS: SystemSetting[] = [
  { key: 'site_name', label: 'اسم الموقع', value: 'مستشفى GULA', category: 'general', description: 'اسم مركز الأشعة' },
  { key: 'default_modality', label: 'الجهاز الافتراضي', value: 'CT', category: 'general', description: 'الجهاز الافتراضي للفحوصات الجديدة' },
  { key: 'auto_assign_worklist', label: 'توزيع تلقائي لقائمة العمل', value: 'true', category: 'worklist', description: 'توزيع الفحوصات تلقائياً على الأجهزة' },
  { key: 'worklist_refresh_seconds', label: 'تحديث قائمة العمل (ثانية)', value: '30', category: 'worklist', description: 'فترة التحديث التلقائي لقائمة العمل' },
  { key: 'critical_finding_notify', label: 'إشعار النتائج الحرجة', value: 'email,sms', category: 'reporting', description: 'طرق إشعار النتائج الحرجة' },
  { key: 'auto_save_draft_seconds', label: 'حفظ تلقائي للمسودات (ثانية)', value: '60', category: 'reporting', description: 'حفظ التقرير تلقائياً كل فترة' },
  { key: 'wado_port', label: 'منفذ WADO-RS', value: '8042', category: 'dicom', description: 'منفذ خدمة WADO-RS' },
  { key: 'qido_max_results', label: 'الحد الأقصى لنتائج QIDO-RS', value: '100', category: 'dicom', description: 'الحد الأقصى لنتائج البحث' }
]

const ROLE_CONFIG: Record<UserRole, { label: string; color: string }> = {
  radiologist: { label: 'طبيب أشعة', color: '#3b82f6' },
  technician: { label: 'فني أشعة', color: '#22c55e' },
  admin: { label: 'مدير نظام', color: '#8b5cf6' },
  scheduler: { label: 'منسق مواعيد', color: '#f59e0b' },
  viewer: { label: 'مشاهد', color: '#94a3b8' }
}

export function Admin() {
  const [activeTab, setActiveTab] = useState<'users' | 'dicom' | 'aetitles' | 'settings'>('users')
  const [users] = useState<RadUser[]>(USERS)
  const [nodes] = useState<DicomNode[]>(DICOM_NODES)
  const [settings] = useState<SystemSetting[]>(SETTINGS)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>إدارة النظام</h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>إدارة مستخدمي النظام وإعدادات RIS</p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>👥 المستخدمين</button>
        <button className={`tab ${activeTab === 'dicom' ? 'active' : ''}`} onClick={() => setActiveTab('dicom')}>🖥️ عقد DICOM</button>
        <button className={`tab ${activeTab === 'aetitles' ? 'active' : ''}`} onClick={() => setActiveTab('aetitles')}>🔗 AE Titles</button>
        <button className={`tab ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>⚙️ الإعدادات</button>
      </div>

      {activeTab === 'users' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary">+ مستخدم جديد</button>
          </div>
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>اسم المستخدم</th>
                  <th>البريد</th>
                  <th>الدور</th>
                  <th>الحالة</th>
                  <th>آخر دخول</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id}>
                    <td style={{ fontWeight: 500 }}>{user.full_name}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>{user.username}</td>
                    <td style={{ fontSize: '0.8rem' }}>{user.email}</td>
                    <td>
                      <span className="badge" style={{
                        backgroundColor: `${ROLE_CONFIG[user.role]?.color}20`,
                        color: ROLE_CONFIG[user.role]?.color
                      }}>
                        {ROLE_CONFIG[user.role]?.label || user.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${user.is_active ? 'badge-success' : 'badge-neutral'}`}>
                        {user.is_active ? 'نشط' : 'غير نشط'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem' }}>{user.last_login || '—'}</td>
                    <td>
                      <button className="btn btn-sm btn-ghost">✏️</button>
                      <button className="btn btn-sm btn-ghost" style={{ color: 'var(--text-danger)' }}>✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'dicom' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary">+ إضافة عقدة</button>
          </div>
          <div className="grid grid-2">
            {nodes.map(node => (
              <div key={node.id} className="card" style={{
                borderColor: node.is_connected ? 'var(--border-success)' : 'var(--border-danger)',
                borderInlineStart: `4px solid ${node.is_connected ? 'var(--accent-success)' : 'var(--accent-danger)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>{node.name}</h3>
                  <span style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: node.is_connected ? 'var(--accent-success)' : 'var(--accent-danger)',
                    display: 'inline-block'
                  }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.8rem' }}>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>AE Title:</span> {node.ae_title}</div>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>النوع:</span> {node.type}</div>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>العنوان:</span> {node.host}:{node.port}</div>
                  {node.modality && <div><span style={{ color: 'var(--text-tertiary)' }}>الجهاز:</span> {node.modality}</div>}
                </div>
                {node.last_heartbeat && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 8 }}>
                    آخر اتصال: {node.last_heartbeat}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'aetitles' && (
        <div className="card">
          <p style={{ color: 'var(--text-tertiary)', textAlign: 'center' }}>
            إدارة AE Titles قادمة في التحديث القادم
          </p>
        </div>
      )}

      {activeTab === 'settings' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {(['general', 'dicom', 'worklist', 'reporting'] as const).map(category => {
            const catSettings = settings.filter(s => s.category === category)
            const catLabels: Record<string, string> = {
              general: 'إعدادات عامة',
              dicom: 'إعدادات DICOM',
              worklist: 'إعدادات قائمة العمل',
              reporting: 'إعدادات التقارير'
            }
            return (
              <div key={category} className="card">
                <div className="card-header">
                  <h3 className="card-title" style={{ fontSize: '0.95rem' }}>{catLabels[category]}</h3>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {catSettings.map(setting => (
                    <div key={setting.key} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <div style={{ flex: 1 }}>
                        <label className="input-label">{setting.label}</label>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{setting.description}</p>
                      </div>
                      <input
                        className="input"
                        value={setting.value}
                        onChange={() => {}}
                        style={{ width: 200, textAlign: 'start' }}
                      />
                      <button className="btn btn-sm btn-ghost">💾</button>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
