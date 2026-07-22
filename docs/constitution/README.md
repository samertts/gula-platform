# GULA Platform Constitution

Version 1.0 — 30 documents defining the architecture, engineering, security, clinical, and governance standards for the GULA healthcare platform.

## Structure

The Constitution is organized into five thematic groups.

### Group A: Foundation (Articles 01-04)

| # | Document | Purpose | Cross-References |
|---|----------|---------|-----------------|
| 01 | VISION | 10-year aspirational vision: what GULA will be in 2035 | 30 |
| 02 | MISSION | Platform's ongoing purpose and core commitments | 01, 29 |
| 03 | CORE VALUES | 12 immutable principles (Ship, Trust, etc.) | 04, 08 |
| 04 | PLATFORM PHILOSOPHY | Design mindset: evolutionary, simple, data-driven | 03, 25 |

### Group B: Architecture & Engineering (Articles 05-07)

| # | Document | Purpose | Cross-References |
|---|----------|---------|-----------------|
| 05 | ARCHITECTURE PRINCIPLES | 15 architecture rules (idempotency, pagination, backend authority) | 14, 08, 12 |
| 06 | DOMAIN MODEL | 6 bounded contexts and their boundaries | 05, 13, 26 |
| 07 | ENGINEERING RULES | 15 coding standards (naming, testing, CI) | 05, 20, 28 |

### Group C: Security & Domain (Articles 08-13)

| # | Document | Purpose | Cross-References |
|---|----------|---------|-----------------|
| 08 | SECURITY CONSTITUTION | 20 security requirements (encryption, auth, audit) | 05, 14, 19 |
| 09 | CLINICAL CONSTITUTION | Patient safety, CDS, clinical workflow integrity | 11, 05 |
| 10 | LABORATORY CONSTITUTION | Specimen integrity, QC, instrument integration | 16, 09 |
| 11 | AI CONSTITUTION | Clinical AI principles, validation, transparency | 09, 08 |
| 12 | UI/UX CONSTITUTION | Arabic-first, accessibility, backend authority | 05 |
| 13 | DATA CONSTITUTION | Data lifecycle, quality, privacy, retention | 08, 15, 05 |

### Group D: Interfaces & Execution (Articles 14-23)

| # | Document | Purpose | Cross-References |
|---|----------|---------|-----------------|
| 14 | API CONSTITUTION | RESTful design, versioning, error formats | 05, 08, 23 |
| 15 | DATABASE CONSTITUTION | SQLAlchemy, migrations, indexing strategy | 13, 05 |
| 16 | EVENT CONSTITUTION | Event-driven architecture, outbox pattern, schemas | 14, 15, 18 |
| 17 | PLUGIN CONSTITUTION | Plugin lifecycle, sandboxing, versioning | 05, 08, 14 |
| 18 | WORKFLOW CONSTITUTION | State machines, workflow engine, notifications | 16, 09, 10 |
| 19 | GOVERNANCE | Bodies, decision process, compliance verification | 27, 20 |
| 20 | TESTING POLICY | Pyramid, coverage thresholds, CI enforcement | 28, 27 |
| 21 | DOCUMENTATION POLICY | What, where, how to document | 19, 07 |
| 22 | RELEASE POLICY | Semantic versioning, release cadence, hotfix process | 25, 19 |
| 23 | BACKWARD COMPATIBILITY | API/DB/integration compatibility guarantees | 22, 14 |

### Group E: Strategy & Evolution (Articles 24-30)

| # | Document | Purpose | Cross-References |
|---|----------|---------|-----------------|
| 24 | WORLD BENCHMARK POLICY | Platform benchmarking against global standards | 25, 19 |
| 25 | EVOLUTION POLICY | What can/cannot change, evolution horizons | 22, 30, 19 |
| 26 | NATIONAL PLATFORM STRATEGY | Multi-tenant hierarchy, national identity | 06, 08 |
| 27 | ARCHITECTURE DECISION PROCESS | ADR lifecycle, template, immutability | 19 |
| 28 | DEFINITION OF DONE | Completion criteria for code, docs, tests | 20, 21 |
| 29 | GULA MANIFESTO | Core beliefs (1-page distillation) | 01, 03, 04 |
| 30 | GULA ROADMAP 2035 | 4 horizons spanning 2025-2035 | 25, 01 |

