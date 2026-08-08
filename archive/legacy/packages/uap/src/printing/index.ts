import { create } from 'zustand';

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
    const id = `print-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
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

export const generateBarcodeSvg = (data: string, width = 200, height = 80): string => {
  const chars = data.split('');
  const barWidth = width / chars.length;
  let bars = '';
  chars.forEach((c, i) => {
    const bar = i % 2 === 0 ? `#000` : `#fff`;
    bars += `<rect x="${i * barWidth}" y="0" width="${barWidth}" height="${height}" fill="${bar}" />`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    ${bars}
    <text x="${width / 2}" y="${height - 5}" text-anchor="middle" font-size="12" fill="#000">${data}</text>
  </svg>`;
};

export const generateQRSvg = (data: string, size = 200): string => {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
    <rect width="${size}" height="${size}" fill="white" rx="8"/>
    <rect x="${size * 0.1}" y="${size * 0.1}" width="${size * 0.8}" height="${size * 0.8}" fill="black" rx="4"/>
    <rect x="${size * 0.15}" y="${size * 0.15}" width="${size * 0.2}" height="${size * 0.2}" fill="white"/>
    <rect x="${size * 0.65}" y="${size * 0.15}" width="${size * 0.2}" height="${size * 0.2}" fill="white"/>
    <rect x="${size * 0.15}" y="${size * 0.65}" width="${size * 0.2}" height="${size * 0.2}" fill="white"/>
    <rect x="${size * 0.38}" y="${size * 0.38}" width="${size * 0.24}" height="${size * 0.24}" fill="white"/>
    <text x="${size / 2}" y="${size - 10}" text-anchor="middle" font-size="${size * 0.06}" fill="black">${data}</text>
  </svg>`;
};

export const printPDF = async (content: string, format: PrintFormat = 'a4'): Promise<void> => {
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
      <body>${content}</body></html>`;
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.focus();
      win.print();
    }
    return;
  }
  printWindow.document.write(content);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
};

export const generateDigitalSignature = (data: string, key: string): string => {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(data + key);
  return Array.from(new Uint8Array(bytes))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
};

export const addWatermark = (content: string, watermark: string): string => {
  return `<div style="position: relative;">
    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg);
      font-size: 72px; opacity: 0.1; color: #000; white-space: nowrap; pointer-events: none;">
      ${watermark}
    </div>
    <div style="position: relative; z-index: 1;">${content}</div>
  </div>`;
};
