const getCrypto = (): Crypto => {
  if (typeof globalThis.crypto === 'undefined' || typeof globalThis.crypto.getRandomValues !== 'function') {
    throw new Error('Secure random source unavailable');
  }
  return globalThis.crypto;
};

export const secureRandomHex = (byteLength = 8): string => {
  if (!Number.isInteger(byteLength) || byteLength < 1 || byteLength > 256) {
    throw new RangeError('byteLength must be between 1 and 256');
  }
  const bytes = new Uint8Array(byteLength);
  getCrypto().getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
};

export const secureId = (prefix: string): string => `${prefix}-${Date.now()}-${secureRandomHex(8)}`;

export const secureRandomInt = (maxExclusive: number): number => {
  if (!Number.isSafeInteger(maxExclusive) || maxExclusive <= 0 || maxExclusive > 0x1_0000_0000) {
    throw new RangeError('maxExclusive must be a positive safe integer');
  }
  const limit = Math.floor(0x1_0000_0000 / maxExclusive) * maxExclusive;
  const values = new Uint32Array(1);
  do {
    getCrypto().getRandomValues(values);
  } while (values[0] >= limit);
  return values[0] % maxExclusive;
};
