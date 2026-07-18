import { apiRequest } from './api';
import { cacheFamily, getCachedFamily } from './offline';
import type { FamilyMember } from '../types';

export async function getFamilyMembers(): Promise<FamilyMember[]> {
  if (!navigator.onLine) {
    return getCachedFamily();
  }

  try {
    const response = await apiRequest<{ members: FamilyMember[] }>('/citizen/family');
    await cacheFamily(response.members);
    return response.members;
  } catch {
    return getCachedFamily();
  }
}

export async function addFamilyMember(
  data: Omit<FamilyMember, 'id' | 'citizenId' | 'createdAt'>,
): Promise<FamilyMember> {
  const response = await apiRequest<{ member: FamilyMember }>('/citizen/family', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.member;
}

export async function updateFamilyMember(
  memberId: string,
  data: Partial<FamilyMember>,
): Promise<FamilyMember> {
  const response = await apiRequest<{ member: FamilyMember }>(`/citizen/family/${memberId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return response.member;
}

export async function removeFamilyMember(memberId: string): Promise<void> {
  await apiRequest(`/citizen/family/${memberId}`, {
    method: 'DELETE',
  });
}

export async function getFamilyMemberHealthData(
  memberId: string,
): Promise<{ labResults: number; appointments: number; medications: number }> {
  return apiRequest(`/citizen/family/${memberId}/health-summary`) as Promise<{
    labResults: number;
    appointments: number;
    medications: number;
  }>;
}

export async function verifyFamilyMemberNationalId(
  nationalId: string,
): Promise<{ valid: boolean; name?: string }> {
  return apiRequest<{ valid: boolean; name?: string }>('/citizen/family/verify-national-id', {
    method: 'POST',
    body: JSON.stringify({ nationalId }),
  });
}
