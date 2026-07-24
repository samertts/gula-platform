from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.authorization import Permission, Role, RolePermission
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.organization import Facility, Organization
from app.models.subscription import LabSubscription

from .models import ALL_BOOTSTRAP_ROLES

logger = logging.getLogger("gula.bootstrap.validation")


@dataclass
class ValidationReport:
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    checks: list[dict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.warnings

    @property
    def is_healthy(self) -> bool:
        return self.failed == 0

    def add_pass(self, name: str, detail: str = "") -> None:
        self.passed += 1
        self.checks.append({"name": name, "status": "PASS", "detail": detail})

    def add_fail(self, name: str, detail: str = "") -> None:
        self.failed += 1
        self.checks.append({"name": name, "status": "FAIL", "detail": detail})

    def add_warning(self, name: str, detail: str = "") -> None:
        self.warnings += 1
        self.checks.append({"name": name, "status": "WARN", "detail": detail})

    def summarize(self) -> str:
        return (
            f"Validation: {self.passed} passed, {self.failed} failed, "
            f"{self.warnings} warnings — health: {'OK' if self.is_healthy else 'ISSUES DETECTED'}"
        )


def validate_bootstrap(db: Session | None = None) -> ValidationReport:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    report = ValidationReport()

    try:
        _validate_organizations(db, report)
        _validate_facilities(db, report)
        _validate_labs(db, report)
        _validate_users(db, report)
        _validate_roles(db, report)
        _validate_permissions(db, report)
        _validate_subscriptions(db, report)
        _validate_relationships(db, report)
    finally:
        if own_session:
            db.close()

    logger.info(report.summarize())
    return report


def _validate_organizations(db: Session, report: ValidationReport) -> None:
    orgs = db.query(Organization).count()
    if orgs > 0:
        report.add_pass("organizations", f"{orgs} organizations found")
    else:
        report.add_fail("organizations", "No organizations found")

    moh = db.query(Organization).filter(Organization.org_type == "ministry").first()
    if moh:
        report.add_pass("ministry_of_health", f"Found: {moh.name_en}")
    else:
        report.add_warning("ministry_of_health", "Ministry of Health not found")

    dirs = db.query(Organization).filter(Organization.org_type == "directorate").count()
    if dirs > 0:
        report.add_pass("directorates", f"{dirs} directorates found")
    else:
        report.add_warning("directorates", "No health directorates found")


def _validate_facilities(db: Session, report: ValidationReport) -> None:
    facilities = db.query(Facility).count()
    if facilities > 0:
        report.add_pass("facilities", f"{facilities} facilities found")
    else:
        report.add_warning("facilities", "No facilities found")

    facility_types = (
        db.query(Facility.facility_type)
        .distinct()
        .all()
    )
    if facility_types:
        types_list = [ft[0] for ft in facility_types]
        report.add_pass("facility_types", f"Types: {', '.join(types_list)}")


def _validate_labs(db: Session, report: ValidationReport) -> None:
    labs = db.query(Lab).count()
    if labs > 0:
        report.add_pass("labs", f"{labs} labs found")
    else:
        report.add_fail("labs", "No labs found")

    active = db.query(Lab).filter(Lab.is_active).count()
    report.add_pass("active_labs", f"{active} active labs")


def _validate_users(db: Session, report: ValidationReport) -> None:
    users = db.query(LabUser).count()
    if users > 0:
        report.add_pass("users", f"{users} users found")
    else:
        report.add_fail("users", "No users found")

    master = db.query(LabUser).filter(LabUser.role == "master_admin").first()
    if master:
        report.add_pass("master_admin", f"Master admin: {master.email}")
    else:
        report.add_fail("master_admin", "No master admin found")

    for role in ["ministry_admin", "organization_admin", "directorate_admin",
                 "lab_manager", "auditor", "security_officer"]:
        count = db.query(LabUser).filter(LabUser.role == role).count()
        if count > 0:
            report.add_pass(f"role_{role}", f"{count} user(s) with role '{role}'")
        else:
            report.add_warning(f"role_{role}", f"No user with role '{role}'")


def _validate_roles(db: Session, report: ValidationReport) -> None:
    db_roles = db.query(Role).count()
    if db_roles > 0:
        report.add_pass("roles", f"{db_roles} roles found in database")
    else:
        report.add_fail("roles", "No roles found in database")

    for role_id in ALL_BOOTSTRAP_ROLES:
        exists = db.query(Role).filter(Role.role_id == role_id).first()
        if exists:
            report.add_pass(f"role_{role_id}", f"Role '{role_id}' exists")
        else:
            report.add_warning(f"role_{role_id}", f"Role '{role_id}' not found")


def _validate_permissions(db: Session, report: ValidationReport) -> None:
    perms = db.query(Permission).count()
    if perms > 0:
        report.add_pass("permissions", f"{perms} permissions found")
    else:
        report.add_fail("permissions", "No permissions found")

    domains = (
        db.query(Permission.domain)
        .distinct()
        .all()
    )
    if domains:
        domain_list = [d[0] for d in domains]
        report.add_pass("permission_domains", f"Domains: {', '.join(sorted(domain_list))}")

    rp = db.query(RolePermission).count()
    if rp > 0:
        report.add_pass("role_permissions", f"{rp} role-permission mappings")
    else:
        report.add_warning("role_permissions", "No role-permission mappings")


def _validate_subscriptions(db: Session, report: ValidationReport) -> None:
    subs = db.query(LabSubscription).count()
    labs = db.query(Lab).filter(Lab.is_active).count()
    if labs > 0 and subs >= labs:
        report.add_pass("subscriptions", f"{subs} subscriptions for {labs} active labs")
    elif subs > 0:
        report.add_warning(
            "subscriptions",
            f"{subs} subscriptions but {labs} active labs — some labs may be missing subscriptions",
        )
    else:
        report.add_warning("subscriptions", "No subscriptions found")


def _validate_relationships(db: Session, report: ValidationReport) -> None:
    orgs_with_parent = (
        db.query(Organization)
        .filter(Organization.parent_org_id.isnot(None))
        .count()
    )
    report.add_pass(
        "org_hierarchy",
        f"{orgs_with_parent} organizations have parent references",
    )

    facilities_with_org = (
        db.query(Facility)
        .filter(Facility.organization_id.isnot(None))
        .count()
    )
    report.add_pass(
        "facility_org_links",
        f"{facilities_with_org} facilities linked to organizations",
    )

    users_with_lab = (
        db.query(LabUser)
        .filter(LabUser.lab_id.isnot(None))
        .count()
    )
    report.add_pass(
        "user_lab_links",
        f"{users_with_lab} users linked to labs",
    )

    subs_with_lab = (
        db.query(LabSubscription)
        .filter(LabSubscription.lab_id.isnot(None))
        .count()
    )
    report.add_pass(
        "subscription_lab_links",
        f"{subs_with_lab} subscriptions linked to labs",
    )
