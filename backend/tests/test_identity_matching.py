"""Unit tests for ``app.services.identity_matching``.

Examples use real Iraqi/Arabic names and Iraqi-style civil data to exercise
the normalizer, the deterministic HID generator, and the weighted scoring.
No database is required — ``find_duplicates`` is exercised via a fake
query object so the matcher logic is tested in isolation.
"""
import os
import sys

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_identity_matching.db")
os.environ.setdefault("SECRET_KEY", "test-secret-idm-not-for-prod-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "b" * 64)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

import pytest
from app.services.identity_matching import (
    MATCH_THRESHOLD,
    calculate_match_score,
    find_duplicates,
    generate_health_id,
    normalize_arabic_name,
    verify_health_id,
)

# ──────────────────────── normalize_arabic_name ──────────────────────────────

class TestNormalizeArabicName:
    def test_strips_tashkeel(self):
        # "مُحَمَّد" with full tashkeel must normalize to "محمد"
        assert normalize_arabic_name("مُحَمَّد") == "محمد"

    def test_unifies_alef_variants(self):
        assert normalize_arabic_name("أحمد") == "احمد"
        assert normalize_arabic_name("إبراهيم") == "ابراهيم"
        assert normalize_arabic_name("آدم") == "ادم"

    def test_ta_marbuta_to_ha(self):
        assert normalize_arabic_name("فاطمة") == "فاطمه"

    def test_alef_maksura_to_ya(self):
        assert normalize_arabic_name("مصطفى") == "مصطفي"

    def test_waw_and_ya_hamza(self):
        assert normalize_arabic_name("مؤمن") == "مومن"
        assert normalize_arabic_name("رائد") == "رايد"

    def test_collapses_whitespace(self):
        assert normalize_arabic_name("  علي   محمد   حسن  ") == "علي محمد حسن"

    def test_empty_and_none(self):
        assert normalize_arabic_name("") == ""
        assert normalize_arabic_name(None) == ""

    def test_latin_lowercased(self):
        assert normalize_arabic_name("Ali AL-Karkhi") == "ali al-karkhi"

    def test_iraqi_full_name(self):
        # Full Iraqi-style name with tashkeel and variants.
        raw = "عَلِيّ حُسَيْنُ الكَرْخِيّ"
        expected = "علي حسين الكرخي"
        assert normalize_arabic_name(raw) == expected


# ───────────────────────── generate_health_id ────────────────────────────────

class TestGenerateHealthId:
    def test_format_is_HID_dash_8_dash_2(self):
        hid = generate_health_id("19900101234")
        # "HID-XXXXXXXX-YY" — 4 + 8 + 1 + 2 = 15 chars
        assert hid.startswith("HID-")
        body, checksum = hid[4:].split("-")
        assert len(body) == 8
        assert len(checksum) == 2

    def test_deterministic(self):
        assert generate_health_id("19900101234") == generate_health_id("19900101234")

    def test_different_nids_produce_different_hids(self):
        a = generate_health_id("19900101234")
        b = generate_health_id("19900101235")
        assert a != b

    def test_ignores_non_digits(self):
        # Iraqi civil IDs are sometimes written with dashes or spaces.
        assert generate_health_id("1990-0101-234") == generate_health_id("19900101234")
        assert generate_health_id("  1990 0101 234  ") == generate_health_id("19900101234")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            generate_health_id("")
        with pytest.raises(ValueError):
            generate_health_id("   ")

    def test_checksum_verifies(self):
        hid = generate_health_id("19880505111")
        assert verify_health_id(hid) is True

    def test_tampered_checksum_rejected(self):
        hid = generate_health_id("19880505111")
        # Flip the last checksum character to something valid but wrong.
        tampered = hid[:-1] + ("A" if hid[-1] != "A" else "B")
        assert verify_health_id(tampered) is False

    def test_tampered_body_rejected(self):
        hid = generate_health_id("19880505111")
        # Flip a body char — checksum no longer matches.
        body = hid[4:12]
        new_body = ("1" + body[1:]) if body[0] != "1" else ("2" + body[1:])
        tampered = "HID-" + new_body + hid[12:]
        assert verify_health_id(tampered) is False

    def test_malformed_rejected(self):
        assert verify_health_id("") is False
        assert verify_health_id("HID-") is False
        assert verify_health_id("HID-SHORT-AB") is False
        assert verify_health_id("XXX-A3F8B2C1-K7") is False


# ──────────────────────── calculate_match_score ──────────────────────────────

def _citizen(**kw):
    """Helper — a plain dict is what the scorer expects to receive."""
    base = {
        "full_name": None,
        "birth_date": None,
        "mother_name": None,
        "governorate": None,
    }
    base.update(kw)
    return base


class TestCalculateMatchScore:
    def test_identical_full_record_is_one(self):
        c = _citizen(
            full_name="علي حسين الكرخي",
            birth_date=date(1990, 5, 12),
            mother_name="فاطمة عبد الله",
            governorate="بغداد",
        )
        assert calculate_match_score(c, dict(c)) == pytest.approx(1.0)

    def test_empty_records_score_zero(self):
        assert calculate_match_score(_citizen(), _citizen()) == 0.0

    def test_name_only_ceiling(self):
        # Only the name matches — max contribution is 0.40.
        a = _citizen(full_name="علي حسين الكرخي")
        b = _citizen(full_name="علي حسين الكرخي")
        assert calculate_match_score(a, b) == pytest.approx(0.40)

    def test_tashkeel_doesnt_break_match(self):
        a = _citizen(full_name="مُحَمَّد عَلِي", birth_date=date(1985, 3, 22))
        b = _citizen(full_name="محمد علي", birth_date=date(1985, 3, 22))
        # name (0.4) + dob (0.3) = 0.7
        assert calculate_match_score(a, b) == pytest.approx(0.70)

    def test_ta_marbuta_mother_match(self):
        a = _citizen(mother_name="فاطمة")
        b = _citizen(mother_name="فاطمه")
        # mother component only
        assert calculate_match_score(a, b) == pytest.approx(0.20)

    def test_same_person_crosses_threshold(self):
        # Same person with minor input noise — must cross 0.85.
        a = _citizen(
            full_name="حسن عبد الرحمن الموسوي",
            birth_date=date(1978, 11, 3),
            mother_name="زينب الحسيني",
            governorate="البصرة",
        )
        b = _citizen(
            full_name="حَسَن عبدالرحمن الموسوي",
            birth_date=date(1978, 11, 3),
            mother_name="زينب الحُسيني",
            governorate="البصره",
        )
        score = calculate_match_score(a, b)
        assert score >= MATCH_THRESHOLD, f"expected ≥ {MATCH_THRESHOLD}, got {score}"

    def test_different_people_stay_below_threshold(self):
        a = _citizen(
            full_name="علي محمد حسن",
            birth_date=date(1990, 1, 1),
            mother_name="فاطمة",
            governorate="بغداد",
        )
        b = _citizen(
            full_name="عمر خالد الجبوري",
            birth_date=date(1975, 6, 15),
            mother_name="خديجة",
            governorate="الموصل",
        )
        assert calculate_match_score(a, b) < MATCH_THRESHOLD

    def test_day_month_swap_gives_partial_credit(self):
        a = _citizen(birth_date=date(1990, 3, 12))
        b = _citizen(birth_date=date(1990, 12, 3))
        # DOB weight 0.3 × swap score 0.5 = 0.15
        assert calculate_match_score(a, b) == pytest.approx(0.15)

    def test_accepts_object_inputs(self):
        class C:
            pass

        a, b = C(), C()
        a.full_name = "علي محمد"
        a.birth_date = date(1990, 1, 1)
        a.mother_name = "فاطمة"
        a.governorate = "بغداد"
        b.full_name = "علي محمد"
        b.birth_date = date(1990, 1, 1)
        b.mother_name = "فاطمه"
        b.governorate = "بغداد"
        assert calculate_match_score(a, b) == pytest.approx(1.0)

    def test_accepts_iso_date_strings(self):
        a = _citizen(full_name="زيد", birth_date="1990-05-05")
        b = _citizen(full_name="زيد", birth_date=date(1990, 5, 5))
        assert calculate_match_score(a, b) == pytest.approx(0.70)


# ─────────────────────────── find_duplicates ─────────────────────────────────

class _FakeQuery:
    """Minimal stand-in for a SQLAlchemy Query — records filter calls and
    returns a preconfigured list. Enough to unit-test the control flow in
    ``find_duplicates`` without spinning up a database."""

    def __init__(self, rows):
        self._rows = rows
        self._filters = []
        self._nid_match = None

    def filter(self, *args, **kwargs):
        self._filters.append((args, kwargs))
        return self

    def limit(self, n):
        return self

    def all(self):
        # If the caller filtered by national_id_hash, return the nid_match rows.
        return list(self._nid_match) if self._nid_match is not None else list(self._rows)


class _FakeDB:
    def __init__(self, patients, nid_hits=None):
        self._patients = patients
        self._nid_hits = nid_hits or []

    def query(self, model):
        q = _FakeQuery(self._patients)
        q._nid_match = None
        # Monkey-patch filter so the first call matching national_id_hash
        # swaps the backing list to the NID hits. This mirrors the service's
        # two-step flow.
        orig_filter = q.filter

        def smart_filter(*args, **kwargs):
            for a in args:
                # SQLAlchemy BinaryExpression stringifies to something like
                # "patients.national_id_hash = :national_id_hash_1"
                if "national_id_hash" in str(a):
                    q._nid_match = self._nid_hits
                    break
            return orig_filter(*args, **kwargs)

        q.filter = smart_filter  # type: ignore[assignment]
        return q


class _Row:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class TestFindDuplicates:
    def test_exact_national_id_short_circuits(self):
        twin = _Row(
            id=42,
            full_name="علي حسين",
            birth_date=date(1990, 1, 1),
            mother_name="فاطمه",
            governorate="بغداد",
        )
        db = _FakeDB(patients=[], nid_hits=[twin])
        hits = find_duplicates(
            db,
            {"national_id": "19900101234", "full_name": "علي حسين"},
        )
        assert len(hits) == 1
        patient, score = hits[0]
        assert patient is twin
        assert score == 1.0

    def test_fuzzy_search_when_no_nid_hit(self):
        match = _Row(
            id=7,
            full_name="حسن عبد الرحمن الموسوي",
            birth_date=date(1978, 11, 3),
            mother_name="زينب الحسيني",
            governorate="البصرة",
        )
        no_match = _Row(
            id=8,
            full_name="عمر خالد الجبوري",
            birth_date=date(1978, 11, 3),
            mother_name="خديجة",
            governorate="الموصل",
        )
        db = _FakeDB(patients=[match, no_match])
        hits = find_duplicates(
            db,
            {
                "full_name": "حَسَن عبدالرحمن الموسوي",
                "birth_date": date(1978, 11, 3),
                "mother_name": "زينب الحُسيني",
                "governorate": "البصره",
            },
        )
        ids = [p.id for p, _ in hits]
        assert 7 in ids
        assert 8 not in ids

    def test_returns_empty_when_no_identifiers(self):
        db = _FakeDB(patients=[])
        assert find_duplicates(db, {}) == []
