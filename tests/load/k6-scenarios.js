import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const errorRate = new Rate('errors');
const latencyTrend = new Trend('request_duration');
const orderCounter = new Counter('orders_created');
const resultCounter = new Counter('results_submitted');

export const options = {
  thresholds: {
    errors: ['rate<0.01'],
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
  scenarios: {
    normal_load: {
      executor: 'constant-vus',
      vus: 100,
      duration: '5m',
      tags: { scenario: 'normal' },
    },
    peak_load: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '2m', target: 500 },
        { duration: '5m', target: 500 },
        { duration: '2m', target: 100 },
      ],
      tags: { scenario: 'peak' },
      startTime: '5m',
    },
    burst: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 1000 },
        { duration: '30s', target: 1000 },
        { duration: '10s', target: 100 },
      ],
      tags: { scenario: 'burst' },
      startTime: '12m',
    },
    endurance: {
      executor: 'constant-vus',
      vus: 200,
      duration: '30m',
      tags: { scenario: 'endurance' },
      startTime: '15m',
    },
  },
};

function login() {
  const payload = JSON.stringify({
    email: 'test@lab.com',
    password: 'test_password',
  });
  const params = {
    headers: { 'Content-Type': 'application/json' },
    tags: { endpoint: 'login' },
  };
  const res = http.post(`${BASE_URL}/api/login`, payload, params);
  check(res, {
    'login status 200': (r) => r.status === 200,
    'login has token': (r) => r.json('access_token') !== undefined,
  });
  errorRate.add(res.status !== 200);
  latencyTrend.add(res.timings.duration);
  return res.json('access_token');
}

function searchPatients(token) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    tags: { endpoint: 'patients' },
  };
  const res = http.get(`${BASE_URL}/api/patients?limit=10`, params);
  check(res, {
    'search patients status 200': (r) => r.status === 200,
    'search patients has results': (r) => r.json('patients') !== undefined,
  });
  errorRate.add(res.status !== 200);
  latencyTrend.add(res.timings.duration);
}

function createOrder(token) {
  const payload = JSON.stringify({
    patient_id: 'test-patient-id',
    tests: ['CBC', 'GLU', 'LIP'],
    priority: 'routine',
  });
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    tags: { endpoint: 'create_order' },
  };
  const res = http.post(`${BASE_URL}/api/orders`, payload, params);
  check(res, {
    'create order status 201': (r) => r.status === 201,
    'create order has id': (r) => r.json('id') !== undefined,
  });
  errorRate.add(res.status !== 201);
  latencyTrend.add(res.timings.duration);
  if (res.status === 201) orderCounter.add(1);
}

function submitResults(token) {
  const payload = JSON.stringify({
    order_id: 'test-order-id',
    results: [
      { test_code: 'CBC', value: '5.2', unit: '10^12/L', flag: 'normal' },
      { test_code: 'GLU', value: '95', unit: 'mg/dL', flag: 'normal' },
    ],
  });
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    tags: { endpoint: 'submit_results' },
  };
  const res = http.post(`${BASE_URL}/api/results`, payload, params);
  check(res, {
    'submit results status 201': (r) => r.status === 201,
  });
  errorRate.add(res.status !== 201);
  latencyTrend.add(res.timings.duration);
  if (res.status === 201) resultCounter.add(1);
}

function getDashboard(token) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    tags: { endpoint: 'dashboard' },
  };
  const res = http.get(`${BASE_URL}/api/dashboard/stats`, params);
  check(res, {
    'dashboard status 200': (r) => r.status === 200,
  });
  errorRate.add(res.status !== 200);
  latencyTrend.add(res.timings.duration);
}

export default function () {
  const token = login();
  if (!token) {
    sleep(1);
    return;
  }
  group('clinical workflow', () => {
    searchPatients(token);
    sleep(Math.random() * 3 + 1);
    createOrder(token);
    sleep(Math.random() * 2 + 1);
    submitResults(token);
    sleep(Math.random() * 2 + 1);
    getDashboard(token);
  });
  sleep(Math.random() * 3 + 2);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify({
      metrics: {
        http_req_duration: data.metrics.http_req_duration.values,
        errors: data.metrics.errors.values,
        http_req_failed: data.metrics.http_req_failed.values,
        iterations: data.metrics.iterations.values,
      },
      scenarios: data.scenarios,
    }, null, 2),
    '/tmp/load-test-results.json': JSON.stringify(data, null, 2),
  };
}
