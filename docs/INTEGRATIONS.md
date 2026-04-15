# GULA — Integrations Guide

This document lists every external system GULA integrates with, the
adapter that owns the integration, the environment variables required to
switch the adapter from **stub** to **live**, and the safety guarantees
built into the gateway layer.

Everything ships in **stub mode by default.** No live call leaves the
platform until an operator explicitly sets the adapter's mode to
`live` *and* fills in the matching credentials. This keeps CI, dev, and
pre-credentialed production deployments fully functional.

---

## 1. Adapter mode (stub | live | shadow)

Every adapter reads its mode via `backend/app/gateways/mode.py`:

| Variable                         | Effect                                         |
|----------------------------------|------------------------------------------------|
| `GULA_ADAPTER_MODE`              | Global default. Missing → `stub`.              |
| `GULA_ADAPTER_MODE_NID`          | Per-adapter override for gov National ID       |
| `GULA_ADAPTER_MODE_INSURANCE`    | Per-adapter override for NHI                   |
| `GULA_ADAPTER_MODE_RESIDENCY`    | Per-adapter override for residency directorate |
| `GULA_ADAPTER_MODE_CLOUDFLARE`   | Per-adapter override for Cloudflare            |

Modes:

- **stub** — offline, deterministic, no network call. Default.
- **live** — real HTTPS call. Requires credentials (see below); missing
  credentials silently downgrade to `stub` and log a warning.
- **shadow** — run the live call and log the result, but return the
  stub value to the caller. Zero-risk way to validate a new provider
  against production traffic.

Introspect the live state at any time:

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.gula.health/integrations/status | jq
```

Force a probe call against one adapter:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
     https://api.gula.health/integrations/national_identity/probe | jq
```

Both endpoints require role `master_admin` or `ministry_admin`.

---

## 2. Iraqi National ID (Ministry of Interior)

- **Adapter**: `backend/app/gateways/national_identity_gateway.py`
- **Trust level**: `NON_CRITICAL` (enrichment — never drives clinical
  decisions).
- **HTTP endpoint** *(inside the backend)*: `POST /national-id/verify`

### Live-mode variables

```
GULA_ADAPTER_MODE_NID=live
MOI_NID_API_URL=https://api.moi.gov.iq
MOI_NID_API_KEY=<provided by MoI>
```

### Safety

- Raw national IDs are hashed via `hash_national_id()` before they
  cross the LIMS/National boundary; see `architecture/FOUNDATION.md`.
- The adapter's response schema is strictly validated (`valid`, `source`
  must be present with the expected types). Unknown shapes are rejected
  and the circuit breaker records a failure.
- Rate limit: 20 calls/minute/adapter. Circuit opens after 3 failures;
  recovers after 120 s.

---

## 3. Iraqi Health Insurance (NHI, Law No. 22 of 2020)

- **Adapter**: `backend/app/gateways/insurance_gateway.py`
- **Trust level**: `NON_CRITICAL` — affects billing only.
- **HTTP endpoint**: `POST /insurance/check`

### Live-mode variables

```
GULA_ADAPTER_MODE_INSURANCE=live
INSURANCE_API_URL=https://nhi.gov.iq
INSURANCE_API_KEY=<provided by NHI>
```

### Safety

- Cache TTL 10 min, stale-flag at 5 min — insurance status changes slowly
  and a stale-but-valid response is better than a billing stall.
- `requires_verification=True` is set on any stale or fallback response;
  billing logic MUST respect it.

---

## 4. Iraqi Residency (MoI — Directorate of Residency Affairs)

- **Adapter**: `backend/app/gateways/residency_gateway.py`
- **Purpose**: verify the residency status of a foreign traveller
  presenting a passport at a lab.
- **Trust level**: `NON_CRITICAL`.

### Live-mode variables

```
GULA_ADAPTER_MODE_RESIDENCY=live
RESIDENCY_API_URL=https://residency.moi.gov.iq
RESIDENCY_API_KEY=<provided by MoI>
```

### Probe shape

```json
{
  "valid": true,
  "source": "stub_local_validation",
  "nationality": "US",
  "status": "pending_verification",
  "message": "Awaiting residency directorate credential"
}
```

---

## 5. Cloudflare (DNS + WAF + Workers + R2)

