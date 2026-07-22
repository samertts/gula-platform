# GULA Event Constitution

## Event-Driven Architecture

1. **Asynchronous communication** between domains uses events. Events enable loose coupling, independent deployability, and fault isolation.

2. **Outbox pattern** is the standard: events are persisted in `outbox_events` table within the same transaction as the business operation. A background worker publishes persisted events to the message broker.

3. **At-least-once delivery** is the guarantee. Consumers must be idempotent. Duplicate events are handled gracefully.

4. **Event schema** follows a consistent structure:
   ```json
   {
     "event_id": "uuid",
     "event_type": "domain.action",
     "source": "service-name",
     "timestamp": "ISO8601",
     "data": { ... },
     "metadata": {
       "correlation_id": "uuid",
       "causation_id": "uuid",
       "tenant_id": "..."
     }
   }
   ```

## Event Types

5. **Domain events** — something happened in a domain that other domains might care about:
   - `patient.created`, `patient.merged`
   - `order.created`, `order.cancelled`
   - `result.posted`, `result.verified`, `result.amended`
   - `sample.collected`, `sample.rejected`

6. **Integration events** — data exchange with external systems:
   - `integration.result.forwarded`
   - `integration.order.received`
   - `integration.device.status_changed`

7. **System events** — platform infrastructure:
   - `system.health.degraded`
   - `system.circuit.opened`
   - `system.background.task.completed`

## Event Handling

8. **Event handlers are idempotent.** Processing the same event twice produces the same result as processing it once.

9. **Failed events** are retried with exponential backoff (3 attempts). After max retries, events are moved to a dead-letter queue for manual investigation.

10. **Event ordering** is preserved per aggregate. Events for the same entity are processed sequentially.

11. **Event sourcing** is not used as the primary persistence model. Events complement, not replace, the current state model.

## Observability

12. **Every event** is logged with `event_id`, `event_type`, processing duration, and outcome.

13. **Event processing metrics** (throughput, latency, error rate, backlog depth) are monitored and alerted.

14. **Event replay** is supported for disaster recovery and data backfill scenarios.
