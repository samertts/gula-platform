import { apiRequest } from './api';
import type { PaymentMethod, PaymentTransaction } from '../types';

export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  return apiRequest<{ methods: PaymentMethod[] }>('/citizen/payments/methods').then(
    (r) => r.methods,
  );
}

export async function addPaymentMethod(
  data: {
    type: PaymentMethod['type'];
    token: string;
    label: string;
    setDefault?: boolean;
  },
): Promise<PaymentMethod> {
  return apiRequest<{ method: PaymentMethod }>('/citizen/payments/methods', {
    method: 'POST',
    body: JSON.stringify(data),
  }).then((r) => r.method);
}

export async function removePaymentMethod(methodId: string): Promise<void> {
  await apiRequest(`/citizen/payments/methods/${methodId}`, {
    method: 'DELETE',
  });
}

export async function setDefaultPaymentMethod(methodId: string): Promise<void> {
  await apiRequest(`/citizen/payments/methods/${methodId}/default`, {
    method: 'POST',
  });
}

export async function getTransactionHistory(
  page: number = 1,
  limit: number = 20,
): Promise<{ transactions: PaymentTransaction[]; total: number; page: number }> {
  return apiRequest(`/citizen/payments/transactions?page=${page}&limit=${limit}`);
}

export async function createPayment(
  data: {
    amount: number;
    type: PaymentTransaction['type'];
    description: string;
    paymentMethodId?: string;
  },
): Promise<PaymentTransaction> {
  return apiRequest<{ transaction: PaymentTransaction }>('/citizen/payments/create', {
    method: 'POST',
    body: JSON.stringify(data),
  }).then((r) => r.transaction);
}

export async function getInvoiceUrl(transactionId: string): Promise<string> {
  return apiRequest<{ url: string }>(`/citizen/payments/transactions/${transactionId}/invoice`).then(
    (r) => r.url,
  );
}
