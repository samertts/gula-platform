import { apiRequest } from './api';

export interface StaffMember {
  id: string;
  employeeId: string;
  name: string;
  nameAr: string;
  email: string;
  phone: string;
  department: string;
  departmentAr: string;
  role: string;
  roleAr: string;
  specialization: string;
  specializationAr: string;
  designation: string;
  designationAr: string;
  employmentType: 'full_time' | 'part_time' | 'contract' | 'locum';
  status: 'active' | 'on_leave' | 'suspended' | 'terminated';
  joiningDate: string;
  contractEndDate: string | null;
  qualifications: string[];
  languages: string[];
  shift: 'morning' | 'evening' | 'night' | 'rotating';
  emergencyContact: string;
  emergencyPhone: string;
  avatar: string | null;
  createdAt: string;
}

export interface StaffSchedule {
  id: string;
  staffId: string;
  staffName: string;
  staffNameAr: string;
  department: string;
  date: string;
  shift: 'morning' | 'evening' | 'night' | 'on_call' | 'off';
  startTime: string;
  endTime: string;
  ward: string;
  wardAr: string;
  notes: string;
}

export interface DepartmentStaffSummary {
  department: string;
  departmentAr: string;
  total: number;
  doctors: number;
  nurses: number;
  technicians: number;
  administrative: number;
  support: number;
  onLeave: number;
  presentToday: number;
}

export async function getStaff(params?: {
  department?: string;
  status?: string;
  role?: string;
  search?: string;
}): Promise<StaffMember[]> {
  const searchParams = new URLSearchParams();
  if (params?.department) searchParams.set('department', params.department);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.role) searchParams.set('role', params.role);
  if (params?.search) searchParams.set('search', params.search);
  const qs = searchParams.toString();
  return apiRequest(`/hospital/hr/staff${qs ? `?${qs}` : ''}`);
}

export async function getStaffMember(id: string): Promise<StaffMember> {
  return apiRequest(`/hospital/hr/staff/${id}`);
}

export async function getStaffSchedule(params?: {
  department?: string;
  date?: string;
  staffId?: string;
}): Promise<StaffSchedule[]> {
  const searchParams = new URLSearchParams();
  if (params?.department) searchParams.set('department', params.department);
  if (params?.date) searchParams.set('date', params.date);
  if (params?.staffId) searchParams.set('staffId', params.staffId);
  const qs = searchParams.toString();
  return apiRequest(`/hospital/hr/schedule${qs ? `?${qs}` : ''}`);
}

export async function getDepartmentStaffSummary(): Promise<DepartmentStaffSummary[]> {
  return apiRequest('/hospital/hr/staff-summary');
}

export async function getStaffStats(): Promise<{
  total: number;
  active: number;
  onLeave: number;
  doctors: number;
  nurses: number;
  technicians: number;
  administrative: number;
  support: number;
  contractEndingSoon: number;
}> {
  return apiRequest('/hospital/hr/stats');
}
