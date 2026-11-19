from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app._compat import UTC
from shared.auth.passwords import hash_password, verify_password

from ..database import get_db
from ..models.oauth2_client import OAuth2Client
from ..models.oauth2_token import OAuth2Token
from ..security.dependencies import get_current_user
from ..security.oauth2_provider import (
    OAuth2IntrospectRequest,
    OAuth2RevokeRequest,
    OAuth2TokenRequest,
    build_openid_config,
    create_access_token_oauth2,
    create_id_token,
    create_refresh_token_oauth2,
    decode_oauth2_refresh_token,
    generate_auth_code,
    generate_client_id,
    generate_client_secret,
    get_jwks,
    hash_token,
    verify_pkce,
)
from ..services.audit_service import log_action

logger = logging.getLogger("gula.routes.oauth2")

router = APIRouter(prefix="/oauth2", tags=["oauth2"])


class ClientRegisterRequest(BaseModel):
    client_name: str
    redirect_uris: list[str] = []
    allowed_scopes: list[str] = []
    grant_types: list[str] = ["authorization_code"]
    response_types: list[str] = ["code"]
    is_confidential: bool = True
    token_endpoint_auth_method: str = "client_secret_basic"


# PORTED from 60c7aa85 (Mustafa's lane), verified independently on this branch.
# OAuth2Client is a platform-global registry -- the model carries no lab_id or
# tenant column at all, by design. This route had only get_current_user, so any
# authenticated user of any role could register a client with attacker-chosen
# redirect_uris, and that client then receives real users' access, refresh and id
# tokens the moment anyone completes /authorize against it. Token theft by
# registration.
#
# The role set is the one service_accounts.py already uses for the same kind of
# security-configuration write, rather than a new vocabulary.
_OAUTH2_CLIENT_ADMIN_ROLES = frozenset({"admin", "master_admin"})


