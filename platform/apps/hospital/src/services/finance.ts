import { apiRequest } from './api';

export interface FinancialSummary {
  totalRevenue: number;
  totalExpenses: number;
  netIncome: number;
  revenueBreakdown: RevenueCategory[];
  expenseBreakdown: ExpenseCategory[];
  periodStart: string;
  periodEnd: string;
}

export interface RevenueCategory {
  category: string;
  categoryAr: string;
  amount: number;
  count: number;
  percentage: number;
}

export interface ExpenseCategory {
  category: string;
  categoryAr: string;
  amount: number;
  percentage: number;
}

export interface Invoice {
  id: string;
  patientId: string;
  patientName: string;
  patientNameAr: string;
  admissionId: string | null;
  invoiceNumber: string;
  amount: number;
  paidAmount: number;
  balance: number;
  status: 'draft' | 'issued' | 'partial' | 'paid' | 'cancelled' | 'write_off';
  services: InvoiceLineItem[];
  insuranceClaim: string | null;
  issuedDate: string;
  dueDate: string;
  paidDate: string | null;
  notes: string;
  createdAt: string;
}

export interface InvoiceLineItem {
  description: string;
  descriptionAr: string;
  quantity: number;
  unitPrice: number;
  total: number;
  category: string;
}

export interface BudgetItem {
  id: string;
  department: string;
  departmentAr: string;
  category: string;
  categoryAr: string;
  allocated: number;
  spent: number;
  remaining: number;
  fiscalYear: number;
  period: 'monthly' | 'quarterly' | 'annual';
}

export async function getFinancialSummary(
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual' = 'monthly',
): Promise<FinancialSummary> {
  return apiRequest(`/hospital/finance/summary?period=${period}`);
}

export async function getInvoices(params?: {
  status?: string;
  patientId?: string;
  page?: number;
  limit?: number;
}): Promise<{ data: Invoice[]; total: number; page: number }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.patientId) searchParams.set('patientId', params.patientId);
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  const qs = searchParams.toString();
  return apiRequest(`/hospital/finance/invoices${qs ? `?${qs}` : ''}`);
}

export async function getBudget(params?: {
  department?: string;
  fiscalYear?: number;
}): Promise<BudgetItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.department) searchParams.set('department', params.department);
  if (params?.fiscalYear) searchParams.set('fiscalYear', String(params.fiscalYear));
  const qs = searchParams.toString();
  return apiRequest(`/hospital/finance/budget${qs ? `?${qs}` : ''}`);
}

export async function getRevenueTrend(
  period: 'daily' | 'weekly' | 'monthly' | 'annual' = 'monthly',
  months: number = 12,
): Promise<{ date: string; revenue: number; expenses: number; net: number }[]> {
  return apiRequest(`/hospital/finance/trend?period=${period}&months=${months}`);
}