## Cross-Reference Map

### By dependency

```
01 VISION ──────────────────────────────────────── 30 ROADMAP
02 MISSION ───── 01
03 CORE VALUES ───────────────── 04, 08
04 PHILOSOPHY ────────────── 03, 25
05 ARCHITECTURE ──────────────────────────── 14, 08, 12
06 DOMAIN MODEL ───── 05, 13, 26
07 ENGINEERING ───── 05, 20, 28
08 SECURITY ─────────────────────────────── 05, 14, 19
09 CLINICAL ──────────────── 11, 05
10 LABORATORY ───── 16, 09
11 AI ───────────────────────────────── 09, 08
12 UI/UX ──────────────────── 05
13 DATA ──────────────────────── 08, 15, 05
14 API ─────────────────────────────────── 05, 08, 23
15 DATABASE ───────────── 13, 05
16 EVENT ────────────────── 14, 15, 18
17 PLUGIN ───── 05, 08, 14
18 WORKFLOW ─── 16, 09, 10
19 GOVERNANCE ── 27, 20
20 TESTING ───── 28, 27
21 DOCS ──────── 19, 07
22 RELEASE ───── 25, 19
23 COMPATIBILITY ────── 22, 14
24 BENCHMARK ── 25, 19
25 EVOLUTION ── 22, 30, 19
26 NATIONAL ─── 06, 08
27 ADR ──────── 19
28 DOD ──────── 20, 21
29 MANIFESTO ── 01, 03, 04
30 ROADMAP ──── 25, 01
```

### By article referenced

| Referenced Article | References From |
|--------------------|-----------------|
| 01 VISION | 02, 29, 30 |
| 03 CORE VALUES | 04, 29 |
| 04 PHILOSOPHY | 29 |
| 05 ARCHITECTURE | 06, 07, 08, 09, 11, 12, 13, 14, 15, 17 |
| 06 DOMAIN MODEL | 26 |
| 08 SECURITY | 03, 05, 11, 13, 14, 17, 26 |
| 09 CLINICAL | 10, 11, 18 |
| 11 AI | 09 |
| 13 DATA | 06, 15 |
| 14 API | 05, 16, 17, 23 |
| 15 DATABASE | 13, 16 |
| 16 EVENT | 10, 18 |
| 18 WORKFLOW | 16 |
| 19 GOVERNANCE | 08, 21, 22, 24, 25, 27 |
| 20 TESTING | 07, 19, 28 |
| 21 DOCS | 28 |
| 22 RELEASE | 23, 25 |
| 23 COMPATIBILITY | 14 |
| 25 EVOLUTION | 04, 22, 24, 30 |
| 26 NATIONAL | 06 |
| 27 ADR | 19, 20 |
| 28 DOD | 07, 20 |
| 30 ROADMAP | 01, 25 |

## Compliance Matrix

Each article is scored for codebase compliance in the [Gap Analysis](#gap-analysis) section. See `compliance_matrix.md` for module-level detail.

## Relationship to CLAUDE.md

CLAUDE.md at repo root is the **operational companion** to the Constitution — it documents the daily commands, file locations, and conventions for effective AI-assisted development. The Constitution is the **normative authority**: where CLAUDE.md describes what exists, the Constitution prescribes what should exist. In a conflict, the Constitution prevails.

## Legacy Documents

The following files in this directory predate the canonical 30-article Constitution and are **superseded**:
- `PLATFORM-CONSTITUTION.md` — Original monolithic constitution (680 lines, frozen 2026-07-16)
- `engineering_constitution.md` / `ENGINEERING_CONSTITUTION.md` — Engineering-focused draft
- `platform_identity.md` — Platform identity and philosophy (superseded by Articles 01-04)
- `digital_dna.md` — Platform DNA document (superseded by Articles 03-04)
- `CONSTITUTION_VALIDATION_REPORT.md` / `CONSTITUTION-VALIDATION-REPORT.md` — Preliminary validation reports (superseded by the compliance matrix and gap analysis in this directory)

These are preserved for reference. The canonical 30 articles (01-30) take precedence in case of conflict.
