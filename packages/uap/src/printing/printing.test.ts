import { describe, expect, it } from 'vitest';

import { generateBarcodeSvg, generateDigitalSignature, generateQRSvg } from './index';

describe('printing safety boundaries', () => {
  it('escapes barcode and QR text payloads', () => {
    const payload = '<script>alert(1)</script>&"';
    expect(generateBarcodeSvg(payload)).not.toContain('<script>');
    expect(generateBarcodeSvg(payload)).toContain('&lt;script&gt;');
    expect(generateQRSvg(payload)).not.toContain('<script>');
    expect(generateQRSvg(payload)).toContain('&lt;script&gt;');
  });

  it('does not expose a browser-side pseudo digital signature', () => {
    expect(() => generateDigitalSignature('data', 'key')).toThrow('SERVER_SIDE_SIGNATURE_REQUIRED');
  });
});
