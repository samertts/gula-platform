import { create } from 'zustand';
import { secureId } from '../security/secureRandom';

export type PrintJobStatus = 'queued' | 'printing' | 'completed' | 'failed';
export type PrintFormat = 'a4' | 'a5' | 'label' | 'thermal' | 'receipt';
export type PrintOrientation = 'portrait' | 'landscape';

export interface PrintJob {
  id: string;
  name: string;
  format: PrintFormat;
  orientation: PrintOrientation;
  copies: number;
  duplex: boolean;
  status: PrintJobStatus;
  content: string;
  createdAt: number;
  completedAt?: number;
  error?: string;
  watermark?: string;
  digitalSignature?: string;
}

interface PrintingState {
  jobs: PrintJob[];
  defaultFormat: PrintFormat;
  activeJobId: string | null;

  print: (job: Omit<PrintJob, 'id' | 'status' | 'createdAt'>) => Promise<string>;
  cancelJob: (id: string) => void;
  getJobStatus: (id: string) => PrintJobStatus | null;
  clearCompleted: () => void;
  setDefaultFormat: (format: PrintFormat) => void;
  getAllJobs: () => PrintJob[];
}

export const usePrinting = create<PrintingState>((set, get) => ({
  jobs: [],
  defaultFormat: 'a4',
  activeJobId: null,

  print: async (job) => {
    const id = secureId('print');
    const printJob: PrintJob = {
      ...job,
      id,
      status: 'queued',
      createdAt: Date.now(),
    };
    set((state) => ({
      jobs: [printJob, ...state.jobs],
      activeJobId: id,
    }));
    // Simulate print completion
    setTimeout(() => {
      set((state) => ({
        jobs: state.jobs.map((j) =>
          j.id === id ? { ...j, status: 'completed' as const, completedAt: Date.now() } : j
        ),
        activeJobId: null,
      }));
    }, 1500);
    return id;
  },

  cancelJob: (id) => {
    set((state) => ({
      jobs: state.jobs.map((j) =>
        j.id === id ? { ...j, status: 'failed' as const, error: 'Cancelled' } : j
      ),
    }));
  },

  getJobStatus: (id) => get().jobs.find((j) => j.id === id)?.status ?? null,
  clearCompleted: () => set((state) => ({ jobs: state.jobs.filter((j) => j.status !== 'completed') })),
  setDefaultFormat: (format) => set({ defaultFormat: format }),
  getAllJobs: () => get().jobs,
}));

const escapeXml = (value: string): string =>
  value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&apos;',
  })[character]!);

const safeDimension = (value: number, fallback: number): number =>
  Number.isFinite(value) && value > 0 && value <= 2000 ? value : fallback;

const sanitizePrintHtml = (content: string): string => {
  const template = document.createElement('template');
  template.innerHTML = content;
  template.content.querySelectorAll('script, iframe, object, embed, form, link').forEach((node) => node.remove());
  template.content.querySelectorAll('*').forEach((element) => {
    [...element.attributes].forEach((attribute) => {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim().toLowerCase();
      if (name.startsWith('on') || name === 'srcdoc') element.removeAttribute(attribute.name);
      if ((name === 'href' || name === 'src' || name === 'xlink:href') && /^(javascript|data|vbscript):/.test(value)) {
        element.removeAttribute(attribute.name);
      }
    });
  });
  return template.innerHTML;
};

export const generateBarcodeSvg = (data: string, width = 200, height = 80): string => {
  const safeWidth = safeDimension(width, 200);
  const safeHeight = safeDimension(height, 80);
  const chars = data.slice(0, 256).split('');
  const barWidth = safeWidth / Math.max(chars.length, 1);
  let bars = '';
  chars.forEach((_, i) => {
    const bar = i % 2 === 0 ? `#000` : `#fff`;
    bars += `<rect x="${i * barWidth}" y="0" width="${barWidth}" height="${safeHeight}" fill="${bar}" />`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${safeWidth}" height="${safeHeight}">
    ${bars}
    <text x="${safeWidth / 2}" y="${safeHeight - 5}" text-anchor="middle" font-size="12" fill="#000">${escapeXml(data.slice(0, 256))}</text>
  </svg>`;
};

export const generateQRSvg = (data: string, size = 200): string => {
  const safeSize = safeDimension(size, 200);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${safeSize}" height="${safeSize}">
    <rect width="${safeSize}" height="${safeSize}" fill="white" rx="8"/>
    <rect x="${safeSize * 0.1}" y="${safeSize * 0.1}" width="${safeSize * 0.8}" height="${safeSize * 0.8}" fill="black" rx="4"/>
    <rect x="${safeSize * 0.15}" y="${safeSize * 0.15}" width="${safeSize * 0.2}" height="${safeSize * 0.2}" fill="white"/>
    <rect x="${safeSize * 0.65}" y="${safeSize * 0.15}" width="${safeSize * 0.2}" height="${safeSize * 0.2}" fill="white"/>
    <rect x="${safeSize * 0.15}" y="${safeSize * 0.65}" width="${safeSize * 0.2}" height="${safeSize * 0.2}" fill="white"/>
    <rect x="${safeSize * 0.38}" y="${safeSize * 0.38}" width="${safeSize * 0.24}" height="${safeSize * 0.24}" fill="white"/>
    <text x="${safeSize / 2}" y="${safeSize - 10}" text-anchor="middle" font-size="${safeSize * 0.06}" fill="black">${escapeXml(data.slice(0, 256))}</text>
  </svg>`;
};

export const printPDF = async (content: string, format: PrintFormat = 'a4'): Promise<void> => {
  const safeContent = sanitizePrintHtml(content);
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    // Fallback: print in current window
    const style = format === 'thermal'
      ? '@page { size: 80mm auto; margin: 0; }'
      : format === 'label'
      ? '@page { size: 100mm 50mm; margin: 2mm; }'
      : '@page { size: A4; margin: 20mm; }';
    const html = `<!DOCTYPE html>
      <html><head><style>${style} body { font-family: sans-serif; }</style></head>
      <body>${safeContent}</body></html>`;
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.focus();
      win.print();
    }
    return;
  }
  printWindow.document.write(safeContent);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
};

/**
 * @deprecated This is intentionally disabled. A browser-side concatenation is
 * not a digital signature; use a server-side, audited cryptographic signer.
 */
export const generateDigitalSignature = (_data: string, _key: string): never => {
  throw new Error('SERVER_SIDE_SIGNATURE_REQUIRED');
};

export const addWatermark = (content: string, watermark: string): string => {
  const safeContent = sanitizePrintHtml(content);
  const safeWatermark = escapeXml(watermark.slice(0, 200));
  return `<div style="position: relative;">
    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg);
      font-size: 72px; opacity: 0.1; color: #000; white-space: nowrap; pointer-events: none;">
      ${safeWatermark}
    </div>
    <div style="position: relative; z-index: 1;">${safeContent}</div>
  </div>`;
};
