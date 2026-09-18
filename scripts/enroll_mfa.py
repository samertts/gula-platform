#!/usr/bin/env python3
"""
Enrol a second factor for a lab user from the host, without a session.

WHY THIS EXISTS
---------------
``/login`` refuses any account whose role is in ``PRIVILEGED_ROLES``
(master_admin, ministry_admin, province_admin) until that account has an
active MFA device (``app/routes/login.py``).  The only enrolment endpoint,
``POST /mfa/totp/setup``, is itself behind ``get_current_user``.

On a fresh deployment the bootstrap creates exactly one account — the
master admin — and it is privileged.  It therefore cannot log in, and it
cannot enrol, so nobody can administer the platform at all.  This script
is the missing out-of-band step.

It does NOT weaken the login gate.  It requires database credentials,
i.e. host access, which is a strictly stronger authority than a session.
Enrolling ADDS a factor; it never removes or bypasses one.

USAGE
-----
    # 1. enrol — prints the secret, the otpauth:// URI and backup codes
    python3 scripts/enroll_mfa.py --email admin@demo.gula.iq

    # 2. confirm the authenticator is in sync before relying on it
    python3 scripts/enroll_mfa.py --email admin@demo.gula.iq --verify 123456

    # replace an existing device (the old one is deactivated)
    python3 scripts/enroll_mfa.py --email admin@demo.gula.iq --force

    # machine-readable, for an automated first-boot provisioning step
    python3 scripts/enroll_mfa.py --email admin@demo.gula.iq --json

Requires ``DATABASE_URL`` (and the usual secret env vars the app needs).

The secret and the backup codes are printed once and never again.  Treat
the output as a credential: capture it, then clear the scrollback.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO_ROOT, os.path.join(REPO_ROOT, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)


def _fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrol a TOTP second factor for a lab user, out of band.",
    )
    parser.add_argument("--email", help="lab_users.email of the account to enrol")
    parser.add_argument(
        "--role",
        help="enrol the (single) account holding this role, e.g. master_admin",
    )
    parser.add_argument("--device-name", default="Operator Authenticator")
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing active device instead of refusing",
    )
    parser.add_argument(
        "--verify",
        metavar="CODE",
        help="verify a code against the enrolled device instead of enrolling",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON on stdout")
    args = parser.parse_args()

    if not args.email and not args.role:
        _fail("give --email or --role")

    # The ORM registry is only consistent once every model module that
    # participates in a relationship has been imported; `app.models` alone
    # leaves Citizen unresolved and the first query raises InvalidRequestError.
    import app.models  # noqa: F401
    import app.services.mpi.models  # noqa: F401
    from sqlalchemy.orm import configure_mappers

    from app.database import SessionLocal
    from app.models.lab_user import LabUser
    from app.security.mfa_service import MFAService
    from app.services.audit_service import log_action

    configure_mappers()

    db = SessionLocal()
    try:
        query = db.query(LabUser)
        if args.email:
            query = query.filter(LabUser.email == args.email)
        if args.role:
            query = query.filter(LabUser.role == args.role)
        matches = query.all()
        if not matches:
            _fail(f"no lab user matches email={args.email!r} role={args.role!r}")
        if len(matches) > 1:
            _fail(
                f"{len(matches)} lab users match; narrow it with --email "
                f"({', '.join(u.email or str(u.id) for u in matches)})",
            )
        user = matches[0]

        service = MFAService(db)

        if args.verify:
            ok = service.verify_totp(user.id, args.verify)
            if args.json:
                print(json.dumps({"user_id": user.id, "email": user.email, "verified": ok}))
            else:
                print(f"verification for {user.email}: {'OK' if ok else 'FAILED'}")
            sys.exit(0 if ok else 2)

        if service.has_mfa_enabled(user.id) and not args.force:
            _fail(
                f"{user.email} already has an active MFA device. "
                f"Re-run with --force to replace it.",
            )

        result = service.setup_totp(user.id, user.email or str(user.id), args.device_name)

        # An enrolment is a security-relevant mutation, so it belongs in the
        # chain like any other. log_action flushes; the commit below is ours.
        log_action(
            db,
            action="mfa_enrolled_out_of_band",
            resource_type="auth",
            resource_id=user.id,
            user_id=user.id,
            user_role=user.role,
            lab_id=user.lab_id,
            details={
                "device_type": "totp",
                "device_id": result["device_id"],
                "device_name": args.device_name,
                "replaced_existing": bool(args.force),
                "channel": "scripts/enroll_mfa.py",
            },
        )
        db.commit()

        if args.json:
            print(json.dumps({
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "device_id": result["device_id"],
                "secret": result["secret"],
                "uri": result["uri"],
                "backup_codes": result["backup_codes"],
            }))
        else:
            print(f"Enrolled TOTP for {user.email} (id={user.id}, role={user.role})")
            print(f"  device id    : {result['device_id']}")
            print(f"  secret       : {result['secret']}")
            print(f"  otpauth URI  : {result['uri']}")
            print("  backup codes :")
            for code in result["backup_codes"]:
                print(f"      {code}")
            print()
            print("Scan the URI, then confirm with:")
            print(f"  python3 scripts/enroll_mfa.py --email {user.email} --verify <code>")
    finally:
        db.close()


if __name__ == "__main__":
    main()
