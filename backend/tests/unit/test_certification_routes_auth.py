"""PROGRAM-GAMMA: regression tests for securing the /certification/* routes.

Covers the HIGH finding (unauthorised arbitrary-path evaluation):
  - all routes now require system:admin
  - module_path is confined to the platform root (no traversal, no absolute
    reads outside the repository)
"""

from __future__ import annotations

import os

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pathlib

import pytest
from app.certification.routes import PROJECT_ROOT, _safe_target
from app.database import Base, get_db
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import create_token, hash_password
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_engine():
    import app.models.audit_log
    import app.models.lab
    import app.models.lab_user
    import app.models.patient
    import app.models.user

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    Session = sessionmaker(bind=db_engine, autoflush=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(db):
    from app.main import app

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _auth_headers(db, role: str) -> dict:
    lab = Lab(name="Cert Lab", is_active=True)
    db.add(lab)
    db.flush()
    user = LabUser(
        lab_id=lab.id,
        name="Cert User",
        email=f"cert-{role}@test.com",
        password_hash=hash_password("Testpass1"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": role})
    return {"Authorization": f"Bearer {token}"}


class TestCertificationRoutesAuth:
    def test_unauthenticated_rejected(self, client):
        resp = client.get("/certification/dimensions")
        assert resp.status_code in (401, 403)

    def test_non_admin_rejected(self, client, db):
        resp = client.get(
            "/certification/dimensions", headers=_auth_headers(db, "technician")
        )
        assert resp.status_code == 403

    def test_master_admin_allowed(self, client, db):
        resp = client.get(
            "/certification/dimensions", headers=_auth_headers(db, "master_admin")
        )
        assert resp.status_code == 200

    def test_path_traversal_rejected(self, client, db):
        resp = client.get(
            "/certification/level/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
            headers=_auth_headers(db, "master_admin"),
        )
        assert resp.status_code == 403

    def test_absolute_outside_root_rejected(self, client, db):
        resp = client.get(
            "/certification/level//etc/passwd",
            headers=_auth_headers(db, "master_admin"),
        )
        assert resp.status_code == 403


class TestSafeTarget:
    def test_none_targets_project_root(self):
        assert _safe_target(None) == PROJECT_ROOT

    def test_relative_in_root_resolves(self):
        target = _safe_target("shared")
        assert PROJECT_ROOT in target.parents

    def test_absolute_in_root_resolves(self):
        target = _safe_target(str(PROJECT_ROOT / "shared"))
        assert target == (PROJECT_ROOT / "shared").resolve()

    def test_outside_root_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _safe_target(str(pathlib.Path("/tmp")))
        assert exc.value.status_code == 403

    def test_traversal_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _safe_target("../../../../etc/passwd")
        assert exc.value.status_code == 403