- **Adapter**: `backend/app/gateways/cloudflare_gateway.py`
- **Trust level**: `ENRICHMENT` — infra/operational only.

### Live-mode variables

```
GULA_ADAPTER_MODE_CLOUDFLARE=live
CF_API_TOKEN=<scoped token>
CF_ACCOUNT_ID=<account id>
CF_ZONE_ID=<zone id for gula.health>
CF_R2_BUCKET=gula-reports
```

### Token scopes (create in Cloudflare → My Profile → API Tokens)

| Scope                           | Required for                       |
|---------------------------------|------------------------------------|
| Zone → Zone → Read              | `/integrations/cloudflare/probe`   |
| Zone → DNS → Read               | DNS audit                          |
| Account → Workers Scripts → Edit| Deploying `cloudflare/worker.js`   |
| Account → R2 Object → Read/Write| R2 report storage                  |

### Repo assets

| File                             | Purpose                                     |
|----------------------------------|---------------------------------------------|
| `cloudflare/wrangler.toml`       | Worker + R2 binding declarations            |
| `cloudflare/worker.js`           | Edge Worker — geo-block + signed origin pass |
| `cloudflare/waf-rules.json`      | WAF rule-set (rate-limit, SQLi, path-traversal) |
| `cloudflare/r2-bucket-spec.json` | R2 bucket lifecycle + CORS                  |
| `cloudflare/dns-records.yaml`    | Declarative DNS zone                        |

Deploy the Worker:

```bash
cd cloudflare/
wrangler login
wrangler secret put CF_SHARED_SECRET
wrangler deploy --env=production
```

Import WAF rules via the dashboard or the Cloudflare API; the JSON in
`cloudflare/waf-rules.json` is machine-readable.

---

## 6. Supabase (managed Postgres / auth)

Supabase is **not** integrated as a gateway. It is an alternative
host for the primary Postgres database. When migrating:

1. Create a Supabase project.
2. Copy the pooled connection string into `.env.deploy` → `DATABASE_URL`.
3. (Optional) populate `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `SUPABASE_SERVICE_KEY` so diagnostic scripts can surface project
   identity in dashboards.
4. Run `alembic upgrade head` against the new DB.

Primary runtime connections always use `DATABASE_URL`.

---

## 7. Render / DigitalOcean

Render and DigitalOcean are **deployment targets**, not adapters.
`scripts/setup-deployment.sh` writes the `.env.deploy` blob consumed by
both and prints the dashboard steps. The platform identifiers
(`RENDER_SERVICE_ID`, `DIGITALOCEAN_APP_ID`) are informational only —
surfaced in `/metrics/prom` labels when set.

---

## 8. Safety invariants (never violate)

1. `trust_level=CRITICAL` must never be set on an adapter. Clinical
   decisions come from the internal database, not from external APIs.
2. Any adapter response must pass `_validate_response()` strict-schema
   check before the circuit counts it as a success.
3. The gateway base logs every call with fields `gateway`, `action`,
   `trust_level`, `success`, `duration_ms`, `source`. Do not add
   adapter-specific logging that bypasses `_audit`.
4. Credentials live in environment variables only — never in source,
   never in `docker-compose.yml`, never in `.env.example`.
5. Missing credentials degrade to `stub`, never to an error.
6. Cloudflare's `CF_SHARED_SECRET` must be rotated whenever the Worker
   is redeployed to a new version; the backend verifies
   `x-cf-signed = HMAC-SHA256(path, CF_SHARED_SECRET)` to reject
   direct-to-origin traffic that bypasses the Worker.

---

## 9. Adding a new adapter

1. Create `backend/app/gateways/<name>_gateway.py` extending
   `ExternalGateway`.
2. Set `name`, `trust_level` (never `CRITICAL`), `_SCHEMA`.
3. Implement `_do_call` with `STUB` → `SHADOW` → `LIVE` branches via
   `resolve_mode(<name>, _REQUIRED_CREDS)`.
4. Register the new adapter in `_GETTERS` / `_PROBES` inside
   `backend/app/routes/integrations.py`.
5. Add env-var placeholders to `scripts/setup-deployment.sh` and
   `backend/app/config.py`.
6. Add a unit test in `backend/tests/test_gateways.py` that confirms
   stub mode produces the expected response shape.
7. Update this file with the new section.
