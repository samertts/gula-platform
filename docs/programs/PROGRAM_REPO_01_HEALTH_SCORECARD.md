# PROGRAM-REPO-01 HEALTH SCORECARD (Phase 7)

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 7 / 8 — 10-Dimension Repository Health Score (ANALYSIS ONLY)
**Date:** 2026-08-08
**Status:** DRAFT — awaiting Program Director approval before execution

---

## Scorecard (0–100 per dimension; overall = mean)

| # | Dimension | Score | Evidence (from Phase 1–6) |
|---|---|---|---|
| 1 | **Application Quality** | **95** | 5089 backend tests passing, ruff 378 (< baseline 379), tsc 0, eslint 0, architecture gate 25/25, domain 11/11, OpenAPI byte-stable |
| 2 | **Security Governance** | **88** | gitleaks pre-commit + `.secrets.baseline`, CodeQL, Dependabot, secret scanning, Scorecard, Semgrep/bandit clean; SECURITY.md present. (−12: OSS disclosure wording + review needed) |
| 3 | **Git Hygiene** | **25** | 125 branches (60+ stale 3–5 mo), 5 garbage tmp packs, 120 merge commits vs rebase policy, tag flood (38 non-semver), version drift |
| 4 | **Repository Structure** | **20** | 156 root `.md`, ~90 docs subdirs, 9+ legacy trees, 12 name-duplicate doc families |
| 5 | **CI/CD Efficiency** | **45** | 26 workflows → redundancy (7 deploy, 5 quality), inconsistent naming; strong security scans present; no hygiene gate |
| 6 | **Documentation** | **55** | 1,192 `.md`, high generated-doc quality, but 156 at root, 1 broken link, no index, massive duplication |
| 7 | **Developer Experience** | **40** | no docs index, no quick-start, multi-env setup manual, no unified test command; strong tooling already present (Makefile, pre-commit) |
| 8 | **Open-Source Readiness** | **50** | governance files all present, but repo surface cluttered, tags/versioning not OSS-clean, no release stream, single CODEOWNER |
| 9 | **Versioning & Release** | **30** | `VERSION`=RC2 vs package.json=1.0.0, feature-tag flood, no automated version sync, no GA release |
| 10 | **Sustainability / Longevity** | **60** | AGENTS.md constitution + live governance engines (self-documenting, self-gating), ADR process active; heavy dormant tree mass to manage |
| | **OVERALL** | **48** | mean of dimensions |

## Trajectory

- **Today: 48/100.**
- **After execution of the 4 waves (Phase 8): target ≈ 85/100.**
  - Git hygiene 25 → 80 (branch cleanup, gc, semver tags, sync).
  - Structure 20 → 85 (root ≤16 `.md`, legacy → archive).
  - Docs 55 → 80 (index, dedup, link gate).
  - DX 40 → 80 (quick-start, one-command test, docs index).
  - CI 45 → 75 (26→12 workflows, hygiene gate).
  - OSS readiness 50 → 85 (clean surface, releases, governance verified).
  - Versioning 30 → 85 (single source of truth + release workflow).
- Unchanged high dims: App Quality 95, Security 88, Sustainability 60 (+ docs consolidation).

## Thresholds

| Band | Score | Meaning |
|---|---|---|
| 0–39 | RED | enterprise/open-source unviable |
| 40–59 | AMBER | viable internally, NOT OSS-ready (current) |
| 60–79 | GREEN | OSS-ready with work |
| 80–100 | BLUE | enterprise-grade OSS (target ≥ 85) |

## Final verdict (Phase 7)

Repository is **internally viable but NOT open-source ready**. The application is excellent;
the repository surface is the blocker. PROGRAM-REPO-01 execution (on approval) closes the gap.
