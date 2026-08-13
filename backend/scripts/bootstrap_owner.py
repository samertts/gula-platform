"""Create or update the single GULA platform owner account from environment.

Required environment variables:
  OWNER_EMAIL, OWNER_PASSWORD, OWNER_NAME
Optional:
  OWNER_LAB_NAME (defaults to GULA Platform)

The password is never printed or persisted in plaintext.
"""
from __future__ import annotations

import os
import sys

from app.database import SessionLocal
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import hash_password


def main() -> int:
    email = os.getenv("OWNER_EMAIL", "").strip().lower()
    password = os.getenv("OWNER_PASSWORD", "")
    name = os.getenv("OWNER_NAME", "").strip()
    lab_name = os.getenv("OWNER_LAB_NAME", "GULA Platform").strip()
    if not email or not password or not name:
        raise SystemExit("OWNER_EMAIL, OWNER_PASSWORD, and OWNER_NAME are required")
    if len(password) < 12:
        raise SystemExit("OWNER_PASSWORD must be at least 12 characters")

    db = SessionLocal()
    try:
        user = db.query(LabUser).filter(LabUser.email == email).first()
        if user is None:
            lab = db.query(Lab).filter(Lab.name == lab_name).first()
            if lab is None:
                lab = Lab(name=lab_name, lab_type="government", director_name=name, is_active=True)
                db.add(lab)
                db.flush()
            user = LabUser(
                lab_id=lab.id,
                name=name,
                email=email,
                password_hash=hash_password(password),
                role="master_admin",
                is_active=True,
            )
            db.add(user)
        else:
            user.name = name
            user.password_hash = hash_password(password)
            user.role = "master_admin"
            user.is_active = True
        db.commit()
        print(f"Owner account ready: {email} (role=master_admin)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
