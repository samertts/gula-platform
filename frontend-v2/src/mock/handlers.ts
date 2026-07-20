import { SyntheticDataStore } from './dataStore';

type ApiResponse = {
  status: number;
  body: any;
  headers?: Record<string, string>;
};

export class MockApiHandlers {
  private store: SyntheticDataStore;

  constructor(store: SyntheticDataStore) {
    this.store = store;
  }

  async handle(request: {
    method: string;
    path: string;
    body?: any;
    params?: Record<string, string>;
    headers?: Record<string, string>;
  }): Promise<ApiResponse> {
    const { method, path } = request;

    const wait = (ms: number) => new Promise(r => setTimeout(r, ms));
    await wait(100 + Math.random() * 200);

    try {
      return await this.route(method, path, request);
    } catch (error: any) {
      return {
        status: 500,
        body: { error: error.message || 'Internal server error' },
      };
    }
  }

  private async route(method: string, path: string, request: any): Promise<ApiResponse> {
    const parts = path.split('/').filter(Boolean);

    if (path === '/api/health') {
      return { status: 200, body: { status: 'healthy', mock: true, timestamp: new Date().toISOString() } };
    }

    if (path === '/api/mock/status') {
      return {
        status: 200,
        body: {
          mock: true,
          demoMode: true,
          data: this.store.getStats(),
          collections: this.store.getCollections(),
        },
      };
    }

    if (path === '/api/mock/reset') {
      this.store.reset();
      await this.store.initialize();
      return { status: 200, body: { message: 'Data store reset' } };
    }

    if (path === '/api/auth/login' || path === '/api/auth/demo-login') {
      return this.handleAuth(request.body);
    }

    if (path.startsWith('/api/patients')) {
      return this.handlePatients(method, path, request);
    }

    if (path.startsWith('/api/labs')) {
      return this.handleCollection(method, path, 'labs', request);
    }

    if (path.startsWith('/api/orders')) {
      return this.handleOrders(method, path, request);
    }

    if (path.startsWith('/api/results')) {
      return this.handleCollection(method, path, 'labResults', request);
    }

    if (path.startsWith('/api/samples')) {
      return this.handleCollection(method, path, 'samples', request);
    }

    if (path.startsWith('/api/documents')) {
      return this.handleCollection(method, path, 'documents', request);
    }

    if (path.startsWith('/api/users')) {
      return this.handleCollection(method, path, 'users', request);
    }

    if (path.startsWith('/api/notifications')) {
      return { status: 200, body: { data: [], total: 0 } };
    }

    if (path.startsWith('/api/analytics') || path.startsWith('/api/stats')) {
      return this.handleAnalytics(method, path);
    }

    if (path.startsWith('/api/ai')) {
      return this.handleAi(method, path, request);
    }

    if (path.startsWith('/api/ocr')) {
      return this.handleOcr(request);
    }

    if (path.startsWith('/api/fhir')) {
      return this.handleFhir(method, path, request);
    }

    if (path.startsWith('/api/dashboard')) {
      return this.handleDashboard();
    }

    if (path.startsWith('/api/feature-flags')) {
      return this.handleFeatureFlags(method, request);
    }

    return { status: 404, body: { error: `Mock endpoint not found: ${path}` } };
  }

  private handleAuth(body: any): ApiResponse {
    const role = body?.role || 'doctor';
    const users = this.store.get<any>('users');
    const user = users.find((u: any) => u.role === role) || {
      id: 'demo-user-1',
      email: `${role}@demo.gula-platform.org`,
      name: `Demo ${role.charAt(0).toUpperCase() + role.slice(1)}`,
      nameAr: role === 'doctor' ? 'طبيب تجريبي' : 'مستخدم تجريبي',
      role,
      labId: 'demo-lab-1',
    };

    return {
      status: 200,
      body: {
        token: `demo-token-${role}-${Date.now()}`,
        user,
        demoMode: true,
        expiresIn: 86400,
      },
    };
  }

  private handlePatients(method: string, path: string, request: any): ApiResponse {
    if (method === 'GET' && path === '/api/patients') {
      const patients = this.store.get<any>('patients');
      const page = parseInt(request.params?.page || '1');
      const limit = parseInt(request.params?.limit || '20');
      const start = (page - 1) * limit;
      return {
        status: 200,
        body: {
          data: patients.slice(start, start + limit),
          total: patients.length,
          page,
          limit,
        },
      };
    }

    if (method === 'GET' && path.match(/^\/api\/patients\/[^/]+$/)) {
      const id = path.split('/').pop()!;
      const patient = this.store.getById('patients', id);
      if (patient) return { status: 200, body: patient };
      return { status: 404, body: { error: 'Patient not found' } };
    }

    if (method === 'POST' && path === '/api/patients') {
      const newPatient = { id: `PAT-${Date.now()}`, ...request.body, createdAt: new Date().toISOString() };
      this.store.add('patients', newPatient);
      return { status: 201, body: newPatient };
    }

    return { status: 404, body: { error: 'Not found' } };
  }

