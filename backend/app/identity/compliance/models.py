from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class ComplianceFramework(IdentityBaseEntity):
    __tablename__ = "niam_comp_frameworks"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    framework_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    framework_type = Column(String(50), nullable=False, index=True)
    version = Column(String(20), nullable=True)
    requirements = Column(JSON, nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class ComplianceCheck(IdentityBaseEntity):
    __tablename__ = "niam_comp_checks"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    check_id = Column(String(100), unique=True, nullable=False, index=True)
    framework_id = Column(String(26), ForeignKey("niam_comp_frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    requirement_id = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=False)
    check_type = Column(String(20), nullable=False)
    status = Column(String(20), default="not_checked", nullable=False)
    checked_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)
    evidence = Column(JSON, nullable=True)
    finding = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class ComplianceReport(IdentityBaseEntity):
    __tablename__ = "niam_comp_reports"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    report_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    framework_id = Column(String(26), ForeignKey("niam_comp_frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    overall_score = Column(Integer, nullable=True)
    passed_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)
    not_applicable_count = Column(Integer, default=0, nullable=False)
    findings = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    generated_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
