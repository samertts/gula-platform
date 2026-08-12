import { apiRequest } from './api';
import type { BarcodeLabel } from '@/utils/types';

export const barcodeService = {
  async generateLabels(sampleIds: string[]): Promise<BarcodeLabel[]> {
    return apiRequest<BarcodeLabel[]>('/barcodes/generate', {
      method: 'POST',
      body: JSON.stringify({ sampleIds }),
    });
  },

  async generateSingle(data: {
    sampleId: string;
    patientName: string;
    patientId: string;
    specimenType: string;
    tests: string[];
    container?: string;
  }): Promise<BarcodeLabel> {
    return apiRequest<BarcodeLabel>('/barcodes/generate-single', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async printLabels(labels: BarcodeLabel[], options?: {
    copies?: number;
    printerName?: string;
    labelSize?: string;
  }): Promise<{ success: boolean; jobId?: string; error?: string }> {
    return apiRequest('/barcodes/print', {
      method: 'POST',
      body: JSON.stringify({ labels, ...options }),
    });
  },

  async getPrintHistory(params: {
    page?: number;
    perPage?: number;
  } = {}): Promise<{ data: any[]; total: number }> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.perPage) query.set('per_page', String(params.perPage));
    return apiRequest(`/barcodes/history?${query.toString()}`);
  },

  async getAvailablePrinters(): Promise<{ name: string; status: string; labelSizes: string[] }[]> {
    return apiRequest('/barcodes/printers');
  },

  parseBarcode(barcode: string): {
    type: 'sample' | 'container' | 'patient' | 'reagent';
    id?: string;
    sampleId?: string;
    patientId?: string;
    code: string;
  } | null {
    if (!barcode) return null;

    if (barcode.startsWith('SMP-')) {
      return { type: 'sample', sampleId: barcode, code: barcode };
    }
    if (barcode.startsWith('PAT-')) {
      return { type: 'patient', patientId: barcode, code: barcode };
    }
    if (barcode.startsWith('RGT-')) {
      return { type: 'reagent', code: barcode };
    }
    if (barcode.startsWith('CTN-')) {
      return { type: 'container', id: barcode, code: barcode };
    }

    return { type: 'sample', code: barcode };
  },

  getBarcodeType(barcode: string): 'code128' | 'code39' | 'ean13' | 'qr' | 'unknown' {
    if (barcode.startsWith('SMP-')) return 'code128';
    if (barcode.startsWith('PAT-')) return 'code128';
    if (barcode.length === 13 && /^\d{13}$/.test(barcode)) return 'ean13';
    if (barcode.length > 20) return 'qr';
    return 'code128';
  },
};
