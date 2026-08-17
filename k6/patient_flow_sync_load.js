/**
 * GULA Government Patient Flow + Offline Sync load test.
 *
 * This test is intentionally staging-only: it writes synthetic encounter.note
 * operations and requires explicit credentials. It never runs against an
 * environment without AUTH_TOKEN and DEVICE_SESSION_TOKEN.
 *
 * Examples:
 *   k6 run -e BASE_URL=https://staging.example.gov \
 *     -e AUTH_TOKEN="$AUTH_TOKEN" \
 *     -e DEVICE_ID=ER-LOAD-001 \
 *     -e DEVICE_SESSION_TOKEN="$DEVICE_SESSION_TOKEN" \
 *     k6/patient_flow_sync_load.js
 *
 * Scenarios:
 *   smoke: 1 VU for 1 minute
 *   load: 0→50 VUs, hold 5 minutes, recover
 *   stress: 0→200 VUs, hold 5 minutes, recover
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || '';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const DEVICE_ID = __ENV.DEVICE_ID || '';
const DEVICE_SESSION_TOKEN = __ENV.DEVICE_SESSION_TOKEN || '';
const HOSPITAL_ID = Number(__ENV.HOSPITAL_ID || '1');
const SCENARIO = __ENV.SCENARIO || 'load';

const errorRate = new Rate('patient_flow_sync_error_rate');
const readLatency = new Trend('patient_flow_sync_read_latency_ms', true);
const writeLatency = new Trend('patient_flow_sync_write_latency_ms', true);
const acceptedOperations = new Counter('patient_flow_sync_accepted_operations');
const duplicateOperations = new Counter('patient_flow_sync_duplicate_operations');
const rejectedOperations = new Counter('patient_flow_sync_rejected_operations');

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
      { duration: '1m', target: 0 },
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
      { duration: '2m', target: 0 },
    ],
    tags: { scenario: 'stress' },
  },
};

export const options = {
  scenarios: { [SCENARIO]: scenarios[SCENARIO] || scenarios.load },
  thresholds: {
    patient_flow_sync_error_rate: ['rate<0.01'],
    patient_flow_sync_read_latency_ms: ['p(95)<500'],
    patient_flow_sync_write_latency_ms: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

function headers() {
  return {
    Authorization: `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json',
    'X-Device-Session': DEVICE_SESSION_TOKEN,
  };
}

function operationId() {
  return `k6-${__VU}-${__ITER}-${Date.now()}`;
}

function record(res, isWrite) {
  const ok = res.status >= 200 && res.status < 300;
  errorRate.add(!ok);
  (isWrite ? writeLatency : readLatency).add(res.timings.duration);
  return ok;
}

export function setup() {
  if (!BASE_URL || !AUTH_TOKEN || !DEVICE_ID || !DEVICE_SESSION_TOKEN || !Number.isInteger(HOSPITAL_ID) || HOSPITAL_ID < 1) {
    throw new Error('Refusing to run: BASE_URL, AUTH_TOKEN, DEVICE_ID, DEVICE_SESSION_TOKEN and valid HOSPITAL_ID are required');
  }
  const health = http.get(`${BASE_URL}/health/ready`);
  if (health.status !== 200) {
    throw new Error(`API is not ready at ${BASE_URL}/health/ready: ${health.status}`);
  }
  return { startedAt: new Date().toISOString() };
}

export default function () {
  const deviceHeaders = headers();
  const status = http.get(`${BASE_URL}/national/sync/status?device_id=${encodeURIComponent(DEVICE_ID)}`, { headers: deviceHeaders, tags: { operation: 'sync_status' } });
  check(status, { 'sync status is successful': (res) => record(res, false) });

  const id = operationId();
  const batch = {
    device_id: DEVICE_ID,
    operations: [{
      operation_id: id,
      idempotency_key: id,
      operation_type: 'encounter.note',
      entity_type: 'Encounter',
      entity_id: `k6-${__VU}`,
      priority: 'routine',
      device_id: DEVICE_ID,
      payload: { hospital_id: HOSPITAL_ID, note: 'synthetic government staging load test' },
      created_at: new Date().toISOString(),
    }],
  };
  const pushed = http.post(`${BASE_URL}/national/sync/operations:batch`, JSON.stringify(batch), { headers: deviceHeaders, tags: { operation: 'sync_batch' } });
  const writeOk = record(pushed, true);
  check(pushed, {
    'sync batch HTTP success': () => writeOk,
    'sync batch has result': (res) => {
      try {
        const body = JSON.parse(res.body);
        const result = body.results?.[0];
        if (result?.status === 'accepted') acceptedOperations.add(1);
        else if (result?.status === 'duplicate') duplicateOperations.add(1);
        else rejectedOperations.add(1);
        return ['accepted', 'duplicate', 'conflict'].includes(result?.status);
      } catch (_) {
        rejectedOperations.add(1);
        return false;
      }
    },
  });
  sleep(0.2 + Math.random() * 0.8);
}
