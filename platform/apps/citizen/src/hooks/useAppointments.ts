import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiRequest } from '../services/api';
import { cacheAppointments, getCachedAppointments } from '../services/offline';
import type { Appointment } from '../types';

export function useAppointments() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAppointments = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);

    try {
      if (navigator.onLine) {
        const response = await apiRequest<{ appointments: Appointment[] }>(
          `/citizen/patients/${user.id}/appointments`,
        );
        setAppointments(response.appointments);
        await cacheAppointments(response.appointments);
      } else {
        const cached = await getCachedAppointments();
        setAppointments(cached);
      }
    } catch (err) {
      const cached = await getCachedAppointments();
      if (cached.length > 0) {
        setAppointments(cached);
      }
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  const bookAppointment = useCallback(async (data: {
    providerId: string;
    facilityId: string;
    type: Appointment['type'];
    date: string;
    startTime: string;
    notes?: string;
    isVirtual?: boolean;
  }): Promise<Appointment> => {
    const response = await apiRequest<{ appointment: Appointment }>('/citizen/appointments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    setAppointments((prev) => [...prev, response.appointment]);
    return response.appointment;
  }, []);

  const cancelAppointment = useCallback(async (appointmentId: string) => {
    await apiRequest(`/citizen/appointments/${appointmentId}`, {
      method: 'DELETE',
    });
    setAppointments((prev) =>
      prev.map((a) =>
        a.id === appointmentId ? { ...a, status: 'cancelled' as const } : a,
      ),
    );
  }, []);

  const upcomingAppointments = appointments.filter(
    (a) => a.status === 'scheduled' || a.status === 'confirmed',
  ).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const pastAppointments = appointments.filter(
    (a) => a.status === 'completed' || a.status === 'cancelled' || a.status === 'no_show',
  ).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return {
    appointments,
    upcomingAppointments,
    pastAppointments,
    isLoading,
    error,
    refetch: fetchAppointments,
    bookAppointment,
    cancelAppointment,
  };
}
