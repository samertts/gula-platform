import React, { useState, useEffect } from 'react'
import { getInventory, getCategories, createInventoryItem, updateInventoryItem, deleteInventoryItem } from '../services/inventory'
import InventoryTable from '../components/InventoryTable'
import type { InventoryItem } from '../services/inventory'

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [controlledFilter, setControlledFilter] = useState<string>('')
  const [categories, setCategories] = useState<string[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null)
  const [formData, setFormData] = useState<Partial<InventoryItem>>({
    drug_code: '',
    drug_name: '',
    generic_name: '',
    category: '',
    dosage_form: '',
    strength: '',
    manufacturer: '',
    supplier: '',
    batch_number: '',
    expiry_date: '',
    quantity: 0,
    unit: 'حبة',
    unit_cost: 0,
    selling_price: 0,
    reorder_level: 10,
    reorder_quantity: 50,
    location: '',
    controlled: false,
    requires_prescription: true,
    is_active: true,
  })

  useEffect(() => {
    getCategories()
      .then((data) => setCategories(data.categories || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    loadInventory()
  }, [page, categoryFilter, controlledFilter])

  async function loadInventory() {
    setLoading(true)
    try {
      const data = await getInventory({
        search: search || undefined,
        category: categoryFilter || undefined,
        controlled: controlledFilter === 'controlled' ? true : controlledFilter === 'non_controlled' ? false : undefined,
        page,
        page_size: 20,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Failed to load inventory', err)
    } finally {
      setLoading(false)
    }
  }

  function handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    setSearch(e.target.value)
    setPage(1)
    const debounce = setTimeout(() => loadInventory(), 300)
    return () => clearTimeout(debounce)
  }

  function handleFormChange(field: string, value: unknown) {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      if (editingItem) {
        await updateInventoryItem(editingItem.id, formData)
      } else {
        await createInventoryItem(formData)
      }
      setShowForm(false)
      setEditingItem(null)
      resetForm()
      loadInventory()
    } catch (err) {
      console.error('Failed to save item', err)
    }
  }

  function handleEdit(item: InventoryItem) {
    setEditingItem(item)
    setFormData({ ...item })
    setShowForm(true)
  }

  async function handleDelete(item: InventoryItem) {
    if (window.confirm(`هل أنت متأكد من حذف ${item.drug_name}؟`)) {
      try {
        await deleteInventoryItem(item.id)
        loadInventory()
      } catch (err) {
        console.error('Failed to delete', err)
      }
    }
  }

  function resetForm() {
    setFormData({
      drug_code: '',
      drug_name: '',
      generic_name: '',
      category: '',
      dosage_form: '',
      strength: '',
      manufacturer: '',
      supplier: '',
      batch_number: '',
      expiry_date: '',
      quantity: 0,
      unit: 'حبة',
      unit_cost: 0,
      selling_price: 0,
      reorder_level: 10,
      reorder_quantity: 50,
      location: '',
      controlled: false,
      requires_prescription: true,
      is_active: true,
    })
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">إدارة المخزون</h1>
          <p className="page-subtitle">إجمالي {total} صنف</p>
        </div>
        <button className="btn btn-primary" onClick={() => { resetForm(); setEditingItem(null); setShowForm(true) }}>
          + إضافة صنف جديد
        </button>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="بحث باسم الدواء أو الكود..."
            value={search}
            onChange={handleSearch}
            aria-label="بحث في المخزون"
          />
        </div>
        <div className="filter-group">
          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1) }}
            aria-label="تصفية بالفئة"
          >
            <option value="">جميع الفئات</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <select
            value={controlledFilter}
            onChange={(e) => { setControlledFilter(e.target.value); setPage(1) }}
            aria-label="تصفية الأدوية المخدرة"
          >
            <option value="">الجميع</option>
            <option value="controlled">مخدرة</option>
            <option value="non_controlled">غير مخدرة</option>
          </select>
        </div>
      </div>

      <div className="card">
        <InventoryTable
          items={items}
          total={total}
          page={page}
          pageSize={20}
          onPageChange={setPage}
          onEdit={handleEdit}
          onDelete={handleDelete}
          loading={loading}
        />
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal" role="dialog" aria-modal="true" aria-label={editingItem ? 'تعديل صنف' : 'إضافة صنف جديد'}>
            <div className="modal-header">
              <h2 className="modal-title">{editingItem ? 'تعديل صنف' : 'إضافة صنف جديد'}</h2>
              <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">كود الدواء</label>
                  <input
                    type="text"
                    value={formData.drug_code || ''}
                    onChange={(e) => handleFormChange('drug_code', e.target.value)}
                    required
                    aria-label="كود الدواء"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">الاسم التجاري</label>
                  <input
                    type="text"
                    value={formData.drug_name || ''}
                    onChange={(e) => handleFormChange('drug_name', e.target.value)}
                    required
                    aria-label="الاسم التجاري"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">الاسم العلمي</label>
                  <input
                    type="text"
                    value={formData.generic_name || ''}
                    onChange={(e) => handleFormChange('generic_name', e.target.value)}
                    aria-label="الاسم العلمي"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">الفئة</label>
                  <select
                    value={formData.category || ''}
                    onChange={(e) => handleFormChange('category', e.target.value)}
                    aria-label="الفئة"
                  >
                    <option value="">اختر...</option>
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                    <option value="مضادات حيوية">مضادات حيوية</option>
                    <option value="مسكنات">مسكنات</option>
                    <option value="ضغط دم">ضغط دم</option>
                    <option value="سكري">سكري</option>
                    <option value="قلب">قلب</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">شكل الجرعة</label>
                  <input
                    type="text"
                    value={formData.dosage_form || ''}
                    onChange={(e) => handleFormChange('dosage_form', e.target.value)}
                    placeholder="أقراص / كبسول / شراب..."
                    aria-label="شكل الجرعة"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">التركيز</label>
                  <input
                    type="text"
                    value={formData.strength || ''}
                    onChange={(e) => handleFormChange('strength', e.target.value)}
                    placeholder="مثال: 500mg"
                    aria-label="التركيز"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">الشركة المصنعة</label>
                  <input
                    type="text"
                    value={formData.manufacturer || ''}
                    onChange={(e) => handleFormChange('manufacturer', e.target.value)}
                    aria-label="الشركة المصنعة"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">المورد</label>
                  <input
                    type="text"
                    value={formData.supplier || ''}
                    onChange={(e) => handleFormChange('supplier', e.target.value)}
                    aria-label="المورد"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">رقم الدفعة</label>
                  <input
                    type="text"
                    value={formData.batch_number || ''}
                    onChange={(e) => handleFormChange('batch_number', e.target.value)}
                    aria-label="رقم الدفعة"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">تاريخ الانتهاء</label>
                  <input
                    type="date"
                    value={formData.expiry_date || ''}
                    onChange={(e) => handleFormChange('expiry_date', e.target.value)}
                    aria-label="تاريخ الانتهاء"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">الكمية</label>
                  <input
                    type="number"
                    min={0}
                    value={formData.quantity || 0}
                    onChange={(e) => handleFormChange('quantity', parseInt(e.target.value) || 0)}
                    aria-label="الكمية"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">الوحدة</label>
                  <select
                    value={formData.unit || 'حبة'}
                    onChange={(e) => handleFormChange('unit', e.target.value)}
                    aria-label="الوحدة"
                  >
                    <option value="حبة">حبة</option>
                    <option value="علبة">علبة</option>
                    <option value="زجاجة">زجاجة</option>
                    <option value="مل">مل</option>
                    <option value="مجم">مجم</option>
                    <option value="أمبولة">أمبولة</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">سعر التكلفة</label>
                  <input
                    type="number"
                    min={0}
                    step={0.001}
                    value={formData.unit_cost || 0}
                    onChange={(e) => handleFormChange('unit_cost', parseFloat(e.target.value) || 0)}
                    aria-label="سعر التكلفة"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">سعر البيع</label>
                  <input
                    type="number"
                    min={0}
                    step={0.001}
                    value={formData.selling_price || 0}
                    onChange={(e) => handleFormChange('selling_price', parseFloat(e.target.value) || 0)}
                    aria-label="سعر البيع"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">حد إعادة الطلب</label>
                  <input
                    type="number"
                    min={1}
                    value={formData.reorder_level || 10}
                    onChange={(e) => handleFormChange('reorder_level', parseInt(e.target.value) || 10)}
                    aria-label="حد إعادة الطلب"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">كمية إعادة الطلب</label>
                  <input
                    type="number"
                    min={1}
                    value={formData.reorder_quantity || 50}
                    onChange={(e) => handleFormChange('reorder_quantity', parseInt(e.target.value) || 50)}
                    aria-label="كمية إعادة الطلب"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">موقع التخزين</label>
                <input
                  type="text"
                  value={formData.location || ''}
                  onChange={(e) => handleFormChange('location', e.target.value)}
                  placeholder="مثال: رف A-12"
                  aria-label="موقع التخزين"
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.controlled || false}
                    onChange={(e) => handleFormChange('controlled', e.target.checked)}
                    style={{ width: 'auto' }}
                  />
                  دواء مخدر / خاضع للرقابة
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.requires_prescription !== false}
                    onChange={(e) => handleFormChange('requires_prescription', e.target.checked)}
                    style={{ width: 'auto' }}
                  />
                  يتطلب وصفة طبية
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.is_active !== false}
                    onChange={(e) => handleFormChange('is_active', e.target.checked)}
                    style={{ width: 'auto' }}
                  />
                  نشط
                </label>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>
                  إلغاء
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingItem ? 'حفظ التعديلات' : 'إضافة الصنف'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
