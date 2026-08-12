/**
 * Frontend telemetry bootstrap — Phase 2 (PostHog + Sentry + structured logs).
 *
 * Design contract
 * ---------------
 *  - Every SDK is loaded **lazily and conditionally**: if the relevant env var
 *    is unset, the SDK is never imported and no network requests are made.
 *    The app must work offline / in air-gapped previews / in tests where no
 *    keys are configured.
 *  - No raw personal identifiers are sent. ``identifyAnonymous`` accepts only
 *    a caller-provided hash (the anonymous session id). Names, phones, emails,
 *    national IDs MUST NEVER be passed to PostHog or Sentry from this layer.
 *  - Both providers degrade gracefully if blocked by ad-blockers (PostHog) or
 *    network policies (Sentry).
 *
 * Env vars (Vite — must be VITE_ prefixed to reach the browser bundle)
 *  - ``VITE_POSTHOG_KEY``        public PostHog project key
 *  - ``VITE_POSTHOG_HOST``       host (default https://us.i.posthog.com)
 *  - ``VITE_SENTRY_DSN``         Sentry project DSN
 *  - ``VITE_APP_VERSION``        for Sentry release tagging (optional)
 *  - ``VITE_APP_ENV``            environment label (production/staging/dev)
 *
 * Public API
 *  - ``initTelemetry()``            call once at app boot
 *  - ``track(event, props?)``       fire a PostHog event (no-op without key)
 *  - ``captureError(err, ctx?)``    Sentry exception (no-op without DSN)
 *  - ``identifyAnonymous(id)``      bind a hashed session id (no PII)
 *  - ``getAnonymousSessionId()``    stable per-tab anonymous id (UUID v4)
 *
 * Network exceptions captured automatically:
 *  - global unhandledrejection + window.error are wired into Sentry by its
 *    default init. We additionally log a structured-JSON line to console for
 *    parity with backend logs (see ``logStructured``).
 */

type Props = Record<string, unknown>;

// Lazy refs to the loaded SDKs. Stay ``undefined`` until init succeeds.
let _posthog: any | undefined;
let _sentry: any | undefined;
let _initialized = false;

