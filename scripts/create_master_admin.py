#!/usr/bin/env python3
"""
Create or reset the master admin account.

Usage (run inside the backend container):
    docker exec -it gula-backend python /scripts/create_master_admin.py

Or with inline args (non-interactive):
    docker exec gula-backend python /scripts/create_master_admin.py \
        --email admin@gula-platform.org --password "YourPassword123"
"""
import sys
import os
import argparse
import getpass

# Allow running from repo root or inside container
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import argparse

def main():
    parser = argparse.ArgumentParser(description='Create or reset master admin')
    parser.add_argument('--email',    default=None)
    parser.add_argument('--password', default=None)
    parser.add_argument('--name',     default='GULA Admin')
    parser.add_argument('--force', action='store_true',
                        help='Update existing master admin (reset password)')
    args = parser.parse_args()

    # Prompt interactively if not provided
    email = args.email or input('Admin email [admin@gula-platform.org]: ').strip() or 'admin@gula-platform.org'
    name  = args.name  or input('Admin name  [GULA Admin]: ').strip() or 'GULA Admin'
    if args.password:
        password = args.password
    else:
        password = getpass.getpass('Admin password: ')
        confirm  = getpass.getpass('Confirm password: ')
        if password != confirm:
            print('ERROR: Passwords do not match.', file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print('ERROR: Password must be at least 8 characters.', file=sys.stderr)
        sys.exit(1)

    # ── DB setup ──────────────────────────────────────────────────────────────
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:gula_default_pg_pass@localhost:5432/labdb'
    )

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Ensure platform lab exists
        lab = db.execute(
            text("SELECT id FROM labs WHERE name = 'GULA Platform' LIMIT 1")
        ).fetchone()

        if not lab:
            db.execute(
                text("INSERT INTO labs (name, city, is_active, created_at) "
                     "VALUES ('GULA Platform', 'Platform', true, now()) RETURNING id")
            )
            db.flush()
            lab = db.execute(
                text("SELECT id FROM labs WHERE name = 'GULA Platform' LIMIT 1")
            ).fetchone()
            print(f'  Created platform lab (id={lab.id})')

        lab_id = lab.id
        pw_hash = pwd_context.hash(password)

        existing = db.execute(
            text("SELECT id, email FROM lab_users WHERE role = 'master_admin' LIMIT 1")
        ).fetchone()

        if existing:
            if not args.force:
                print(f'\n  Master admin already exists (id={existing.id}, email={existing.email})')
                print('  Use --force to reset email/password.')
                return
            # --force: reset password and email
            db.execute(
                text("UPDATE lab_users SET email=:email, name=:name, "
                     "password_hash=:pw, is_active=true, perm_version=COALESCE(perm_version,1)+1 "
                     "WHERE id=:id"),
                {'email': email, 'name': name, 'pw': pw_hash, 'id': existing.id}
            )
            db.commit()
            print(f'\n  Master admin RESET (id={existing.id})')
        else:
            db.execute(
                text("INSERT INTO lab_users (lab_id, name, email, password_hash, role, is_active, created_at) "
                     "VALUES (:lab_id, :name, :email, :pw, 'master_admin', true, now())"),
                {'lab_id': lab_id, 'name': name, 'email': email, 'pw': pw_hash}
            )
            db.commit()
            print(f'\n  Master admin CREATED')

        print(f'  Email   : {email}')
        print(f'  Role    : master_admin  (full platform access)\n')

    except Exception as e:
        db.rollback()
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