  private handleOrders(method: string, path: string, request: any): ApiResponse {
    if (method === 'GET' && path === '/api/orders') {
      const orders = this.store.get<any>('orders');
      return { status: 200, body: { data: orders, total: orders.length } };
    }
    if (method === 'POST' && path === '/api/orders') {
      const newOrder = { id: `ORD-${Date.now()}`, ...request.body, createdAt: new Date().toISOString() };
      this.store.add('orders', newOrder);
      return { status: 201, body: newOrder };
    }
    return { status: 200, body: { data: this.store.get<any>('orders'), total: this.store.get<any>('orders').length } };
  }

  private handleCollection(method: string, path: string, collection: string, request: any): ApiResponse {
    const data = this.store.get<any>(collection);

    if (method === 'GET') {
      const id = path.split('/').pop();
      if (id && path.match(new RegExp(`/api/${collection}/[^/]+$`))) {
        const item = data.find((d: any) => d.id === id);
        if (item) return { status: 200, body: item };
        return { status: 404, body: { error: 'Not found' } };
      }
      return { status: 200, body: { data, total: data.length } };
    }

    if (method === 'POST') {
      const newItem = { id: `${collection.toUpperCase().slice(0, 3)}-${Date.now()}`, ...request.body };
      this.store.add(collection, newItem);
      return { status: 201, body: newItem };
    }

    if (method === 'PUT' || method === 'PATCH') {
      const id = path.split('/').pop();
      const updated = this.store.update(collection, id!, request.body);
      if (updated) return { status: 200, body: updated };
      return { status: 404, body: { error: 'Not found' } };
    }

    if (method === 'DELETE') {
      const id = path.split('/').pop();
      const deleted = this.store.delete(collection, id!);
      if (deleted) return { status: 200, body: { message: 'Deleted' } };
      return { status: 404, body: { error: 'Not found' } };
    }

    return { status: 200, body: { data, total: data.length } };
  }

  private handleAnalytics(method: string, path: string): ApiResponse {
    const patients = this.store.get<any>('patients');
    const results = this.store.get<any>('labResults');
    const orders = this.store.get<any>('orders');

    if (path.includes('dashboard') || path.endsWith('/analytics')) {
      return {
        status: 200,
        body: {
          totalPatients: patients.length,
          totalResults: results.length,
          totalOrders: orders.length,
          pendingOrders: orders.filter(o => o.status === 'pending').length,
          completedToday: results.filter(r =>
            r.completedAt && new Date(r.completedAt).toDateString() === new Date().toDateString()
          ).length,
          abnormalResults: results.filter(r => r.isAbnormal).length,
          averageProcessingTime: Math.round(45 + Math.random() * 60),
          testsByType: this.generateTestDistribution(results),
          monthlyTrend: this.generateMonthlyTrend(12),
          labPerformance: this.store.get<any>('labs').slice(0, 5).map(lab => ({
            labId: lab.id,
            labName: lab.name,
            testsProcessed: Math.floor(Math.random() * 500) + 100,
            avgTurnaround: Math.floor(Math.random() * 120) + 30,
            accuracy: 95 + Math.random() * 5,
          })),
        },
      };
    }

    return { status: 200, body: {} };
  }

  private generateTestDistribution(results: any[]): Record<string, number> {
    const dist: Record<string, number> = {};
    for (const r of results.slice(0, 200)) {
      dist[r.testName] = (dist[r.testName] || 0) + 1;
    }
    return dist;
  }

  private generateMonthlyTrend(months: number): { month: string; count: number }[] {
    const trend: { month: string; count: number }[] = [];
    const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for (let i = 0; i < months; i++) {
      trend.push({
        month: names[i % 12],
        count: Math.floor(Math.random() * 500) + 200,
      });
    }
    return trend;
  }

