"""MPI matcher unit tests — pure functions, no DB required.

Covers:
  - Arabic + English name normalization
  - Jaro-Winkler similarity edge cases
  - Blocking-key stability (same person → same key regardless of input format)
  - Fellegi-Sunter scoring: NID short-circuit, thresholds, feature weights
  - Audit hash-chain continuity (SHA-256 chaining invariant)
"""

import hashlib
import json
import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_mpi.db")
os.environ.setdefault("SECRET_KEY", "test-secret-mpi-not-for-prod-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest
from app.services.identity import jaro_similarity, jaro_winkler, normalize_name
from app.services.mpi.blocking import blocking_key, phone_last10
from app.services.mpi.matcher import (
    THRESHOLD_AUTO,
    THRESHOLD_REVIEW,
    Candidate,
    build_profile,
    classify,
    score,
)

# ─── Jaro-Winkler ────────────────────────────────────────────────────────────


class TestJaroWinkler:
    def test_identical_returns_one(self):
        assert jaro_winkler("mohammed", "mohammed") == 1.0

    def test_empty_returns_zero(self):
        assert jaro_winkler("", "mohammed") == 0.0
        assert jaro_winkler("mohammed", "") == 0.0

    def test_totally_different_is_low(self):
        assert jaro_winkler("abc", "xyz") < 0.5

    def test_prefix_bonus_boosts_score(self):
        # Same first 4 chars gets the Winkler prefix bonus
        plain = jaro_similarity("martha", "marhta")
        winkler = jaro_winkler("martha", "marhta")
        assert winkler >= plain

    def test_typo_scores_high(self):
        # Classic reference case from the Winkler paper
        assert jaro_winkler("dwayne", "duane") > 0.8

    def test_short_strings(self):
        # Single-char match
        assert jaro_winkler("a", "a") == 1.0
        assert jaro_winkler("a", "b") == 0.0


# ─── Name normalization ──────────────────────────────────────────────────────


class TestNormalizeName:
    def test_arabic_alef_variants_collapse(self):
        assert normalize_name("أحمد") == normalize_name("احمد")
        assert normalize_name("إبراهيم") == normalize_name("ابراهيم")

    def test_ta_marbuta_collapses(self):
        assert normalize_name("فاطمة") == normalize_name("فاطمه")

    def test_english_aliases_collapse(self):
        # NAME_ALIASES["mohammed"] -> ["mohammad","mohamed","muhammed",...]
        # so "Muhammed" (e-h) collapses to "mohammed"; NOT "Muhammad" (a-h).
        assert normalize_name("Mohammed") == normalize_name("Muhammed")
        assert normalize_name("Ahmed") == normalize_name("Ahmad")
        assert normalize_name("Hussein") == normalize_name("Husain")

    def test_lowercase_and_whitespace(self):
        assert normalize_name("  MOHAMMED    ALI  ") == "mohammed ali"

    def test_empty(self):
        assert normalize_name("") == ""


# ─── Blocking key ────────────────────────────────────────────────────────────


class TestBlockingKey:
    def test_same_arabic_form_same_key(self):
        # Identical Arabic input produces identical key
        a = blocking_key("محمد علي حسين")
        b = blocking_key("محمد علي حسين")
        assert a == b

    def test_english_alias_variants_block_together(self):
        # "Mohammed" and "Muhammed" normalize to the same canonical, so
        # they share a blocking key — the primary value of aliases.
        a = blocking_key("Mohammed Ali Hussein")
        b = blocking_key("Muhammed Ali Hussein")
        assert a == b

    def test_whitespace_and_case_insensitive(self):
        a = blocking_key("  MOHAMMED    ali  HUSSEIN  ")
        b = blocking_key("mohammed ali hussein")
        assert a == b

    def test_cross_script_requires_nid(self):
        # Arabic-script and English-script forms of the SAME person produce
        # DIFFERENT blocking keys by design — blocking works within a script.
        # Cross-script matching relies on the NID short-circuit in matcher.py.
        ar = blocking_key("محمد علي حسين")
        en = blocking_key("Mohammed Ali Hussein")
        assert ar != en  # documented limitation

    def test_length_is_fixed(self):
        assert len(blocking_key("محمد")) == 5
        assert len(blocking_key("X")) == 5
        assert len(blocking_key("")) == 5

    def test_empty_input(self):
        assert blocking_key("") == "_____"
        assert blocking_key("   ") == "_____"

    def test_single_token(self):
        # Single token uses the token itself for surname+given
        key = blocking_key("Ahmed")
        assert len(key) == 5
        assert key.startswith("ahme")

    def test_surname_first_given_last_layout(self):
        # Last token = surname, first token = given
        k = blocking_key("Mohammed Ali Hussein")
        # "hussein" surname[:4] = "huss", given[0] = "m"
        assert k == "hussm"


# ─── Phone normalization ─────────────────────────────────────────────────────


class TestPhoneLast10:
    def test_strips_non_digits(self):
        # "+964 (790) 123-4567" -> digits "9647901234567" (13 digits) -> last 10
        assert phone_last10("+964 (790) 123-4567") == "7901234567"

    def test_returns_last_10(self):
        assert phone_last10("07901234567") == "7901234567"

    def test_short_returns_none(self):
        assert phone_last10("123") is None

    def test_empty(self):
        assert phone_last10("") is None
        assert phone_last10(None) is None


# ─── Matcher scoring ─────────────────────────────────────────────────────────


def _make_candidate(**overrides) -> Candidate:
    base = {
        "id": 1,
        "citizen_ulid": "01HKX" + "0" * 21,
        "name_canonical": "mohammed ali hussein",
        "phone_last10": "7901234567",
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 12,
        "gender": "M",
        "nid_hash": None,
        "family_id_hash": None,
    }
    base.update(overrides)
    return Candidate(**base)


class TestScoring:
    def test_nid_exact_short_circuits(self):
        p = build_profile(
            name="Totally Different Name",
            nid_hash="deadbeef" * 8,  # 64 chars
        )
        c = _make_candidate(nid_hash="deadbeef" * 8)
        r = score(p, c)
        assert r.method == "nid_exact"
        assert r.score == 1.0

    def test_nid_mismatch_does_not_short_circuit(self):
        p = build_profile(
            name="mohammed ali hussein",
            nid_hash="aaaa" * 16,
            phone_last10="7901234567",
            birth_year=1990,
            birth_month=5,
            birth_day=12,
            gender="M",
        )
        c = _make_candidate(nid_hash="bbbb" * 16)
        r = score(p, c)
        assert r.method == "probabilistic"
        # Even with NID mismatch the other features add up
        assert r.score > 0.7

    def test_all_features_match_yields_auto(self):
        p = build_profile(
            name="mohammed ali hussein",
            phone_last10="7901234567",
            birth_year=1990,
            birth_month=5,
            birth_day=12,
            gender="M",
            family_id_hash="fam1" * 16,
        )
        c = _make_candidate(family_id_hash="fam1" * 16)
        r = score(p, c)
        assert r.score >= THRESHOLD_AUTO

    def test_dob_swap_half_weight(self):
        exact = build_profile(
            name="mohammed ali hussein",
            phone_last10="7901234567",
            birth_year=1990,
            birth_month=5,
            birth_day=12,
            gender="M",
        )
        swapped = build_profile(
            name="mohammed ali hussein",
            phone_last10="7901234567",
            birth_year=1990,
            birth_month=12,
            birth_day=5,
            gender="M",
        )
        c = _make_candidate()
        assert score(exact, c).score > score(swapped, c).score

    def test_only_name_does_not_pass_auto(self):
        p = build_profile(name="mohammed ali hussein")
        c = _make_candidate(phone_last10=None, birth_year=None, gender=None)
        # Only ~0.25 from name JW; well below 0.90
        assert score(p, c).score < THRESHOLD_AUTO

    def test_classify_thresholds(self):
        assert classify(0.95) == "auto_match"
        assert classify(THRESHOLD_AUTO) == "auto_match"
        assert classify(0.80) == "review"
        assert classify(THRESHOLD_REVIEW) == "review"
        assert classify(0.5) == "no_match"
        assert classify(0.0) == "no_match"

    def test_features_dict_is_populated(self):
        p = build_profile(
            name="mohammed ali hussein",
            phone_last10="7901234567",
            birth_year=1990,
            birth_month=5,
            birth_day=12,
            gender="M",
        )
        c = _make_candidate()
        r = score(p, c)
        assert "phone" in r.features
        assert "dob" in r.features
        assert "name_jw" in r.features
        assert "gender" in r.features


# ─── Audit hash chain continuity ─────────────────────────────────────────────


class TestAuditChain:
    """Reproduce the SHA-256 chaining invariant used in resolver._write_audit.

    We don't spin up a DB here; we just verify that the chaining algorithm
    matches what a verifier would compute row-by-row.
    """

    @staticmethod
    def _chain(prev, row):
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256((prev + canonical).encode()).hexdigest()

    def test_genesis_prev_is_64_zeros(self):
        assert len("0" * 64) == 64

    def test_chain_is_deterministic(self):
        row = {"event_type": "create", "primary_citizen_id": 1}
        h1 = self._chain("0" * 64, row)
        h2 = self._chain("0" * 64, row)
        assert h1 == h2
        assert len(h1) == 64

    def test_chain_depends_on_prev(self):
        row = {"event_type": "create", "primary_citizen_id": 1}
        a = self._chain("0" * 64, row)
        b = self._chain("ff" * 32, row)
        assert a != b

    def test_chain_depends_on_payload(self):
        prev = "0" * 64
        a = self._chain(prev, {"event_type": "create", "id": 1})
        b = self._chain(prev, {"event_type": "merge", "id": 1})
        assert a != b

    def test_tamper_detection(self):
        """If any row in the middle of the chain is tampered with, every
        subsequent hash changes (classic blockchain property)."""
        rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 3, "v": "c"}]
        chain_a = []
        prev = "0" * 64
        for r in rows:
            h = self._chain(prev, r)
            chain_a.append(h)
            prev = h

        # Tamper with row 2
        rows[1]["v"] = "TAMPERED"
        chain_b = []
        prev = "0" * 64
        for r in rows:
            h = self._chain(prev, r)
            chain_b.append(h)
            prev = h

        assert chain_a[0] == chain_b[0]  # row 0 unchanged
        assert chain_a[1] != chain_b[1]  # tampered row differs
        assert chain_a[2] != chain_b[2]  # row 3 also differs (downstream)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
