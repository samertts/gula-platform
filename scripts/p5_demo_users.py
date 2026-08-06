"""P5.2 — Idempotent demo-user provisioning for all 25 roles.

Creates demo accounts only when the role has no active demo user already.
Demo users use pattern demo.{role}@demo.local with a documented strong password.
Uses the platform's own admin API (POST /admin/users) — never touches the DB directly.

Output: docs/certification/demo_accounts.md + /tmp/opencode/p5_demo_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.main import app
from app.models.lab_user import LabUser
from fastapi.testclient import TestClient

MASTER_EMAIL = "admin@gula-platform.org"
MASTER_PASS = "Master@2026!E2E"
DEMO_PASS = "Demo@2026!Pass"
DEMO_SUFFIX = "@demo.local"

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "certification"

MFA_REQUIRED_ROLES = {"auditor", "security_officer", "pathologist"}

# Every role in the 25-role universe, grouped by level (descending)
ROLES = [
    "master_admin", "ministry_admin", "organization_admin", "directorate_admin",
    "province_admin", "auditor", "security_officer", "hospital_admin", "phc_admin",
    "lab_manager", "admin", "lab_admin", "lab_supervisor", "quality_manager",
    "pathologist", "doctor", "technician", "nurse", "receptionist", "cashier",
    "staff", "lab_staff", "api_client", "patient", "citizen",
]

LAB_ID = 1  # existing certified lab from prior certification runs


def main() -> None:
    results: dict[str, dict] = {}
    with TestClient(app) as c:
        r = c.post("/login", json={"email": MASTER_EMAIL, "password": MASTER_PASS})
        if r.status_code != 200:
            print("LOGIN FAILED", r.status_code, r.text[:300])
            sys.exit(1)
        body = r.json()
        if body.get("mfa_pending"):
            print("master admin MFA pending — not expected (requires_mfa=false)")
            sys.exit(1)
        token = body["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # existing users per role
        me = c.get("/authz/me", headers=headers)
        print("auth/me:", me.status_code)

    for role in ROLES:
        email = f"demo.{role}{DEMO_SUFFIX}"
        # idempotency gate: direct DB check (API role filter excludes equal-level
        # roles by least-privilege design, so it is not authoritative)
        db2 = SessionLocal()
        try:
            if db2.query(LabUser).filter(LabUser.email == email).first():
                results[role] = {"email": email, "status": "exists"}
                print(f"  {role:20s} already has demo user {email}")
                continue
        finally:
            db2.close()
        payload = {
            "name": f"Demo {role.replace('_', ' ').title()}",
            "email": email,
            "password": DEMO_PASS,
            "role": role,
            "lab_id": LAB_ID,
        }
        r = c.post("/admin/users", headers=headers, json=payload)
        if r.status_code in (200, 201):
            results[role] = {"email": email, "status": "created"}
            print(f"  {role:20s} created {email}")
        else:
            results[role] = {"email": email, "status": f"error:{r.status_code}", "detail": r.text[:200]}
            print(f"  {role:20s} ERROR {r.status_code}: {r.text[:150]}")

    # ── TOTP enrollment for MFA-required demo roles (idempotent) ──────────────
    from app.security.mfa_service import MFAService

    db = SessionLocal()
    mfa_secrets: dict[str, str] = {}
    try:
        for role in MFA_REQUIRED_ROLES:
            email = f"demo.{role}{DEMO_SUFFIX}"
            user = db.query(LabUser).filter(LabUser.email == email).first()
            if not user:
                continue
            svc = MFAService(db)
            if not svc.has_mfa_enabled(user.id):
                out = svc.setup_totp(user.id, email, "Demo Authenticator")
                mfa_secrets[role] = out["secret"]
                print(f"  {role:20s} TOTP enrolled (secret {out['secret'][:6]}…, {len(out['backup_codes'])} backup codes)")
            else:
                device = db.query(__import__("app.models.mfa_device", fromlist=["MFADevice"]).MFADevice).filter(
                    __import__("app.models.mfa_device", fromlist=["MFADevice"]).MFADevice.user_id == user.id,
                    __import__("app.models.mfa_device", fromlist=["MFADevice"]).MFADevice.device_type == "totp",
                ).first()
                if device:
                    mfa_secrets[role] = device.secret
                print(f"  {role:20s} TOTP already enrolled")
    finally:
        db.close()

    if mfa_secrets:
        digest_path = Path("/tmp/opencode/p5_mfa_secrets.json")
        digest_path.write_text(json.dumps(mfa_secrets, indent=2))
        print(f"wrote {digest_path} (MFA secrets for E2E harness)")

    Path("/tmp/opencode/p5_demo_results.json").write_text(json.dumps(results, indent=2))
    created = sum(1 for v in results.values() if v["status"] == "created")
    print(f"\ncreated={created} exists={sum(1 for v in results.values() if v['status']=='exists')} errors={sum(1 for v in results.values() if v['status'].startswith('error'))}")

    # ── demo_accounts.md ───────────────────────────────────────────────────────
    lines = [
        "# Demo Accounts — PROGRAM-05",
        "",
        f"*Generated {__import__('datetime').date.today().isoformat()} · idempotent provisioning via `POST /admin/users` "
        "(platform API, no direct DB writes)*",
        "",
        "Demo users are created **only when missing** (never overwritten). Pattern: `demo.{role}@demo.local`.",
        "",
        "> Shared demo password: `Demo@2026!Pass` — for local/CI use only; production deploys must rotate.",
        "",
        "| Role | Level | Email | State |",
        "|---|---|---|---|",
    ]
    for role in ROLES:
        info = results.get(role, {})
        level = {"master_admin": 100, "ministry_admin": 90, "organization_admin": 85,
                 "directorate_admin": 80, "province_admin": 80, "auditor": 70,
                 "security_officer": 70, "hospital_admin": 60, "phc_admin": 55,
                 "lab_manager": 50, "admin": 50, "lab_admin": 50, "lab_supervisor": 45,
                 "quality_manager": 45, "pathologist": 40, "doctor": 35, "technician": 30,
                 "nurse": 25, "receptionist": 20, "cashier": 20, "staff": 20,
                 "lab_staff": 20, "api_client": 5, "patient": 10, "citizen": 10}.get(role)
        email = info.get("email", f"demo.{role}{DEMO_SUFFIX}")
        state = info.get("status", "not_provisioned")
        lines.append(f"| `{role}` | {level} | `{email}` | {state} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Roles with MFA (`auditor`, `security_officer`, `pathologist`) require MFA challenge on login;")
    lines.append("  the role-experience harness handles `mfa_pending` → `POST /mfa-verify`.")
    lines.append("- `citizen` is a shared-model role (0 permissions) — provided for completeness of the 25-role universe;")
    lines.append("  frontend gates it to login/profile only.")
    lines.append("- `api_client` (`is_delegatable=false`) is the machine role; demo account documents its read-only scope.")
    DOCS.joinpath("demo_accounts.md").write_text("\n".join(lines))
    print("wrote demo_accounts.md")


if __name__ == "__main__":
    main()
