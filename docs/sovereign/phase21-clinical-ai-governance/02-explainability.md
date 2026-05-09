# Phase 21-02 — Explainability Framework

## Why Explainability

A clinician acting on AI advice must be able to:

- understand what the AI saw
- understand why the AI said what it did
- verify the AI's confidence level
- defend their action in a medico-legal review

Explainability is therefore not a nice-to-have. It is a clinical-safety
requirement.

## Required Metadata Per AI Output

| Field | Description |
|-------|-------------|
| `capability_id` | The capability slug |
| `model_id` | Concrete model artefact reference |
| `model_version` | Versioned identifier |
| `confidence` | Numeric (0..1) or model-defined alternative |
| `feature_snapshot_id` | Hash of the inputs the model saw, persisted to a snapshot store |
| `decision_rationale` | Free-text or structured per-capability |
| `evidence_lineage` | Pointers to the source rows / aggregates that contributed |
| `output_emitted_at` | Timestamp |
| `review_required` | Boolean — must the clinician explicitly accept? |

If any required field is missing, the consumer route MUST reject the
output and emit an audit row tagged `ai.metadata_missing`.

## Evidence Lineage

Each input row that contributed materially to the output has a pointer in
the evidence_lineage array. A reviewer can fetch the same rows the model
saw (subject to RBAC) for forensic comparison.

For `aggregate`-scope capabilities, the lineage points to anonymised
aggregates with a deterministic redacted view; never to raw rows.

## Feature Snapshot Store

Snapshots:

- are immutable
- have configurable retention (≥ regulator floor)
- carry the same hash as the audit row
- never contain plaintext national_id or other direct identifiers

A snapshot is the "what the model saw" replay artefact.

## Per-Capability Explanation Style

Three styles are supported:

1. **Rule-based** — emitted as a structured trace (which rules fired, with
   thresholds).
2. **Feature-importance** — top-k features with weights.
3. **Counterfactual** — "if X had been Y, output would have differed".

A capability declares its style in the capability registry. Multiple styles
allowed if the model produces them.

## What Is NOT Explainability

- "Confidence: 0.92" alone is not explainability.
- Black-box model output without metadata is not explainability.
- Showing the prompt to a clinician is not, by itself, explainability for
  generative models — it must be paired with the model's reasoning trace
  or evidence lineage.

## Use-Case Examples (illustrative)

- **Critical-result triage AI:** advisory flag with confidence + feature
  importance (e.g., "abnormal hemoglobin + chronic kidney metric"). Clinician
  reviews and accepts.
- **Lab QC anomaly AI:** rule trace listing which QC rule fired. Lab
  director reviews and accepts.
- **Insurance fraud-flag AI:** feature importance + similar-case
  counterfactual; reviewer escalates or dismisses.

In every case the human is the actor.

## Standards Touchpoints

- ISO/IEC 42001 (AI management) — explainability is a control area
- WHO Ethics & governance of AI for health — transparency principle
- EU AI Act high-risk practices — record-keeping + transparency clauses

## Out of Scope (this phase)

- Auto-generated model cards (they should exist; production format is
  decided in implementation phase)
- Public-facing explainability portal (regulator access only initially)
