"""Idempotent seed loader for the Medical Ontology Core.

Reads ``data/ontology/*.yaml`` and upserts:

  * concepts.yaml           → medical_ontology_concepts,
                              medical_ontology_codes
  * synonyms.yaml           → medical_ontology_synonyms
  * relations.yaml          → medical_ontology_relations
  * reference_ranges.yaml   → medical_ontology_reference_ranges
  * unit_conversions.yaml   → medical_ontology_unit_conversions

Running twice with an unchanged YAML tree is a no-op. Running after edits
inserts new rows and updates changed rows; deletions in the YAML tree do
NOT delete rows from the DB (deprecation is a separate physician-review
workflow — automated deletion of medical concepts is disallowed).

Usage
-----
    DATABASE_URL=postgresql://... python scripts/seed_medical_ontology.py
    DATABASE_URL=... python scripts/seed_medical_ontology.py --data-dir custom/
    DATABASE_URL=... python scripts/seed_medical_ontology.py --dry-run

Exit codes: 0 success, 1 any I/O or DB error, 2 validation error in a YAML
file (e.g. unknown concept_key in synonyms.yaml).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # PyYAML — already in requirements.txt
except ImportError:  # pragma: no cover - explicit friendly message
    print("PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

# Model imports must come after sys.path munging.
# Loading ``app.models`` registers the ontology tables plus every other ORM
# class that has a cross-package relationship dependency (e.g. CitizenLink →
# Citizen). Without the mpi.models import the mapper configuration blows up
# on first query because ``Citizen`` lives in a separate package.
from app import models  # noqa: F401,E402
from app.services.mpi import models as _mpi_models  # noqa: F401,E402
from app.models.medical_ontology import (  # noqa: E402
    MedicalOntologyCode,
    MedicalOntologyConcept,
    MedicalOntologyReferenceRange,
    MedicalOntologyRelation,
    MedicalOntologySynonym,
    MedicalOntologyUnitConversion,
)
from app.services.medical_ontology.normalize import normalize_text  # noqa: E402

log = logging.getLogger("gula.seed.medical_ontology")


# ─── YAML I/O ────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: top-level must be a mapping")
    return data


# ─── Upsert helpers ──────────────────────────────────────────────────────────

def _now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc)


class Stats:
    def __init__(self) -> None:
        self.inserted = 0
        self.updated = 0
        self.unchanged = 0

    def bump(self, kind: str) -> None:
        setattr(self, kind, getattr(self, kind) + 1)

    def summary(self) -> str:
        return (f"inserted={self.inserted} "
                f"updated={self.updated} "
                f"unchanged={self.unchanged}")


def _upsert_concepts(session: Session, concepts: Iterable[dict[str, Any]],
                     stats: Stats) -> dict[str, Any]:
    """Upsert concepts + their codes. Returns {concept_key: concept_id}."""
    key_to_id: dict[str, Any] = {}
    now = _now()
    for c in concepts:
        key = c["concept_key"]
        existing = session.execute(
            select(MedicalOntologyConcept)
            .where(MedicalOntologyConcept.concept_key == key)
        ).scalar_one_or_none()

        payload = {
            "category":              c["category"],
            "display_en":            c.get("display_en"),
            "display_ar":            c.get("display_ar"),
            "description_en":        c.get("description_en"),
            "description_ar":        c.get("description_ar"),
            "canonical_unit_key":    c.get("canonical_unit"),
            "default_specimen_key":  c.get("default_specimen"),
            "attributes":            c.get("attributes"),
            "status":                c.get("status", "active"),
        }

        if existing is None:
            row = MedicalOntologyConcept(
                concept_key=key,
                created_at=now,
                updated_at=now,
                **payload,
            )
            session.add(row)
            session.flush()
            key_to_id[key] = row.id
            stats.bump("inserted")
        else:
            dirty = False
            for k, v in payload.items():
                if getattr(existing, k) != v:
                    setattr(existing, k, v)
                    dirty = True
            if dirty:
                existing.updated_at = now
                existing.version = (existing.version or 1) + 1
                stats.bump("updated")
            else:
                stats.bump("unchanged")
            key_to_id[key] = existing.id

        # Codes: additive only; never delete existing codes.
        for code_entry in c.get("codes") or []:
            _upsert_code(session, key_to_id[key], code_entry, stats)

    return key_to_id


def _upsert_code(session: Session, concept_id: Any,
                 entry: dict[str, Any], stats: Stats) -> None:
    code_system = entry["system"]
    code = entry["code"]
    existing = session.execute(
        select(MedicalOntologyCode)
        .where(MedicalOntologyCode.concept_id == concept_id)
        .where(MedicalOntologyCode.code_system == code_system)
        .where(MedicalOntologyCode.code == code)
    ).scalar_one_or_none()
    if existing is None:
        session.add(MedicalOntologyCode(
            concept_id=concept_id,
            code_system=code_system,
            code=code,
            display=entry.get("display"),
            is_primary=bool(entry.get("primary", False)),
            created_at=_now(),
        ))
        stats.bump("inserted")
    else:
        stats.bump("unchanged")


def _upsert_synonyms(session: Session, synonyms: Iterable[dict[str, Any]],
                     key_to_id: dict[str, Any], stats: Stats) -> None:
    now = _now()
    for s in synonyms:
        key = s["concept_key"]
        if key not in key_to_id:
            raise ValueError(
                f"synonyms.yaml references unknown concept_key: {key}"
            )
        term = s["term"]
        locale = s["locale"]
        normalized = normalize_text(term)
        existing = session.execute(
            select(MedicalOntologySynonym)
            .where(MedicalOntologySynonym.concept_id == key_to_id[key])
            .where(MedicalOntologySynonym.term_normalized == normalized)
            .where(MedicalOntologySynonym.locale == locale)
        ).scalar_one_or_none()

        payload = {
            "term":       term,
            "variant":    s.get("variant"),
            "source":     s.get("source"),
            "confidence": float(s.get("confidence", 1.0)),
        }
        if existing is None:
            session.add(MedicalOntologySynonym(
                concept_id=key_to_id[key],
                term_normalized=normalized,
                locale=locale,
                created_at=now,
                **payload,
            ))
            stats.bump("inserted")
        else:
            dirty = False
            for k, v in payload.items():
                if getattr(existing, k) != v:
                    setattr(existing, k, v)
                    dirty = True
            stats.bump("updated" if dirty else "unchanged")


def _upsert_relations(session: Session, relations: Iterable[dict[str, Any]],
                      key_to_id: dict[str, Any], stats: Stats) -> None:
    now = _now()
    for rel in relations:
        src, tgt = rel["source"], rel["target"]
        if src not in key_to_id or tgt not in key_to_id:
            raise ValueError(
                f"relations.yaml references unknown concept: "
                f"source={src} target={tgt}"
            )
        rel_type = rel["relation"]
        existing = session.execute(
            select(MedicalOntologyRelation)
            .where(MedicalOntologyRelation.source_concept_id == key_to_id[src])
            .where(MedicalOntologyRelation.target_concept_id == key_to_id[tgt])
            .where(MedicalOntologyRelation.relation_type == rel_type)
        ).scalar_one_or_none()

        payload = {
            "strength":   rel.get("strength"),
            "provenance": rel.get("provenance"),
            "attributes": rel.get("attributes"),
        }
        if existing is None:
            session.add(MedicalOntologyRelation(
                source_concept_id=key_to_id[src],
                target_concept_id=key_to_id[tgt],
                relation_type=rel_type,
                created_at=now,
                **payload,
            ))
            stats.bump("inserted")
        else:
            dirty = False
            for k, v in payload.items():
                if getattr(existing, k) != v:
                    setattr(existing, k, v)
                    dirty = True
            stats.bump("updated" if dirty else "unchanged")


def _upsert_reference_ranges(session: Session,
                             ranges: Iterable[dict[str, Any]],
                             key_to_id: dict[str, Any],
                             stats: Stats) -> None:
    now = _now()
    for r in ranges:
        key = r["concept_key"]
        if key not in key_to_id:
            raise ValueError(
                f"reference_ranges.yaml references unknown concept: {key}"
            )
        # Range identity: (concept, unit, sex, pregnancy, age_min, age_max,
        # specimen, analyzer, source, source_version, lab_id). We match on
        # the full demographic tuple so seed edits are idempotent.
        stmt = (
            select(MedicalOntologyReferenceRange)
            .where(MedicalOntologyReferenceRange.concept_id == key_to_id[key])
            .where(MedicalOntologyReferenceRange.unit_key == r["unit"])
            .where(MedicalOntologyReferenceRange.sex == r.get("sex", "any"))
            .where(MedicalOntologyReferenceRange.pregnancy_status
                   == r.get("pregnancy_status", "any"))
        )
        existing = session.execute(stmt).scalars().all()
        match = None
        for row in existing:
            if (row.age_min_years == r.get("age_min_years")
                    and row.age_max_years == r.get("age_max_years")
                    and row.specimen_key == r.get("specimen")
                    and row.analyzer == r.get("analyzer")
                    and row.source == r.get("source")
                    and row.source_version == r.get("source_version")
                    and row.lab_id == r.get("lab_id")):
                match = row
                break

        payload = {
            "low":            r.get("low"),
            "high":           r.get("high"),
            "critical_low":   r.get("critical_low"),
            "critical_high":  r.get("critical_high"),
            "severity_bands": r.get("severity_bands"),
            "source_url":     r.get("source_url"),
            "notes":          r.get("notes"),
            "status":         r.get("status", "active"),
        }
        if match is None:
            session.add(MedicalOntologyReferenceRange(
                concept_id=key_to_id[key],
                unit_key=r["unit"],
                age_min_years=r.get("age_min_years"),
                age_max_years=r.get("age_max_years"),
                sex=r.get("sex", "any"),
                pregnancy_status=r.get("pregnancy_status", "any"),
                specimen_key=r.get("specimen"),
                analyzer=r.get("analyzer"),
                lab_id=r.get("lab_id"),
                source=r.get("source", "internal"),
                source_version=r.get("source_version"),
                created_at=now,
                updated_at=now,
                **payload,
            ))
            stats.bump("inserted")
        else:
            dirty = False
            for k, v in payload.items():
                if getattr(match, k) != v:
                    setattr(match, k, v)
                    dirty = True
            if dirty:
                match.updated_at = now
                stats.bump("updated")
            else:
                stats.bump("unchanged")


def _upsert_unit_conversions(session: Session,
                             conversions: Iterable[dict[str, Any]],
                             stats: Stats) -> None:
    now = _now()
    for c in conversions:
        stmt = (
            select(MedicalOntologyUnitConversion)
            .where(MedicalOntologyUnitConversion.from_unit_key
                   == c["from_unit"])
            .where(MedicalOntologyUnitConversion.to_unit_key
                   == c["to_unit"])
        )
        scope = c.get("concept_scope")
        if scope is None:
            stmt = stmt.where(
                MedicalOntologyUnitConversion.concept_scope_key.is_(None)
            )
        else:
            stmt = stmt.where(
                MedicalOntologyUnitConversion.concept_scope_key == scope
            )
        existing = session.execute(stmt).scalar_one_or_none()

        payload = {
            "factor": float(c["factor"]),
            "offset": float(c.get("offset", 0.0)),
            "source": c.get("source"),
        }
        if existing is None:
            session.add(MedicalOntologyUnitConversion(
                from_unit_key=c["from_unit"],
                to_unit_key=c["to_unit"],
                concept_scope_key=scope,
                created_at=now,
                **payload,
            ))
            stats.bump("inserted")
        else:
            dirty = False
            for k, v in payload.items():
                if getattr(existing, k) != v:
                    setattr(existing, k, v)
                    dirty = True
            stats.bump("updated" if dirty else "unchanged")


# ─── Entry point ─────────────────────────────────────────────────────────────

def _resolve_data_dir(cli_dir: str | None) -> Path:
    if cli_dir:
        return Path(cli_dir).expanduser().resolve()
    return REPO_ROOT / "data" / "ontology"


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", help="Override data/ontology directory")
    parser.add_argument("--database-url",
                        help="Override DATABASE_URL from environment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Roll back at the end instead of committing")
    args = parser.parse_args(argv)

    data_dir = _resolve_data_dir(args.data_dir)
    log.info("seeding ontology from %s", data_dir)

    url = args.database_url or os.getenv("DATABASE_URL")
    if not url:
        log.error("DATABASE_URL not set (and no --database-url)")
        return 1

    concepts = _load_yaml(data_dir / "concepts.yaml").get("concepts") or []
    synonyms = _load_yaml(data_dir / "synonyms.yaml").get("synonyms") or []
    relations = _load_yaml(data_dir / "relations.yaml").get("relations") or []
    ranges = _load_yaml(
        data_dir / "reference_ranges.yaml"
    ).get("ranges") or []
    conversions = _load_yaml(
        data_dir / "unit_conversions.yaml"
    ).get("conversions") or []

    engine = create_engine(url, future=True)
    stats = {kind: Stats() for kind in
             ("concepts", "synonyms", "relations", "ranges", "units")}

    with Session(engine, future=True) as session:
        try:
            key_to_id = _upsert_concepts(session, concepts, stats["concepts"])
            _upsert_synonyms(session, synonyms, key_to_id, stats["synonyms"])
            _upsert_relations(session, relations, key_to_id,
                              stats["relations"])
            _upsert_reference_ranges(session, ranges, key_to_id,
                                     stats["ranges"])
            _upsert_unit_conversions(session, conversions, stats["units"])
        except ValueError as exc:
            log.error("validation error: %s", exc)
            session.rollback()
            return 2
        except Exception:
            log.exception("seed failed; rolling back")
            session.rollback()
            return 1

        if args.dry_run:
            session.rollback()
            log.info("dry-run: rolled back")
        else:
            session.commit()

    for kind, s in stats.items():
        log.info("%-10s %s", kind, s.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
