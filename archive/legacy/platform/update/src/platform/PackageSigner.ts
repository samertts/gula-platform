export interface KeyPair {
  publicKey: string;
  privateKey: string;
  algorithm: string;
  created: string;
  expires: string | null;
}

export interface SignatureResult {
  signature: string;
  algorithm: string;
  signedBy: string;
  signedAt: string;
  certificateChain: string[];
}

export class PackageSigner {
  private keyStore: Map<string, KeyPair> = new Map();
  private trustedCertificates: Set<string> = new Set();

  async generateKeyPair(
    keyId: string,
    algorithm: 'ECDSA-P256' | 'ECDSA-P384' | 'RSA-PSS-2048' | 'RSA-PSS-4096' = 'ECDSA-P256',
    expiresInDays: number | null = 365,
  ): Promise<KeyPair> {
    let keyAlgorithm: EcKeyGenParams | RsaHashedKeyGenParams;

    if (algorithm.startsWith('ECDSA')) {
      const namedCurve = algorithm === 'ECDSA-P384' ? 'P-384' : 'P-256';
      keyAlgorithm = {
        name: 'ECDSA',
        namedCurve,
      } as EcKeyGenParams;
    } else {
      keyAlgorithm = {
        name: 'RSA-PSS',
        modulusLength: algorithm === 'RSA-PSS-4096' ? 4096 : 2048,
        publicExponent: new Uint8Array([1, 0, 1]),
        hash: 'SHA-256',
      };
    }

    const keyPair = await crypto.subtle.generateKey(
      keyAlgorithm,
      true,
      ['sign', 'verify'],
    );

    const publicKeyRaw = await crypto.subtle.exportKey('spki', keyPair.publicKey);
    const privateKeyRaw = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);

    const keyPairRecord: KeyPair = {
      publicKey: this.arrayBufferToBase64(publicKeyRaw),
      privateKey: this.arrayBufferToBase64(privateKeyRaw),
      algorithm,
      created: new Date().toISOString(),
      expires: expiresInDays
        ? new Date(Date.now() + expiresInDays * 86400000).toISOString()
        : null,
    };

    this.keyStore.set(keyId, keyPairRecord);
    return keyPairRecord;
  }

  async sign(
    data: ArrayBuffer | string,
    keyId: string,
  ): Promise<SignatureResult> {
    const keyPair = this.keyStore.get(keyId);
    if (!keyPair) {
      throw new Error(`Key not found: ${keyId}`);
    }

    const privateKey = await crypto.subtle.importKey(
      'pkcs8',
      this.base64ToArrayBuffer(keyPair.privateKey),
      this.getKeyAlgorithm(keyPair.algorithm, false),
      false,
      ['sign'],
    );

    const dataBuffer = typeof data === 'string' ? new TextEncoder().encode(data).buffer : data;

    const params = keyPair.algorithm.startsWith('ECDSA')
      ? { name: 'ECDSA', hash: 'SHA-256' }
      : { name: 'RSA-PSS', saltLength: 32 };

    const signature = await crypto.subtle.sign(params, privateKey, dataBuffer);

    return {
      signature: this.arrayBufferToBase64(signature),
      algorithm: keyPair.algorithm,
      signedBy: keyId,
      signedAt: new Date().toISOString(),
      certificateChain: this.getCertificateChain(keyId),
    };
  }

  async verifySignature(
    data: ArrayBuffer | string,
    signature: string,
    certificatePem: string,
  ): Promise<boolean> {
    try {
      const publicKeyData = this.pemToArrayBuffer(certificatePem);
      const algorithm = this.detectAlgorithmFromKey(publicKeyData);

      const publicKey = await crypto.subtle.importKey(
        'spki',
        publicKeyData,
        this.getKeyAlgorithm(algorithm, true),
        false,
        ['verify'],
      );

      const dataBuffer = typeof data === 'string'
        ? new TextEncoder().encode(data).buffer
        : data;

      const params = algorithm.startsWith('ECDSA')
        ? { name: 'ECDSA', hash: 'SHA-256' }
        : { name: 'RSA-PSS', saltLength: 32 };

      return await crypto.subtle.verify(
        params,
        publicKey,
        this.base64ToArrayBuffer(signature),
        dataBuffer,
      );
    } catch {
      return false;
    }
  }

  addTrustedCertificate(certificatePem: string): void {
    this.trustedCertificates.add(certificatePem);
  }

  removeTrustedCertificate(certificatePem: string): void {
    this.trustedCertificates.delete(certificatePem);
  }

  isCertificateTrusted(certificatePem: string): boolean {
    return this.trustedCertificates.has(certificatePem);
  }

  exportPublicKey(keyId: string): string {
    const keyPair = this.keyStore.get(keyId);
    if (!keyPair) {
      throw new Error(`Key not found: ${keyId}`);
    }
    return this.arrayBufferToPem(this.base64ToArrayBuffer(keyPair.publicKey), 'PUBLIC KEY');
  }

  exportPrivateKey(keyId: string): string {
    const keyPair = this.keyStore.get(keyId);
    if (!keyPair) {
      throw new Error(`Key not found: ${keyId}`);
    }
    return this.arrayBufferToPem(this.base64ToArrayBuffer(keyPair.privateKey), 'PRIVATE KEY');
  }

  private getKeyAlgorithm(algorithm: string, forVerify: boolean): RsaHashedImportParams | EcKeyImportParams {
    if (algorithm.startsWith('ECDSA')) {
      const namedCurve = algorithm === 'ECDSA-P384' ? 'P-384' : 'P-256';
      return { name: 'ECDSA', namedCurve } as EcKeyImportParams;
    }
    return { name: 'RSA-PSS', hash: 'SHA-256' };
  }

  private detectAlgorithmFromKey(keyData: ArrayBuffer): string {
    const view = new Uint8Array(keyData);
    const pemStr = this.arrayBufferToBase64(keyData);
    if (pemStr.length > 500) return 'RSA-PSS-4096';
    if (pemStr.length > 300) return 'RSA-PSS-2048';
    return 'ECDSA-P256';
  }

  private getCertificateChain(keyId: string): string[] {
    return [...this.trustedCertificates].slice(0, 3);
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  private arrayBufferToPem(buffer: ArrayBuffer, label: string): string {
    const base64 = this.arrayBufferToBase64(buffer);
    const lines = base64.match(/.{1,64}/g) || [];
    return [
      `-----BEGIN ${label}-----`,
      ...lines,
      `-----END ${label}-----`,
    ].join('\n');
  }

  private pemToArrayBuffer(pem: string): ArrayBuffer {
    const base64 = pem
      .replace(/-----BEGIN [\w\s]+-----/g, '')
      .replace(/-----END [\w\s]+-----/g, '')
      .replace(/\s/g, '');
    return this.base64ToArrayBuffer(base64);
  }

  clearKeys(): void {
    this.keyStore.clear();
  }
}
