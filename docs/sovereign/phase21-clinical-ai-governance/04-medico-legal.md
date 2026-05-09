# Phase 21-04 — Medico-Legal Traceability

## Position

In a medico-legal review, the platform must answer:

- "What did the AI say at the time?"
- "What evidence did the AI see?"
- "Who was the human decision-maker?"
- "Did the human follow or override the AI?"
- "Was the AI capability authorised at the time?"

Phase 21's combined audit + explainability + capability registry answers
these questions.

## Reconstruction Procedure

Given a clinical event (e.g., a critical result decision):

1. Identify the request_id (from the audit chain).
2. Fetch the AI invocation audit rows for that request_id.
3. Fetch the capability registry snapshot at the invocation's
   `output_emitted_at`.
4. Fetch the input snapshot from the snapshot store.
5. Fetch the human-action audit row that consumed the AI output.
6. Replay (where deterministic): same inputs + same model → expected
   outputs.

If any step fails, the medico-legal record is **incomplete**. An
incomplete record is itself a SEV-2 issue.

## Evidence-Lineage Discipline

- Evidence-lineage pointers are persistent. A pointer to a row that has
  since been logically merged (Phase 19) MUST resolve via the canonical id
  to the constituent that was authoritative at invocation time.
- Reconciliation events that change canonical ids are visible in the
  lineage; a reviewer can trace "the AI saw record X, which was later
  merged into canonical Y".

## Liability Surface

The platform documents:

- AI is advisory; clinician is responsible for the action.
- The platform preserves the AI's output as evidence the clinician could
  see at the time.
- The platform preserves the clinician's accept/reject decision.
- The platform does not advise on liability allocation; that is for the
  legal system and the institution's policies.

## Regulator Read on Demand

A regulator with `REGULATOR_READ_FULL` on a relevant warrant scope can:

- query the AI audit rows
- fetch the snapshots
- read the IRB-AI minutes for the capability
- export a packaged "AI evidence packet"

Each query is itself audited.

## Cross-Border Considerations

If a medico-legal proceeding is in a jurisdiction other than the data's
sovereign jurisdiction:

- the export pipeline observes data sovereignty rules
- the export goes through a regulator-approved cross-border protocol
- the AI evidence packet is sealed (signed, integrity-checked) before
  transmission

## Retention

AI audit rows + snapshots retain for the same period as the clinical
record they relate to (typically 30+ years per jurisdictional floor for
clinical records).

A snapshot whose only purpose was a transient invocation that was
discarded retains for the audit-row retention floor (jurisdictional;
≥ 10 years suggested).

## Limitations

- Generative-AI outputs may be non-deterministic at re-invocation. Replay
  produces the same outputs only when the model's randomness is
  deterministic (seed captured) or the model is purely deterministic. The
  capability registry records which property holds.
- Model-version retirement: a retired model's binary is preserved
  alongside the audit chain to permit replay.

## Out of Scope

- Defending the clinician (that is the institution's responsibility)
- Indemnification language (legal counsel)
