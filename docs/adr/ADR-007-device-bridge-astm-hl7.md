# ADR-007: Device Bridge ASTM/HL7

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, Integration Team Lead

## Context

Medical laboratories use analyser instruments from multiple vendors (Sysmex, Roche, Mindray, etc.) that communicate via ASTM or HL7 protocols. The platform must ingest lab results from these instruments in real time, normalise them, and forward them to the GULA backend for processing and storage.

## Decision

Implement a dedicated device bridge service (`services/device_bridge/`) that handles ASTM and HL7 communication with lab instruments and forwards normalised results to the GULA backend.

### Architecture
- **Device Bridge** runs as a separate Docker container (`docker compose --profile device-bridge up`)
- Supports ASTM E1381/1382 and HL7 v2.x protocols
- Normalises instrument-specific result formats into a standard internal schema
- Communicates with GULA backend via `app/integration/gula_client.py` (authenticated HTTP)
- Configurable device profiles for each instrument model

### Supported Instruments
- Sysmex haematology analysers
- Roche clinical chemistry analysers
- Mindray diagnostics
- Generic ASTM/HL7 devices

## Alternatives Considered

### 1. Direct Instrument Integration in Monolith

**Pros:** Simpler deployment, no inter-service communication.
**Cons:** Monolith would need to handle real-time device protocols, blocking I/O, and restart on device connection changes.
**Rejected because:** Device protocols require persistent connections and specialised handling that would complicate the monolith's request-response model.

### 2. Vendor SDK Integration

**Pros:** Vendor-optimised, potentially easier setup.
**Cons:** Vendor lock-in, different SDKs for each instrument, licensing costs.
**Rejected because:** Vendor-agnostic approach provides flexibility for laboratories to choose instruments.

### 3. MQTT/Message Queue Bridge

**Pros:** Asynchronous, durable message delivery, decoupled.
**Cons:** Additional infrastructure (RabbitMQ/Kafka), operational complexity.
**Rejected because:** For current scale, synchronous HTTP forwarding with retry logic is simpler and sufficient.

## Consequences

### Positive
- Device protocols are isolated from the monolith
- Instruments can be added without backend changes
- Connection failures in device bridge don't affect main platform
- Device bridge can be scaled independently if needed

### Negative
- Additional service to deploy and monitor
- Network hop adds latency to result ingestion
- Device bridge must handle instrument authentication securely

### Neutral
- Device bridge uses the same Python stack as the monolith
- Forwarding uses the same auth as other API clients
- Device profiles are configuration files, not code

## References
- `services/device_bridge/` — Device bridge service
- `services/device_bridge/app/integration/gula_client.py` — GULA API client
- `backend/app/integration/` — Backend integration module
- `docker-compose.yml` — Docker Compose configuration (profile device-bridge)
