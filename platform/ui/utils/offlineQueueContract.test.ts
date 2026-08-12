import assert from 'node:assert/strict';
import {
  buildQueueRequestInit,
  classifyQueueResponse,
  createQueueEnvelope,
  nextQueueEnvelopeState,
} from './offlineQueueContract';

const first = await createQueueEnvelope({
  url: '/clinical/vitals',
  method: 'post',
  entityType: 'vital-signs',
  entityId: 'patient-1',
  action: 'create',
  expectedVersion: 3,
  body: { heartRate: 72, systolic: 120 },
  operationId: 'op-1',
  now: '2026-08-12T00:00:00.000Z',
});
const same = await createQueueEnvelope({
  url: '/clinical/vitals',
  method: 'POST',
  entityType: 'vital-signs',
  entityId: 'patient-1',
  action: 'create',
  expectedVersion: 3,
  body: { systolic: 120, heartRate: 72 },
  operationId: 'op-1',
  now: '2026-08-12T00:00:00.000Z',
});
assert.equal(first.idempotencyKey, 'op-1');
assert.equal(first.requestFingerprint, same.requestFingerprint);
assert.equal(first.state, 'pending');

const requestInit = buildQueueRequestInit(first);
assert.equal(requestInit.credentials, 'include');
assert.equal((requestInit.headers as Record<string, string>)['Idempotency-Key'], 'op-1');
assert.equal((requestInit.headers as Record<string, string>)['If-Match'], '3');

assert.equal(classifyQueueResponse(201), 'synced');
assert.equal(classifyQueueResponse(409), 'conflict');
assert.equal(classifyQueueResponse(412), 'conflict');
assert.equal(classifyQueueResponse(422), 'rejected');
assert.equal(classifyQueueResponse(503), 'retry');

const conflict = nextQueueEnvelopeState(first, 'conflict', 'version conflict', {
  status: 409,
  detectedAt: '2026-08-12T00:01:00.000Z',
  serverBody: { currentVersion: 4 },
});
assert.equal(conflict.state, 'conflict');
assert.equal(conflict.attempt, 0);
assert.equal(conflict.conflict?.status, 409);

const retry = nextQueueEnvelopeState(first, 'retry', 'temporary outage');
assert.equal(retry.state, 'pending');
assert.equal(retry.attempt, 1);

console.log('offlineQueueContract tests passed');
