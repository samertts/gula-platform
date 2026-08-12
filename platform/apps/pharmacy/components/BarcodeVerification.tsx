import React, { useState, useEffect, useRef } from 'react'

interface BarcodeVerificationProps {
  expectedPatient?: string
  expectedDrug?: string
  expectedDose?: string
  expectedRoute?: string
  onVerified: (result: VerificationResult) => void
  onCancel: () => void
  patientName?: string
  drugName?: string
}

export interface VerificationResult {
  patient_match: boolean
  drug_match: boolean
  dose_match: boolean
  route_match: boolean
  time_match: boolean
  all_match: boolean
  scanned_data: Record<string, string>
}

type RightStatus = 'pending' | 'success' | 'fail'

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

function normalizeScannedValue(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, ' ')
}

interface RightCheck {
  key: string
  label: string
  expected: string
  scanned: string
  status: RightStatus
}

export default function BarcodeVerification({
  expectedPatient,
  expectedDrug,
  expectedDose,
  expectedRoute,
  onVerified,
  onCancel,
  patientName,
  drugName,
}: BarcodeVerificationProps) {
  const [scanning, setScanning] = useState(true)
  const [scannedCode, setScannedCode] = useState('')
  const [scannedData, setScannedData] = useState<Record<string, string>>({})
  const [rights, setRights] = useState<RightCheck[]>([
    { key: 'patient', label: 'المريض الصحيح', expected: expectedPatient || '', scanned: '', status: 'pending' },
    { key: 'drug', label: 'الدواء الصحيح', expected: expectedDrug || '', scanned: '', status: 'pending' },
    { key: 'dose', label: 'الجرعة الصحيحة', expected: expectedDose || '', scanned: '', status: 'pending' },
    { key: 'route', label: 'الطريق الصحيح', expected: expectedRoute || '', scanned: '', status: 'pending' },
    { key: 'time', label: 'الوقت الصحيح', expected: new Date().toISOString(), scanned: '', status: 'pending' },
  ])
  const [manualMode, setManualMode] = useState(false)
  const manualInputRef = useRef<HTMLInputElement>(null)
  const scanInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scanInputRef.current?.focus()
  }, [])

  function simulateScan() {
    if (!DEMO_MODE) return
    const demoBarcode = JSON.stringify({
      patient: patientName || 'demo-patient',
      drug: drugName || 'DEMO-MEDICATION',
      dose: expectedDose || 'demo-dose',
      route: expectedRoute || 'demo-route',
      timestamp: new Date().toISOString(),
    })
    processScannedData(demoBarcode)
  }

  function processScannedData(raw: string) {
    setScannedCode(raw)
    setScanning(false)

    let parsed: Record<string, string> = {}
    try {
      parsed = JSON.parse(raw)
    } catch {
      const parts = raw.split(/[|,\n]/)
      if (parts.length >= 3) {
        parsed = {
          patient: parts[0]?.trim() || '',
          drug: parts[1]?.trim() || '',
          dose: parts[2]?.trim() || '',
          route: parts[3]?.trim() || '',
        }
      } else {
        parsed = { raw }
      }
    }

    const updatedRights: RightCheck[] = rights.map((right) => {
      const scannedRaw = parsed[right.key] || ''
      const scannedVal = normalizeScannedValue(scannedRaw)
      const expectedVal = normalizeScannedValue(right.expected)
      const isMatch = right.key === 'time'
        ? Number.isFinite(Date.parse(scannedRaw)) && Math.abs(Date.now() - Date.parse(scannedRaw)) <= 5 * 60 * 1000
        : Boolean(scannedVal && expectedVal && scannedVal === expectedVal)
      return {
        ...right,
        scanned: parsed[right.key] || '',
        status: isMatch ? 'success' : 'fail',
      }
    })

    setRights(updatedRights)
    setScannedData(parsed)

    const result: VerificationResult = {
      patient_match: updatedRights[0].status === 'success',
      drug_match: updatedRights[1].status === 'success',
      dose_match: updatedRights[2].status === 'success',
      route_match: updatedRights[3].status === 'success',
      time_match: updatedRights[4].status === 'success',
      all_match: updatedRights.every((r) => r.status === 'success'),
      scanned_data: parsed,
    }
  }

  function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (manualInputRef.current?.value) {
      processScannedData(manualInputRef.current.value)
    }
  }

  function retryScan() {
    setScanning(true)
    setScannedCode('')
    setRights((prev) =>
      prev.map((r) => ({ ...r, scanned: '', status: 'pending' })),
    )
    setManualMode(false)
    setTimeout(() => scanInputRef.current?.focus(), 100)
  }

  const allMatch = rights.every((r) => r.status === 'success')

  return (
    <div className="modal-overlay">
      <div className="modal" style={{ maxWidth: '500px' }} role="dialog" aria-modal="true" aria-label="التحقق بالباركود">
        <div className="modal-header">
          <h2 className="modal-title">التحقق بالباركود - الحقوق الخمسة</h2>
          <button className="modal-close" onClick={onCancel} aria-label="إغلاق">
            ✕
          </button>
        </div>

        {scanning ? (
          <div>
            <div className="scanner-frame" style={{ margin: '0 auto 1rem' }} />
            <p className="scanner-text">قم بتوجيه الماسح الضوئي نحو الباركود</p>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', justifyContent: 'center' }}>
                      {DEMO_MODE && (
                  <button className="btn btn-primary" onClick={simulateScan}>
                    محاكاة المسح (Demo فقط)
                  </button>
                )}
              <button
                className="btn btn-secondary"
                onClick={() => setManualMode(true)}
              >
                إدخال يدوي
              </button>
              <button className="btn btn-ghost" onClick={onCancel}>
                إلغاء
              </button>
            </div>

            <input
              ref={scanInputRef}
              type="text"
              style={{
                position: 'absolute',
                opacity: 0,
                height: 0,
                width: 0,
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const val = (e.target as HTMLInputElement).value
                  if (val) processScannedData(val)
                }
              }}
              aria-hidden="true"
              tabIndex={-1}
            />
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                البيانات الممسوحة:
              </h3>
              <div
                style={{
                  padding: '0.5rem',
                  background: 'var(--bg-primary)',
                  borderRadius: 'var(--radius-md)',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  wordBreak: 'break-all',
                  direction: 'ltr',
                  textAlign: 'left',
                }}
              >
                {scannedCode}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
              {rights.map((right) => (
                <div
                  key={right.key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.625rem',
                    borderRadius: 'var(--radius-md)',
                    background:
                      right.status === 'success'
                        ? 'rgba(34,197,94,0.1)'
                        : right.status === 'fail'
                          ? 'rgba(239,68,68,0.1)'
                          : 'var(--bg-primary)',
                    border: `1px solid ${
                      right.status === 'success'
                        ? 'rgba(34,197,94,0.3)'
                        : right.status === 'fail'
                          ? 'rgba(239,68,68,0.3)'
                          : 'var(--border-color)'
                    }`,
                  }}
                >
                  <span style={{ fontSize: '1.25rem' }}>
                    {right.status === 'success'
                      ? '✅'
                      : right.status === 'fail'
                        ? '❌'
                        : '⏳'}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                      {right.label}
                    </div>
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: 'var(--text-secondary)',
                        marginTop: '2px',
                      }}
                    >
                      متوقع: {right.expected} | ممسوح: {right.scanned || '-'}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {manualMode && (
              <form onSubmit={handleManualSubmit} style={{ marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">إدخال الباركود يدوياً</label>
                  <input
                    ref={manualInputRef}
                    type="text"
                    placeholder="أدخل بيانات الباركود"
                    dir="ltr"
                    style={{ textAlign: 'left' }}
                  />
                </div>
                <button type="submit" className="btn btn-primary">
                  تحقق
                </button>
              </form>
            )}

            <div
              style={{
                display: 'flex',
                gap: '0.75rem',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary" onClick={retryScan}>
                  🔄 إعادة مسح
                </button>
                <button className="btn btn-ghost" onClick={onCancel}>
                  إلغاء
                </button>
              </div>
              <button
                className={`btn ${allMatch ? 'btn-success' : 'btn-secondary'}`}
                onClick={() => {
                  if (!allMatch) return
                  onVerified({
                    patient_match: rights[0].status === 'success',
                    drug_match: rights[1].status === 'success',
                    dose_match: rights[2].status === 'success',
                    route_match: rights[3].status === 'success',
                    time_match: rights[4].status === 'success',
                    all_match: true,
                    scanned_data: scannedData,
                  })
                }}
                disabled={!allMatch}
              >
                {allMatch ? '✓ تأكيد وصرف' : 'أكمل التحقق قبل التأكيد'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
