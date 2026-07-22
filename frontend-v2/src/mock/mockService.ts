import { MockApiHandlers } from './handlers';
import { SyntheticDataStore } from './dataStore';
import { getConfig } from './config';

export class MockService {
  private static instance: MockService;
  private store: SyntheticDataStore;
  private handlers: MockApiHandlers;
  private initialized = false;

  private constructor() {
    this.store = SyntheticDataStore.getInstance();
    this.handlers = new MockApiHandlers(this.store);
  }

  static getInstance(): MockService {
    if (!MockService.instance) {
      MockService.instance = new MockService();
    }
    return MockService.instance;
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;
    await this.store.initialize();
    this.initialized = true;

    if (typeof window !== 'undefined') {
      this.installInterceptor();
    }
  }

  private installInterceptor(): void {
    const originalFetch = window.fetch.bind(window);

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
      const method = init?.method || 'GET';
      const config = getConfig();

      if (!config.enabled) {
        return originalFetch(input, init);
      }

      if (!this.shouldMock(url)) {
        return originalFetch(input, init);
      }

      const body = init?.body ? JSON.parse(init.body as string) : undefined;
      const path = url.replace(/^https?:\/\/[^/]+/, '').split('?')[0] ?? '';

      const response = await this.handlers.handle({
        method,
        path,
        body,
        headers: init?.headers as Record<string, string> | undefined,
      });

      return new Response(JSON.stringify(response.body), {
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'X-Mock': 'true',
          'X-Demo': 'true',
          ...response.headers,
        },
      });
    };
  }

  private shouldMock(url: string): boolean {
    const config = getConfig();
    if (!config.enabled) return false;

    const path = url.replace(/^https?:\/\/[^/]+/, '').split('?')[0];

    if (path!.startsWith('/api/mock/')) return true;
    if (path!.startsWith('/api/')) return true;

    return false;
  }

  getStore(): SyntheticDataStore {
    return this.store;
  }

  async reset(): Promise<void> {
    this.store.reset();
    await this.store.initialize();
  }

  isInitialized(): boolean {
    return this.initialized;
  }
}
