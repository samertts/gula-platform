import React, { useState, useEffect, useRef, useCallback } from 'react'
import { searchDrugs, getDrugInfo } from '../services/interactions'
import type { DrugInfo } from '../services/interactions'

interface DrugSearchProps {
  onSelect: (drug: DrugInfo) => void
  selectedDrugs?: DrugInfo[]
  placeholder?: string
  autoFocus?: boolean
}

export default function DrugSearch({
  onSelect,
  selectedDrugs = [],
  placeholder = 'ابحث عن دواء...',
  autoFocus = false,
}: DrugSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<DrugInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState(false)
  const [selected, setSelected] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const search = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const data = await searchDrugs(q)
      setResults(data.drugs || [])
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(query), 250)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, search])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setFocused(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleSelect(drug: DrugInfo) {
    if (selectedDrugs.find((d) => d.drug_code === drug.drug_code)) return
    onSelect(drug)
    setQuery('')
    setResults([])
    setFocused(false)
    inputRef.current?.focus()
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelected((prev) => Math.min(prev + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelected((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && selected >= 0 && results[selected]) {
      e.preventDefault()
      handleSelect(results[selected])
    } else if (e.key === 'Escape') {
      setFocused(false)
      inputRef.current?.blur()
    }
  }

  const isSelected = (drugCode: string) =>
    selectedDrugs.some((d) => d.drug_code === drugCode)

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <div className="form-group" style={{ margin: 0 }}>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setSelected(-1)
            setFocused(true)
          }}
          onFocus={() => setFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
          role="combobox"
          aria-expanded={focused && results.length > 0}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          aria-label="بحث عن دواء"
        />
        {loading && (
          <span
            style={{
              position: 'absolute',
              left: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
            }}
          >
            <span className="spinner" />
          </span>
        )}
      </div>

      {focused && results.length > 0 && (
        <div
          role="listbox"
          aria-label="نتائج البحث"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 50,
            marginTop: '4px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            maxHeight: '300px',
            overflowY: 'auto',
            boxShadow: 'var(--shadow-lg)',
          }}
        >
          {results.map((drug, idx) => {
            const alreadySelected = isSelected(drug.drug_code)
            return (
              <button
                key={drug.drug_code}
                role="option"
                aria-selected={idx === selected}
                style={{
                  width: '100%',
                  textAlign: 'right',
                  padding: '0.625rem 0.875rem',
                  background:
                    idx === selected
                      ? 'var(--bg-hover)'
                      : 'transparent',
                  color: 'var(--text-primary)',
                  borderBottom: '1px solid var(--border-color)',
                  cursor: alreadySelected ? 'not-allowed' : 'pointer',
                  opacity: alreadySelected ? 0.5 : 1,
                }}
                onClick={() => !alreadySelected && handleSelect(drug)}
                onMouseEnter={() => setSelected(idx)}
              >
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                  {drug.drug_name}
                </div>
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-secondary)',
                    marginTop: '2px',
                  }}
                >
                  {drug.generic_name} - {drug.drug_class}
                  {alreadySelected && ' ✓'}
                </div>
              </button>
            )
          })}
        </div>
      )}

      {focused && query.length >= 2 && results.length === 0 && !loading && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 50,
            marginTop: '4px',
            padding: '1rem',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.875rem',
          }}
        >
          لا توجد نتائج
        </div>
      )}
    </div>
  )
}
