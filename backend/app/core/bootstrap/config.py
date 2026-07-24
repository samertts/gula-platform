from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class BootstrapConfig:
    enable_bootstrap: bool
    enable_national_bootstrap: bool
    enable_demo_data: bool
    admin_email: str
    admin_name: str
    admin_password: str
    admin_password_hash: str
    ministry_admin_email: str
    ministry_admin_password: str
    organization_admin_email: str
    directorate_admin_email: str
    lab_manager_email: str
    auditor_email: str
    security_officer_email: str
    bootstrap_country: str
    bootstrap_language: str
    bootstrap_timezone: str
    master_admin_nid: str
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> BootstrapConfig:
        return cls(
            enable_bootstrap=os.getenv("ENABLE_BOOTSTRAP", "true").lower() == "true",
            enable_national_bootstrap=os.getenv("ENABLE_NATIONAL_BOOTSTRAP", "true").lower() == "true",
            enable_demo_data=os.getenv("ENABLE_DEMO_DATA", "false").lower() == "true",
            admin_email=os.getenv("GULA_ADMIN_EMAIL", "admin@gula-platform.org"),
            admin_name=os.getenv("GULA_ADMIN_NAME", "GULA Platform Admin"),
            admin_password=os.getenv("GULA_ADMIN_PASSWORD", ""),
            admin_password_hash=os.getenv("GULA_ADMIN_PASSWORD_HASH", ""),
            ministry_admin_email=os.getenv("MINISTRY_ADMIN_EMAIL", "ministry@gula-platform.org"),
            ministry_admin_password=os.getenv("MINISTRY_ADMIN_PASSWORD", ""),
            organization_admin_email=os.getenv("ORGANIZATION_ADMIN_EMAIL", "org-admin@gula-platform.org"),
            directorate_admin_email=os.getenv("DIRECTORATE_ADMIN_EMAIL", "directorate-admin@gula-platform.org"),
            lab_manager_email=os.getenv("LAB_MANAGER_EMAIL", "lab-manager@gula-platform.org"),
            auditor_email=os.getenv("AUDITOR_EMAIL", "auditor@gula-platform.org"),
            security_officer_email=os.getenv("SECURITY_OFFICER_EMAIL", "security@gula-platform.org"),
            bootstrap_country=os.getenv("BOOTSTRAP_COUNTRY", "IQ"),
            bootstrap_language=os.getenv("BOOTSTRAP_LANGUAGE", "ar"),
            bootstrap_timezone=os.getenv("BOOTSTRAP_TIMEZONE", "Asia/Baghdad"),
            master_admin_nid=os.getenv("MASTER_ADMIN_NID", ""),
            extra={},
        )


def load_bootstrap_config() -> BootstrapConfig:
    return BootstrapConfig.from_env()
