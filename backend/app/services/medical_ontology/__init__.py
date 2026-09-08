"""GULA Medical Ontology service package.

Runtime consumers of the ontology graph. All of this code is gated behind
``ENABLE_MEDICAL_ONTOLOGY`` (see ``core.sndhs_flags``) — legacy consumers
that use ``services.interpretation`` continue to work unchanged when the
flag is off.

Public API
----------
    normalize.normalize_text(text, locales=None)      -> str  (canonical form)
    normalize.resolve_concept(session, text)          -> ConceptMatch | None
    units.convert(session, value, from_unit, to_unit, concept_scope=None) -> float
    reference_range.interpret(session, concept_key, value, unit_key, *,
                              age_years, sex, pregnancy_status='not_pregnant',
                              specimen=None, analyzer=None, lab_id=None)
                                                       -> Interpretation
"""

from __future__ import annotations