  private handleDashboard(): ApiResponse {
    const patients = this.store.get<any>('patients');
    const results = this.store.get<any>('labResults');
    const orders = this.store.get<any>('orders');

    return {
      status: 200,
      body: {
        stats: {
          patients: patients.length,
          results: results.length,
          orders: orders.length,
          activeLabs: this.store.get<any>('labs').filter(l => l.status === 'active').length,
          pendingReviews: orders.filter(o => o.status === 'completed').length,
          criticalResults: results.filter(r => r.isAbnormal).length,
        },
        recentActivity: results.slice(-10).map(r => ({
          id: r.id,
          type: 'result',
          message: `Result ${r.testName} completed`,
          timestamp: r.completedAt,
        })),
        alerts: [
          { id: '1', severity: 'high', message: 'Abnormal results pending review', count: results.filter(r => r.isAbnormal).length },
          { id: '2', severity: 'medium', message: 'Quality control checks due', count: 5 },
          { id: '3', severity: 'low', message: 'System running optimally', count: 0 },
        ],
      },
    };
  }

  private handleAi(method: string, path: string, request: any): ApiResponse {
    if (path.includes('chat') || path.includes('assistant')) {
      const query = request.body?.query || request.body?.message || '';
      const isArabic = /[\u0600-\u06FF]/.test(query);
      return {
        status: 200,
        body: {
          response: isArabic
            ? 'هذه استجابة تجريبية من المساعد الطبي. في الإنتاج، سيتم تحليل بياناتك الطبية وتقديم توصيات مخصصة.'
            : 'This is a demo response from the medical assistant. In production, your medical data will be analyzed and personalized recommendations provided.',
          model: 'demo-gemini',
          confidence: 0.95,
          demoMode: true,
        },
      };
    }

    if (path.includes('analyze')) {
      return {
        status: 200,
        body: {
          summary: 'Demo analysis completed. Patient results are within normal ranges.',
          findings: [
            { parameter: 'Hemoglobin', value: '14.2 g/dL', status: 'normal' },
            { parameter: 'WBC', value: '7.5 K/uL', status: 'normal' },
            { parameter: 'Glucose', value: '95 mg/dL', status: 'normal' },
          ],
          recommendations: ['Continue regular monitoring', 'Maintain healthy diet'],
          demoMode: true,
        },
      };
    }

    if (path.includes('summarize')) {
      return {
        status: 200,
        body: {
          summary: 'Patient has completed routine blood work. All results are within expected ranges.',
          keyFindings: ['Normal complete blood count', 'Normal metabolic panel'],
          recommendations: [],
        },
      };
    }

    return { status: 200, body: { response: 'AI service is running in demo mode.', demoMode: true } };
  }

  private handleOcr(request: any): ApiResponse {
    return {
      status: 200,
      body: {
        text: 'Demo OCR Text: Patient Name: John Doe\nDate: 2024-01-15\nHemoglobin: 14.2 g/dL\nWBC: 7.5 K/uL\nGlucose: 95 mg/dL',
        confidence: 0.97,
        processingTimeMs: 1250,
        pages: 1,
        language: 'eng',
        demoMode: true,
      },
    };
  }

  private handleFhir(method: string, path: string, request: any): ApiResponse {
    if (path.includes('Patient')) {
      return {
        status: 200,
        body: {
          resourceType: 'Bundle',
          type: 'searchset',
          total: this.store.get<any>('patients').length,
          entry: this.store.get<any>('patients').slice(0, 10).map((p: any) => ({
            resource: {
              resourceType: 'Patient',
              id: p.id,
              name: [{ text: p.name, given: [p.firstName], family: p.lastName }],
              gender: p.gender,
              birthDate: p.dateOfBirth?.split('T')[0],
            },
          })),
        },
      };
    }

    if (path.includes('Observation')) {
      return {
        status: 200,
        body: {
          resourceType: 'Bundle',
          type: 'searchset',
          total: this.store.get<any>('labResults').length,
          entry: this.store.get<any>('labResults').slice(0, 10).map((r: any) => ({
            resource: {
              resourceType: 'Observation',
              id: r.id,
              status: 'final',
              code: { text: r.testName },
              valueQuantity: { value: parseFloat(r.value), unit: r.unit },
              referenceRange: [{ text: r.referenceRange }],
            },
          })),
        },
      };
    }

    return { status: 200, body: { resourceType: 'Bundle', entry: [] } };
  }

  private handleFeatureFlags(method: string, request: any): ApiResponse {
    if (method === 'GET') {
      return {
        status: 200,
        body: {
          ai: true,
          ocr: true,
          fhir: true,
          notifications: true,
          analytics: true,
          knowledgeGraph: true,
          experimental: false,
          demoMode: true,
        },
      };
    }
    if (method === 'PUT' || method === 'PATCH') {
      return { status: 200, body: { ...request.body, updated: true } };
    }
    return { status: 200, body: { message: 'Feature flags service' } };
  }
}
