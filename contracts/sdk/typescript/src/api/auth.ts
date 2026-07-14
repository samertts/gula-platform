import { GulaClient } from '../client';
import {
  LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
  ChangePasswordRequest, CitizenRegisterRequest, StaffRegisterRequest,
  DoctorRegisterRequest, LabRegisterRequest, DeviceTokenRequest,
  CitizenLoginRequest, LinkIdentityRequest,
} from '../types';

export class AuthAPI {
  constructor(private client: GulaClient) {}

  async login(data: LoginRequest): Promise<LoginResponse> {
    return this.client.post<LoginResponse>('/login', data);
  }

  async refresh(data: RefreshRequest): Promise<RefreshResponse> {
    return this.client.post<RefreshResponse>('/auth/refresh', data);
  }

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    return this.client.post('/auth/change-password', data);
  }

  async registerLab(data: LabRegisterRequest): Promise<{ id: number; message: string }> {
    return this.client.post('/register', data);
  }

  async registerCitizen(data: CitizenRegisterRequest): Promise<LoginResponse> {
    return this.client.post<LoginResponse>('/register/citizen', data);
  }

  async registerStaff(data: StaffRegisterRequest): Promise<LoginResponse> {
    return this.client.post<LoginResponse>('/register/staff', data);
  }

  async registerDoctor(data: DoctorRegisterRequest): Promise<LoginResponse> {
    return this.client.post<LoginResponse>('/register/doctor', data);
  }

  async citizenLogin(data: CitizenLoginRequest): Promise<LoginResponse> {
    return this.client.post<LoginResponse>('/citizen/login', data);
  }

  async registerDevice(data: DeviceTokenRequest): Promise<void> {
    return this.client.post('/mobile/register-device', data);
  }

  async linkIdentity(data: LinkIdentityRequest): Promise<void> {
    return this.client.post('/identity/link', data);
  }

  async verifyNationalId(data: { national_id: string }): Promise<{ valid: boolean }> {
    return this.client.post('/national-id/verify', data);
  }

  async getProfile(): Promise<{ id: number; email: string; name: string; role: string; lab_id?: number }> {
    return this.client.get('/auth/me');
  }
}
