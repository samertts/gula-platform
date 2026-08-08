export const GULA_SDK_VERSION = '1.0.0';

export interface SDKConfig {
  apiUrl: string;
  appId: string;
  version: string;
  locale?: string;
  debug?: boolean;
  offline?: boolean;
  telemetry?: boolean;
}

export class GulaSDK {
  private config: SDKConfig;
  private initialized = false;

  constructor(config: SDKConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;
    if (this.config.debug) {
      console.log(`[GULA SDK] Initializing v${GULA_SDK_VERSION}`);
    }
    this.initialized = true;
  }

  getConfig(): SDKConfig {
    return { ...this.config };
  }

  updateConfig(partial: Partial<SDKConfig>): void {
    this.config = { ...this.config, ...partial };
  }

  async callApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.config.apiUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-App-Id': this.config.appId,
        'X-App-Version': this.config.version,
      },
      ...options,
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  }
}

export const createSDK = (config: SDKConfig): GulaSDK => new GulaSDK(config);

export const generateBoilerplate = (type: 'app' | 'plugin' | 'theme' | 'integration'): string => {
  const templates: Record<string, string> = {
    app: `import { GulaSDK, createSDK } from '@gula/uap/sdk';

const sdk = createSDK({
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  appId: 'my-gula-app',
  version: '1.0.0',
});

export default sdk;
`,
    plugin: `import { usePluginLoader } from '@gula/uap/runtime';

export const manifest = {
  id: 'my-plugin',
  name: 'My Plugin',
  version: '1.0.0',
  description: 'A GULA plugin',
  author: 'Developer',
  permissions: [],
  entryPoint: '/plugins/my-plugin/index.js',
};

export const activate = () => {
  console.log('Plugin activated');
};

export const deactivate = () => {
  console.log('Plugin deactivated');
};
`,
    theme: `export default {
  name: 'custom-theme',
  colors: {
    primary: { 500: '#6366F1', 600: '#4F46E5' },
  },
  typography: {
    fontFamily: { arabic: '"Cairo", sans-serif' },
  },
};
`,
    integration: `import { GulaSDK } from '@gula/uap/sdk';

export class Integration {
  constructor(private sdk: GulaSDK) {}
  async connect(): Promise<void> {}
  async disconnect(): Promise<void> {}
  async send(data: unknown): Promise<void> {}
  async receive(): Promise<unknown> { return null; }
}
`,
  };
  return templates[type] || templates.app;
};
