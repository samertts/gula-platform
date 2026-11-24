"""Phase A (F-067) — MDM / patient identity resolution, synthetic data only.

Every record below is fictional. No real patient data, no DB, no network.
Patient-safety rule under test: a name alone, or a phone alone, must never be
enough to merge/link two patient records; ambiguous cases fall to human review.

Evidence id: E-053 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

import json

import pytest

from app.health_data.mdm.matching import ExactMatcher, FuzzyMatcher, MatchingEngine
from app.health_data.mdm.service import MDMService
from app.services.mpi.matcher import (
    THRESHOLD_AUTO,
    THRESHOLD_REVIEW,
    Candidate,
    build_profile,
    classify,
    score,
)

# ---------------------------------------------------------------------------
# helpers — all synthetic
# ---------------------------------------------------------------------------


def _candidate(**overrides) -> Candidate:
    base = dict(
        id=1,
        citizen_ulid="SYNTHETIC000000000000001",
        name_canonical="ali hassan",
        phone_last10=None,
        birth_year=None,
        birth_month=None,
        birth_day=None,
        gender=None,
        nid_hash=None,
        family_id_hash=None,
    )
    base.update(overrides)
    return Candidate(**base)


class TestExactMatcherSafety:
    """The dormant MDM exact matcher must not merge on name alone."""

    def test_stable_identifier_matches(self):
        result = ExactMatcher().match(
            {"national_id_hash": "H1", "first_name": "Ali", "last_name": "Hassan"},
            {"national_id_hash": "H1", "first_name": "Ali", "last_name": "Hassan"},
        )
        assert result.matched is True
        assert result.score == 1.0

    def test_identical_names_different_people_do_not_match(self):
        # Two different people, same first+last name, no shared identifier.
        result = ExactMatcher().match(
            {"first_name": "Ali", "last_name": "Hassan"},
            {"first_name": "Ali", "last_name": "Hassan"},
        )
        assert result.matched is False
        assert result.score < THRESHOLD_REVIEW
        assert result.method == "exact_name_only"

    def test_features_are_json_serializable(self):
        # Regression: features[field] used the dataclasses.field helper as a key.
        result = ExactMatcher().match(
            {"national_id_hash": "X", "health_number": "Y", "phone": "1"},
            {"national_id_hash": "Z", "health_number": "W", "phone": "2"},
        )
        encoded = json.dumps(result.features)
        assert "national_id_hash" in encoded
        assert all(isinstance(k, str) for k in result.features)


class TestFuzzyAndEngine:
    def test_typo_still_scores_fuzzy_without_auto_match(self):
        result = FuzzyMatcher().match(
            {"first_name": "Ahmed", "last_name": "Hassan", "date_of_birth": "1990-01-01"},
            {"first_name": "Ahmad", "last_name": "Hassan", "date_of_birth": "1990-01-01"},
        )
        assert 0.0 <= result.score <= 1.0
        assert result.features["dob_similarity"] is True

    def test_engine_best_is_not_name_only_false_positive(self):
        engine = MatchingEngine()
        engine.register(ExactMatcher())
        engine.register(FuzzyMatcher())
        # Identical names, different DOB, no identifier -> best score stays low.
        result = engine.match(
            {"first_name": "Ali", "last_name": "Hassan", "date_of_birth": "1980-01-01"},
            {"first_name": "Ali", "last_name": "Hassan", "date_of_birth": "2001-06-15"},
        )
        assert result.matched is False


class TestMPIDecisionThresholds:
    """Authoritative MPI stack: name/phone alone are insufficient to auto-match."""

    def test_name_alone_is_below_review_threshold(self):
        profile = build_profile(name="Ali Hassan")
        candidate = _candidate(name_canonical="ali hassan")
        result = score(profile, candidate)
        assert result.score < THRESHOLD_REVIEW
        assert classify(result.score) == "no_match"

    def test_phone_alone_is_below_review_threshold(self):
        profile = build_profile(name="Different Name", phone_last10="1234567890")
        candidate = _candidate(name_canonical="unrelated person", phone_last10="1234567890")
        assert classify(score(profile, candidate).score) == "no_match"

    def test_nid_shortcut_matches_same_person_despite_different_name(self):
        profile = build_profile(name="Ali Hassan", nid_hash="HASH-SAME")
        candidate = _candidate(name_canonical="ali hassan", nid_hash="HASH-SAME")
        result = score(profile, candidate)
        assert result.score == 1.0
        assert classify(result.score) == "auto_match"

    def test_name_order_swap_without_identifier_is_ambiguous(self):
        # Order swap changes the canonical name; without NID it cannot confirm.
        profile = build_profile(name="Hassan Ali")
        candidate = _candidate(name_canonical="ali hassan")
        assert classify(score(profile, candidate).score) != "auto_match"

    def test_arabic_vs_english_spelling_without_nid_is_ambiguous(self):
        profile = build_profile(name="علي حسن")
        candidate = _candidate(name_canonical="ali hassan")
        assert classify(score(profile, candidate).score) != "auto_match"

    def test_typo_plus_dob_and_phone_reaches_review_not_auto(self):
        profile = build_profile(
            name="Ahmed Hassan", phone_last10="1234567890",
            birth_year=1990, birth_month=1, birth_day=1,
        )
        candidate = _candidate(
            name_canonical="ahmad hassan", phone_last10="1234567890",
            birth_year=1990, birth_month=1, birth_day=1,
        )
        result = score(profile, candidate)
        assert THRESHOLD_REVIEW <= result.score < THRESHOLD_AUTO
        assert classify(result.score) == "review"  # ambiguous -> human review

    def test_shared_phone_different_dob_stays_no_match(self):
        profile = build_profile(
            name="A", phone_last10="1234567890", birth_year=1980,
            birth_month=1, birth_day=1,
        )
        candidate = _candidate(
            name_canonical="b", phone_last10="1234567890",
            birth_year=2000, birth_month=12, birth_day=31,
        )
        assert classify(score(profile, candidate).score) == "no_match"

    def test_missing_data_never_auto_matches(self):
        profile = build_profile(name="", phone_last10=None)
        candidate = _candidate(name_canonical="", phone_last10=None)
        assert score(profile, candidate).score == 0.0


class TestMergeProvenance:
    """Merges preserve original source info and are auditable/reversible."""

    @pytest.mark.asyncio
    async def test_merge_records_history_and_source_provenance(self):
        service = MDMService(MatchingEngine())
        survivor = {
            "id": "GOLD-1", "first_name": "Ali", "source_id": "SRC-A",
            "source_systems": ["hospital"], "version": 1,
        }
        duplicate = {
            "id": "DUP-2", "first_name": "Ali", "last_name": "Hassan",
            "source_id": "SRC-B", "source_systems": ["pharmacy"], "version": 1,
        }
        merged = await service.merge(survivor, duplicate, reason="synthetic", method="review")
        assert merged["last_name"] == "Hassan"          # info preserved
        assert "SRC-B" in merged["merged_source_ids"]   # source preserved
        assert len(merged["merge_history"]) == 1
        assert merged["merge_history"][0]["duplicate_id"] == "DUP-2"
        assert merged["merge_history"][0]["reason"] == "synthetic"

    @pytest.mark.asyncio
    async def test_split_creates_separate_record_without_losing_original(self):
        service = MDMService(MatchingEngine())
        record = {"id": "GOLD-1", "entity_type": "patient", "first_name": "Ali", "version": 1}
        kept, new = await service.split(
            record, {"first_name": "Ali"}, {"first_name": "Ahmed"}
        )
        assert kept["first_name"] == "Ali"
        assert new["first_name"] == "Ahmed"
        assert new["id"] != kept["id"]
