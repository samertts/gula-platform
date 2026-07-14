import { GulaClient } from '../client';
import {
  FhirPatient, FhirPractitioner, FhirOrganization,
  FhirObservation, FhirDiagnosticReport, FhirSpecimen,
  FhirServiceRequest, FhirDevice, FhirEncounter, FhirBundle,
} from '../types';

export class FHIRAPI {
  constructor(private client: GulaClient) {}

  // ── Patient ──
  async readPatient(id: string): Promise<FhirPatient> {
    return this.client.get<FhirPatient>(`/fhir/Patient/${id}`);
  }

  async searchPatient(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Patient', params);
  }

  async createPatient(data: FhirPatient): Promise<FhirPatient> {
    return this.client.post<FhirPatient>('/fhir/Patient', data);
  }

  async updatePatient(id: string, data: FhirPatient): Promise<FhirPatient> {
    return this.client.put<FhirPatient>(`/fhir/Patient/${id}`, data);
  }

  // ── Practitioner ──
  async readPractitioner(id: string): Promise<FhirPractitioner> {
    return this.client.get<FhirPractitioner>(`/fhir/Practitioner/${id}`);
  }

  async searchPractitioner(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Practitioner', params);
  }

  // ── Organization ──
  async readOrganization(id: string): Promise<FhirOrganization> {
    return this.client.get<FhirOrganization>(`/fhir/Organization/${id}`);
  }

  async searchOrganization(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Organization', params);
  }

  // ── Observation ──
  async readObservation(id: string): Promise<FhirObservation> {
    return this.client.get<FhirObservation>(`/fhir/Observation/${id}`);
  }

  async searchObservation(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Observation', params);
  }

  async createObservation(data: FhirObservation): Promise<FhirObservation> {
    return this.client.post<FhirObservation>('/fhir/Observation', data);
  }

  // ── DiagnosticReport ──
  async readDiagnosticReport(id: string): Promise<FhirDiagnosticReport> {
    return this.client.get<FhirDiagnosticReport>(`/fhir/DiagnosticReport/${id}`);
  }

  async searchDiagnosticReport(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/DiagnosticReport', params);
  }

  async createDiagnosticReport(data: FhirDiagnosticReport): Promise<FhirDiagnosticReport> {
    return this.client.post<FhirDiagnosticReport>('/fhir/DiagnosticReport', data);
  }

  // ── Specimen ──
  async readSpecimen(id: string): Promise<FhirSpecimen> {
    return this.client.get<FhirSpecimen>(`/fhir/Specimen/${id}`);
  }

  async searchSpecimen(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Specimen', params);
  }

  async createSpecimen(data: FhirSpecimen): Promise<FhirSpecimen> {
    return this.client.post<FhirSpecimen>('/fhir/Specimen', data);
  }

  // ── ServiceRequest ──
  async readServiceRequest(id: string): Promise<FhirServiceRequest> {
    return this.client.get<FhirServiceRequest>(`/fhir/ServiceRequest/${id}`);
  }

  async searchServiceRequest(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/ServiceRequest', params);
  }

  // ── Device ──
  async readDevice(id: string): Promise<FhirDevice> {
    return this.client.get<FhirDevice>(`/fhir/Device/${id}`);
  }

  async searchDevice(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Device', params);
  }

  // ── Encounter ──
  async readEncounter(id: string): Promise<FhirEncounter> {
    return this.client.get<FhirEncounter>(`/fhir/Encounter/${id}`);
  }

  async searchEncounter(params?: Record<string, string>): Promise<FhirBundle> {
    return this.client.get<FhirBundle>('/fhir/Encounter', params);
  }

  // ── Capability Statement ──
  async capabilityStatement(): Promise<Record<string, unknown>> {
    return this.client.get('/fhir/metadata');
  }

  // ── Batch/Transaction ──
  async batch(data: FhirBundle): Promise<FhirBundle> {
    return this.client.post<FhirBundle>('/fhir', data);
  }
}