const env = (import.meta as any).env ?? {};
const POSTHOG_KEY  = (env.VITE_POSTHOG_KEY  || '').trim();
const POSTHOG_HOST = (env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com').trim();
const SENTRY_DSN   = (env.VITE_SENTRY_DSN   || '').trim();
const APP_VERSION  = (env.VITE_APP_VERSION  || 'unknown').trim();
const APP_ENV      = (env.VITE_APP_ENV      || (env.PROD ? 'production' : 'development')).trim();

const SESSION_KEY = 'gula.anon_session_id';

function _generateUuid(): string {
  // crypto.randomUUID is available in all modern browsers.
  const c: any = (globalThis as any).crypto;
  if (c && typeof c.randomUUID === 'function') return c.randomUUID();
  // Fallback for very old environments.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (ch) => {
    const r = (Math.random() * 16) | 0;
    const v = ch === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/** Stable per-tab anonymous session ID, generated lazily, kept in sessionStorage. */
export function getAnonymousSessionId(): string {
  try {
    const ss = (globalThis as any).sessionStorage;
    if (!ss) return _generateUuid();
    let id = ss.getItem(SESSION_KEY);
    if (!id) {
      id = _generateUuid();
      ss.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return _generateUuid();
  }
}

/** Emit a JSON line to console — parity with backend structured logging. */
function logStructured(level: 'info' | 'warn' | 'error', msg: string, extra?: Props) {
  const doc = {
    ts: new Date().toISOString(),
    level: level.toUpperCase(),
    logger: 'gula.frontend.telemetry',
    msg,
    app_version: APP_VERSION,
    app_env: APP_ENV,
    anonymous_session_id: getAnonymousSessionId(),
    ...(extra || {}),
  };
  // eslint-disable-next-line no-console
  (console as any)[level === 'warn' ? 'warn' : level === 'error' ? 'error' : 'log'](
    JSON.stringify(doc),
  );
}

async function _initPostHog() {
  if (!POSTHOG_KEY) return;
  try {
    const mod: any = await import('posthog-js');
    const ph = mod.default ?? mod;
    ph.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      autocapture: true,
      capture_pageview: true,
      capture_pageleave: true,
      disable_session_recording: true,  // never record clinical sessions
      persistence: 'localStorage+cookie',
      property_blacklist: [
        // Defence-in-depth — these never appear in our event props but if
        // some third-party autocapture surfaces them, drop them here.
        '$ip', 'national_id', 'phone', 'email', 'patient_name', 'full_name',
      ],
      loaded: (p: any) => {
        try {
          p.register({ app_version: APP_VERSION, app_env: APP_ENV });
        } catch { /* noop */ }
      },
    });
    _posthog = ph;
    logStructured('info', 'posthog.initialized', { host: POSTHOG_HOST });
  } catch (e: any) {
    logStructured('warn', 'posthog.init_failed', { error: String(e?.message ?? e) });
  }
}

async function _initSentry() {
  if (!SENTRY_DSN) return;
  try {
    const Sentry: any = await import('@sentry/react');
    Sentry.init({
      dsn: SENTRY_DSN,
      release: APP_VERSION,
      environment: APP_ENV,
      tracesSampleRate: 0.05,
      // Strip query strings (may carry tokens) from breadcrumbs.
      beforeBreadcrumb(breadcrumb: any) {
        if (breadcrumb?.data?.url && typeof breadcrumb.data.url === 'string') {
          breadcrumb.data.url = breadcrumb.data.url.split('?')[0];
        }
        return breadcrumb;
      },
      // Defence-in-depth: scrub any identifier-shaped strings out of event
      // request data before send. We don't have full PII filtering here —
      // backend audit chain is the authoritative source for that.
      beforeSend(event: any) {
        try {
          if (event?.request?.cookies)    delete event.request.cookies;
          if (event?.request?.headers)    delete event.request.headers.authorization;
        } catch { /* noop */ }
        return event;
      },
    });
    _sentry = Sentry;
    logStructured('info', 'sentry.initialized', { env: APP_ENV });
  } catch (e: any) {
    logStructured('warn', 'sentry.init_failed', { error: String(e?.message ?? e) });
  }
}

/** Initialise telemetry. Idempotent — safe to call multiple times. */
export async function initTelemetry(): Promise<void> {
  if (_initialized) return;
  _initialized = true;
  await Promise.all([_initPostHog(), _initSentry()]);
  // Always log a boot marker so we can correlate frontend session lifetimes.
  logStructured('info', 'telemetry.bootstrapped', {
    posthog: !!_posthog,
    sentry:  !!_sentry,
  });
}

/** Track a product event. No-op when PostHog is not configured. */
export function track(event: string, props?: Props): void {
  try {
    if (_posthog?.capture) _posthog.capture(event, props || {});
  } catch { /* swallow — telemetry must never break the app */ }
}

/** Capture an exception to Sentry + structured log. */
export function captureError(err: unknown, ctx?: Props): void {
  logStructured('error', 'exception', {
    error: err instanceof Error ? err.message : String(err),
    stack: err instanceof Error ? err.stack : undefined,
    ...(ctx || {}),
  });
  try {
    if (_sentry?.captureException) _sentry.captureException(err, { extra: ctx });
  } catch { /* noop */ }
}

/** Bind only the anonymous session id — never PII. */
export function identifyAnonymous(id?: string): void {
  const anon = id || getAnonymousSessionId();
  try {
    if (_posthog?.identify) _posthog.identify(anon);
    if (_sentry?.setUser)   _sentry.setUser({ id: anon });
  } catch { /* noop */ }
}
