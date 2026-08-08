import { apiGet, apiPost, apiPut, apiDelete } from './api'

export interface InventoryItem {
  id: string
  drug_code: string
  drug_name: string
  generic_name: string
  category: string
  dosage_form: string
  strength: string
  manufacturer: string
  supplier: string
  batch_number: string
  expiry_date: string
  quantity: number
  unit: string
  unit_cost: number
  selling_price: number
  reorder_level: number
  reorder_quantity: number
  location: string
  controlled: boolean
  schedule: string | null
  requires_prescription: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface InventoryMovement {
  id: string
  item_id: string
  type: 'received' | 'dispensed' | 'returned' | 'wasted' | 'adjusted' | 'transferred'
  quantity: number
  batch_number: string
  reference: string
  notes: string
  performed_by: string
  created_at: string
}

export interface StockAlert {
  id: string
  item_id: string
  drug_name: string
  alert_type: 'low_stock' | 'expiring' | 'expired' | 'overstock'
  current_quantity: number
  threshold: number
  expiry_date: string | null
  days_until_expiry: number | null
  created_at: string
}

export interface Supplier {
  id: string
  name: string
  contact_person: string
  phone: string
  email: string
  address: string
  is_active: boolean
}

export async function getInventory(params?: {
  search?: string
  category?: string
  controlled?: boolean
  low_stock?: boolean
  page?: number
  page_size?: number
}) {
  const query = new URLSearchParams()
  if (params?.search) query.set('search', params.search)
  if (params?.category) query.set('category', params.category)
  if (params?.controlled !== undefined) query.set('controlled', String(params.controlled))
  if (params?.low_stock) query.set('low_stock', 'true')
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))
  const qs = query.toString()
  return apiGet<{ items: InventoryItem[]; total: number; page: number; page_size: number }>(
    `/pharmacy/inventory${qs ? `?${qs}` : ''}`,
  )
}

export async function getInventoryItem(id: string) {
  return apiGet<InventoryItem>(`/pharmacy/inventory/${id}`)
}

export async function createInventoryItem(data: Partial<InventoryItem>) {
  return apiPost<InventoryItem>('/pharmacy/inventory', data)
}

export async function updateInventoryItem(id: string, data: Partial<InventoryItem>) {
  return apiPut<InventoryItem>(`/pharmacy/inventory/${id}`, data)
}

export async function deleteInventoryItem(id: string) {
  return apiDelete(`/pharmacy/inventory/${id}`)
}

export async function getStockAlerts() {
  return apiGet<{ alerts: StockAlert[] }>('/pharmacy/inventory/alerts')
}

export async function getMovements(
  itemId?: string,
  params?: { type?: string; page?: number; page_size?: number },
) {
  const query = new URLSearchParams()
  if (itemId) query.set('item_id', itemId)
  if (params?.type) query.set('type', params.type)
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))
  const qs = query.toString()
  return apiGet<{ movements: InventoryMovement[]; total: number }>(
    `/pharmacy/inventory/movements${qs ? `?${qs}` : ''}`,
  )
}

export async function adjustStock(
  itemId: string,
  data: { quantity: number; type: string; notes: string; reference?: string },
) {
  return apiPost<InventoryMovement>(`/pharmacy/inventory/${itemId}/adjust`, data)
}

export async function getSuppliers() {
  return apiGet<{ suppliers: Supplier[] }>('/pharmacy/suppliers')
}

export async function createSupplier(data: Partial<Supplier>) {
  return apiPost<Supplier>('/pharmacy/suppliers', data)
}

export async function getCategories() {
  return apiGet<{ categories: string[] }>('/pharmacy/inventory/categories')
}
