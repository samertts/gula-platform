# Phase 21-01 — AI Governance Architecture

## Layers

```
+------------------------------------------------+
|  IRB-AI (governance body, Phase 18)            |
+------------------+-----------------------------+
                   |
+------------------v-----------------------------+
|  AI Capability Registry (Phase 21)             |
|   - capability id, version, model id           |
|   - authority class (advisory only)            |
|   - scope (tenant / aggregate)                 |
|   - inputs / outputs schema                    |
|   - kill-switch flag                           |
+------------------+-----------------------------+
                   |
+------------------v-----------------------------+
|  AI Sandbox (Phase 21)                         |
|   - per-capability isolation                    |
|   - no DB write privilege                       |
|   - no adapter call privilege                   |
|   - explainability metadata required             |
+------------------+-----------------------------+
                   |
+------------------v-----------------------------+
|  Consumer routes (existing clinical/financial) |
|   - call AI capability                          |
|   - reject outputs missing metadata             |
|   - never auto-act on AI output                 |
+------------------+-----------------------------+
                   |
+------------------v-----------------------------+
|  Audit chain (existing, AI integration Phase 21)|
+------------------------------------------------+
```

## Capability Registry (recap)

A row per capability:

- `capability_id` — slug
- `version` — semantic
- `model_id` — opaque pointer to model artifact
- `authority_class` — `advisory` (only)
- `scope` — `tenant` | `aggregate`
- `inputs_schema` — JSON Schema
- `outputs_schema` — JSON Schema (must include explainability fields)
- `kill_switch_flag` — env var or DB flag
- `governance_record` — link to IRB-AI approval
- `status` — `active` | `suspended` | `retired`

Capabilities not present → not callable. There is no "stealth mode".

## Sandbox

Each AI capability runs inside a sandbox with:

- read-only DB credentials (or none, if it accepts inputs only)
- no outbound HTTP except to its model server (allowlisted)
- no filesystem write outside scratch
- bounded CPU + memory
- timeout

A sandbox escape is a SEV-1 incident.

## Authority Class

Only `advisory` is permitted. The platform's `assistive` and `automated`
authority classes are reserved for future approval and currently inert.

`advisory`:

- output is presented to a clinician or operator
- output never directly mutates clinical state
- the human user explicitly accepts or rejects
- acceptance is logged

## Scope

- `tenant` — all inputs come from a single tenant; outputs return to that
  tenant; no cross-tenant data observation.
- `aggregate` — runs over the analytical perimeter (Phase 20); never sees
  raw identifiers.

Cross-tenant scope outside `aggregate` is forbidden.

## Kill Switch

Each capability has a kill switch. Triggering it:

- immediately rejects new invocations of the capability
- audits the trigger
- preserves in-flight outputs for review (does not erase)

## Lifecycle

```
[propose] -> [IRB-AI review] -> [sandbox build] -> [evaluation]
   -> [approval gate] -> [staged rollout] -> [active]
   -> [monitoring] -> [retire / suspend]
```

Each stage is signed by IRB-AI minutes.

## Integration with Existing AI Code

The existing `backend/app/ai/` and `services/ai` packages contain clinical
AI scaffolding. The Phase 21 framework wraps them; existing code paths
that already enforce fail-closed behaviour are honoured.

## Out of Scope (Phase 21 deferred coding)

- The capability registry table or service
- The sandbox runtime
- The consumer-route metadata-rejection logic
- The kill-switch DB flag
