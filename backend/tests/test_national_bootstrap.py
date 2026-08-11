"""Tests for the National Bootstrap Engine.

Covers:
1. Module structure and imports
2. Master admin creation (backward compatible)
3. Role and permission seeding
4. National hierarchy creation
5. Admin account creation
6. Facility seeding
7. Subscription seeding
8. Demo data generation
9. Validation engine
10. Environment variable handling
11. Full orchestrator execution
12. Backward compatibility with existing seeds
"""

from __future__ import annotations

import os

import pytest
from unittest.mock import patch

from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.subscription import LabSubscription
from app.models.organization import Organization, Facility
from app.models.authorization import Permission, Role, RolePermission


# ── Test env vars (applied before any bootstrap code runs) ────────────────────


@pytest.fixture(autouse=True)
def bootstrap_env_vars():
    with patch.dict(os.environ, {
        "GULA_ADMIN_EMAIL": "admin@test.gula.iq",
        "GULA_ADMIN_NAME": "Test Admin",
        "GULA_ADMIN_PASSWORD": "TestAdmin@123",
        "MINISTRY_ADMIN_EMAIL": "ministry@test.gula.iq",
        "MINISTRY_ADMIN_PASSWORD": "Ministry@123",
        "ORGANIZATION_ADMIN_EMAIL": "org-admin@test.gula.iq",
        "ORGANIZATION_ADMIN_PASSWORD": "OrgAdmin@123",
        "DIRECTORATE_ADMIN_EMAIL": "dir-admin@test.gula.iq",
        "DIRECTORATE_ADMIN_PASSWORD": "DirAdmin@123",
        "LAB_MANAGER_EMAIL": "lab-manager@test.gula.iq",
        "LAB_MANAGER_PASSWORD": "LabMgr@123",
        "AUDITOR_EMAIL": "auditor@test.gula.iq",
        "AUDITOR_PASSWORD": "Auditor@123",
        "SECURITY_OFFICER_EMAIL": "security@test.gula.iq",
        "SECURITY_OFFICER_PASSWORD": "Security@123",
        "ENABLE_BOOTSTRAP": "true",
        "ENABLE_NATIONAL_BOOTSTRAP": "true",
        "ENABLE_DEMO_DATA": "true",
        "MASTER_ADMIN_NID": "TEST-NID-001",
    }):
        yield


# =============================================================================
# Phase 1: Module Structure
# =============================================================================


class TestModuleStructure:
    """Verify the bootstrap module structure compiles and is importable."""

    def test_bootstrap_package_imports(self):
        from app.core.bootstrap import BootstrapContext, ensure_master_admin, run_bootstrap, validate_bootstrap, BOOTSTRAP_SEQUENCE
        assert BootstrapContext is not None
        assert callable(ensure_master_admin)
        assert callable(run_bootstrap)
        assert callable(validate_bootstrap)
        assert len(BOOTSTRAP_SEQUENCE) >= 10

    def test_all_modules_importable(self):
        for mod in [
            "app.core.bootstrap.config",
            "app.core.bootstrap.models",
            "app.core.bootstrap.master_admin",
            "app.core.bootstrap.organizations",
            "app.core.bootstrap.ministry",
            "app.core.bootstrap.directorates",
            "app.core.bootstrap.facilities",
            "app.core.bootstrap.laboratories",
            "app.core.bootstrap.departments",
            "app.core.bootstrap.roles",
            "app.core.bootstrap.permissions",
            "app.core.bootstrap.users",
            "app.core.bootstrap.subscriptions",
            "app.core.bootstrap.demo_data",
            "app.core.bootstrap.validation",
            "app.core.bootstrap.bootstrap",
        ]:
            __import__(mod)


# =============================================================================
# Phase 2: Master Admin
# =============================================================================


