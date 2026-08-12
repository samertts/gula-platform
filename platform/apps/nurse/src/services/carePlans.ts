import { api } from './api';
import type { CarePlan as Plan, CareGoal, CareIntervention } from '../utils/types';

interface BackendActivity {
  id?: string;
  description?: string;
  description_ar?: string;
  frequency?: string;
  status?: string;
}

interface BackendGoal {
  id?: string;
  description?: string;
  description_ar?: string;
  target_date?: string | null;
  status?: string;
  activities?: BackendActivity[];
}

interface BackendCarePlan {
  id?: string;
  patient_id?: string;
  title?: string;
  title_ar?: string;
  description?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  status?: string;
  created_by?: string | null;
  goals?: BackendGoal[];
}

function text(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function mapGoal(goal: BackendGoal, index: number): CareGoal {
  const status = goal.status === 'achieved' || goal.status === 'revised' ? goal.status : 'pending';
  return {
    id: text(goal.id, `goal-${index}`),
    description: text(goal.description_ar || goal.description, '—'),
    targetDate: text(goal.target_date, '—'),
    status,
  };
}

function mapInterventions(goals: BackendGoal[]): CareIntervention[] {
  return goals.flatMap((goal) => (goal.activities || []).map((activity, index) => ({
    id: text(activity.id, `activity-${index}`),
    description: text(activity.description_ar || activity.description, '—'),
    frequency: text(activity.frequency, '—'),
    status: activity.status === 'discontinued' ? 'discontinued' : 'active',
  })));
}

export function mapBackendCarePlan(plan: BackendCarePlan): Plan {
  const goals = plan.goals || [];
  return {
    id: text(plan.id, 'unknown'),
    patientId: text(plan.patient_id, 'unknown'),
    patientName: text(plan.patient_id, 'معرّف المريض'),
    bed: '—',
    diagnosis: text(plan.title_ar || plan.title || plan.description, '—'),
    goals: goals.map(mapGoal),
    interventions: mapInterventions(goals),
    startDate: text(plan.period_start, '—'),
    reviewDate: text(plan.period_end, '—'),
    status: plan.status === 'completed' ? 'completed' : plan.status === 'revised' ? 'revised' : 'active',
    createdBy: text(plan.created_by, 'Backend'),
  };
}

export async function getPatientCarePlans(patientId: string): Promise<Plan[]> {
  const response = await api.get<BackendCarePlan[]>(`/patients/${encodeURIComponent(patientId)}/care-plans`);
  return response.map(mapBackendCarePlan);
}
