import { apiRequest } from './api';

export type OrderPriority = 'routine' | 'urgent' | 'stat' | 'asap';
export type OrderStatus = 'draft' | 'pending' | 'active' | 'completed' | 'cancelled' | 'discontinued';
export type OrderCategory = 'medication' | 'lab' | 'radiology' | 'procedure' | 'consultation' | 'diet' | 'nursing';

export interface ClinicalOrder {
  id: string;
  patientId: string;
  visitId?: string;
  category: OrderCategory;
  priority: OrderPriority;
  status: OrderStatus;
  code?: string;
  description: string;
  descriptionAr: string;
  instructions?: string;
  instructionsAr?: string;
  indications?: string;
  orderedBy: string;
  orderedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
  completedAt?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface LabOrderRequest {
  testCode: string;
  testName: string;
  testNameAr: string;
  sampleType?: string;
  sampleContainer?: string;
  fastingRequired?: boolean;
  notes?: string;
}

export interface LabOrder extends ClinicalOrder {
  tests: LabOrderRequest[];
  sampleId?: string;
  sampleCollectedAt?: string;
  resultStatus: 'pending' | 'in_progress' | 'completed' | 'verified';
}

export interface RadiologyOrderRequest {
  examCode: string;
  examName: string;
  examNameAr: string;
  bodyPart: string;
  contrastRequired?: boolean;
  clinicalIndication: string;
  notes?: string;
}

export interface RadiologyOrder extends ClinicalOrder {
  exams: RadiologyOrderRequest[];
  scheduledAt?: string;
  resultStatus: 'pending' | 'in_progress' | 'completed' | 'verified';
}

export async function getOrders(patientId: string, category?: OrderCategory): Promise<ClinicalOrder[]> {
  const query = category ? `?category=${category}` : '';
  return apiRequest<ClinicalOrder[]>(`/patients/${patientId}/orders${query}`);
}

export async function createOrder(
  patientId: string,
  order: Omit<ClinicalOrder, 'id' | 'patientId' | 'orderedAt' | 'createdAt' | 'updatedAt' | 'status'>,
): Promise<ClinicalOrder> {
  return apiRequest<ClinicalOrder>(`/patients/${patientId}/orders`, {
    method: 'POST',
    body: JSON.stringify(order),
    offlinePriority: 'high',
  });
}

export async function updateOrderStatus(
  patientId: string,
  orderId: string,
  status: OrderStatus,
  notes?: string,
): Promise<ClinicalOrder> {
  return apiRequest<ClinicalOrder>(`/patients/${patientId}/orders/${orderId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status, notes }),
  });
}

export async function createLabOrder(
  patientId: string,
  order: {
    priority: OrderPriority;
    tests: LabOrderRequest[];
    instructions?: string;
    indications?: string;
  },
): Promise<LabOrder> {
  return apiRequest<LabOrder>(`/patients/${patientId}/lab-orders`, {
    method: 'POST',
    body: JSON.stringify(order),
    offlinePriority: 'high',
  });
}

export async function createRadiologyOrder(
  patientId: string,
  order: {
    priority: OrderPriority;
    exams: RadiologyOrderRequest[];
    instructions?: string;
    clinicalIndication: string;
  },
): Promise<RadiologyOrder> {
  return apiRequest<RadiologyOrder>(`/patients/${patientId}/radiology-orders`, {
    method: 'POST',
    body: JSON.stringify(order),
    offlinePriority: 'high',
  });
}

export async function getLabOrders(patientId: string): Promise<LabOrder[]> {
  return apiRequest<LabOrder[]>(`/patients/${patientId}/lab-orders`);
}

export async function getRadiologyOrders(patientId: string): Promise<RadiologyOrder[]> {
  return apiRequest<RadiologyOrder[]>(`/patients/${patientId}/radiology-orders`);
}

export async function discontinueOrder(patientId: string, orderId: string, reason: string): Promise<ClinicalOrder> {
  return updateOrderStatus(patientId, orderId, 'discontinued', reason);
}
