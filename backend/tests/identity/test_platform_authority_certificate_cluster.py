"""Platform Authority coverage extension (certificate/CA/API-key cluster):
the six previously-unprotected operations -- rotate_certificate,
register_ca, generate_crl, generate_api_key, revoke_api_key, rotate_api_key.
Each was reachable by any authenticated NIAM account (router-level
`_AUTH_REQUIRED` already required a valid actor) but had no platform-
capability check, no audit trail, never committed, and (register_ca/
rotate_certificate/generate_crl/generate_api_key/revoke_api_key/
rotate_api_key) used the sync `Depends(get_db)` dependency with async
`await session.execute(...)` calls -- a real crash (see
docs/security/CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md).

Same established pattern as test_platform_authority_workstream1.py: a
hand-built fake session, real route/service functions called directly (no
real async engine in this test tier -- the real-Postgres proof lives in
docs/security/CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.certificates import routes as certificates_routes
from app.identity.certificates.models import APIKey, CertificateAuthority, DigitalCertificate
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformCapability,
)
from fastapi import HTTPException


class _Result:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._row

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDb:
    """Generic fake session: dispatches execute() by target table name,
    honors identity_id/capability filters for the platform-authority
    table, returns a configured entity for certificate/CA/CRL/API-key
    lookups, and treats FK-reference lookups (organization/person/
    enterprise-account existence) as satisfied unless explicitly listed
    in `missing_refs`. Tracks add/flush/commit for assertions."""

    def __init__(self, *, active_assignment=None, entity=None, missing_refs=None):
        self.active_assignment = active_assignment
        self.entity = entity
        self.missing_refs = missing_refs or set()
        self.added: list = []
        self.commit_count = 0
        self.flush_count = 0
        self._counter = 0

    def add(self, obj):
        self._counter += 1
        if getattr(obj, "id", None) is None:
            obj.id = f"GENERATED-{self._counter:04d}"
        self.added.append(obj)

    async def flush(self):
        self.flush_count += 1

    async def commit(self):
        self.commit_count += 1

    async def execute(self, stmt):
        table = stmt.get_final_froms()[0].name
        if table == "niam_platform_authority_assignments":
            if self.active_assignment is None:
                return _Result(None)
            params = {k.rsplit("_", 1)[0]: v for k, v in stmt.compile().params.items()}
            if params.get("identity_id") != self.active_assignment.identity_id:
                return _Result(None)
            if params.get("capability") != self.active_assignment.capability:
                return _Result(None)
            return _Result(self.active_assignment)
        if table in ("niam_organizations", "niam_persons", "niam_enterprise_accounts"):
            params = list(stmt.compile().params.values())
            value = params[0] if params else None
            if value in self.missing_refs:
                return _Result(None)
            return _Result(value)
        if table in ("niam_cert_certificates", "niam_cert_authorities", "niam_cert_crls", "niam_cert_api_keys"):
            return _Result(self.entity)
        return _Result(None)


def _actor(identity_id="IDENTITY0000000000000001", account_id="ACCOUNT0000000000000001"):
    return SimpleNamespace(account=SimpleNamespace(id=account_id, identity_id=identity_id))


def _assignment(identity_id="IDENTITY0000000000000001", capability=None):
    return PlatformAuthorityAssignment(
        id="PA0000000000000000000001", uuid="pa-uuid-1", identity_id=identity_id,
        capability=capability, status="active",
    )


def _grant():
    return _assignment(capability=PlatformCapability.certificates_manage.value)


def _cert():
    return DigitalCertificate(
        id="CERT0000000000000000000001", uuid="cert-uuid-1", certificate_id="cert-1",
        serial_number="SN1", subject="cn=x", issuer="cn=x", certificate_type="tls",
        public_key="pub", private_key_encrypted="priv", certificate_pem="pem",
        signature_algorithm="SHA256withRSA", key_size=2048, thumbprint="thumb",
        status="active", is_active=True, rotation_period_days=365,
    )


def _ca():
    return CertificateAuthority(
        id="CA00000000000000000000001", uuid="ca-uuid-1", ca_id="ca-1", name="x",
        ca_type="root", certificate="pub", private_key_encrypted="priv", public_key="pub",
        valid_from=None, valid_to=None, status="active", signing_algorithm="SHA256withRSA",
        is_active=True, revoked_certificate_count=0,
    )


def _api_key():
    return APIKey(
        id="AK00000000000000000000001", uuid="ak-uuid-1", api_key_id="ak-1",
        key_prefix="gula_abcd", key_hash="h" * 64, name="k", organization_id="ORG1",
        scopes=[], permissions=[], status="active", is_active=True,
    )


# ── rotate_certificate ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rotate_certificate_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None, entity=_cert())
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.rotate_certificate(certificate_id="cert-1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_rotate_certificate_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_grant(), entity=_cert())
    result = await certificates_routes.rotate_certificate(certificate_id="cert-1", db=db, actor=_actor())
    assert result["status"] == "active"
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "CERTIFICATE_ROTATED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_rotate_certificate_not_found_never_commits():
    db = _FakeDb(active_assignment=_grant(), entity=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.rotate_certificate(certificate_id="does-not-exist", db=db, actor=_actor())
    assert exc.value.status_code == 404
    assert db.commit_count == 0


# ── register_ca ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_ca_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.register_ca(name="x", ca_type="root", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.added == []
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_register_ca_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_grant())
    result = await certificates_routes.register_ca(name="x", ca_type="root", db=db, actor=_actor())
    assert result["name"] == "x"
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "CERTIFICATE_AUTHORITY_REGISTERED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_register_ca_never_stores_the_raw_private_key():
    db = _FakeDb(active_assignment=_grant())
    result = await certificates_routes.register_ca(name="x", ca_type="root", db=db, actor=_actor())
    stored_ca = next(o for o in db.added if type(o).__name__ == "CertificateAuthority")
    assert not stored_ca.private_key_encrypted.startswith("-----BEGIN")
    assert "-----BEGIN" not in str(result.get("private_key_encrypted", ""))


@pytest.mark.asyncio
async def test_wrong_capability_still_denies_register_ca():
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.trust_manage.value))
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.register_ca(name="x", ca_type="root", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


# ── generate_crl ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_crl_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None, entity=_ca())
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.generate_crl(ca_id="ca-1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_generate_crl_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_grant(), entity=_ca())
    result = await certificates_routes.generate_crl(ca_id="ca-1", db=db, actor=_actor())
    assert "crl_id" in result
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "CERTIFICATE_CRL_GENERATED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_generate_crl_not_found_never_commits():
    db = _FakeDb(active_assignment=_grant(), entity=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.generate_crl(ca_id="does-not-exist", db=db, actor=_actor())
    assert exc.value.status_code == 404
    assert db.commit_count == 0


# ── generate_api_key ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_api_key_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.generate_api_key(name="k", organization_id="ORG1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.added == []
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_generate_api_key_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_grant())
    result = await certificates_routes.generate_api_key(name="k", organization_id="ORG1", db=db, actor=_actor())
    assert "raw_key" in result
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "API_KEY_GENERATED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_generate_api_key_rejects_spoofed_created_by():
    """Mass-assignment probe: a client-supplied `created_by` that does not
    reference a real person must be rejected (422), never silently
    accepted and never a raw 500 DB-constraint crash."""
    db = _FakeDb(active_assignment=_grant(), missing_refs={"person-does-not-exist"})
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.generate_api_key(
            name="k", organization_id="ORG1", created_by="person-does-not-exist",
            db=db, actor=_actor(),
        )
    assert exc.value.status_code == 422
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_generate_api_key_rejects_nonexistent_organization():
    db = _FakeDb(active_assignment=_grant(), missing_refs={"org-does-not-exist"})
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.generate_api_key(
            name="k", organization_id="org-does-not-exist", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 422
    assert db.commit_count == 0


# ── revoke_api_key ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_api_key_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None, entity=_api_key())
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.revoke_api_key(api_key_id="ak-1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_revoke_api_key_succeeds_and_commits_with_audit():
    ak = _api_key()
    db = _FakeDb(active_assignment=_grant(), entity=ak)
    result = await certificates_routes.revoke_api_key(api_key_id="ak-1", db=db, actor=_actor())
    assert result["status"] == "revoked"
    assert ak.status == "revoked"
    assert ak.is_active is False
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "API_KEY_REVOKED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_revoke_api_key_not_found_never_commits():
    db = _FakeDb(active_assignment=_grant(), entity=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.revoke_api_key(api_key_id="does-not-exist", db=db, actor=_actor())
    assert exc.value.status_code == 404
    assert db.commit_count == 0


# ── rotate_api_key ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rotate_api_key_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None, entity=_api_key())
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.rotate_api_key(api_key_id="ak-1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_rotate_api_key_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_grant(), entity=_api_key())
    result = await certificates_routes.rotate_api_key(api_key_id="ak-1", db=db, actor=_actor())
    assert "raw_key" in result
    event_types = {getattr(o, "event_type", None) for o in db.added if type(o).__name__ == "IdentityAuditEntry"}
    assert "API_KEY_ROTATED" in event_types
    assert "API_KEY_GENERATED" in event_types
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_rotate_api_key_not_found_never_commits():
    db = _FakeDb(active_assignment=_grant(), entity=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.rotate_api_key(api_key_id="does-not-exist", db=db, actor=_actor())
    assert exc.value.status_code == 404
    assert db.commit_count == 0
