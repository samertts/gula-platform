# GULA Governor — Engine Communication Contract

> Phase 10 (GULA-GOVERNOR-001).

Every governed engine must expose a standardized communication contract.
No direct undocumented communication is permitted. All engine-to-engine
communication must flow through the contract fields below.

## Mandatory Contract Fields

| Field | Description |
|---|---|
| `inputs` | What the engine consumes |
| `outputs` | What the engine produces |
| `status` | Current lifecycle state (idle/running/done/failed) |
| `events` | Events the engine emits |
| `progress` | Completion progress indicator |
| `health` | Engine health indicator |
| `errors` | Errors the engine may raise/report |
| `artifacts` | Artifacts the engine produces |
| `dependencies` | Engines this engine depends on |
| `completion` | What signals completion |

## Enforcement

The Governor validates every engine contract with
`scripts/governor/engine_contract.py`:

```python
from scripts.governor import authority, engine_contract

violations = engine_contract.validate_all_engines(authority.ENGINE_REGISTRY)
```

`python scripts/governor.py check` exits non-zero when any engine's contract
is incomplete.

## Registered Engines

All engines in `scripts/governor/core.py::ENGINE_REGISTRY` (architect,
orchestrator, reviewer, builder, deployer, learner, optimizer) declare the
full contract. Engines added in the future MUST declare all ten fields.
