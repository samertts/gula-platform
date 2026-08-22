from pathlib import Path

from gula_citizen_portal import GulaCitizenPortal
from gula_registration_portal import GulaRegistrationPortal


def test_citizen_portal_uses_versioned_password_hash_and_authentication(tmp_path: Path):
    portal = GulaCitizenPortal(str(tmp_path / "citizens.db"))
    result = portal.register_citizen(
        "synthetic-national-id",
        "synthetic-insurance-id",
        "Synthetic Citizen",
        "0000000000",
        "synthetic-password-123",
    )
    assert result["status"] == "SUCCESS"

    with portal._connect() as conn:
        stored = conn.execute(
            "SELECT password_hash FROM citizens WHERE national_id = ?",
            ("synthetic-national-id",),
        ).fetchone()[0]
    assert stored.startswith("pbkdf2_sha256$")
    assert portal._verify_password("synthetic-password-123", stored)
    assert not portal._verify_password("wrong-password-123", stored)
    assert not portal._verify_password("synthetic-password-123", "legacy-fixed-sha256")

    rejected = portal.add_medical_record(
        "synthetic-national-id",
        "wrong-password-123",
        "Synthetic Hospital",
        "synthetic diagnosis",
        "synthetic prescription",
        "synthetic result",
    )
    assert rejected["status"] == "ERROR"

    accepted = portal.add_medical_record(
        "synthetic-national-id",
        "synthetic-password-123",
        "Synthetic Hospital",
        "synthetic diagnosis",
        "synthetic prescription",
        "synthetic result",
    )
    assert accepted["status"] == "SUCCESS"


def test_registration_portal_uses_randomized_hashing_and_rejects_weak_password(tmp_path: Path):
    portal = GulaRegistrationPortal(str(tmp_path / "users.db"))
    first = portal.register_user(
        "synthetic-user",
        "synthetic-password-123",
        "Synthetic User",
        "PHYSICIAN",
        "LAB",
    )
    assert first["status"] == "SUCCESS"

    with portal._connect() as conn:
        stored = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            ("synthetic-user",),
        ).fetchone()[0]
    assert stored.startswith("pbkdf2_sha256$")
    assert portal.verify_password("synthetic-password-123", stored)
    assert not portal.verify_password("wrong-password-123", stored)
    assert not portal.verify_password("synthetic-password-123", "legacy-fixed-sha256")

    weak = portal.register_user(
        "weak-user",
        "short",
        "Synthetic User",
        "NURSE",
        "LAB",
    )
    assert weak["status"] == "ERROR"
