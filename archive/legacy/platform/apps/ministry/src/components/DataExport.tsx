import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react';

interface DataExportProps {
  data: Record<string, any>[];
  filename: string;
  label?: string;
  className?: string;
  columns?: { key: string; header: string }[];
}

export function DataExport({ data, filename, label, className, columns }: DataExportProps) {
  const [exporting, setExporting] = useState<'csv' | 'pdf' | null>(null);

  const exportCSV = async () => {
    setExporting('csv');
    try {
      const cols = columns || (data.length > 0 ? Object.keys(data[0]).map(k => ({ key: k, header: k })) : []);
      const header = cols.map(c => c.header).join(',');
      const rows = data.map(row => cols.map(c => {
        const val = row[c.key];
        const str = val == null ? '' : String(val);
        return str.includes(',') ? `"${str}"` : str;
      }).join(','));
      const csv = [header, ...rows].join('\n');
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(null);
    }
  };

  const exportPDF = async () => {
    setExporting('pdf');
    try {
      const { default: html2canvas } = await import('html2canvas');
      const { default: jsPDF } = await import('jspdf');
      const element = document.createElement('div');
      element.style.cssText = 'padding: 20px; background: white; color: black; font-family: Cairo, sans-serif; direction: rtl;';
      element.innerHTML = `
        <h2 style="text-align:center;margin-bottom:20px;">${filename}</h2>
        <table style="width:100%;border-collapse:collapse;">
          ${data.slice(0, 50).map(row => `<tr>${Object.values(row).map(v => `<td style="border:1px solid #ddd;padding:4px 8px;font-size:10px;">${v ?? ''}</td>`).join('')}</tr>`).join('')}
        </table>
      `;
      document.body.appendChild(element);
      const canvas = await html2canvas(element);
      document.body.removeChild(element);
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('l', 'mm', 'a4');
      const imgWidth = 280;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      pdf.save(`${filename}.pdf`);
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
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
