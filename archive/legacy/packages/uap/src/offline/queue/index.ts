import type { SyncOperation, SyncConfig } from '../types';
import { DEFAULT_SYNC_CONFIG } from '../types';

export interface CompressionResult {
  data: string;
  originalSize: number;
  compressedSize: number;
  ratio: number;
}

export const compress = async (data: unknown): Promise<CompressionResult> => {
  const json = JSON.stringify(data);
  const encoder = new TextEncoder();
  const bytes = encoder.encode(json);

  if (typeof CompressionStream !== 'undefined') {
    try {
      const cs = new CompressionStream('gzip');
      const writer = cs.writable.getWriter();
      writer.write(bytes);
      writer.close();
      const reader = cs.readable.getReader();
      const chunks: Uint8Array[] = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }
      const compressed = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
      let offset = 0;
      for (const chunk of chunks) {
        compressed.set(chunk, offset);
        offset += chunk.length;
      }
      const compressedStr = btoa(String.fromCharCode(...compressed));
      return {
        data: compressedStr,
        originalSize: bytes.length,
        compressedSize: compressed.length,
        ratio: compressed.length / bytes.length,
      };
    } catch {
      // fallback to no compression
    }
  }

  return {
    data: json,
    originalSize: bytes.length,
    compressedSize: bytes.length,
    ratio: 1,
  };
};

export const decompress = async (data: string): Promise<unknown> => {
  try {
    const binaryStr = atob(data);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    if (typeof DecompressionStream !== 'undefined') {
      try {
        const ds = new DecompressionStream('gzip');
        const writer = ds.writable.getWriter();
        writer.write(bytes);
        writer.close();
        const reader = ds.readable.getReader();
        const chunks: Uint8Array[] = [];
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
        }
        const decompressed = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
        let offset = 0;
        for (const chunk of chunks) {
          decompressed.set(chunk, offset);
          offset += chunk.length;
        }
        const decoder = new TextDecoder();
        return JSON.parse(decoder.decode(decompressed));
      } catch {
        return JSON.parse(data);
      }
    }
    return JSON.parse(data);
  } catch {
    return JSON.parse(data);
  }
};

export const calculateBackoff = (attempt: number, baseMs: number = DEFAULT_SYNC_CONFIG.retryBackoffMs): number => {
  return Math.min(baseMs * Math.pow(2, attempt), 30000);
};

export const shouldRetry = (operation: SyncOperation, config: SyncConfig = DEFAULT_SYNC_CONFIG): boolean => {
  return operation.retries < config.retryMaxAttempts;
};

export const batchOperations = (operations: SyncOperation[], batchSize: number = DEFAULT_SYNC_CONFIG.batchSize): SyncOperation[][] => {
  const batches: SyncOperation[][] = [];
  for (let i = 0; i < operations.length; i += batchSize) {
    batches.push(operations.slice(i, i + batchSize));
  }
  return batches;
};

export const generateDeltaPatch = (old: unknown, updated: unknown): Record<string, unknown> => {
  const patch: Record<string, unknown> = {};
  const oldObj = (old || {}) as Record<string, unknown>;
  const newObj = (updated || {}) as Record<string, unknown>;
  for (const key of new Set([...Object.keys(oldObj), ...Object.keys(newObj)])) {
    if (oldObj[key] !== newObj[key]) {
      patch[key] = newObj[key];
    }
  }
  return patch;
};
