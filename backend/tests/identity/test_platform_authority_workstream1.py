"""Platform Authority coverage extension (Workstream 1): the five
previously-unprotected lifecycle operations --
federation.register_provider, trust.activate_framework,
certificates.issue_certificate, certificates.revoke_certificate,
governance.create_authority. Each was reachable by any authenticated NIAM
account (router-level `_AUTH_REQUIRED` already required a valid actor) but
had no platform-capability check, no audit trail, and never committed.

Same established pattern as test_platform_authority_phase10.py: hand-built
fake session objects, real route/service functions called directly (no
real async engine anywhere in this codebase).

`trust.supersede_framework` has a service method but no route -- it is
unreachable via HTTP and therefore has nothing to authorize; documented,
not fabricated a route for.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.certificates import routes as certificates_routes
from app.identity.federation import routes as federation_routes
from app.identity.governance import routes as governance_routes
from app.identity.governance.models import IdentityAuthority
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformCapability,
)
from app.identity.trust import routes as trust_routes
from app.identity.trust.models import TrustFramework
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
    table (same technique as test_platform_authority_phase10.py's
    _FakeDb), returns a configured entity for any other table (or None),
    tracks add/flush/commit for assertions."""

    def __init__(self, *, active_assignment=None, entity=None):
        self.active_assignment = active_assignment
        self.entity = entity
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
        if table in ("niam_trust_frameworks", "niam_fed_providers", "niam_cert_certificates"):
            return _Result(self.entity)
        return _Result(None)  # e.g. the audit hash-chain lookup -- harmless


def _actor(identity_id="IDENTITY0000000000000001", account_id="ACCOUNT0000000000000001"):
    return SimpleNamespace(account=SimpleNamespace(id=account_id, identity_id=identity_id))


def _assignment(identity_id="IDENTITY0000000000000001", capability=None):
    return PlatformAuthorityAssignment(
        id="PA0000000000000000000001",
        uuid="pa-uuid-1",
        identity_id=identity_id,
        capability=capability,
        status="active",
    )


def _framework():
    return TrustFramework(
        id="TF0000000000000000000001",
        framework_id="fw-1",
        name_en="Old Name",
        name_ar="اسم قديم",
        version="1.0",
        status="draft",
        is_active=True,
    )


# ── register_provider ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_provider_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await federation_routes.register_provider(
            provider_id="new-prov", name_en="New", issuer_url="https://x.example",
            db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert db.added == []
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_register_provider_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.federation_manage.value))
    result = await federation_routes.register_provider(
        provider_id="new-prov", name_en="New", issuer_url="https://x.example",
        db=db, actor=_actor(),
    )
    assert result["provider_id"] == "new-prov"
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)
    assert any(type(o).__name__ == "FederatedProvider" for o in db.added)
    assert db.commit_count == 1


# ── activate_framework ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_activate_framework_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None, entity=_framework())
    with pytest.raises(HTTPException) as exc:
        await trust_routes.activate_framework(framework_id="fw-1", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_activate_framework_succeeds_and_commits_with_audit():
    framework = _framework()
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.trust_manage.value), entity=framework)
    result = await trust_routes.activate_framework(framework_id="fw-1", db=db, actor=_actor())
    assert result["status"] == "active"
    assert framework.status == "active"
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_activate_framework_not_found_never_commits():
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.trust_manage.value), entity=None)
    result = await trust_routes.activate_framework(framework_id="does-not-exist", db=db, actor=_actor())
    assert result == {"error": "not_found"}
    assert db.commit_count == 0


# ── issue_certificate / revoke_certificate ──────────────────────────────────


@pytest.mark.asyncio
async def test_issue_certificate_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.issue_certificate(
            cert_type="tls", subject="cn=test", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert db.added == []
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_issue_certificate_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.certificates_manage.value))
    cert = await certificates_routes.issue_certificate(
        cert_type="tls", subject="cn=test", db=db, actor=_actor(),
    )
    assert cert["status"] == "active"
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)
    assert any(type(o).__name__ == "DigitalCertificate" for o in db.added)
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_issue_certificate_never_stores_the_raw_private_key():
    """Real, previously-undiscovered P0: private_key_encrypted was the
    literal PKCS8 PEM private key with NoEncryption(), stored verbatim --
    not encrypted despite the column name. Fixed to call the existing
    canonical app.security.encryption.encrypt(). This proves the stored
    value is no longer a raw PEM block."""
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.certificates_manage.value))
    await certificates_routes.issue_certificate(
        cert_type="tls", subject="cn=test", db=db, actor=_actor(),
    )
    stored_cert = next(o for o in db.added if type(o).__name__ == "DigitalCertificate")
    assert not stored_cert.private_key_encrypted.startswith("-----BEGIN")


@pytest.mark.asyncio
async def test_revoke_certificate_denies_actor_without_capability():
    from app.identity.certificates.models import DigitalCertificate

    cert = DigitalCertificate(
        id="CERT0000000000000000000001", uuid="cert-uuid-1", certificate_id="cert-1",
        serial_number="SN1", subject="cn=x", issuer="cn=x", certificate_type="tls",
        public_key="pub", private_key_encrypted="priv", certificate_pem="pem",
        signature_algorithm="SHA256withRSA", key_size=2048, thumbprint="thumb",
        status="active", is_active=True,
    )
    db = _FakeDb(active_assignment=None, entity=cert)
    with pytest.raises(HTTPException) as exc:
        await certificates_routes.revoke_certificate(
            certificate_id="cert-1", reason="compromised", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert db.commit_count == 0


# ── create_authority ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_authority_denies_actor_without_capability():
    db = _FakeDb(active_assignment=None)
    with pytest.raises(HTTPException) as exc:
        await governance_routes.create_authority(
            authority_id="auth-1", name_en="New Authority", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert db.added == []
    assert db.commit_count == 0


@pytest.mark.asyncio
async def test_create_authority_succeeds_and_commits_with_audit():
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.governance_manage.value))
    result = await governance_routes.create_authority(
        authority_id="auth-1", name_en="New Authority", db=db, actor=_actor(),
    )
    assert result["authority_id"] == "auth-1"
    assert any(type(o).__name__ == "IdentityAuditEntry" for o in db.added)
    assert any(type(o).__name__ == "IdentityAuthority" for o in db.added)
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_wrong_capability_still_denies_create_authority():
    """Holding a DIFFERENT platform capability must not authorize this one --
    proves capabilities aren't fungible."""
    db = _FakeDb(active_assignment=_assignment(capability=PlatformCapability.trust_manage.value))
    with pytest.raises(HTTPException) as exc:
        await governance_routes.create_authority(
            authority_id="auth-1", name_en="New Authority", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert db.commit_count == 0