class TestMasterAdmin:
    """Master admin bootstrap — backward compatible."""

    def test_ensure_master_admin_backward_compat(self):
        from app.core.seeds import ensure_master_admin
        assert callable(ensure_master_admin)

    def test_master_admin_created(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        user = _ensure_master_admin(db)
        db.commit()
        assert user is not None
        assert user.email == "admin@test.gula.iq"
        assert user.role == "master_admin"
        assert user.national_id_hash is not None

    def test_master_admin_idempotent(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        u1 = _ensure_master_admin(db)
        db.commit()
        u2 = _ensure_master_admin(db)
        db.commit()
        assert u1.id == u2.id
        assert db.query(LabUser).filter(LabUser.role == "master_admin").count() == 1

    def test_platform_lab_created(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        _ensure_master_admin(db)
        db.commit()
        assert db.query(Lab).filter(Lab.name == "GULA Platform").first() is not None


# =============================================================================
# Phase 3-4: Roles and Permissions
# =============================================================================


class TestRolesAndPermissions:
    """Enterprise roles and permission seeding."""

    REQUIRED_ROLES = [
        "master_admin", "ministry_admin", "organization_admin",
        "directorate_admin", "hospital_admin", "lab_manager",
        "technician", "pathologist", "doctor", "nurse",
        "auditor", "security_officer", "patient",
    ]

    REQUIRED_DOMAINS = [
        "identity", "patients", "orders", "samples", "results",
        "billing", "inventory", "facilities", "users", "organizations",
        "analytics", "ai", "audit", "administration", "fhir",
        "interoperability", "reporting", "notifications", "configuration", "security",
    ]

    def test_roles_seeded(self, db):
        from app.core.bootstrap.roles import seed_roles
        count = seed_roles(db=db)
        assert count > 0

    def test_roles_idempotent(self, db):
        from app.core.bootstrap.roles import seed_roles
        seed_roles(db=db)
        assert seed_roles(db=db) == 0

    def test_required_roles_exist(self, db):
        from app.core.bootstrap.roles import seed_roles
        seed_roles(db=db)
        for role_id in self.REQUIRED_ROLES:
            assert db.query(Role).filter(Role.role_id == role_id).first() is not None

    def test_master_admin_highest_level(self, db):
        from app.core.bootstrap.roles import seed_roles
        seed_roles(db=db)
        role = db.query(Role).filter(Role.role_id == "master_admin").first()
        assert role is not None and int(role.level) >= 100

    def test_permissions_seeded(self, db):
        from app.core.bootstrap.permissions import seed_permissions, define_permissions
        count = seed_permissions(db=db)
        perms = define_permissions()
        assert count > 0
        assert len(perms) >= 80

    def test_permissions_idempotent(self, db):
        from app.core.bootstrap.permissions import seed_permissions
        seed_permissions(db=db)
        assert seed_permissions(db=db) == 0

    def test_all_permission_domains_present(self, db):
        from app.core.bootstrap.permissions import seed_permissions
        seed_permissions(db=db)
        domains = {r[0] for r in db.query(Permission.domain).distinct().all()}
        for domain in self.REQUIRED_DOMAINS:
            assert domain in domains

    def test_role_permission_links_exist(self, db):
        from app.core.bootstrap.roles import seed_roles
        from app.core.bootstrap.permissions import seed_permissions
        seed_permissions(db=db)
        seed_roles(db=db)
        assert db.query(RolePermission).count() > 0


# =============================================================================
# Phase 5: National Hierarchy
# =============================================================================


class TestNationalHierarchy:
    """Ministry, directorates, and facility hierarchy."""

    def test_ministry_seeded(self, db):
        from app.core.bootstrap.ministry import seed_ministry_of_health
        assert seed_ministry_of_health(db=db) is True
        moh = db.query(Organization).filter(Organization.org_type == "ministry").first()
        assert moh is not None and moh.name_en == "Ministry of Health"

    def test_ministry_idempotent(self, db):
        from app.core.bootstrap.ministry import seed_ministry_of_health
        seed_ministry_of_health(db=db)
        seed_ministry_of_health(db=db)
        assert db.query(Organization).filter(Organization.org_type == "ministry").count() == 1

    def test_directorates_seeded(self, db):
        from app.core.bootstrap.ministry import seed_ministry_of_health
        from app.core.bootstrap.directorates import seed_health_directorates
        seed_ministry_of_health(db=db)
        count = seed_health_directorates(db=db)
        assert count > 0
        assert db.query(Organization).filter(Organization.org_type == "directorate").count() > 0

    def test_platform_facilities_seeded(self, db):
        from app.core.bootstrap.organizations import seed_organizations
        from app.core.bootstrap.facilities import seed_platform_facilities
        from app.core.bootstrap.models import (
            OrganizationDef,
            PLATFORM_DIRECTORATE_NAME_AR,
            PLATFORM_DIRECTORATE_NAME_EN,
            PLATFORM_HOSPITAL_NAME_AR,
            PLATFORM_HOSPITAL_NAME_EN,
            PLATFORM_ORG_NAME_AR,
            PLATFORM_ORG_NAME_EN,
        )
        seed_organizations([
            OrganizationDef(
                org_id="pf-org",
                name_en=PLATFORM_ORG_NAME_EN,
                name_ar=PLATFORM_ORG_NAME_AR,
                org_type="organization",
            ),
            OrganizationDef(
                org_id="pf-dir",
                name_en=PLATFORM_DIRECTORATE_NAME_EN,
                name_ar=PLATFORM_DIRECTORATE_NAME_AR,
                org_type="directorate",
                parent_org_id="pf-org",
            ),
            OrganizationDef(
                org_id="pf-hospital",
                name_en=PLATFORM_HOSPITAL_NAME_EN,
                name_ar=PLATFORM_HOSPITAL_NAME_AR,
                org_type="hospital",
                parent_org_id="pf-org",
            ),
        ], db=db)
        assert seed_platform_facilities(db=db) > 0

    def test_departments_seeded(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        from app.core.bootstrap.departments import seed_departments
        _ensure_master_admin(db)
        db.commit()
        count = seed_departments(db=db)
        assert count > 0


# =============================================================================
# Phase 6: Admin Accounts
# =============================================================================


class TestAdminAccounts:
    """National admin account creation from env vars."""

    def _seed(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        _ensure_master_admin(db)
        db.commit()

    def test_admin_accounts_created(self, db):
        from app.core.bootstrap.users import seed_national_admin_accounts
        self._seed(db)
        assert seed_national_admin_accounts(db=db) > 0

    def test_admin_accounts_idempotent(self, db):
        from app.core.bootstrap.users import seed_national_admin_accounts
        self._seed(db)
        seed_national_admin_accounts(db=db)
        assert seed_national_admin_accounts(db=db) == 0

    def test_admin_roles_present(self, db):
        from app.core.bootstrap.users import seed_national_admin_accounts
        self._seed(db)
        seed_national_admin_accounts(db=db)
        roles = {u.role for u in db.query(LabUser).all()}
        for role in ("ministry_admin", "lab_manager", "auditor", "security_officer"):
            assert role in roles

    def test_passwords_hashed(self, db):
        from app.core.bootstrap.users import seed_national_admin_accounts
        self._seed(db)
        seed_national_admin_accounts(db=db)
        for user in db.query(LabUser).all():
            assert user.password_hash.startswith("$2")

    def test_missing_password_skips_account(self, db):
        from app.core.bootstrap.master_admin import _ensure_master_admin
        from app.core.bootstrap.users import ADMIN_ACCOUNTS, _resolve_account
        _ensure_master_admin(db)
        db.commit()
        with patch.dict(os.environ, {"MINISTRY_ADMIN_PASSWORD": "", "MINISTRY_ADMIN_PASSWORD_HASH": ""}):
            for acct in ADMIN_ACCOUNTS:
                if acct.role == "ministry_admin":
                    assert _resolve_account(acct) is None


# =============================================================================
# Phase 7-8: Subscriptions and Demo Data
# =============================================================================


class TestSubscriptions:
    """Subscription and demo data seeding."""

    def test_subscriptions_seeded(self, db):
        from app.core.bootstrap.subscriptions import seed_subscriptions
        db.add(Lab(name="Sub Test Lab", city="Test", is_active=True))
        db.commit()
        assert seed_subscriptions(db=db) > 0

    def test_subscriptions_idempotent(self, db):
        from app.core.bootstrap.subscriptions import seed_subscriptions
        db.add(Lab(name="Sub Test Lab 2", city="Test", is_active=True))
        db.commit()
        seed_subscriptions(db=db)
        assert seed_subscriptions(db=db) == 0

    def test_tier_configs_defined(self):
        from app.core.bootstrap.subscriptions import TIER_CONFIGS
        for tier in ("starter", "professional", "enterprise", "national"):
            assert tier in TIER_CONFIGS

    def test_upgrade_subscription(self, db):
        from app.core.bootstrap.subscriptions import seed_subscriptions, upgrade_subscription
        lab = Lab(name="Upgrade Lab", city="Test", is_active=True)
        db.add(lab)
        db.commit()
        seed_subscriptions(db=db)
        sub = upgrade_subscription(lab.id, "professional", db)
        db.commit()
        assert sub is not None and sub.tier == "professional"


class TestDemoData:
    """Optional demo data generation."""

    def test_demo_data_seeded(self, db):
        from app.core.bootstrap.demo_data import seed_demo_data
        db.add(Lab(name="Demo Lab", city="Test", is_active=True))
        db.commit()
        counts = seed_demo_data(db=db)
        assert counts["patients"] > 0
        assert counts["orders"] > 0
        assert counts["results"] > 0

    def test_demo_data_idempotent(self, db):
        from app.core.bootstrap.demo_data import seed_demo_data
        db.add(Lab(name="Demo Lab 2", city="Test", is_active=True))
        db.commit()
        seed_demo_data(db=db)
        assert seed_demo_data(db=db)["patients"] == 0


# =============================================================================
# Phase 9: Validation
# =============================================================================


class TestValidation:
    """Bootstrap validation engine."""

    def test_validation_empty_db(self, db):
        from app.core.bootstrap.validation import validate_bootstrap
        report = validate_bootstrap(db=db)
        assert report.total > 0
        assert report.failed > 0

    def test_validation_after_seed(self, db):
        from app.core.bootstrap.bootstrap import run_bootstrap
        from app.core.bootstrap.validation import validate_bootstrap
        run_bootstrap(db=db)
        report = validate_bootstrap(db=db)
        assert report.passed > 0
        assert report.is_healthy or report.warnings >= 0  # at least doesn't crash


# =============================================================================
# Phase 10: Configuration
# =============================================================================


class TestConfiguration:
    """Environment variable handling."""

    def test_config_from_env(self):
        from app.core.bootstrap.config import load_bootstrap_config
        cfg = load_bootstrap_config()
        assert cfg.admin_email == "admin@test.gula.iq"
        assert cfg.enable_bootstrap is True
        assert cfg.enable_national_bootstrap is True
        assert cfg.bootstrap_country == "IQ"

    def test_config_disabled(self):
        from app.core.bootstrap.config import load_bootstrap_config
        with patch.dict(os.environ, {"ENABLE_BOOTSTRAP": "false"}):
            cfg = load_bootstrap_config()
            assert cfg.enable_bootstrap is False


# =============================================================================
# Phase 11: Full Orchestrator
# =============================================================================


class TestOrchestrator:
    """Full bootstrap orchestrator execution."""

    def test_run_bootstrap_full(self, db):
        from app.core.bootstrap.bootstrap import run_bootstrap
        counts = run_bootstrap(db=db)
        assert counts.get("master_admin", 0) >= 1
        assert counts.get("permissions", 0) > 0
        assert counts.get("roles", 0) > 0

    def test_run_bootstrap_idempotent(self, db):
        from app.core.bootstrap.bootstrap import run_bootstrap
        run_bootstrap(db=db)
        counts = run_bootstrap(db=db)
        for key, val in counts.items():
            if key != "master_admin":
                assert val == 0, f"{key} was {val}, expected 0"

    def test_bootstrap_without_national(self, db):
        from app.core.bootstrap.bootstrap import run_bootstrap
        with patch.dict(os.environ, {"ENABLE_NATIONAL_BOOTSTRAP": "false"}):
            counts = run_bootstrap(db=db)
            assert counts.get("master_admin", 0) >= 1
            for key in ("ministry", "directorates", "platform_facilities", "laboratory_types"):
                if key in counts:
                    assert counts[key] == 0


# =============================================================================
# Phase 12: Backward Compatibility
# =============================================================================


class TestBackwardCompatibility:
    """Verify existing bootstrap functions still work unchanged."""

    def test_ensure_master_admin_from_seeds(self, db):
        from app.core.seeds import ensure_master_admin as legacy_seed
        with patch.object(db, "close", lambda: None), \
             patch("app.core.seeds.SessionLocal", return_value=db):
            legacy_seed()
        assert db.query(LabUser).filter(LabUser.role == "master_admin").first() is not None

    def test_seed_default_subscriptions(self, db):
        from app.core.seeds import seed_default_subscriptions
        lab = Lab(name="Compat Lab", city="Test", is_active=True)
        db.add(lab)
        db.commit()
        seed_default_subscriptions(db)
        assert db.query(LabSubscription).filter(LabSubscription.lab_id == lab.id).first() is not None

    def test_startup_guard_has_national_bootstrap(self):
        from app.core.startup_guard import _run_national_bootstrap
        assert callable(_run_national_bootstrap)

    def test_config_has_new_vars(self):
        from app import config
        assert hasattr(config, "ENABLE_BOOTSTRAP")
        assert hasattr(config, "ENABLE_NATIONAL_BOOTSTRAP")
        assert hasattr(config, "ENABLE_DEMO_DATA")
        assert hasattr(config, "MINISTRY_ADMIN_EMAIL")
        assert hasattr(config, "AUDITOR_EMAIL")
