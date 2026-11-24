"""NHID canonicalization readiness — synthetic compatibility tests.

These tests do **not** implement a canonical NHID, change any existing
identifier, or migrate data. They (a) pin the single canonical NID-normalization
contract that any future NHID issuance must rely on, (b) characterize the legacy
`HID-` generator/validator, and (c) document namespace divergences that require
an owner decision before a canonical NHID model can be adopted.

Synthetic fixtures only. No real patient data. Source inventory evidence is in
`GOVERNANCE/IDENTITY_REMEDIATION/NHID_CANONICALIZATION_READINESS.md`.
"""

from __future__ import annotations

import pytest
from app.services.identity import hash_national_id, nid_hash_candidates, normalize_national_id
from app.services.identity_matching import (
    _hid_checksum,
    generate_health_id,
    verify_health_id,
)

# Synthetic, non-real national-id-like digit strings (never patient data).
_SYN_WESTERN = "123456789"
_SYN_ARABIC_INDIC = "١٢٣٤٥٦٧٨٩"
_SYN_EXTENDED = "۱۲۳۴۵۶۷۸۹"


# ── Canonical NID normalization (the ONLY sanctioned NHID input contract) ────


@pytest.mark.parametrize("form", [_SYN_WESTERN, _SYN_ARABIC_INDIC, _SYN_EXTENDED])
def test_equivalent_digit_representations_normalize_and_hash_identically(form):
    assert normalize_national_id(form) == "123456789"
    assert hash_national_id(form) == hash_national_id(_SYN_WESTERN)


@pytest.mark.parametrize("form", ["  123456789  ", "1-2 3/4 5.6 7 8 9", "1(234)56789"])
def test_leading_trailing_whitespace_and_punctuation_ignored(form):
    assert normalize_national_id(form) == "123456789"
    assert hash_national_id(form) == hash_national_id(_SYN_WESTERN)


@pytest.mark.parametrize("empty", ["", "   ", "----", None])
def test_empty_or_non_digit_input_yields_empty(empty):
    assert normalize_national_id(empty) == ""
    assert hash_national_id(empty) == ""


def test_nid_hash_candidates_include_canonical_first_and_legacy_forms():
    candidates = nid_hash_candidates(_SYN_ARABIC_INDIC)
    assert candidates
    assert candidates[0] == hash_national_id(_SYN_ARABIC_INDIC)
    assert hash_national_id(_SYN_WESTERN) in candidates  # legacy-equivalent discoverable
    assert len(candidates) == len(set(candidates))  # distinct, no duplicate candidates


def test_duplicate_detection_across_representations():
    """A canonical hash written for one representation is found from another."""
    stored = hash_national_id(_SYN_WESTERN)  # canonical write
    lookup_input = nid_hash_candidates(_SYN_ARABIC_INDIC)  # equivalent representation
    assert stored in lookup_input  # -> duplicate detected, no second identity


# ── Legacy HID generator/validator characterization (NO change made) ─────────


def test_generate_verify_hid_roundtrip():
    hid = generate_health_id("790000000001")
    assert hid.startswith("HID-")
    assert verify_health_id(hid) is True


def test_verify_hid_rejects_tampered_checksum():
    hid = generate_health_id("790000000002")
    body = hid[4:-3]
    real_checksum = _hid_checksum(body)
    alt_first = "A" if real_checksum[0] != "A" else "B"
    bad = f"HID-{body}-{alt_first}{real_checksum[1]}"
    assert bad != hid
    assert verify_health_id(bad) is False


@pytest.mark.parametrize("bad", ["", "HID-", "HID-123-K7", "XYZ-A1B2C3D4-K7", "A1B2C3D4-K7", None])
def test_verify_hid_rejects_malformed_and_empty(bad):
    assert verify_health_id(bad) is False


def test_hid_collision_resistance_synthetic():
    ids = {generate_health_id(f"79{i:011d}") for i in range(500)}
    assert len(ids) == 500  # 8-hex body space is ample for this synthetic cohort


def test_legacy_shared_generator_shape_not_accepted_by_structural_validator():
    """Documents namespace incompatibility — NOT a desired end state.

    `shared/identity/service.py::generate_health_id` emits `HID-<8hex>-<8hex>`,
    which the `identity_matching.py` structural validator (expecting a 2-char
    base32 checksum) rejects. A single canonical model requires an owner
    decision; this test records current behaviour, it does not bless it.
    """
    legacy_shared_shape = "HID-A1B2C3D4-DEADBEEF"
    assert verify_health_id(legacy_shared_shape) is False


def test_KNOWN_RISK_hid_generator_does_not_canonicalize_arabic_digits():
    """Characterization of a DEFECT/risk, not desired behaviour.

    `identity_matching._clean_national_id` strips non-digits with ``\\D`` but
    does not map Unicode decimal digits, unlike the canonical helper. Equivalent
    Arabic-Indic/Western representations therefore derive DIFFERENT legacy HIDs.
    Fixing this (or retiring the NID-derived HID) is `NEEDS_OWNER_DECISION`;
    this test deliberately pins the current behaviour and must be revisited when
    the canonical NHID model is approved.
    """
    assert generate_health_id(_SYN_ARABIC_INDIC) != generate_health_id(_SYN_WESTERN)
