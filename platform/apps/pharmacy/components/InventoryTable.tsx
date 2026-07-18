import React, { useState, useMemo } from 'react'
import StockIndicator from './StockIndicator'
import type { InventoryItem } from '../services/inventory'

interface InventoryTableProps {
  items: InventoryItem[]
  onSelect?: (item: InventoryItem) => void
  onEdit?: (item: InventoryItem) => void
  onDelete?: (item: InventoryItem) => void
  page?: number
  pageSize?: number
  total?: number
  onPageChange?: (page: number) => void
  loading?: boolean
}

export default function InventoryTable({
  items,
  onSelect,
  onEdit,
  onDelete,
  page = 1,
  pageSize = 20,
  total = 0,
  onPageChange,
  loading = false,
}: InventoryTableProps) {
  const [sortField, setSortField] = useState<string>('drug_name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const totalPages = Math.ceil(total / pageSize)

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      const aVal = String((a as unknown as Record<string, unknown>)[sortField] ?? '')
      const bVal = String((b as unknown as Record<string, unknown>)[sortField] ?? '')
      return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    })
  }, [items, sortField, sortDir])

  function handleSort(field: string) {
    if (sortField === field) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  function renderSortIcon(field: string) {
    if (sortField !== field) return ' ⇅'
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="spinner" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table role="grid" aria-label="جدول المخزون">
          <thead>
            <tr>
              <th
                onClick={() => handleSort('drug_code')}
                style={{ cursor: 'pointer' }}
                aria-sort={
                  sortField === 'drug_code'
                    ? sortDir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                الكود{renderSortIcon('drug_code')}
              </th>
              <th
                onClick={() => handleSort('drug_name')}
                style={{ cursor: 'pointer' }}
                aria-sort={
                  sortField === 'drug_name'
                    ? sortDir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                الاسم{renderSortIcon('drug_name')}
              </th>
              <th
                onClick={() => handleSort('category')}
                style={{ cursor: 'pointer' }}
                aria-sort={
                  sortField === 'category'
                    ? sortDir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                الفئة{renderSortIcon('category')}
              </th>
              <th>الجرعة</th>
              <th>الدفعة</th>
              <th>تاريخ الانتهاء</th>
              <th
                onClick={() => handleSort('quantity')}
                style={{ cursor: 'pointer' }}
                aria-sort={
                  sortField === 'quantity'
                    ? sortDir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                المخزون{renderSortIcon('quantity')}
              </th>
              <th>الحالة</th>
              <th>الخيارات</th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  لا توجد أصناف في المخزون
                </td>
              </tr>
            ) : (
              sorted.map((item) => {
                const isExpiringSoon =
                  item.expiry_date &&
                  new Date(item.expiry_date) <
                    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
                const isExpired =
                  item.expiry_date && new Date(item.expiry_date) < new Date()
                return (
                  <tr
                    key={item.id}
                    onClick={() => onSelect?.(item)}
                    style={{
                      cursor: onSelect ? 'pointer' : 'default',
                      opacity: item.is_active ? 1 : 0.5,
                    }}
                    role="row"
                    aria-label={`${item.drug_name} - الكمية: ${item.quantity}`}
                  >
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {item.drug_code}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.drug_name}</div>
                      <div
                        style={{
                          fontSize: '0.7rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {item.generic_name}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-neutral">{item.category}</span>
                    </td>
                    <td>
                      {item.strength} {item.dosage_form}
                    </td>
                    <td style={{ fontSize: '0.8rem', fontFamily: 'monospace' }}>
                      {item.batch_number}
                    </td>
                    <td>
                      <span
                        style={{
                          color: isExpired
                            ? 'var(--accent-danger)'
                            : isExpiringSoon
                              ? 'var(--accent-warning)'
                              : 'var(--text-primary)',
                          fontWeight: isExpired || isExpiringSoon ? 700 : 400,
                        }}
                      >
                        {item.expiry_date
                          ? new Date(item.expiry_date).toLocaleDateString(
                              'ar-IQ',
                            )
                          : '-'}
                      </span>
                      {isExpired && (
                        <span className="badge badge-danger" style={{ marginRight: '0.5rem' }}>
                          منتهي
                        </span>
                      )}
                      {isExpiringSoon && !isExpired && (
                        <span className="badge badge-warning" style={{ marginRight: '0.5rem' }}>
                          وشيك
                        </span>
                      )}
                    </td>
                    <td>
                      <StockIndicator
                        current={item.quantity}
                        reorderLevel={item.reorder_level}
                        showLabel
                        size="sm"
                      />
                    </td>
                    <td>
                      {item.controlled && (
                        <span className="badge badge-danger">مخدر</span>
                      )}
                      {!item.controlled && item.quantity <= item.reorder_level && (
                        <span className="badge badge-warning">طلب</span>
                      )}
                      {!item.controlled &&
                        item.quantity > item.reorder_level && (
                          <span className="badge badge-success">متوفر</span>
                        )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        {onEdit && (
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              onEdit(item)
                            }}
                            aria-label={`تعديل ${item.drug_name}`}
                          >
                            ✏️
                          </button>
                        )}
                        {onDelete && (
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              onDelete(item)
                            }}
                            aria-label={`حذف ${item.drug_name}`}
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination" role="navigation" aria-label="تصفح الصفحات">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange?.(page - 1)}
            aria-label="الصفحة السابقة"
          >
            ‹
          </button>
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
            let p: number
            if (totalPages <= 7) {
              p = i + 1
            } else if (page <= 4) {
              p = i + 1
            } else if (page >= totalPages - 3) {
              p = totalPages - 6 + i
            } else {
              p = page - 3 + i
            }
            return (
              <button
                key={p}
                className={p === page ? 'active' : ''}
                onClick={() => onPageChange?.(p)}
                aria-label={`الصفحة ${p}`}
                aria-current={p === page ? 'page' : undefined}
              >
                {p}
              </button>
            )
          })}
          <button
            disabled={page >= totalPages}
            onClick={() => onPageChange?.(page + 1)}
            aria-label="الصفحة التالية"
          >
            ›
          </button>
        </div>
      )}

      <div
        style={{
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          marginTop: '0.5rem',
        }}
      >
        إجمالي {total} صنف - الصفحة {page} من {totalPages || 1}
      </div>
    </div>
  )
}