@router.post("/register")
def register_client(
    data: ClientRegisterRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in _OAUTH2_CLIENT_ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to register an OAuth2 client",
        )

    client_id = generate_client_id()
    client_secret = generate_client_secret()
    client = OAuth2Client(
        client_id=client_id,
        client_secret_hash=hash_password(client_secret),
        redirect_uris=json.dumps(data.redirect_uris),
        allowed_scopes=json.dumps(data.allowed_scopes),
        grant_types=json.dumps(data.grant_types),
        response_types=json.dumps(data.response_types),
        is_confidential=data.is_confidential,
        is_active=True,
        token_endpoint_auth_method=data.token_endpoint_auth_method,
    )
    db.add(client)
    db.flush()
    # A new OAuth2 client can receive other users' tokens, so who created it --
    # and with which redirect_uris -- has to be recoverable. The secret itself is
    # never recorded; only its hash is stored, on the client row.
    log_action(
        db,
        action="oauth2.client.registered",
        resource_type="oauth2_client",
        resource_id=client.id,
        user_id=current_user.id,
        user_role=current_user.role,
        lab_id=getattr(current_user, "lab_id", None),
        details={
            "client_id": client_id,
            "client_name": data.client_name,
            "redirect_uris": data.redirect_uris,
            "grant_types": data.grant_types,
            "allowed_scopes": data.allowed_scopes,
            "token_endpoint_auth_method": data.token_endpoint_auth_method,
        },
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(client)
    return {
        "client_id": client.client_id,
        "client_secret": client_secret,
        "client_name": data.client_name,
    }


@router.get("/authorize")
def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str | None = None,
    scope: str | None = None,
    state: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(OAuth2Client).filter(
        OAuth2Client.client_id == client_id,
        OAuth2Client.is_active.is_(True),
    ).first()
    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    response_types = json.loads(client.response_types) if client.response_types else []
    if "code" not in response_types:
        raise HTTPException(status_code=400, detail="Invalid response_type")

    if redirect_uri:
        if not client.redirect_uris:
            raise HTTPException(status_code=400, detail="Client has no registered redirect URIs")
        allowed = json.loads(client.redirect_uris)
        if redirect_uri not in allowed:
            raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    elif client.redirect_uris:
        allowed = json.loads(client.redirect_uris)
        redirect_uri = allowed[0]

    if not code_challenge or not code_challenge_method:
        raise HTTPException(status_code=400, detail="PKCE is required (code_challenge and code_challenge_method)")
    if code_challenge_method not in ("S256",):
        raise HTTPException(status_code=400, detail="Invalid code_challenge_method, only S256 is supported")

    auth_code = generate_auth_code()
    token = OAuth2Token(
        client_id=client_id,
        user_id=current_user.id,
        token_type="authorization_code",
        token_hash=hash_token(auth_code),
        scope=scope,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        is_revoked=False,
    )
    db.add(token)
    db.commit()

    params = f"code={auth_code}"
    if state:
        params += f"&state={state}"
    if redirect_uri:
        return RedirectResponse(url=f"{redirect_uri}?{params}")
    return {"code": auth_code, "state": state}


@router.post("/token")
def token(
    data: OAuth2TokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client = _authenticate_client(request, data, db)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    if data.grant_type == "authorization_code":
        return _handle_auth_code_grant(data, client, db)
    if data.grant_type == "client_credentials":
        return _handle_client_credentials_grant(data, client, db)
    if data.grant_type == "refresh_token":
        return _handle_refresh_token_grant(data, client, db)
    raise HTTPException(status_code=400, detail="Unsupported grant_type")


@router.post("/introspect")
def introspect(
    data: OAuth2IntrospectRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Introspect a token issued to the calling client (RFC 7662).

    This endpoint answered an unauthenticated request and, on a hit, disclosed
    client_id, user_id, scope, token_type and exp. RFC 7662 §2.1 requires
    authorization here specifically "to prevent token scanning attacks": without it
    the endpoint is an oracle for testing whether any token is valid, and a hit
    identifies the user behind it.

    The control was already in this module — /token has always called
    _authenticate_client — and only these two endpoints omitted it.
    """
    client = _authenticate_client(request, data, db)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    token_hash = hash_token(data.token)
    token_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == token_hash,
        OAuth2Token.is_revoked.is_(False),
        # A client may only introspect its own tokens. RFC 7662 says to answer
        # `active: false` rather than an error, so this does not become an oracle
        # for which tokens exist under another client.
        OAuth2Token.client_id == client.client_id,
    ).first()
    if not token_record:
        return {"active": False}

    now = datetime.now(UTC)
    if token_record.expires_at < now:
        return {"active": False}

    return {
        "active": True,
        "client_id": token_record.client_id,
        "user_id": token_record.user_id,
        "scope": token_record.scope,
        "token_type": token_record.token_type,
        "exp": int(token_record.expires_at.timestamp()),
    }


@router.post("/revoke")
def revoke(
    data: OAuth2RevokeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Revoke a token issued to the calling client (RFC 7009).

    This endpoint answered an unauthenticated request and committed
    the revocation of any token whose value the caller supplied — an
    unauthenticated, targeted denial of service against any session or grant.
    """
    client = _authenticate_client(request, data, db)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    token_hash = hash_token(data.token)
    token_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == token_hash,
        OAuth2Token.is_revoked.is_(False),
        # RFC 7009 §2.1: the server ensures the token was issued to this client.
        OAuth2Token.client_id == client.client_id,
    ).first()
    if token_record:
        token_record.is_revoked = True
        db.commit()
    # RFC 7009 §2.2: answer 200 whether or not the token existed, so the response
    # does not reveal which tokens are valid.
    return {"message": "Token revoked"}


@router.get("/.well-known/openid-configuration")
def openid_config():
    return build_openid_config()


@router.get("/jwks.json")
def jwks_json():
    return {"keys": get_jwks()}


def _authenticate_client(
    request: Request,
    data: OAuth2TokenRequest | OAuth2IntrospectRequest | OAuth2RevokeRequest,
    db: Session,
) -> OAuth2Client | None:
    client_id = data.client_id
    client_secret = data.client_secret

    if not client_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            decoded = base64.b64decode(auth_header[6:]).decode()
            client_id, client_secret = decoded.split(":", 1)

    if not client_id:
        return None

    client = db.query(OAuth2Client).filter(
        OAuth2Client.client_id == client_id,
        OAuth2Client.is_active.is_(True),
    ).first()
    if not client:
        return None

    if client.token_endpoint_auth_method == "none":
        return client

    if not client_secret:
        return None

    if verify_password(client_secret, client.client_secret_hash):
        return client
    return None


def _handle_auth_code_grant(data: OAuth2TokenRequest, client: OAuth2Client, db: Session) -> dict:
    if not data.code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    code_hash = hash_token(data.code)
    token_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == code_hash,
        OAuth2Token.client_id == client.client_id,
        OAuth2Token.token_type == "authorization_code",
        OAuth2Token.is_revoked.is_(False),
    ).first()
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    now = datetime.now(UTC)
    if token_record.expires_at < now:
        raise HTTPException(status_code=400, detail="Authorization code expired")

    if token_record.code_challenge and token_record.code_challenge_method:
        if not data.code_verifier:
            raise HTTPException(status_code=400, detail="Code verifier required")
        if not verify_pkce(data.code_verifier, token_record.code_challenge, token_record.code_challenge_method):
            raise HTTPException(status_code=400, detail="PKCE verification failed")

    token_record.is_revoked = True
    db.commit()

    access_token, expires_in = create_access_token_oauth2(
        client_id=client.client_id,
        user_id=token_record.user_id,
        scope=token_record.scope,
    )
    refresh_token = create_refresh_token_oauth2(
        client_id=client.client_id,
        user_id=token_record.user_id,
        scope=token_record.scope,
    )

    _store_token(db, client.client_id, token_record.user_id, "access", access_token, token_record.scope, expires_in)
    _store_token(db, client.client_id, token_record.user_id, "refresh", refresh_token, token_record.scope, 86400 * 30)

    result = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "scope": token_record.scope,
    }

    if token_record.user_id and "openid" in (token_record.scope or "").split():
        id_token = create_id_token(
            user_id=token_record.user_id,
            client_id=client.client_id,
        )
        result["id_token"] = id_token

    return result


