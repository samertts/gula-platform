# GULA Platform — Go-Live Runbook

**Target**: unified national health record, one record per citizen, 48M citizens
**Owner**: Project Manager on duty
**Last reviewed**: 2026-04-16

This runbook walks through a production launch from cold start to live traffic in a single session. Work top-to-bottom — do not skip steps.

---

## 0. Pre-launch go/no-go (T-24h)

- [ ] MPI migration `20260413_0001_mpi_citizen_registry` is in `alembic upgrade head`.
- [ ] `create_patient` endpoint calls `mpi_resolver.resolve_identity` (backend/app/routes/patients.py).
- [ ] Backup schedule is enabled in `.env` (`BACKUP_ENABLED=true`).
- [ ] DNS A record for `gula-platform.org` points at the load balancer.
- [ ] TLS certificate issued (Let's Encrypt or managed).
- [ ] Staging smoke test passed (see §5).

If any item is **No**, postpone launch.

---

## 1. Generate launch secrets (T-6h)

Run the generator once and store the output immediately:

```bash
bash scripts/generate-launch-secrets.sh > .env.launch
chmod 600 .env.launch
```

Commit the values to the secret store you use (1Password, AWS Secrets Manager,
Render dashboard — **never git**). `ENCRYPTION_KEY` and `NID_HMAC_KEY` are
immutable after the first record is written: print them on paper and lock them
in a safe.

Sanity-check: no `CHANGE_ME_*` strings remain.

```bash
grep -c CHANGE_ME .env.launch    # must be 0
```

---

## 2. Database provisioning (T-4h)

Capacity plan for 48M citizens:
- **Primary**: PostgreSQL 16, 16 vCPU / 64 GB RAM / 2 TB NVMe minimum.
- **Read replica**: same spec, for reporting and admin reads.
- **Connection pooling**: pgBouncer or RDS Proxy at 300 connections.
- **Expected hot tables**: `patients`, `citizens`, `identity_claims`, `lab_results`.

```bash
# Apply migrations on an empty production DB
docker compose run --rm gula-backend alembic upgrade head

# Confirm the MPI tables exist
docker compose exec gula-postgres psql -U postgres -d labdb \
    -c "\dt citizens identity_claims mpi_merge_audit"
```

Downgrade rehearsal (must not error):

```bash
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

---

## 3. Bootstrap the master admin (T-3h)

```bash
docker compose run --rm gula-backend python scripts/create_master_admin.py
```

Verify you can log in, then immediately rotate the password to something only
you know. The initial admin will approve every lab that registers.

---

## 4. Horizontal scale-up (T-2h)

For an expected peak of ~3K requests/sec at launch (48M × 0.0001% active):

```bash
docker compose -f docker-compose.yml -f docker-compose.scale.yml \
    up -d --scale gula-backend=5
```

Confirm HAProxy sees five healthy backends:

```bash
curl -s http://localhost:8404/stats | grep gula-backend
```

Prometheus + Grafana should be green:

```bash
docker compose --profile monitoring up -d
open http://localhost:3000    # Grafana
```

---

## 5. Staging smoke test (T-1h)

Run each of these and confirm HTTP 200/201:

```bash
# Health
curl -s https://gula-platform.org/health/deep | jq .grade   # expect: "GREEN"

# Lab registration → admin approval → first patient
LAB_ID=$(curl -s -X POST https://gula-platform.org/register \
    -H "Content-Type: application/json" \
    -d '{"lab_name":"Staging Lab","admin_name":"QA","email":"qa@example.com","password":"Launch123!"}' \
    | jq -r .lab_id)

# Approve as master admin (use the token from step 3)
curl -s -X PUT "https://gula-platform.org/admin/labs/$LAB_ID/activate" \
    -H "Authorization: Bearer $MASTER_TOKEN"

# Log in as the lab admin (returns lab_token)
# ... then:
curl -s -X POST https://gula-platform.org/patients \
    -H "Authorization: Bearer $LAB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"full_name":"Ahmad Ali","phone":"07701234567","national_id":"199012345678"}' \
    | jq '.patient.citizen_ulid'   # must be a 26-char ULID
```

If `citizen_ulid` is `null`, MPI integration failed. **Abort launch** and
investigate before rolling to production.

---

## 6. Dedup assertion — the core promise (T-30min)

Create the same patient in two different labs. They must resolve to the same
`citizen_ulid`.

```bash
# Lab A
curl -s -X POST https://gula-platform.org/patients \
    -H "Authorization: Bearer $LAB_A_TOKEN" \
    -d '{"full_name":"Sara Hassan","phone":"07811111111","national_id":"198511122233"}' \
    | jq '.patient.citizen_ulid'

# Lab B (different auth, same citizen)
curl -s -X POST https://gula-platform.org/patients \
    -H "Authorization: Bearer $LAB_B_TOKEN" \
    -d '{"full_name":"Sara Hassan","phone":"07811111111","national_id":"198511122233"}' \
    | jq '.patient.citizen_ulid'
```

Both calls must return the **same** ULID, with `match_method="nid_exact"` on
the second. If they differ, stop — the MPI is not deduplicating.

---

## 7. Flip DNS + monitor (T-0)

Point `gula-platform.org` at the load balancer. For the first 2 hours, keep
all four dashboards open:

1. Grafana → Platform overview (p95 latency, error rate, DB pool).
2. HAProxy stats → backend health.
3. `docker compose logs -f gula-backend | grep -i error`.
4. Sentry issue stream.

Alert thresholds (page on-call):
- p95 latency > 500ms for 5 minutes
- 5xx rate > 1% for 3 minutes
- `/health/deep` grade = RED
- DB connections > 80% of pool

---

## 8. Post-launch (T+24h)

- [ ] Review audit log volume — ensure every mutation logged.
- [ ] Sample 20 patient records from different labs; confirm each has an
      `IdentityClaim` row.
- [ ] Confirm backups landed in S3/off-site (list objects in the bucket).
- [ ] Run `make integrity-test` and `make chaos` — must pass.
- [ ] Schedule weekly MPI merge audit review with ministry admin.

---

## Rollback plan

If the platform is unusable within the first 2 hours:

1. Flip DNS back to the maintenance page.
2. `docker compose down` — keeps data intact.
3. Restore last pre-launch DB snapshot if any writes corrupted state.
4. File a post-mortem within 48h; no relaunch until root cause is fixed
   and a regression test added.

Never run `alembic downgrade` on a live DB that has taken real writes.
Schema rollbacks are forward-only (new migration that reverses the effect).
