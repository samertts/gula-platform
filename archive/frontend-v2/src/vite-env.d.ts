/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_ENV: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_API_BASE: string;
  readonly VITE_USE_MOCK: string;
  readonly VITE_DEMO_MODE: string;
  readonly VITE_DEMO_BANNER: string;
  readonly VITE_FEATURE_AI: string;
  readonly VITE_FEATURE_OCR: string;
  readonly VITE_FEATURE_FHIR: string;
  readonly VITE_FEATURE_NOTIFICATIONS: string;
  readonly VITE_FEATURE_ANALYTICS: string;
  readonly VITE_FEATURE_KNOWLEDGE_GRAPH: string;
  readonly VITE_FEATURE_EXPERIMENTAL: string;
  readonly VITE_POSTHOG_KEY: string;
  readonly VITE_POSTHOG_HOST: string;
  readonly VITE_SENTRY_DSN: string;
  readonly VITE_TELEMETRY_DISABLED: string;
  readonly VITE_GEMINI_API_KEY: string;
  readonly VITE_MOCK_LATENCY: string;
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
