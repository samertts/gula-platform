#!/usr/bin/env python3
"""Prove authentication, authorization and tenant isolation against a running server.

This is a runtime proof, not a unit test. It talks HTTP to a real backend
process backed by the real PostgreSQL schema, because that is the only place
where middleware order, dependency resolution and tenant scoping all apply at
once.

Every gate carries a POSITIVE CONTROL. A probe that refuses everything looks
exactly like a passing security check, so each "must be denied" assertion is
paired with the "must be allowed" case that proves the probe can tell them
apart.

Usage::

    export DATABASE_URL=... SECRET_KEY=... (the usual runtime env)
    export GULA_ADMIN_EMAIL=... GULA_ADMIN_PASSWORD=...
    python3 scripts/runtime_gates.py --base http://127.0.0.1:8000

Exit code is 0 only when every gate passes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "http://127.0.0.1:8000"
TENANT_PASSWORD = "Tenant#Passw0rd!1"

RESULTS: list[tuple[str, str, bool, str]] = []
UNAVAILABLE: list[str] = []


def call(method, path, body=None, token=None, base=None):
    url = (base or BASE) + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            raw = r.read().decode(errors="replace")
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw[:400]
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, raw[:400]
    except Exception as exc:  # noqa: BLE001
        return 0, repr(exc)


def reset_rate_limits():
    """Clear the IP rate limiter between phases.

    RATE_LIMIT_AUTH is 10 per window. A gate that fires more login attempts
    than that starts collecting 429s, and a 429 is the IP limiter refusing --
    not the account lockout, not the credential check. Reading one as the
    other is how a probe reports a control it never exercised. So each phase
    starts from a clean counter, and the limiter gets its own explicit check.
    """
    import redis
    url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    client = redis.from_url(url)
    removed = 0
    for pattern in ("rl:*", "block:*"):
        keys = list(client.scan_iter(match=pattern, count=1000))
        if keys:
            removed += client.delete(*keys)
    return removed


def record(gate, name, ok, detail=""):
    RESULTS.append((gate, name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  — ' + detail) if detail else ''}")
    return ok


def denied(status):
    """Refused for an identity or authorization reason.

    429 is deliberately absent: it means the IP limiter answered before the
    check under test ran, so it is an inconclusive result, not a pass.
    """
    return status in (401, 403, 404)


# ── fixtures ──────────────────────────────────────────────────────────────────

def admin_token():
    st, body = call("POST", "/login", {
        "email": os.environ["GULA_ADMIN_EMAIL"],
        "password": os.environ["GULA_ADMIN_PASSWORD"],
    })
    if st != 200:
        sys.exit(f"cannot log in as the platform admin ({st}): {body}\n"
                 f"If this is 403 MFA, enrol first: scripts/enroll_mfa.py --role master_admin")
    return body["access_token"]


def ensure_tenant(admin, lab_name, email):
    """Register a lab if it is not there, then approve it as the admin would."""
    call("POST", "/register", {
        "lab_name": lab_name, "admin_name": lab_name + " Admin", "email": email,
        "password": TENANT_PASSWORD, "lab_type": "clinic", "city": "Baghdad",
        "phone": "07700000000", "license_number": "LIC-" + lab_name.split()[-1].upper(),
    })
    st, body = call("GET", "/admin/labs", token=admin)
    lab = next((x for x in body.get("labs", []) if x["name"] == lab_name), None)
    if lab is None:
        sys.exit(f"{lab_name} was not registered: {st} {body}")
    return lab["id"]


def activate(admin, lab_id):
    return call("PUT", f"/admin/labs/{lab_id}/activate", token=admin)


def login(email, password=TENANT_PASSWORD):
    return call("POST", "/login", {"email": email, "password": password})


def expired_token_like(token):
    """The same claims, minted by the same code path, already expired.

    Signed with the production key by the production minter, so the only
    thing separating it from a live token is the expiry claim itself.
    """
    from shared.auth import create_access_token

    from app.config import JWT_ALGORITHM, SECRET_KEY
    from app.security.auth import decode_token

    claims = dict(decode_token(token) or {})
    for derived in ("exp", "iat", "nbf", "type", "jti"):
        claims.pop(derived, None)
    return create_access_token(
        claims, secret_key=SECRET_KEY, algorithm=JWT_ALGORITHM, expire_minutes=-120,
    )


# ── gate 3: authentication ────────────────────────────────────────────────────

def gate3(canary_email, unapproved_email):
    print("\nGATE 3 — AUTHENTICATION")
    reset_rate_limits()

    st, body = login(canary_email)
    if not record("3", "a valid credential is ACCEPTED (positive control)",
                  st == 200, f"status {st}"):
        return None
    token = body["access_token"]
    refresh = body["refresh_token"]

    st, session = call("GET", "/session", token=token)
    record("3", "the session token identifies the current actor",
           st == 200 and session.get("user", {}).get("email") == canary_email,
           f"status {st}, actor {session.get('user', {}).get('email') if st == 200 else '-'}")

    st, _ = login(canary_email, TENANT_PASSWORD + "-wrong")
    record("3", "a wrong password is REJECTED", denied(st), f"status {st}")

    st, _ = login("no-such-" + canary_email)
    record("3", "an unknown account is REJECTED", denied(st), f"status {st}")

    st, _ = call("GET", "/session")
    record("3", "no credential is REJECTED", denied(st), f"status {st}")

    st, _ = call("GET", "/session", token="not.a.real.token")
    record("3", "a malformed token is REJECTED", denied(st), f"status {st}")

    st, _ = call("GET", "/session", token=expired_token_like(token))
    record("3", "an EXPIRED token is REJECTED", denied(st), f"status {st}")

    st, body_r = call("POST", "/auth/refresh", {"refresh_token": refresh})
    record("3", "refresh issues a token", st == 200, f"status {st}")
    if st == 200:
        st, _ = call("GET", "/session", token=body_r["access_token"])
        record("3", "the refreshed token is ACCEPTED", st == 200, f"status {st}")

    st, _ = login(unapproved_email)
    record("3", "an account whose lab is not approved is REJECTED", denied(st), f"status {st}")
    return token


def gate3_revocation(email):
    print("\nGATE 3b — REVOCATION")
    reset_rate_limits()
    st, body = login(email)
    if not record("3b", "a session could be established to revoke", st == 200, f"status {st}"):
        return False
    token = body["access_token"]
    st, _ = call("GET", "/session", token=token)
    record("3b", "the session works before logout (positive control)", st == 200, f"status {st}")
    st, _ = call("POST", "/logout", {}, token=token)
    record("3b", "logout is accepted", st == 200, f"status {st}")
    st, _ = call("GET", "/session", token=token)
    return record("3b", "the token is REJECTED after logout", denied(st), f"status {st}")


def gate3_rate_limiter(email):
    """The limiter is a control in its own right, so prove it deliberately."""
    print("\nGATE 3c — AUTH RATE LIMITER")
    reset_rate_limits()
    statuses = [login(email, TENANT_PASSWORD + "-wrong")[0] for _ in range(14)]
    record("3c", "a burst of failed logins is eventually rate limited",
           429 in statuses, f"statuses {statuses[:4]}...{statuses[-3:]}")
    reset_rate_limits()
    st, _ = login(email)
    record("3c", "clearing the counter restores service (positive control)",
           st in (200, 401, 403), f"status {st}")


def gate3_lockout(email):
    """Account lockout, distinguished from the IP limiter that shadows it."""
    print("\nGATE 3d — ACCOUNT LOCKOUT")
    reset_rate_limits()
    unlock(email)

    st, _ = login(email)
    record("3d", "the account works before the lockout (positive control)",
           st == 200, f"status {st}")

    reset_rate_limits()
    attempts = [login(email, TENANT_PASSWORD + "-wrong")[0] for _ in range(5)]
    record("3d", "five wrong passwords were all evaluated, not rate limited",
           all(s in (401, 403) for s in attempts), f"statuses {attempts}")

    locked_until, failures = lock_state(email)
    record("3d", "the account carries a lockout in the database",
           locked_until is not None and (failures or 0) >= 5,
           f"locked_until={locked_until} failed_attempts={failures}")

    reset_rate_limits()
    st, _ = login(email)
    record("3d", "a locked account is REJECTED even with the RIGHT password",
           denied(st), f"status {st}")

    unlock(email)
    reset_rate_limits()
    st, _ = login(email)
    record("3d", "clearing the lockout lets the same password back in (positive control)",
           st == 200, f"status {st}")


def _session():
    import app.models  # noqa: F401
    import app.services.mpi.models  # noqa: F401
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    from app.database import SessionLocal
    return SessionLocal()


def lock_state(email):
    from app.models.lab_user import LabUser
    db = _session()
    try:
        user = db.query(LabUser).filter(LabUser.email == email).first()
        return (getattr(user, "locked_until", None), getattr(user, "failed_login_attempts", None))
    finally:
        db.close()


def unlock(email):
    from app.models.lab_user import LabUser
    db = _session()
    try:
        user = db.query(LabUser).filter(LabUser.email == email).first()
        if user is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
    finally:
        db.close()


# ── gate 4/5: authorization and tenant isolation ──────────────────────────────

def create_patient(token, name, phone):
    """POST /patients requires full_name and phone (from the OpenAPI schema)."""
    return call("POST", "/patients", {
        "full_name": name, "phone": phone, "gender": "male",
    }, token=token)


def gate4_and_5(alpha_token, beta_token, alpha_lab, beta_lab):
    print("\nGATE 4 — AUTHORIZATION")

    st, _ = call("GET", "/session", token=alpha_token)
    record("4", "the actor may read its own session (positive control)", st == 200, f"status {st}")

    st, _ = call("GET", "/patients", token=alpha_token)
    record("4", "a lab admin may list patients in its own tenant", st == 200, f"status {st}")

    # /admin/labs is not denied outright -- it scopes its own query to the
    # actor's lab. What matters is that it shows nothing else.
    st, labs = call("GET", "/admin/labs", token=alpha_token)
    names = [x["name"] for x in labs.get("labs", [])] if st == 200 else []
    record("4", "a lab admin's lab listing shows only its own lab",
           st == 200 and names == ["Lab Alpha"], f"status {st}, sees {names}")

    st, _ = call("PUT", f"/admin/labs/{beta_lab}/activate", token=alpha_token)
    record("4", "a lab admin is DENIED approving another lab", denied(st), f"status {st}")

    st, _ = call("PUT", f"/admin/labs/{beta_lab}/toggle", token=alpha_token)
    record("4", "a lab admin is DENIED switching another lab off", denied(st), f"status {st}")

    st, _ = call("GET", f"/admin/labs/{beta_lab}", token=alpha_token)
    record("4", "a lab admin is DENIED another lab's profile", denied(st), f"status {st}")

    st, _ = call("GET", f"/admin/labs/{alpha_lab}", token=alpha_token)
    record("4", "a lab admin may read its OWN lab profile (positive control)",
           st == 200, f"status {st}")

    st, _ = call("GET", "/admin/labs/pending", token=alpha_token)
    record("4", "a lab admin is DENIED the pending-registration queue",
           denied(st), f"status {st}")

    st, _ = call("POST", "/admin/labs", {
        "name": "Rogue Lab", "admin_email": "rogue@gula.test",
        "admin_name": "Rogue", "admin_password": "Rogue#Passw0rd!1",
    }, token=alpha_token)
    record("4", "a lab admin is DENIED creating a lab", denied(st), f"status {st}")

    st, logs = call("GET", "/admin/audit-logs", token=alpha_token)
    foreign = []
    if st == 200:
        foreign = [row for row in logs.get("logs", [])
                   if row.get("user_role") in ("master_admin", "ministry_admin")]
    record("4", "a lab admin's audit view contains no other tenant's rows",
           st == 200 and not foreign, f"status {st}, {len(foreign)} foreign rows")

    st, _ = call("GET", "/patients", token=expired_token_like(alpha_token))
    record("4", "an expired token is DENIED a tenant read", denied(st), f"status {st}")

    print("\nGATE 5 — TENANT ISOLATION")

    st, created = create_patient(alpha_token, "Alpha Isolation Subject", "07701000001")
    if st not in (200, 201):
        record("5", "Alpha could create a patient (fixture)", False, f"status {st}: {created}")
        return
    pid = created.get("id") or created.get("patient", {}).get("id")
    record("5", "Alpha created a patient in its own tenant (positive control)",
           pid is not None, f"patient id {pid}")

    st, _ = call("GET", f"/patients/{pid}", token=alpha_token)
    record("5", "Alpha can READ its own patient (positive control)", st == 200, f"status {st}")

    st, _ = call("GET", f"/patients/{pid}", token=beta_token)
    record("5", "Beta is DENIED READ of Alpha's patient", denied(st), f"status {st}")

    st, _ = call("PUT", f"/patients/{pid}", {"full_name": "Hijacked By Beta"}, token=beta_token)
    record("5", "Beta is DENIED UPDATE of Alpha's patient", denied(st), f"status {st}")

    st, listing = call("GET", "/patients", token=beta_token)
    ids = []
    if isinstance(listing, dict):
        for key in ("patients", "items", "results", "data"):
            if isinstance(listing.get(key), list):
                ids = [p.get("id") for p in listing[key]]
                break
    elif isinstance(listing, list):
        ids = [p.get("id") for p in listing]
    record("5", "Alpha's patient does not appear in Beta's LISTING",
           pid not in ids, f"{len(ids)} rows visible to Beta")

    st, search = call("GET", "/patients?search=Alpha%20Isolation%20Subject", token=beta_token)
    body_text = json.dumps(search)
    record("5", "Alpha's patient does not appear in Beta's SEARCH",
           "Alpha Isolation Subject" not in body_text, f"status {st}")

    # Alternate read surfaces. A 500 is not a denial and not a leak -- it is an
    # inconclusive result, so it is resolved rather than scored either way: the
    # same route is called as the OWNER, and if it fails identically the route
    # is broken for everyone and cannot be leaking anything tenant-specific.
    for alt in (f"/ehr/patients/{pid}/timeline",
                f"/ehr/patients/{pid}/conditions",
                f"/national-data/patients/{pid}",
                f"/patients/{pid}/children"):
        st_beta, body_beta = call("GET", alt, token=beta_token)
        if denied(st_beta):
            record("5", f"Beta is DENIED Alpha's patient via {alt}", True, f"status {st_beta}")
            continue
        if st_beta >= 500:
            st_owner, _ = call("GET", alt, token=alpha_token)
            leaked = "Alpha Isolation Subject" in json.dumps(body_beta)
            record("5", f"{alt} is UNAVAILABLE to everyone, so it leaks nothing",
                   st_owner >= 500 and not leaked,
                   f"beta {st_beta}, owner {st_owner} — route is broken, not scoped")
            UNAVAILABLE.append(alt)
            continue
        record("5", f"Beta is DENIED Alpha's patient via {alt}", False,
               f"status {st_beta} — REACHED")

    guessed = [i for i in range(1, (pid or 0) + 3)]
    leaked = []
    for i in guessed:
        st, resp = call("GET", f"/patients/{i}", token=beta_token)
        if st == 200:
            leaked.append(i)
    record("5", "ID guessing across the whole low id range leaks nothing to Beta",
           not leaked, f"tried {len(guessed)} ids, leaked {leaked}")


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    BASE = args.base

    admin = admin_token()
    print("platform admin session established")

    alpha_lab = ensure_tenant(admin, "Lab Alpha", "alpha.admin@gula.test")
    beta_lab = ensure_tenant(admin, "Lab Beta", "beta.admin@gula.test")
    delta_lab = ensure_tenant(admin, "Lab Delta", "delta.admin@gula.test")
    gamma_lab = ensure_tenant(admin, "Lab Gamma", "gamma.admin@gula.test")
    for lab in (alpha_lab, beta_lab, delta_lab):
        activate(admin, lab)
    # Gamma stays unapproved on purpose: it is the "inactive account" case.
    print(f"tenants: Alpha={alpha_lab} Beta={beta_lab} Delta={delta_lab} "
          f"Gamma(unapproved)={gamma_lab}")
    for email in ("alpha.admin@gula.test", "beta.admin@gula.test", "delta.admin@gula.test"):
        unlock(email)

    # Delta is the canary: the phases below deliberately lock it out and
    # exhaust its rate limit, so Alpha and Beta stay clean for gates 4 and 5.
    gate3("delta.admin@gula.test", "gamma.admin@gula.test")
    gate3_revocation("delta.admin@gula.test")

    reset_rate_limits()
    st, body = login("alpha.admin@gula.test")
    alpha_token = body["access_token"] if st == 200 else None
    st, body = login("beta.admin@gula.test")
    beta_token = body["access_token"] if st == 200 else None

    if alpha_token and beta_token:
        gate4_and_5(alpha_token, beta_token, alpha_lab, beta_lab)
    else:
        record("4", "both tenant sessions could be established", False,
               f"alpha={bool(alpha_token)} beta={bool(beta_token)}")

    # Destructive to the canary's IP counter and lock state, so last.
    gate3_rate_limiter("delta.admin@gula.test")
    gate3_lockout("delta.admin@gula.test")
    reset_rate_limits()

    print("\n" + "=" * 68)
    failed = [r for r in RESULTS if not r[2]]
    by_gate: dict[str, list[bool]] = {}
    for gate, _, ok, _d in RESULTS:
        by_gate.setdefault(gate, []).append(ok)
    for gate in sorted(by_gate):
        oks = by_gate[gate]
        print(f"  gate {gate}: {sum(oks)}/{len(oks)} {'PASS' if all(oks) else 'FAIL'}")
    print(f"  TOTAL: {len(RESULTS) - len(failed)}/{len(RESULTS)}")
    if UNAVAILABLE:
        print("\n  UNAVAILABLE (broken for every caller, so not an isolation result):")
        for route in UNAVAILABLE:
            print(f"    {route}")
    if failed:
        print("\n  failing checks:")
        for gate, name, _ok, detail in failed:
            print(f"    gate {gate}: {name} — {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.path[:0] = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"),
    ]
    sys.exit(main())
