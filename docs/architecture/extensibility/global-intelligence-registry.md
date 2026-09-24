# Global health systems intelligence registry

**PROGRAM-EXT-001, Phase 12.** Foundation only — the structure, not the
research.

## 1. What this is for

GULA is not the first national health platform. PROGRAM-GLOBAL-001 will study
what other countries and projects built, what worked and what failed, and
record it in a form that can be cited in a design decision rather than
remembered in a meeting.

This page establishes the structure. **The sweep has not been run**, and the
registry ships empty on purpose: filling it from memory would put unsourced
claims into the one document whose entire value is the quality of its evidence.

## 2. Where it lives

* Data: `docs/architecture/extensibility/global-intelligence-registry.json`
* Types and validation:
  `app/kernel/extensibility.py::GlobalIntelligenceEntry`,
  `load_global_intelligence`
* Guard: `backend/tests/test_extensibility_guards.py::TestGlobalIntelligence`

## 3. Fields

| Field | Meaning |
| --- | --- |
| `entry_id` | stable key |
| `source` | the citation — a document, standard or published report |
| `country` | where it was deployed |
| `system` | what it is called |
| `domain` | which part of health it covers |
| `architecture` | how it is built |
| `scale` | population, facilities, transactions — numbers, not adjectives |
| `standards` | FHIR, HL7v2, SNOMED, ICD, IHE profiles |
| `interoperability` | how it exchanges with systems it does not own |
| `security`, `privacy`, `governance` | controls, data protection, who decides |
| `success_factors` | what is credited with making it work |
| `failure_modes` | what went wrong — **the most valuable field here** |
| `evidence_quality` | `PEER_REVIEWED` / `OFFICIAL_REPORT` / `VENDOR_CLAIM` / `ANECDOTAL` / `UNKNOWN` |
| `licence` | required by Free/Open Source First before anything is adopted |
| `gula_relevance` | what it would change here, specifically |
| `recommendation` | `ADOPT` / `ADAPT` / `INSPIRE` / `REJECT` |

## 4. The four verdicts

* **ADOPT** — take it as it stands. Requires a licence that permits it and
  evidence stronger than anecdote.
* **ADAPT** — the idea holds; the implementation must change for Iraq's
  constraints (Arabic-first, intermittent connectivity, cost governance).
* **INSPIRE** — read it, then design our own.
* **REJECT** — recorded *with the reason*, so the next person to propose it
  finds out why before spending a month on it.

## 5. Two rules the validator enforces

1. **ADOPT may not rest on anecdote.** `recommendation = ADOPT` with
   `evidence_quality` of `ANECDOTAL` or `UNKNOWN` is a violation. A strong
   verdict on weak evidence is how a rumour becomes a roadmap item, and it is
   the specific failure this registry exists to prevent.
2. **Every entry declares a licence.** The Platform Constitution's Free First,
   Open Source First and No Vendor Lock-In articles cannot be applied to
   something whose licence nobody wrote down.

`evidence_quality` is deliberately separate from `recommendation`: they are
different judgements, and collapsing them hides which one is weak.

## 6. Adding an entry

Append to `entries` in the JSON, then:

```python
from app.kernel.extensibility import load_global_intelligence
assert all(not e.violations() for e in load_global_intelligence())
```

The guard runs this in CI, so a malformed entry fails the build rather than
sitting in the file looking authoritative.

## 7. Scope boundary

PROGRAM-EXT-001 was asked to establish the reusable structure and explicitly not
to perform the sweep. It has not. An empty registry that says so is a truthful
artifact; a pre-seeded one would not be.
