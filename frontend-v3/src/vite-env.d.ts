/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_DEMO_MODE_ENABLED?: string;
  readonly VITE_DEMO_MODE_EXPIRES_AT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
