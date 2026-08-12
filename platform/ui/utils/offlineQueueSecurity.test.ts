import assert from 'node:assert/strict';
import {
  inspectQueuePayload,
  inspectQueueRecord,
  isSensitiveQueueKey,
  sanitizeQueueHeaders,
} from './offlineQueueSecurity';

const sensitiveHeaders = sanitizeQueueHeaders({
  Authorization: 'Bearer legacy-token',
  'Content-Type': 'application/json',
  'X-Request-ID': 'request-1',
});
assert.equal(sensitiveHeaders.hadSensitiveHeader, true);
assert.deepEqual(sensitiveHeaders.headers, {
  'Content-Type': 'application/json',
  'X-Request-ID': 'request-1',
});

assert.equal(isSensitiveQueueKey('refresh_token'), true);
assert.equal(isSensitiveQueueKey('secretaryName'), false);
assert.equal(isSensitiveQueueKey('patientId'), false);

assert.equal(inspectQueuePayload({ vitals: { pulse: 72 }, patientId: 'p-1' }).safe, true);
assert.equal(inspectQueuePayload({ refresh_token: 'legacy-token' }).safe, false);
assert.equal(inspectQueuePayload(JSON.stringify({ authorization: 'Bearer legacy-token' })).safe, false);
assert.equal(inspectQueuePayload({ note: 'Bearer legacy-token' }).safe, false);

assert.equal(inspectQueueRecord({
  headers: { Authorization: 'Bearer legacy-token' },
  body: JSON.stringify({ safe: true }),
}).safe, false);
assert.equal(inspectQueueRecord({
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ clinicalNote: 'stable' }),
}).safe, true);

console.log('offlineQueueSecurity tests passed');
