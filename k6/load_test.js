/**
 * GULA Platform — k6 Load Test
 *
 * Scenarios:
 *   smoke    — 1 VU × 1 min  (sanity: does the API respond?)
 *   load     — ramp 0→50 VUs over 2 min, hold 5 min, ramp down
 *   stress   — ramp 0→200 VUs over 5 min, hold 5 min, ramp down
 *   soak     — 30 VUs × 30 min (memory leaks, DB pool exhaustion)
 *
 * Run examples:
 *   k6 run k6/load_test.js                            # default (load scenario)
 *   k6 run -e SCENARIO=smoke k6/load_test.js
 *   k6 run -e SCENARIO=stress k6/load_test.js
 *   k6 run -e BASE_URL=http://staging.gula-platform.org k6/load_test.js
 *
 * SLOs (enforced via thresholds):
 *   p(95) latency  ≤ 500 ms   for reads
 *   p(95) latency  ≤ 1000 ms  for writes
 *   error rate     < 1%
 *   health probe   p(99) < 200 ms
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ── Config ────────────────────────────────────────────────────────────────────

const BASE_URL   = __ENV.BASE_URL   || 'http://localhost:8000';
const SCENARIO   = __ENV.SCENARIO   || 'load';
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || '';  // set via env in CI

// ── Custom metrics ────────────────────────────────────────────────────────────

const errorRate     = new Rate('error_rate');
const writeLatency  = new Trend('write_latency_ms', true);
const readLatency   = new Trend('read_latency_ms',  true);

// ── Scenario definitions ──────────────────────────────────────────────────────

const scenarios = {
  smoke: {
    executor: 'constant-vus',
    vus: 1,
    duration: '1m',
    tags: { scenario: 'smoke' },
  },
  load: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 50 },
      { duration: '5m', target: 50 },
      { duration: '1m', target: 0  },
    ],
    tags: { scenario: 'load' },
  },
  stress: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 100 },
      { duration: '3m', target: 200 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 0   },
    ],
    tags: { scenario: 'stress' },
  },
  soak: {
    executor: 'constant-vus',
    vus: 30,
    duration: '30m',
    tags: { scenario: 'soak' },
  },
};

// ── Thresholds ────────────────────────────────────────────────────────────────

export const options = {
  scenarios: { [SCENARIO]: scenarios[SCENARIO] || scenarios.load },
  thresholds: {
    // Global error rate must stay below 1%
    error_rate:            ['rate<0.01'],
    // Read p95 under 500ms
    read_latency_ms:       ['p(95)<500'],
    // Write p95 under 1000ms
    write_latency_ms:      ['p(95)<1000'],
    // Health endpoint very fast
    'http_req_duration{url:' + BASE_URL + '/health}': ['p(99)<200'],
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function authHeaders() {
  if (ADMIN_TOKEN) {
    return { Authorization: `Bearer ${ADMIN_TOKEN}` };
  }
  return {};
}

function record(res, isWrite = false) {
  const ok = res.status >= 200 && res.status < 400;
  errorRate.add(!ok);
  if (isWrite) {
    writeLatency.add(res.timings.duration);
  } else {
    readLatency.add(res.timings.duration);
  }
  return ok;
}

// ── Default function (runs once per VU iteration) ────────────────────────────

export default function () {

  // ── Liveness / health ─────────────────────────────────────────────────────
  group('health_probes', () => {
    const h = http.get(`${BASE_URL}/health`);
    check(h, { 'health 200': (r) => r.status === 200 });
    record(h);

    const r = http.get(`${BASE_URL}/health/ready`);
    check(r, { 'ready 200': (r) => r.status === 200 });
    record(r);
  });

  sleep(0.1);

  // ── Public read: test types catalog ──────────────────────────────────────
  group('test_types_catalog', () => {
    const res = http.get(`${BASE_URL}/test-types`);
    const ok = check(res, {
      'test-types 200': (r) => r.status === 200,
      'test-types has data': (r) => {
        try { return JSON.parse(r.body).length > 0; } catch { return false; }
      },
    });
    record(res);
  });

  sleep(0.2);

  // ── Authenticated read: lab info ──────────────────────────────────────────
  if (ADMIN_TOKEN) {
    group('authenticated_reads', () => {
      const res = http.get(`${BASE_URL}/labs/me`, { headers: authHeaders() });
      check(res, { 'labs/me 200 or 404': (r) => [200, 404].includes(r.status) });
      record(res);
    });

    sleep(0.1);

    // ── Dashboard (heavy read) ───────────────────────────────────────────────
    group('dashboard', () => {
      const res = http.get(`${BASE_URL}/dashboard`, { headers: authHeaders() });
      check(res, { 'dashboard 200': (r) => r.status === 200 });
      record(res);
    });

    sleep(0.2);
  }

  // ── Deep health (diagnostic) ──────────────────────────────────────────────
  if (Math.random() < 0.05) {  // 5% of iterations
    group('deep_health', () => {
      const res = http.get(`${BASE_URL}/health/deep`);
      check(res, {
        'deep health 200':   (r) => r.status === 200,
        'grade not RED':     (r) => {
          try { return JSON.parse(r.body).grade !== 'RED'; } catch { return false; }
        },
      });
      record(res);
    });
  }

  sleep(0.5 + Math.random() * 0.5);  // 0.5–1s between iterations
}

// ── Setup: log run config ─────────────────────────────────────────────────────

export function setup() {
  console.log(`[GULA Load Test] BASE_URL=${BASE_URL} SCENARIO=${SCENARIO}`);
  const health = http.get(`${BASE_URL}/health`);
  if (health.status !== 200) {
    throw new Error(`API not reachable at ${BASE_URL}/health — status ${health.status}`);
  }
  console.log(`[GULA Load Test] API healthy — starting scenario '${SCENARIO}'`);
}

// ── Teardown: print summary ───────────────────────────────────────────────────

export function teardown(data) {
  console.log('[GULA Load Test] Completed. Check thresholds above for pass/fail.');
}
