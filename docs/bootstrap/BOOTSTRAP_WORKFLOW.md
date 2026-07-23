# GULA Platform — Bootstrap Workflow

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Execution Flow

```
Application Startup
│
├─ factory.py: create_app()
│   ├─ import_all_models()
│   └─ lifespan.startup
│       └─ run_startup_guard()
│           ├─ validate_config()        ← secrets check
│           ├─ wait_for_db()            ← DB reachability
│           ├─ check_redis()            ← Redis connectivity
│           ├─ check_migrations()       ← alembic state
│           └─ seed_critical_data()
│               ├─ perm_version migration
│               ├─ test types catalog
│               ├─ master admin         ← ensure_master_admin() [backward compat]
│               ├─ default subscriptions ← seed_default_subscriptions()
│               ├─ NATIONAL BOOTSTRAP   ← run_bootstrap() [NEW]
│               │   ├─ step 1: master_admin (idempotent check)
│               │   ├─ step 2: permissions (80+ permissions)
│               │   ├─ step 3: roles (19 enterprise roles)
│               │   ├─ step 4: ministry (Ministry of Health)
│               │   ├─ step 5: directorates (19 governorates)
│               │   ├─ step 6: platform facilities (9 facilities)
│               │   ├─ step 7: laboratory types
│               │   ├─ step 8: departments (16 depts per lab)
│               │   ├─ step 9: admin accounts (6 national admins)
│               │   ├─ step 10: subscriptions (all labs)
│               │   └─ step 11: demo data [optional]
│               └─ audit log trigger
```

## Phase Details

### Phase 1: Master Admin
- Checks for existing `LabUser` with `role = "master_admin"`
- If absent, creates "GULA Platform" lab and master admin user
- Links national ID if `MASTER_ADMIN_NID` is set
- **Idempotent**: skips if master admin already exists

### Phase 2: Permissions
- Seeds 80+ `Permission` rows across 20 domains
- Each permission has: permission_id, name_en/ar, domain, resource, action, risk_level
- **Idempotent**: skips existing permission by `permission_id`

### Phase 3: Roles
- Creates 19 `Role` rows with level and scope
- Links role-permission mappings from permission definitions
- **Idempotent**: skips existing roles by `role_id`

### Phase 4: Ministry of Health
- Creates Ministry organization (`org_type = "ministry"`)
- **Idempotent**: skips if `org-iraq-moh` exists

### Phase 5: Health Directorates
- Creates 19 organizations (`org_type = "directorate"`) for all Iraqi governorates
- Each linked to Ministry of Health as parent
- **Idempotent**: skips existing by `org_id`

### Phase 6: Platform Facilities
- Creates 6+ facilities (lab, blood bank, PH lab, forensic, reference, research)
- Linked to platform directorate organization
- **Idempotent**: skips existing by `facility_id`

### Phase 7: Departments
- Creates 16 standard lab departments per active lab
- Departments: Chemistry, Hematology, Microbiology, etc.
- **Idempotent**: skips existing by lab_id + code

### Phase 8: Admin Accounts
- Reads email/password from env vars for 6 roles
- Creates `LabUser` for each configured account
- **Idempotent**: skips existing by email

### Phase 9: Subscriptions
- Creates `LabSubscription` (starter tier) for every active lab without one
- Supports 4 tiers: starter, professional, enterprise, national
- **Idempotent**: skips labs with existing subscriptions

### Phase 10: Demo Data (Optional)
- Controlled by `ENABLE_DEMO_DATA=true`
- Creates 15 demo patients, 3 technicians, 3 doctors
- Generates orders, samples, and results with deterministic data
- **Idempotent**: skips if >5 patients already exist

## Idempotency Guarantee

Every bootstrap module follows the same pattern:

```python
existing = db.query(Model).filter(Model.key == value).first()
if existing:
    # skip — already exists
    continue
# create new record
```

Running the bootstrap 100 times on the same database produces the same result
as running it once. No duplicates, no errors.

## Rollback Strategy

### During Startup
If any bootstrap step fails during startup:
1. The failed step is logged as non-fatal
2. Startup continues (the app starts in degraded mode)
3. The bootstrap can be retried by restarting the app

### Manual Rollback
To undo bootstrap seeding:

```sql
-- Remove demo data
DELETE FROM lab_results WHERE order_id LIKE 'DEMO-%';
DELETE FROM samples WHERE lab_id IN (SELECT id FROM labs WHERE name = 'GULA Platform');
DELETE FROM lab_orders WHERE order_id LIKE 'DEMO-%';
DELETE FROM lab_users WHERE email LIKE '%@demo.gula.iq';
DELETE FROM patients WHERE phone LIKE '07700000%';

-- Remove admin accounts (except master_admin)
DELETE FROM lab_users WHERE role IN ('ministry_admin', 'organization_admin',
  'directorate_admin', 'lab_manager', 'auditor', 'security_officer')
  AND lab_id = (SELECT id FROM labs WHERE name = 'GULA Platform');

-- Remove departments
DELETE FROM lims_departments WHERE lab_id IN (SELECT id FROM labs WHERE name = 'GULA Platform');

-- Remove facilities
DELETE FROM facilities WHERE facility_id LIKE 'fac-platform-%';

-- Remove laboratory types
DELETE FROM facilities WHERE facility_id LIKE 'lab-type-%';

-- Remove directorates
DELETE FROM organizations WHERE org_type = 'directorate'
  AND parent_org_id = 'org-iraq-moh';

-- Remove ministry
DELETE FROM organizations WHERE org_id = 'org-iraq-moh';

-- Remove subscriptions
DELETE FROM lab_subscriptions WHERE lab_id IN (SELECT id FROM labs WHERE name = 'GULA Platform');

-- Remove role-permission mappings (CASCADE)
DELETE FROM role_permissions;

-- Remove permissions (CASCADE)
DELETE FROM permissions;

-- Remove roles (CASCADE)
DELETE FROM roles;

-- Remove platform facilities
DELETE FROM facilities WHERE facility_id LIKE 'fac-platform-%';
```

## Security

1. **Password Isolation**: Admin passwords are read from env vars only —
   never logged, never stored in source code
2. **Hash All Passwords**: All passwords are bcrypt-hashed before storage
3. **Hash Override**: Pre-hashed passwords can be provided via `*_PASSWORD_HASH`
   env vars for environments that cannot pass plaintext secrets
4. **No Secrets in Code**: The bootstrap module has zero hardcoded secrets

## Testing

Run the bootstrap tests with:

```bash
cd backend && python -m pytest tests/test_national_bootstrap.py -v
```

The test suite covers:
- Fresh database seeding
- Idempotent re-execution
- Missing environment variables
- Permission and role validation
- National hierarchy validation
- Integration with existing seeds
