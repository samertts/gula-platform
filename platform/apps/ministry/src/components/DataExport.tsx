import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react';

interface DataExportProps {
  data?: Record<string, any>[];
  filename?: string;
  label?: string;
  className?: string;
  columns?: { key: string; header: string }[];
}

const safeFilename = (filename: string): string =>
  filename.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 120) || 'gula-export';

const csvCell = (value: unknown): string => {
  let text = value == null ? '' : String(value);
  // Excel/LibreOffice formula injection: neutralize formula-like cells while
  // preserving ordinary negative numeric values as numeric CSV cells.
  if (/^[\t\r ]*[=+@]/.test(text) || /^-\D/.test(text)) text = `'${text}`;
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

export function DataExport({ data = [], filename = 'gula-export', label, className, columns }: DataExportProps) {
  const [exporting, setExporting] = useState<'csv' | 'pdf' | null>(null);

  const exportCSV = async () => {
    setExporting('csv');
    try {
      const cols = columns || (data.length > 0 ? Object.keys(data[0]).map((key) => ({ key, header: key })) : []);
      const header = cols.map((column) => csvCell(column.header)).join(',');
      const rows = data.map((row) => cols.map((column) => csvCell(row[column.key])).join(','));
      const csv = [header, ...rows].join('\n');
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${safeFilename(filename)}.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(null);
    }
  };

  const exportPDF = async () => {
    setExporting('pdf');
    let element: HTMLDivElement | null = null;
    try {
      const { default: html2canvas } = await import('html2canvas');
      const { default: jsPDF } = await import('jspdf');
      const safeName = safeFilename(filename);
      const cols = columns || (data.length > 0 ? Object.keys(data[0]).map((key) => ({ key, header: key })) : []);
      element = document.createElement('div');
      element.style.cssText = 'padding: 20px; background: white; color: black; font-family: Cairo, sans-serif; direction: rtl;';

      const heading = document.createElement('h2');
      heading.style.cssText = 'text-align:center;margin-bottom:20px;';
      heading.textContent = filename;
      element.appendChild(heading);

      const table = document.createElement('table');
      table.style.cssText = 'width:100%;border-collapse:collapse;';
      const headerRow = document.createElement('tr');
      cols.forEach((column) => {
        const cell = document.createElement('th');
        cell.style.cssText = 'border:1px solid #ddd;padding:4px 8px;font-size:10px;';
        cell.textContent = column.header;
        headerRow.appendChild(cell);
      });
      table.appendChild(headerRow);
      data.slice(0, 50).forEach((row) => {
        const tableRow = document.createElement('tr');
        cols.forEach((column) => {
          const cell = document.createElement('td');
          cell.style.cssText = 'border:1px solid #ddd;padding:4px 8px;font-size:10px;';
          cell.textContent = row[column.key] == null ? '' : String(row[column.key]);
          tableRow.appendChild(cell);
        });
        table.appendChild(tableRow);
      });
      element.appendChild(table);
      document.body.appendChild(element);
      const canvas = await html2canvas(element);
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('l', 'mm', 'a4');
      const imgWidth = 280;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      pdf.save(`${safeName}.pdf`);
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      element?.remove();
      setExporting(null);
    }
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <button
        onClick={exportCSV}
        disabled={exporting !== null}
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 border border-white/10 text-xs font-bold text-slate-300 hover:bg-white/20 hover:text-white transition-all disabled:opacity-50"
      >
        {exporting === 'csv' ? <Loader2 size={16} className="animate-spin" /> : <FileSpreadsheet size={16} />}
        CSV
      </button>
      <button
        onClick={exportPDF}
        disabled={exporting !== null}
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 border border-white/10 text-xs font-bold text-slate-300 hover:bg-white/20 hover:text-white transition-all disabled:opacity-50"
      >
        {exporting === 'pdf' ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
        PDF
      </button>
    </div>
  );
}
