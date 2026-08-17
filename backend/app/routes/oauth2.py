from __future__ import annotations
from app.services.route_audit import audit_route_mutation

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


@audit_route_mutation(action="route.register_client", resource_type="oauth2")
@router.post("/register")
def register_client(
    data: ClientRegisterRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    client = OAuth2Client(
        client_id=client_id,
        client_secret_hash=hash_password(client_secret),
        redirect_uris=json.dumps(data.redirect_uris),
        allowed_scopes=json.dumps(data.allowed_scopes),
        grant_types=json.dumps(data.grant_types),
        response_types=json.dumps(data.response_types),
        is_confidential=1 if data.is_confidential else 0,
        is_active=1,
        token_endpoint_auth_method=data.token_endpoint_auth_method,
    )
    db.add(client)
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
        OAuth2Client.is_active == 1,
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
        is_revoked=0,
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
    token_hash = hash_token(data.token)
    token_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == token_hash,
        OAuth2Token.is_revoked == 0,
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


@audit_route_mutation(action="route.revoke", resource_type="oauth2")
@router.post("/revoke")
def revoke(
    data: OAuth2RevokeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    token_hash = hash_token(data.token)
    token_record = db.query(OAuth2Token).filter(
        OAuth2Token.token_hash == token_hash,
        OAuth2Token.is_revoked == 0,
    ).first()
    if token_record:
        token_record.is_revoked = 1
        db.commit()
    return {"message": "Token revoked"}


@router.get("/.well-known/openid-configuration")
def openid_config():
    return build_openid_config()


@router.get("/jwks.json")
def jwks_json():
    return {"keys": get_jwks()}


def _authenticate_client(request: Request, data: OAuth2TokenRequest, db: Session) -> OAuth2Client | None:
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
        OAuth2Client.is_active == 1,
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
        OAuth2Token.is_revoked == 0,
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

    token_record.is_revoked = 1
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
        OAuth2Token.is_revoked == 0,
    ).first()
    if old_record:
        old_record.is_revoked = 1
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
        is_revoked=0,
    )
    db.add(record)
    db.commit()
    return record
