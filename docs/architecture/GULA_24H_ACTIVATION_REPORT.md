# GULA — activation report

Everything below was produced by running the thing it describes, on the
production runtime target. Nothing is carried over from an earlier status
document; every number was recomputed.

## SYSTEM STATUS

| | |
|---|---|
| **Platform state** | **C — RUNNABLE, CORE VERIFIED** |
| **Deployment** | **BLOCKED** — three specific reasons, below |
| **Build** | FastAPI 2.5.0, Python 3.13, PostgreSQL 16, Redis 7 |
| **HEAD** | `1110adae` |
| **Branch** | `claude/p0-2-pharmacy-reconciliation` (PR #258) |
| **Worktree** | clean |
| **CI** | **UNAVAILABLE — external.** Runs 596–599 each complete as `failure` in 3–5 s with no runner assigned, no steps recorded, 404 on log download. Unchanged since 2026-09-18T07:40Z. Every gate below was therefore run locally. |
| **Database** | clean `gula_run`, `alembic upgrade head` from empty → **423 tables**, head `20260916_0001`, exit 0 |
| **Migrations** | applied from empty four times during this pass; each followed by a full gate run |

## GATES

| Gate | State | Checks |
|---|---|---|
| 1 Startup | **VERIFIED** | startup guard passed in 1.1–2.2 s across 10 cold boots; `system_ready: true`; 1794 OpenAPI paths served |
| 2 Database | **VERIFIED** | migration → startup → query → write → read → transaction → rollback |
| 3 Authentication | **VERIFIED** | 21/21 |
| 4 Authorization | **VERIFIED** | 11/11 |
| 5 Tenant isolation | **VERIFIED** | 11/11 |
| 6 Core clinical path | **VERIFIED**, 2 steps UNAVAILABLE | 14/14 |
| 7 Frontend ↔ backend | **PARTIALLY VERIFIED** | contract only: 367 of 434 called paths served |
| Golden path (§24) | **VERIFIED to step 13**, plus 14–15 | restart proven coherent; frontend step not run |
| Clean start (§25) | **VERIFIED** | dropped database + flushed Redis → 57/57 |

`scripts/runtime_gates.py` — **57/57, exit 0**. Every assertion carries a
positive control, because a probe that refuses everything looks exactly like a
passing security check.

**AUTH** — valid credential accepted; wrong password, unknown account, no
credential, malformed token, expired token and an unapproved lab all rejected;
refresh issues a working token; logout revokes; a login burst is rate limited;
a locked account is refused **with the right password** and works again once
unlocked.

**AUTHORIZATION** — a lab admin reads its own session, patients and lab
profile, and is refused another lab's profile, the pending-registration queue,
lab creation, lab approval and lab deactivation. Expired token refused a tenant
read. Its audit view holds no other tenant's rows.

**TENANT ISOLATION** — Beta cannot read, update, list, search or id-guess
Alpha's patient.

**CLINICAL SAFETY** — the optimistic lock is driven in all three directions: no
`If-Match` → 428, stale → 409, observed version → 200, and the value reads
back. Two steps are **UNAVAILABLE** and reported as such rather than skipped.

**AUDIT** — the chain carries `('create', patient)`, `('create', lab_order)`,
`('create', sample)`, `('update', lab_result)`, plus `login`, `login_failed`,
`login_denied_mfa_required`, `login_lockout_started`, `login_denied_lockout`,
`activate_lab` and `mfa_enrolled_out_of_band`.

**RECOVERY** — the stack was restarted mid-session and the clinical record came
back byte-identical through the API.

**IDENTITY / MOBILE / AI** — not exercised this pass.

## FIXED (9)

| ID | Sev | What was actually wrong |
|---|---|---|
| NR-111 | P0 | A fresh deployment could not be administered at all. `/login` refuses a privileged role without MFA; the only enrolment endpoint needs a session; the bootstrap creates exactly one account and it is privileged. Added `scripts/enroll_mfa.py` — enrolment by database credential, a strictly stronger authority than the session it substitutes for. The login gate is untouched. |
| NR-112 | P1 | `create_master_admin.py`, the documented recovery path, died with `NameError('os')` before opening a connection and swallowed every exception silently. Seven more undefined names behind it, including `Lab` in `generate_demo_data.py`. 8 → 0. |
| NR-113 | P1 | 26 SQL filters compiled to `WHERE false`. The lab approval queue returned 0 with two labs waiting; a shared radiology study could not be revoked; 20 LIMS list endpoints returned nothing whatever the data held. |
| NR-115 | P0 | Logout was a no-op for every non-browser client. `POST /logout` → 200, then the same bearer token → 200. Now 401. |
| NR-116 | P0 | Any lab admin could activate another lab (200), **deactivate a live laboratory** (200), create labs (201), read another lab's licence and every pending registrant's email. |
| NR-117 | P0 | `POST /patients` answered 500 for every request. Two column overflows — a 21-character id in a `varchar(20)`, and a validator that accepted `"male"` for a `varchar(1)`. SQLite does not enforce varchar length, which is why the suite never saw either. |
| NR-122 | P1 | 60 identity routes were served at `/niam/niam/…` because three routers repeated the prefix their parent applies. 24 frontend calls were 404ing against the address they correctly asked for. |
| NR-124 | P2 | A test imported through the `backend.` shadow root that NR-056 and NR-058 exist to prevent, polluting `sys.modules` for the session. |
| NR-125 | P2 | Two startup-guard tests set an environment variable the code had already frozen into a module constant. |

## REGISTERED, NOT FIXED (6)

| ID | Sev | Why it is still open |
|---|---|---|
| NR-114 | P1 | **MFA is an enrolment checkbox, never a challenge.** After enrolling, email and password alone return a full access token — the second factor is never presented. A stolen password still yields a privileged session. The fix changes `/login`'s response shape for privileged accounts, which CLAUDE.md reserves for human approval. |
| NR-119 | P1 | `national_patients` is built by no migration, so three EHR reads **and** `POST /ehr/clinical-notes` 500. The fix is a migration, which CLAUDE.md reserves. |
| NR-121 | P1 | `nhdw_queue_entries.encounter_id` is in the ORM and not in the table, so patient check-in 500s. Migration, reserved. |
| NR-118 | P2 | 87 unit tests fail only in company. Three attributed and fixed; 84 remain in five clusters. |
| NR-123 | P2 | 21 frontend calls request a path with an empty segment. The contract guard was skipping exactly those; it no longer does. |
| NR-120 | P2 | Clinical audit rows carry a NULL `lab_id`. Nothing leaks today; any query keyed on `lab_id` misses them. |

## REMAINING BLOCKERS TO DEPLOYMENT

1. **NR-114** — a stolen password alone yields a full privileged session.
2. **NR-119 / NR-121** — check-in, queue and clinical notes answer 500 on a
   migration-built schema.
3. **No frontend evidence** — the API is proven, the product is not. Contract
   alignment is measured; no rendered login has been run.
4. **CI cannot confirm any of it** — the runners have not provisioned since
   07:40Z, so every claim here rests on local execution.

## TESTS

| | |
|---|---|
| Full unit suite | **3041 passed, 84 failed** (HEAD baseline: 3021 / 87) |
| The 84 | pre-existing and order-dependent — all pass under `--lf` in 42 s; measured at HEAD and after, same clusters |
| Focused suites | 494 passed (patients/admin/login/auth/tenant), 577 (identity/niam), 680 (contract/capability) |
| New guards | 15 in `test_runtime_activation_guards.py`, 4 in `test_frontend_backend_contract.py`, 2 in `test_engineering_tooling_imports.py` |
| Negative proofs | **13/13 held** — 8 for the activation guards, 5 for the contract guards. Every file restored and byte-compared. |

## EXACT COMMANDS USED FOR FINAL VERIFICATION

```bash
# clean slate — this is the §25 clean-start test
redis-cli -n 0 FLUSHDB
psql -c "DROP DATABASE IF EXISTS gula_run;" -c "CREATE DATABASE gula_run;"
cd backend && alembic upgrade head          # 423 tables, head 20260916_0001, exit 0

# the real server, then the one account a clean database has
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python3 scripts/enroll_mfa.py --role master_admin        # NR-111

# the gates
python3 scripts/runtime_gates.py --base http://127.0.0.1:8000    # 57/57, exit 0

# the guards CI would run
cd backend
python3 -m pytest tests/test_runtime_activation_guards.py -q
python3 -m pytest tests/test_frontend_backend_contract.py -q
python3 -m pytest tests/test_engineering_tooling_imports.py -q
python3 -m pytest tests/ -q -p no:randomly -m "not integration"
```

## METHOD NOTE

Four of the nine fixes were invisible to every static gate the repository has,
because each is valid Python that does the wrong thing at runtime:
`filter(not Model.flag)` compiles and matches nothing; a 21-character id fits a
Python string and not the column; a cookie read returns `None` instead of
failing; a router prefix applied twice serves a real route at an address nobody
calls. They were found by starting the system and using it.

Two were found in the guards rather than the code: the frontend contract guard
was skipping exactly the calls that are certainly broken, and one of my own
guards reported a clean result when its checker was not installed. A guard that
cannot fail is worth less than no guard, because it also carries a claim.
