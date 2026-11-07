# GULA Stable v1.0.0 — Program Charter

**Status:** Phase 0 — Baseline and setup  
**Repository:** `samertts/gula-platform` (private)  
**Protected baseline:** `main` at `46158e905fd97f57ca21c61bb5574d03aed90293`  
**Working branch:** `recovery/stable-v1`

## Mission
Stabilize the existing GULA platform and deliver a defensible Stable v1.0.0 release. This is a recovery and verification program, not a rewrite.

## Product boundary
- GULA LIS remains the primary product.
- `backend/app/` remains the canonical backend.
- `frontend-v3/` is the documented primary web client; reconcile its operational relationship with `gula-web-suite` before asserting deployment ownership.
- `services/` remains future decomposition unless evidence and an approved ADR establish otherwise.
- Existing modules are preserved. Dormant or future modules are not deleted merely because they are outside the v1 pilot.

## Non-negotiable controls
1. Never commit directly to `main`.
2. No rewrite, broad restructuring, or Platform-Core restructuring during this program.
3. No deletion or replacement of modules, data, migrations, configuration, or workflows without an approved, evidence-backed change.
4. No destructive database operation; migrations require explicit review, backups, and clean/existing-database evidence.
5. No secrets, real patient data, or production credentials in Git, prompts, or test fixtures.
6. Unknown is not verified. A test claim requires an executed command, environment, result, and retained evidence.
7. AI agents may inspect, propose, and implement bounded changes; they cannot certify clinical safety, security, migration safety, or production readiness.
8. Human review is mandatory for clinical workflows, identity/access control, data retention, migrations, cryptography, and release gates.

## Delivery model
Ubuntu and Windows are supported development environments. OpenCode and VS Code AI are permitted agents under the same repository rules. Low AI budget means local deterministic tools and targeted context first; avoid repeated whole-repository prompts and unnecessary model calls.

## Release principle
Stable v1.0.0 is earned only when the approved acceptance gates pass with reproducible evidence. No schedule overrides safety or evidence.