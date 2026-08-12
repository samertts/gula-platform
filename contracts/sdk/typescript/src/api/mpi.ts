import { GulaClient } from '../client';
import {
  ResolveRequest, ResolveResponse, CitizenResponse,
  MergeRequest, MergeResponse, PendingReviewPage,
  ResolveDecisionBody,
} from '../types';

export class MPIAPI {
  constructor(private client: GulaClient) {}

  async resolve(data: ResolveRequest): Promise<ResolveResponse> {
    return this.client.post<ResolveResponse>('/mpi/resolve', data);
  }

  async getCitizen(ulid: string): Promise<CitizenResponse> {
    return this.client.get<CitizenResponse>(`/mpi/citizens/${ulid}`);
  }

  async merge(data: MergeRequest): Promise<MergeResponse> {
    return this.client.post<MergeResponse>('/mpi/merge', data);
  }

  async getPendingReview(): Promise<PendingReviewPage> {
    return this.client.get<PendingReviewPage>('/mpi/review');
  }

  async resolveClaim(claimId: number, data: ResolveDecisionBody): Promise<void> {
    return this.client.post(`/mpi/review/${claimId}/decide`, data);
  }
}