def _handle_client_credentials_grant(data: OAuth2TokenRequest, client: OAuth2Client, db: Session) -> dict:
    scope = data.scope
    if scope and client.allowed_scopes:
        allowed = json.loads(client.allowed_scopes)
        for s in scope.split():
            if s not in allowed:
                raise HTTPException(status_code=400, detail=f"Scope '{s}' not allowed")

    access_token, expires_in = create_access_token_oauth2(
        client_id=client.client_id,
        user_id=None,
        scope=scope,
    )
    _store_token(db, client.client_id, None, "access", access_token, scope, expires_in)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "scope": scope or "",
    }


def _handle_refresh_token_grant(data: OAuth2TokenRequest, client: OAuth2Client, db: Session) -> dict:
    if not data.refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")

    payload = decode_oauth2_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid refresh_token")

    if payload.get("client_id") != client.client_id:
        raise HTTPException(status_code=400, detail="Client mismatch")

    old_hash = hash_token(data.refresh_token)
    old_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == old_hash,
        OAuth2Token.is_revoked.is_(False),
    ).first()
    if old_record:
        old_record.is_revoked = True
        db.commit()

    user_id = payload.get("user_id")
    scope = payload.get("scope") or data.scope

    access_token, expires_in = create_access_token_oauth2(
        client_id=client.client_id,
        user_id=user_id,
        scope=scope,
    )
    new_refresh_token = create_refresh_token_oauth2(
        client_id=client.client_id,
        user_id=user_id,
        scope=scope,
    )

    _store_token(db, client.client_id, user_id, "access", access_token, scope, expires_in)
    _store_token(db, client.client_id, user_id, "refresh", new_refresh_token, scope, 86400 * 30)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": new_refresh_token,
        "scope": scope or "",
    }


def _store_token(
    db: Session,
    client_id: str,
    user_id: int | None,
    token_type: str,
    token: str,
    scope: str | None,
    expires_in: int,
) -> OAuth2Token:
    record = OAuth2Token(
        client_id=client_id,
        user_id=user_id,
        token_type=token_type,
        token_hash=hash_token(token),
        scope=scope,
        expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
        is_revoked=False,
    )
    db.add(record)
    db.commit()
    return record
