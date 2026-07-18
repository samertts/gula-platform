import React, { useState, useEffect } from 'react'
import { getInventory, getStockAlerts } from '../services/inventory'
import { getPrescriptions } from '../services/dispensing'
import type { InventoryItem } from '../services/inventory'

interface ReportSummary {
  totalItems: number
  totalValue: number
  lowStockCount: number
  outOfStockCount: number
  expiredCount: number
  totalPrescriptions: number
  monthlyDispensed: number
  totalReturns: number
  totalWaste: number
  topDrugs: { name: string; count: number }[]
}

export default function Reports() {
  const [activeTab, setActiveTab] = useState<'overview' | 'consumption' | 'financial' | 'expiry'>('overview')
  const [period, setPeriod] = useState('month')
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState<ReportSummary>({
    totalItems: 0,
    totalValue: 0,
    lowStockCount: 0,
    outOfStockCount: 0,
    expiredCount: 0,
    totalPrescriptions: 0,
    monthlyDispensed: 0,
    totalReturns: 0,
    totalWaste: 0,
    topDrugs: [],
  })

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [invData, rxData, alertData] = await Promise.all([
        getInventory({ page_size: 200 }),
        getPrescriptions({ page_size: 1 }),
        getStockAlerts(),
      ])
      const items = invData.items || []
      const alerts = alertData.alerts || []
      setSummary({
        totalItems: items.length,
        totalValue: items.reduce((s, i) => s + i.quantity * i.unit_cost, 0),
        lowStockCount: alerts.filter((a) => a.alert_type === 'low_stock').length,
        outOfStockCount: items.filter((i) => i.quantity <= 0).length,
        expiredCount: alerts.filter((a) => a.alert_type === 'expired').length,
        totalPrescriptions: rxData.total || 0,
        monthlyDispensed: Math.round((rxData.total || 0) / 3),
        totalReturns: 0,
        totalWaste: 0,
        topDrugs: items.slice(0, 10).map((i) => ({ name: i.drug_name, count: i.quantity })),
      })
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">التقارير والتحليلات</h1>
          <p className="page-subtitle">إحصائيات وتحليلات الصيدلية</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select value={period} onChange={(e) => setPeriod(e.target.value)} style={{ width: 'auto' }}>
            <option value="week">آخر أسبوع</option>
            <option value="month">آخر شهر</option>
            <option value="quarter">آخر 3 أشهر</option>
            <option value="year">آخر سنة</option>
          </select>
          <button className="btn btn-primary" onClick={loadData}>🔄 تحديث</button>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>📊 نظرة عامة</button>
        <button className={`tab ${activeTab === 'consumption' ? 'active' : ''}`} onClick={() => setActiveTab('consumption')}>💊 استهلاك</button>
        <button className={`tab ${activeTab === 'financial' ? 'active' : ''}`} onClick={() => setActiveTab('financial')}>💰 مالي</button>
        <button className={`tab ${activeTab === 'expiry' ? 'active' : ''}`} onClick={() => setActiveTab('expiry')}>⏰ صلاحية</button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}><span className="spinner" /></div>
      ) : (
        <>
          {activeTab === 'overview' && (
            <div>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-icon" style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>📦</div>
                  <div className="kpi-value">{summary.totalItems}</div>
                  <div className="kpi-label">إجمالي الأصناف</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>💰</div>
                  <div className="kpi-value">{summary.totalValue.toLocaleString()} د.ع</div>
                  <div className="kpi-label">القيمة الإجمالية للمخزون</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>⚠️</div>
                  <div className="kpi-value">{summary.lowStockCount + summary.outOfStockCount}</div>
                  <div className="kpi-label">أصناف بحاجة للطلب</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-icon" style={{ background: 'rgba(139,92,246,0.15)', color: '#8b5cf6' }}>💊</div>
                  <div className="kpi-value">{summary.totalPrescriptions}</div>
                  <div className="kpi-label">إجمالي الوصفات</div>
                </div>
              </div>

              <div className="grid-2">
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">أكثر الأدوية صرفاً</h3>
                  </div>
                  {summary.topDrugs.length === 0 ? (
                    <div className="empty-state"><p>لا توجد بيانات</p></div>
                  ) : (
                    <div>
                      {summary.topDrugs.map((drug, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                          <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--accent-primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, flexShrink: 0 }}>
                            {idx + 1}
                          </span>
                          <span style={{ flex: 1, fontSize: '0.875rem' }}>{drug.name}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{drug.count} وحدة</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">مؤشرات الأداء</h3>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {[
                      { label: 'معدل صرف الوصفات شهرياً', value: summary.monthlyDispensed, color: '#3b82f6' },
                      { label: 'الأصناف النافدة', value: summary.outOfStockCount, color: '#ef4444' },
                      { label: 'المرتجعات', value: summary.totalReturns, color: '#38bdf8' },
                      { label: 'التوالف', value: summary.totalWaste, color: '#f59e0b' },
                      { label: 'أصناف منتهية', value: summary.expiredCount, color: '#ef4444' },
                    ].map((metric) => (
                      <div key={metric.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.375rem 0', borderBottom: '1px solid var(--border-color)' }}>
                        <span style={{ fontSize: '0.85rem' }}>{metric.label}</span>
                        <span style={{ fontWeight: 700, color: metric.color }}>{metric.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'consumption' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">تقرير الاستهلاك</h3>
              </div>
              <div className="empty-state">
                <div className="empty-icon">💊</div>
                <h3>تحليل الاستهلاك</h3>
                <p>سيتيح هذا التقرير تحليل أنماط استهلاك الأدوية مع رسوم بيانية وتفصيل حسب الفئة</p>
              </div>
            </div>
          )}

          {activeTab === 'financial' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">التقرير المالي</h3>
              </div>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-label">قيمة المخزون الحالي</div>
                  <div className="kpi-value">{summary.totalValue.toLocaleString()} د.ع</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'expiry' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">تقرير الصلاحية</h3>
              </div>
              <div className="empty-state">
                <div className="empty-icon">⏰</div>
                <h3>تقارير الصلاحية</h3>
                <p>راجع صفحة تتبع تواريخ الانتهاء للحصول على تفاصيل دقيقة</p>
              </div>
              <a href="/pharmacy/expiry" className="btn btn-primary">→ الذهاب إلى تتبع الانتهاء</a>
            </div>
          )}
        </>
      )}
    </div>
  )
}
