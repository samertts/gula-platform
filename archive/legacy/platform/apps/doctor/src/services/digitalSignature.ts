import { apiRequest } from './api';

export interface SignatureRequest {
  documentType: 'clinical_note' | 'prescription' | 'lab_order' | 'radiology_order' | 'referral' | 'discharge_summary' | 'consent_form';
  documentId: string;
  documentTitle: string;
  documentTitleAr: string;
  patientId: string;
  patientName: string;
  contentHash: string;
  metadata?: Record<string, unknown>;
}

export interface SignedDocument {
  id: string;
  documentType: string;
  documentId: string;
  documentTitle: string;
  documentTitleAr: string;
  patientId: string;
  signerId: string;
  signerName: string;
  signerTitle: string;
  signatureData: string;
  signatureType: 'draw' | 'typed' | 'biometric' | 'certificate';
  contentHash: string;
  verifiedAt: string;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface SignatureVerification {
  isValid: boolean;
  documentId: string;
  signedBy: string;
  signedAt: string;
  contentTampered: boolean;
  certificateValid?: boolean;
  details?: string;
}

export async function submitSignature(
  signature: Omit<SignatureRequest, 'contentHash'> & {
    signatureData: string;
    signatureType: 'draw' | 'typed' | 'certificate';
  },
): Promise<SignedDocument> {
  return apiRequest<SignedDocument>('/signatures', {
    method: 'POST',
    body: JSON.stringify(signature),
    offlinePriority: 'high',
  });
}

export async function verifySignature(documentId: string, documentType: string): Promise<SignatureVerification> {
  return apiRequest<SignatureVerification>(`/signatures/verify/${documentType}/${documentId}`);
}

export async function getSignatureHistory(
  documentType: string,
  documentId: string,
): Promise<SignedDocument[]> {
  return apiRequest<SignedDocument[]>(`/signatures/history/${documentType}/${documentId}`);
}

export async function getPendingSignatures(): Promise<SignatureRequest[]> {
  return apiRequest<SignatureRequest[]>('/signatures/pending');
}

export async function getUserSignatures(page = 1, pageSize = 20): Promise<{
  signatures: SignedDocument[];
  total: number;
  page: number;
  pageSize: number;
}> {
  return apiRequest(`/signatures/user?page=${page}&pageSize=${pageSize}`);
}

export async function generateContentHash(content: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(content);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
