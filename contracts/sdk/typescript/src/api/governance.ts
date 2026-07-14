import { GulaClient } from '../client';
import {
  NodeCreate, GovernanceNode, DelegationCreate, ActingAppoint,
  WorkerCreate, HealthcareWorker, LabRegister, GovernanceLab,
  ListResponse, PaginationParams,
} from '../types';

export class GovernanceAPI {
  constructor(private client: GulaClient) {}

  async createNode(data: NodeCreate): Promise<GovernanceNode> {
    return this.client.post<GovernanceNode>('/governance/nodes', data);
  }

  async listNodes(params?: PaginationParams & { node_type?: string }): Promise<ListResponse<GovernanceNode>> {
    return this.client.get<ListResponse<GovernanceNode>>('/governance/nodes', params as Record<string, unknown>);
  }

  async getNode(id: number): Promise<GovernanceNode> {
    return this.client.get<GovernanceNode>(`/governance/nodes/${id}`);
  }

  async updateNode(id: number, data: Partial<NodeCreate>): Promise<GovernanceNode> {
    return this.client.put<GovernanceNode>(`/governance/nodes/${id}`, data);
  }

  async deleteNode(id: number): Promise<void> {
    return this.client.delete(`/governance/nodes/${id}`);
  }

  async createDelegation(data: DelegationCreate): Promise<{ id: number }> {
    return this.client.post('/governance/delegations', data);
  }

  async listDelegations(params?: PaginationParams): Promise<ListResponse<{ id: number; delegator: string; delegate: string }>> {
    return this.client.get('/governance/delegations', params as Record<string, unknown>);
  }

  async appointActing(data: ActingAppoint): Promise<{ id: number }> {
    return this.client.post('/governance/acting-appointments', data);
  }

  async listActingAppointments(params?: PaginationParams): Promise<ListResponse<{ id: number; node: string; acting_node: string }>> {
    return this.client.get('/governance/acting-appointments', params as Record<string, unknown>);
  }

  async createWorker(data: WorkerCreate): Promise<HealthcareWorker> {
    return this.client.post<HealthcareWorker>('/governance/workers', data);
  }

  async listWorkers(params?: PaginationParams & { profession?: string }): Promise<ListResponse<HealthcareWorker>> {
    return this.client.get<ListResponse<HealthcareWorker>>('/governance/workers', params as Record<string, unknown>);
  }

  async getWorker(id: number): Promise<HealthcareWorker> {
    return this.client.get<HealthcareWorker>(`/governance/workers/${id}`);
  }

  async updateWorker(id: number, data: Partial<WorkerCreate>): Promise<HealthcareWorker> {
    return this.client.put<HealthcareWorker>(`/governance/workers/${id}`, data);
  }

  async registerLab(data: LabRegister): Promise<GovernanceLab> {
    return this.client.post<GovernanceLab>('/governance/laboratories', data);
  }

  async listGovernanceLabs(params?: PaginationParams): Promise<ListResponse<GovernanceLab>> {
    return this.client.get<ListResponse<GovernanceLab>>('/governance/laboratories', params as Record<string, unknown>);
  }

  async getGovernanceLab(id: number): Promise<GovernanceLab> {
    return this.client.get<GovernanceLab>(`/governance/laboratories/${id}`);
  }
}
