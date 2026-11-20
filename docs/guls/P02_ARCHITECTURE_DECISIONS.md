# P02 - Architecture Decision Records

## ADR-GULS-001: Additive unified language system

Status: Accepted.

Decision: Add a shared GULS core under `backend/app/localization/`, `shared/guls/`, and `frontend-v3/src/guls/` instead of replacing existing localization runtimes.

Rationale: existing components are used by multiple surfaces. Replacing them would create compatibility risk. Additive adapters preserve current consumers while establishing one contract.

Consequences: migration is gradual; old identifiers remain temporarily supported where necessary; docs must state which surfaces are fully integrated.

## ADR-GULS-002: English fallback is mandatory

Status: Accepted.

Decision: `en` is the only permitted fallback language. Unknown or unavailable languages resolve to English. Blocked or pending languages never become effective UI languages.

Rationale: patient safety and predictable behavior. Existing backend fallback to Arabic is corrected narrowly.

## ADR-GULS-003: Language identifiers are not locale tags

Status: Accepted.

Decision: `language_id` is a stable internal identifier. `locale_tag` is a validated BCP 47 value and may be null until a standard is approved. Resolution accepts either form but never invents a locale tag.

Rationale: Iraqi Turkmen and Syriac standards are pending; Kurmanji must be addable later without redesign.

## ADR-GULS-004: Registry is data, not code

Status: Accepted.

Decision: `shared/guls/language_registry.json` is the canonical registry. Python and TypeScript read the same data. Adding a language is a registry and pack operation, not a runtime code change.

## ADR-GULS-005: Packs are data-only signed archives

Status: Accepted.

Decision: language packs are ZIP archives with JSON catalogs, metadata, terminology, formatting, and licensed font files only. Manifests are signed with Ed25519 and content is verified with SHA-256. No script, binary, executable, symlink, or path traversal entry is permitted.

Rationale: prevents code execution and archive attacks while supporting offline installation.

## ADR-GULS-006: No new operational database tables

Status: Accepted.

Decision: reuse `accessibility_profiles.preferences` for language preference. Pack metadata lives in local filesystem storage; large binaries are never stored in the operational database.

Rationale: avoids duplicate tables and migrations. Existing data remains intact.

## ADR-GULS-007: Atomic install and preserve previous version

Status: Accepted.

Decision: a pack is staged, verified, written to a versioned directory, and activated through an atomic state-file replace. Previous version metadata is retained. Failed updates roll back automatically.

## ADR-GULS-008: Clinical text is display-only localization

Status: Accepted.

Decision: translated clinical display strings are stored separately from original values, units, identifiers, and codes. LOINC, UCUM, ICD, and medication code bindings must be evidence-based. No translated display string may alter a clinical value.

## ADR-GULS-009: Four-level governance classification

Status: Accepted.

Decision: L1 general UI, L2 operational healthcare instructions, L3 health education/medical information, L4 high-risk clinical content. L4 requires documented human clinical approval and distinct translator, linguistic reviewer, and clinical reviewer roles.

## ADR-GULS-010: Delivery service is auxiliary

Status: Accepted.

Decision: `/api/v1/localization/` provides discovery and short-lived download authorization. Installed packs are read locally. Delivery failure must not affect clinical services.

## ADR-GULS-011: Logical layout only

Status: Accepted.

Decision: RTL/LTR uses `dir`, `lang`, logical CSS properties, and platform-native direction APIs. No manual character reversal and no global mirroring of icons, charts, or medical diagrams without semantic justification.

## ADR-GULS-012: Synthetic packs are environment-gated

Status: Accepted.

Decision: synthetic packs enable download/verification tests but require `GULS_ALLOW_SYNTHETIC_PACKS=1`. They are marked `synthetic_test_only` and must never be treated as approved translations.
