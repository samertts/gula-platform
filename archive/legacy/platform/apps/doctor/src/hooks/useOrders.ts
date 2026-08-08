import { useState, useCallback } from 'react';
import {
  getOrders, createOrder, updateOrderStatus, createLabOrder, createRadiologyOrder,
  type ClinicalOrder, type OrderCategory, type OrderPriority, type OrderStatus,
  type LabOrderRequest, type RadiologyOrderRequest,
} from '../services/orders';

export function useOrders(patientId: string) {
  const [orders, setOrders] = useState<ClinicalOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async (category?: OrderCategory) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getOrders(patientId, category);
      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل الطلبات');
    } finally {
      setIsLoading(false);
    }
  }, [patientId]);

  const placeOrder = useCallback(async (
    order: Omit<ClinicalOrder, 'id' | 'patientId' | 'orderedAt' | 'createdAt' | 'updatedAt' | 'status'>,
  ): Promise<ClinicalOrder | null> => {
    setError(null);
    try {
      const result = await createOrder(patientId, order);
      setOrders(prev => [...prev, result]);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل إنشاء الطلب');
      return null;
    }
  }, [patientId]);

  const changeOrderStatus = useCallback(async (
    orderId: string,
    status: OrderStatus,
    notes?: string,
  ): Promise<ClinicalOrder | null> => {
    setError(null);
    try {
      const result = await updateOrderStatus(patientId, orderId, status, notes);
      setOrders(prev => prev.map(o => o.id === orderId ? result : o));
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحديث الطلب');
      return null;
    }
  }, [patientId]);

  const placeLabOrder = useCallback(async (
    priority: OrderPriority,
    tests: LabOrderRequest[],
    instructions?: string,
    indications?: string,
  ) => {
    setError(null);
    try {
      const result = await createLabOrder(patientId, { priority, tests, instructions, indications });
      setOrders(prev => [...prev, result]);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل إنشاء طلب المختبر');
      return null;
    }
  }, [patientId]);

  const placeRadiologyOrder = useCallback(async (
    priority: OrderPriority,
    exams: RadiologyOrderRequest[],
    clinicalIndication: string,
    instructions?: string,
  ) => {
    setError(null);
    try {
      const result = await createRadiologyOrder(patientId, { priority, exams, clinicalIndication, instructions });
      setOrders(prev => [...prev, result]);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل إنشاء طلب الأشعة');
      return null;
    }
  }, [patientId]);

  return {
    orders,
    isLoading,
    error,
    loadOrders,
    placeOrder,
    changeOrderStatus,
    placeLabOrder,
    placeRadiologyOrder,
  };
}
