from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime
from app._compat import UTC

from sqlalchemy.orm import Session

from shared.auth.passwords import hash_password, verify_password

from ..models.service_account import ServiceAccount

logger = logging.getLogger("gula.service_accounts")


def _generate_api_key() -> str:
    import uuid as _uuid
    ulid_part = str(_uuid.uuid4()).replace("-", "")[:26]
    random_hex = secrets.token_hex(24)
    return f"gula_{ulid_part}_{random_hex}"


def create_service_account(
    db: Session,
    name: str,
    description: str | None = None,
    roles: list[str] | None = None,
    scopes: list[str] | None = None,
    created_by: int | None = None,
    expires_at: datetime | None = None,
) -> tuple[ServiceAccount, str]:
    api_key = _generate_api_key()
    api_key_hash = hash_password(api_key)
    account = ServiceAccount(
        name=name,
        description=description or "",
        api_key_hash=api_key_hash,
        roles=json.dumps(roles or ["staff"]),
        scopes=json.dumps(scopes or []),
        is_active=True,
        created_by=created_by,
        expires_at=expires_at,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account, api_key


def rotate_api_key(db: Session, account_id: int) -> str | None:
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account or not account.is_active:
        return None
    new_key = _generate_api_key()
    account.api_key_hash = hash_password(new_key)
    db.commit()
    return new_key


def validate_api_key(db: Session, api_key: str) -> ServiceAccount | None:
    if not api_key.startswith("gula_"):
        return None
    accounts = db.query(ServiceAccount).filter(ServiceAccount.is_active.is_(True)).all()
    for account in accounts:
        if verify_password(api_key, account.api_key_hash):
            if account.expires_at and account.expires_at < datetime.now(UTC):
                return None
            account.last_used_at = datetime.now(UTC)
            db.commit()
            return account
    return None


def revoke_service_account(db: Session, account_id: int) -> bool:
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        return False
    account.is_active = False
    db.commit()
    return True


def list_service_accounts(db: Session) -> list[ServiceAccount]:
    return db.query(ServiceAccount).order_by(ServiceAccount.created_at.desc()).all()
