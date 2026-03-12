/**
 * GULA Platform - k6 Load Test
 * Tests: 10,000 requests/minute across all core services
 *
 * Run:
 *   k6 run tests/load/gula-load-test.js
 *   k6 run --vus 100 --duration 5m tests/load/gula-load-test.js
 *
 * With output:
 *   k6 run --out influxdb=http://localhost:8086/k6 tests/load/gula-load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate     = new Rate('error_rate');
const auditEvents   = new Counter('audit_events_total');
const resultLatency = new Trend('result_service_latency');
const aiLatency     = new Trend('ai_service_latency');

const BASE       = __ENV.BASE_URL       || 'http://localhost';
const PATIENT_SVC = __ENV.PATIENT_URL  || 'http://localhost:8002';
const ORDER_SVC   = __ENV.ORDER_URL    || 'http://localhost:8003';
const RESULT_SVC  = __ENV.RESULT_URL   || 'http://localhost:8004';
const SAMPLE_SVC  = __ENV.SAMPLE_URL   || 'http://localhost:8005';
const AI_SVC      = __ENV.AI_URL       || 'http://localhost:9000';

export const options = {
  scenarios: {
    // ==========================================================================
    // Scenario 1: Ramp up to 10k req/min (~167 req/s)
    // ==========================================================================
    ramp_to_10k: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 500,
      stages: [
        { target: 50,  duration: '2m' },   // ramp to 50 req/s
        { target: 167, duration: '5m' },   // ramp to ~10k req/min
        { target: 167, duration: '10m' },  // sustain
        { target: 0,   duration: '2m' },   // ramp down
      ],
    },

    // ==========================================================================
    // Scenario 2: Spike test (simulate lab opening time)
    // ==========================================================================
    spike: {
      executor: 'ramping-arrival-rate',
      startRate: 5,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 1000,
      startTime: '20m',
      stages: [
        { target: 5,   duration: '30s' },
        { target: 500, duration: '30s' },  // sudden spike
        { target: 500, duration: '2m' },   // hold spike
        { target: 5,   duration: '30s' },  // recover
      ],
    },
  },

  thresholds: {
    // API must respond within 500ms for 95% of requests
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    // Error rate must stay below 1%
    error_rate: ['rate<0.01'],
    // Result service under 1s
    result_service_latency: ['p(95)<1000'],
    // AI service under 3s (Ollama inference time)
    ai_service_latency: ['p(95)<3000'],
  },
};

// Shared patient/lab IDs created during setup
let sharedState = { labId: 1, patientId: null };

export function setup() {
  // Create a test lab and patient for use during load test
  const labRes = http.post(`${BASE}/api/labs/laboratories`, JSON.stringify({
    lab_name: `LoadTest-Lab-${Date.now()}`,
    city: 'Riyadh',
  }), { headers: { 'Content-Type': 'application/json' } });

  const patientRes = http.post(`${PATIENT_SVC}/patients`, JSON.stringify({
    first_name: 'LoadTest',
    last_name: 'Patient',
    gender: 'M',
    age: 30,
    lab_id: 1,
  }), { headers: { 'Content-Type': 'application/json' } });

  const patientId = patientRes.status === 201
    ? JSON.parse(patientRes.body).id
    : 1;

  return { labId: 1, patientId };
}

export default function (data) {
  const headers = { 'Content-Type': 'application/json' };
  const patientId = data.patientId || 1;

  // ==========================================================================
  // Group 1: Read operations (60% of traffic)
  // ==========================================================================
  group('READ: List patients', () => {
    const res = http.get(`${PATIENT_SVC}/patients?limit=20`, { tags: { name: 'list_patients' } });
    check(res, { 'patients list OK': r => r.status === 200 });
    errorRate.add(res.status !== 200);
  });

  group('READ: List orders', () => {
    const res = http.get(`${ORDER_SVC}/orders?limit=20`, { tags: { name: 'list_orders' } });
    check(res, { 'orders list OK': r => r.status === 200 });
    errorRate.add(res.status !== 200);
  });

  // ==========================================================================
  // Group 2: Write operations (30% of traffic) — create order + result
  // ==========================================================================
  group('WRITE: Create order + result', () => {
    // Create order
    const orderRes = http.post(`${ORDER_SVC}/orders`, JSON.stringify({
      lab_id: data.labId,
      patient_id: patientId,
      test_id: Math.floor(Math.random() * 5) + 1,
      priority: 'routine',
    }), { headers, tags: { name: 'create_order' } });

    check(orderRes, { 'order created': r => r.status === 201 });
    errorRate.add(orderRes.status !== 201);

    if (orderRes.status === 201) {
      const orderId = JSON.parse(orderRes.body).id;
      auditEvents.add(1, { event: 'OrderCreated' });

      // Create result
      const start = Date.now();
      const resultRes = http.post(`${RESULT_SVC}/results`, JSON.stringify({
        order_id: orderId,
        value: (Math.random() * 20 + 5).toFixed(1),
        numeric_value: Math.random() * 20 + 5,
        unit: 'g/dL',
        is_abnormal: Math.random() < 0.1,
      }), { headers, tags: { name: 'create_result' } });

      resultLatency.add(Date.now() - start);
      check(resultRes, { 'result created': r => r.status === 201 });
      errorRate.add(resultRes.status !== 201);

      if (resultRes.status === 201) {
        auditEvents.add(1, { event: 'ResultUpdated' });
      }
    }
  });

  // ==========================================================================
  // Group 3: AI requests (10% of traffic)
  // ==========================================================================
  if (Math.random() < 0.1) {
    group('AI: Clinical analysis', () => {
      const start = Date.now();
      const aiRes = http.post(`${AI_SVC}/analyze`, JSON.stringify({
        prompt: 'Hemoglobin 8.5 g/dL. Patient is 45 year old male. Is this abnormal?',
        tier: 'clinical',
        max_tokens: 256,
      }), { headers, tags: { name: 'ai_clinical' }, timeout: '10s' });

      aiLatency.add(Date.now() - start);
      check(aiRes, { 'AI responded': r => r.status === 200 });
      errorRate.add(aiRes.status !== 200);
    });
  }

  // ==========================================================================
  // Group 4: Health checks (background — simulate monitoring)
  // ==========================================================================
  if (Math.random() < 0.05) {
    http.get(`${BASE}/health`, { tags: { name: 'healthcheck' } });
  }

  sleep(0.1);
}

export function teardown(data) {
  console.log(`Load test complete. Created with patientId=${data.patientId}`);
}
