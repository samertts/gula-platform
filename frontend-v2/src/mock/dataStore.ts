import { DemoDataGenerator } from './demoData';

export class SyntheticDataStore {
  private static instance: SyntheticDataStore;
  private data: Record<string, any[]> = {};
  private generator: DemoDataGenerator;

  private constructor() {
    this.generator = new DemoDataGenerator();
  }

  static getInstance(): SyntheticDataStore {
    if (!SyntheticDataStore.instance) {
      SyntheticDataStore.instance = new SyntheticDataStore();
    }
    return SyntheticDataStore.instance;
  }

  async initialize(): Promise<void> {
    this.data = {
      patients: this.generator.generatePatients(1000),
      labs: this.generator.generateLabs(100),
      hospitals: this.generator.generateHospitals(20),
      doctors: this.generator.generateDoctors(100),
      labResults: this.generator.generateLabResults(5000),
      documents: this.generator.generateDocuments(2000),
      orders: this.generator.generateOrders(3000),
      samples: this.generator.generateSamples(3000),
      notifications: [],
      users: this.generator.generateUsers(50),
      appointments: this.generator.generateAppointments(2000),
      auditLogs: [],
    };
  }

  get<T>(collection: string): T[] {
    return (this.data[collection] || []) as T[];
  }

  getById<T extends { id: string }>(collection: string, id: string): T | undefined {
    return (this.data[collection] || []).find((item: any) => item.id === id) as T | undefined;
  }

  query<T>(collection: string, filter: (item: T) => boolean): T[] {
    return (this.data[collection] || []).filter(filter) as T[];
  }

  add(collection: string, item: any): void {
    if (!this.data[collection]) this.data[collection] = [];
    this.data[collection].push(item);
  }

  update(collection: string, id: string, updates: Record<string, any>): any | undefined {
    const index = (this.data[collection] || []).findIndex((item: any) => item.id === id);
    if (index !== -1) {
      this.data[collection][index] = { ...this.data[collection][index], ...updates };
      return this.data[collection][index];
    }
    return undefined;
  }

  delete(collection: string, id: string): boolean {
    const index = (this.data[collection] || []).findIndex((item: any) => item.id === id);
    if (index !== -1) {
      this.data[collection].splice(index, 1);
      return true;
    }
    return false;
  }

  getStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    for (const [key, val] of Object.entries(this.data)) {
      stats[key] = val.length;
    }
    return stats;
  }

  getCollections(): string[] {
    return Object.keys(this.data);
  }

  reset(): void {
    this.data = {};
  }
}
