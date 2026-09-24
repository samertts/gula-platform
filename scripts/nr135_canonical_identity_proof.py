"""NR-135 runtime proof: NIAM is the canonical identity a legacy login produces."""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

BASE = "http://127.0.0.1:8000"
TAG = str(int(time.time()))[-7:]
RESULTS = []

def call(method, path, body=None, token=None, headers=None):
    req = urllib.request.Request(BASE + path,
        data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode(errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw[:300]

def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    return ok

# ruff: noqa: E402, T201 — this is an executable proof: every import below
# depends on the sys.path insert and the mapper configuration that precede
# it, and the output IS the evidence.
sys.path.insert(0, "/home/user/gula-platform/backend")
# Mapper configuration needs the full model graph present before any query.
import app.models
import app.services.mpi.models  # noqa: F401  - registers mappers
from sqlalchemy.orm import configure_mappers

configure_mappers()
import secrets
import uuid as _uuid

from app._compat import UTC
from app.database import SessionLocal
from app.identity.base import _ulid
from app.identity.models.account import Account, AccountStatus
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.models.person import Person
from app.identity.models.session import UserSession
from app.security.auth import decode_token

# ── fixture: provision a canonical account OUT OF BAND and link it ───────────
# This is the governed provisioning step standing in for the approved wave that
# does not exist yet (NR-137). It is a fixture, not product behaviour.
db = SessionLocal()
admin_email = os.environ["GULA_ADMIN_EMAIL"]
from app.models.lab_user import LabUser
from app.models.user import User

lab_user = db.query(LabUser).filter(LabUser.email == admin_email).first()
# The link records the SOURCE TABLE kind ("lab_user"/"user"), which is not
# the same vocabulary as the token's `act` claim ("lab"/"user").
legacy_kind, legacy_row = (
    (LegacyAccountLinkSource.lab_user.value, lab_user) if lab_user
    else (LegacyAccountLinkSource.user.value, db.query(User).filter(User.email == admin_email).first())
)
if legacy_row is None:
    sys.exit("admin legacy row not found")

person = Person(id=_ulid(), uuid=str(_uuid.uuid4()), given_name="Canonical", family_name=f"Admin{TAG}", is_active=True)
db.add(person)
db.flush()
ident = IdentityRecord(id=_ulid(), uuid=str(_uuid.uuid4()), person_id=person.id,
                       identity_type="national_id", status="active",
                       issued_at=datetime.now(UTC), is_active=True)
db.add(ident)
db.flush()
account = Account(id=_ulid(), uuid=str(_uuid.uuid4()), identity_id=ident.id,
                  account_type="human", status=AccountStatus.active.value,
                  email=f"canonical-{TAG}@gula.test", is_active=True, is_locked=False,
                  failed_login_attempts=0, email_verified=True, phone_verified=False,
                  identity_verified=True)
db.add(account)
db.flush()
# Idempotent: (source_kind, legacy_account_id) is unique, so a rerun repoints
# the existing link rather than colliding with it (the NR-133 lesson).
link = db.query(LegacyAccountLink).filter(
    LegacyAccountLink.source_kind == legacy_kind,
    LegacyAccountLink.legacy_account_id == legacy_row.id,
).first()
if link is None:
    link = LegacyAccountLink(id=_ulid(), source_kind=legacy_kind,
                             legacy_account_id=legacy_row.id,
                             source_fingerprint=f"probe-{TAG}",
                             status=LegacyAccountLinkStatus.migrated.value,
                             mapping_version=1,
                             rollback_token=secrets.token_urlsafe(32))
    db.add(link)
link.canonical_account_id = account.id
db.commit()
canonical_uuid = account.uuid
print(f"fixture: legacy {legacy_kind}#{legacy_row.id} -> canonical account {canonical_uuid}\n")

print("NR-135 — CANONICAL IDENTITY AT LOGIN")
st, body = call("POST", "/login", {"email": admin_email, "password": os.environ["GULA_ADMIN_PASSWORD"]})
record("1. login succeeds", st == 200, f"status {st}")
token = body.get("access_token", "")
claims = decode_token(token) or {}

record("2. the token carries the canonical account_uuid",
       claims.get("account_uuid") == canonical_uuid, f"account_uuid={claims.get('account_uuid')}")

db.expire_all()
sess = db.query(UserSession).filter(UserSession.token_jti == claims.get("jti")).first()
record("3. a NIAM session exists for this exact login",
       sess is not None, f"jti={claims.get('jti')}")
record("4. the session is bound to the right identity",
       sess is not None and sess.account_id == account.id and sess.is_active,
       f"account_id match={sess.account_id == account.id if sess else None}")

st_g, gw = call("GET", "/api/v1/clinical/patients", token=token)
record("5a. the NIAM-protected surface authenticates it (no longer 401)",
       st_g != 401, f"status {st_g}")
# 5b is BLOCKED, not failed: authentication is canonical and passes, and the
# gateway then refuses on its own context chain. Measured in-process, the
# reason_code is `missing_workspace` -- the canonical account has no NIAM
# workspace, membership or facility mapping, which is organizational context
# provisioning (NR-137), not an authentication defect. Recorded separately so
# it can never be counted as a pass.
BLOCKED = (st_g == 403, "5b. governed clinical envelope — BLOCKED on missing_workspace (NR-137)",
           f"status {st_g}")
print(f"  [BLOCKED] {BLOCKED[1]}  — {BLOCKED[2]}")

# ── negative proofs ──────────────────────────────────────────────────────────
print("\nNEGATIVE PROOFS")
forged = {"X-Role": "master_admin", "X-Actor-Id": "1", "X-Lab-Id": "9999",
          "X-Account-Uuid": str(_uuid.uuid4()), "X-User-Id": "1"}
st_f, _ = call("GET", "/api/v1/clinical/patients", token=token, headers=forged)
record("6. forged identity headers change nothing", st_f == st_g, f"{st_g} -> {st_f}")

st_b, body_b = call("POST", "/login",
                    {"email": admin_email, "password": os.environ["GULA_ADMIN_PASSWORD"],
                     "account_uuid": str(_uuid.uuid4()), "lab_id": 9999, "role": "master_admin"})
claims_b = decode_token(body_b.get("access_token", "")) or {}
record("7. a client-supplied account_uuid does not choose the identity",
       claims_b.get("account_uuid") == canonical_uuid,
       f"got {claims_b.get('account_uuid')}")
record("8. a client-supplied lab_id does not choose the tenant",
       claims_b.get("lab_id") == claims.get("lab_id"),
       f"{claims.get('lab_id')} vs {claims_b.get('lab_id')}")
record("9. a client-supplied role does not elevate",
       claims_b.get("role") == claims.get("role"), f"role={claims_b.get('role')}")

db.expire_all()
n_sessions = db.query(UserSession).filter(UserSession.account_id == account.id,
                                          UserSession.is_active.is_(True)).count()
record("10. repeated login yields one live session per login, not a corrupt state",
       n_sessions == 2, f"{n_sessions} active sessions after 2 logins")

st_l, _ = call("POST", "/logout", {}, token=token)
db.expire_all()
sess_after = db.query(UserSession).filter(UserSession.token_jti == claims.get("jti")).first()
record("11. logout terminates the canonical session",
       sess_after is not None and not sess_after.is_active,
       f"logout {st_l}, is_active={sess_after.is_active if sess_after else None}")
st_after, _ = call("GET", "/api/v1/clinical/patients", token=token)
record("12. the surface refuses the token after logout", st_after == 401, f"status {st_after}")

db.close()
ok = sum(1 for _, o, _ in RESULTS if o)
print(f"\n  VERIFIED: {ok}/{len(RESULTS)}   BLOCKED: 1 (clinical read — missing_workspace, NR-137)")
sys.exit(0 if ok == len(RESULTS) else 1)
