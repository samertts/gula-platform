"""Absence of a renal guideline must not be reported as "no adjustment needed".

``DoseEngine.calculate_renal_adjustment`` previously returned, in every case
where it found no matching adjustment::

    {"requires_adjustment": False,
     "recommendation": "No adjustment needed based on guidelines"}

including the case where the platform holds no renal guideline for the drug at
all.  That is a clinical-safety defect of the "absence presented as a negative
finding" class: many drugs require a reduced dose in renal impairment, so
telling a prescriber that no adjustment is needed, for a drug nothing is known
about, can leave a full dose in place for a patient with a low eGFR.

SCOPE OF THIS FILE -- stated plainly so it is not read as more than it is.

These are unit tests of the decision logic, driven through a stub session.
They are NOT evidence that ``POST /pharmacy/clinical/dose/renal-adjust`` works:
that endpoint returns 500 today, because the ``DoseGuideline`` ORM model and the
physical ``pharmacy_dose_guidelines`` table are two different designs sharing one
name (``drug_code`` vs ``drug_id``, ``age_min_months`` vs ``age_min_years``), so
any query naming ``drug_code`` raises ``UndefinedColumn``.  That divergence is a
separate finding and a human decision -- months and years are not the same
clinical quantity and must not be mapped to one another here.

The fix is therefore ordered deliberately: this unsafe default is latent while
the endpoint 500s, and would become live the moment the schema drift is
repaired.  Guarding it first means the drift repair cannot silently ship it.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.pharmacy.clinical import DoseEngine


class _Query:
    """Minimal stand-in for the one query calculate_renal_adjustment issues."""

    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _Session:
    def __init__(self, result):
        self._result = result

    def query(self, *args, **kwargs):
        return _Query(self._result)


def _engine(guideline):
    return DoseEngine(_Session(guideline), lab_id=1)


def test_no_guideline_on_file_is_reported_as_not_assessed():
    """The defect in its original form: nothing known, yet a negative asserted."""
    result = _engine(None).calculate_renal_adjustment("UNKNOWN-DRUG", egfr=22.0)

    assert result["assessed"] is False
    # Not False: False would claim an assessment concluded no adjustment.
    assert result["requires_adjustment"] is None
    assert "NOT been assessed" in result["recommendation"]
    assert "No adjustment needed" not in result["recommendation"]


def test_guideline_present_but_unreadable_adjustment_is_not_assessed():
    """A guideline whose renal data is not the eGFR band list this code reads."""
    guideline = SimpleNamespace(renal_adjustment={"unexpected": "shape"})
    result = _engine(guideline).calculate_renal_adjustment("SOME-DRUG", egfr=22.0)

    assert result["assessed"] is False
    assert result["requires_adjustment"] is None
    assert "NOT been assessed" in result["recommendation"]


def test_egfr_outside_every_band_is_assessed_and_distinguished():
    """A real assessment that found no applicable band is a different answer.

    This one may legitimately say no adjustment is specified, because a guideline
    was read -- and the response must make clear which of the two it is.
    """
    guideline = SimpleNamespace(
        renal_adjustment=[{"egfr_range": {"min": 0, "max": 15}, "dose": "half"}]
    )
    result = _engine(guideline).calculate_renal_adjustment("SOME-DRUG", egfr=90.0)

    assert result["assessed"] is True
    assert result["requires_adjustment"] is False
    assert "falls outside all of them" in result["recommendation"]


def test_matching_band_still_returns_the_adjustment():
    """The safety change must not break the case the function exists for."""
    guideline = SimpleNamespace(
        renal_adjustment=[
            {
                "egfr_range": {"min": 0, "max": 30},
                "dose": "250mg q24h",
                "recommendation": "Reduce dose and extend interval",
            }
        ]
    )
    result = _engine(guideline).calculate_renal_adjustment("SOME-DRUG", egfr=22.0)

    assert result["assessed"] is True
    assert result["requires_adjustment"] is True
    assert result["adjusted_dose"] == "250mg q24h"
    assert result["recommendation"] == "Reduce dose and extend interval"
    assert result["adjustment_detail"]["egfr_range"] == {"min": 0, "max": 30}
