# GULA AI Kernel — Engine Contract

> Phase 3 (GULA-KERNEL-001).

Every engine running inside the Kernel MUST declare a 16-field contract. No
undocumented engine behavior is permitted; all engine behavior must be
describable by, and verifiable against, the contract below.

## Mandatory Contract Fields

| # | Field | Description |
|---|---|---|
| 1 | `inputs` | What the engine consumes |
| 2 | `outputs` | What the engine produces |
| 3 | `events` | Events the engine emits |
| 4 | `errors` | Errors the engine may raise/report |
| 5 | `artifacts` | Artifacts the engine produces |
| 6 | `ownership` | Who owns the engine's decisions |
| 7 | `dependencies` | Engines/resources this engine depends on |
| 8 | `health` | Engine health indicator |
| 9 | `progress` | Completion progress indicator |
| 10 | `checkpoint` | Checkpoint/restore capability |
| 11 | `capabilities` | What the engine is allowed to do |
| 12 | `resources` | Resource budget (time/files/memory) |
| 13 | `timeout` | Execution timeout |
| 14 | `retry` | Retry policy |
| 15 | `version` | Contract version |
| 16 | `status` | Current lifecycle state (idle/running/done/failed) |

## Enforcement

The Kernel validates every engine contract with
`scripts/kernel/contract.py`:

```python
from scripts.kernel import contract

violations = contract.validate_engines()
```

`python scripts/kernel.py check` exits non-zero when any engine's contract is
incomplete or conformance fails.

## Registered Engines

`scripts/kernel/core.py::ENGINE_REGISTRY` declares the seven engines:
Architect, Orchestrator, Reviewer, Builder, Deployer, Learner, Optimizer.
Engines added in the future MUST declare all sixteen fields.

## Autonomy

Engine autonomy is bounded by Phase 2 levels (L0 read-only → L8 dangerous).
The Kernel's maximum autonomous level is **L5**; anything above always requires
human approval (see `scripts/kernel/autonomy.py` and the `ALWAYS_APPROVE` set).
