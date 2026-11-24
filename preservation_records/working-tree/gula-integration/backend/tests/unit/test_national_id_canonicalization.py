"""P0-A regression tests — canonical national-ID normalization and HMAC.

Synthetic identifiers only. No real patient data, no operational database.
These tests pin the defect where Arabic-Indic digits hashed differently from
Western digits and where registration raw-hashed the NID.
"""

# RUF001: Arabic-Indic digits are intentional synthetic test data here.
# ruff: noqa: RUF001

from __future__ import annotations

import hashlib
import hmac
from datetime import date

import pytest
from app.config import NID_HMAC_KEY
from app.governance.base import GovernanceBase
from app.governance.services.identity_persistence_service import (
    PersistedIdentityGovernanceService,
)
from app.services.identity import (
    hash_family_id,
    hash_national_id,
    nid_hash_candidates,
    normalize_national_id,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Pure canonicalization / hashing ──────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1234567890", "1234567890"),
        ("١٢٣٤٥٦٧٨٩٠", "1234567890"),  # Arabic-Indic
        ("۱۲۳۴۵۶۷۸۹۰", "1234567890"),  # Extended Arabic-Indic
        ("١2٣4٥6٧8٩0", "1234567890"),  # mixed scripts
        ("1234-567 890", "1234567890"),  # separators
        (" ١٢٣٤٥٦٧٨٩٠ ", "1234567890"),  # whitespace
        ("abc", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_national_id(raw, expected):
    assert normalize_national_id(raw) == expected


def test_hash_equal_across_arabic_indic_and_western_digits():
    canonical = hash_national_id("1234567890")
    assert canonical
    for raw in ("١٢٣٤٥٦٧٨٩٠", "۱۲۳۴۵۶۷۸۹۰", "1234-567 890", " ١٢٣٤٥٦٧٨٩٠ "):
        assert hash_national_id(raw) == canonical


def test_hash_empty_or_nonnumeric_returns_empty():
    assert hash_national_id("") == ""
    assert hash_national_id("abc") == ""


def test_family_hash_uses_same_canonicalization_but_distinct_prefix():
    assert hash_family_id("١٢٣") == hash_family_id("123")
    assert hash_family_id("123") != hash_national_id("123")


def test_candidate_hashes_canonical_is_first_and_includes_western_equivalent():
    candidates = nid_hash_candidates("١٢٣")
    assert candidates[0] == hash_national_id("١٢٣")
    assert hash_national_id("123") in candidates


def test_candidate_hashes_include_legacy_raw_form():
    key = NID_HMAC_KEY.encode()
    legacy_raw_hash = hmac.new(key, "١٢٣".encode(), hashlib.sha256).hexdigest()
    assert legacy_raw_hash in nid_hash_candidates("١٢٣")


def test_candidate_hashes_unique_and_empty_input():
    candidates = nid_hash_candidates("1-2 3")
    assert candidates
    assert len(candidates) == len(set(candidates))
    assert nid_hash_candidates("") == []


# ── Persistence: no raw NID at rest (P0-A3) ──────────────────────────────────


@pytest.fixture()
def gov_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    GovernanceBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)(expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        GovernanceBase.metadata.drop_all(engine)
        engine.dispose()


def test_register_citizen_never_persists_raw_nid(gov_db):
    svc = PersistedIdentityGovernanceService(gov_db, nid_hmac_key="test-hmac-key")
    raw_nid = "1234567890"
    record = svc.register_citizen(
        full_name="Synthetic Person",
        national_id=raw_nid,
        date_of_birth=date(1990, 5, 15),
    )
    docs = record.documents_json or {}
    nid_doc = docs["iraqi_national_id"]
    assert nid_doc["document_number"] != raw_nid
    assert "[REDACTED" in nid_doc["document_number"]
    assert nid_doc["document_number_ref"] == record.national_id_hash


def test_governance_duplicate_detected_across_digit_scripts(gov_db):
    svc = PersistedIdentityGovernanceService(gov_db, nid_hmac_key="test-hmac-key")
    svc.register_citizen(full_name="A", national_id="1234567890")
    # Arabic-Indic form is now the same canonical identity — must be rejected.
    with pytest.raises(ValueError, match="already registered"):
        svc.register_citizen(full_name="B", national_id="١٢٣٤٥٦٧٨٩٠")
