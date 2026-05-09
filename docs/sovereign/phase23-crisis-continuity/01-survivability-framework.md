# Phase 23-01 — Crisis Survivability Framework

## Crisis Classes

| Class | Examples | Response posture |
|-------|----------|------------------|
| Cyber | Ransomware, intrusion, DDoS | Isolate, rotate, recover from cold archive |
| Connectivity | Internet outage, regional ISP failure | Edge-first operation; queued sync |
| Power | Regional power loss | Edge battery + paper fallback |
| Datacenter | Tier-1 site loss | Tier-2 cutover (RB-09) |
| Mass-displacement | Population movement, refugee flows | Mobile collection points; identity reconciliation buffered |
| Conflict | War conditions | All of the above; sovereign comms fallback |

## Survivability Tenets

1. **Edge-first** in crisis: the province continues regardless of central
   reachability.
2. **Audit never paused.** Audit chain continues at the level the system
   operates at; replay reconciles on reconnect.
3. **No silent degradation** of clinical-critical workflows. Degraded
   modes are explicit, named, and visible.
4. **Paper-fallback** is real, signed, and reconcilable.
5. **Sovereign comms fallback** (SMS/USSD) for critical-result delivery
   when primary comms unavailable.

## Survivability Modes (recap from Phase 17 ladder)

1. GREEN — full operation
2. YELLOW — slow DB; non-clinical writes feature-gated
3. RED — DB circuit open; reads continue; clinical writes prefer replica
4. CRISIS — central platform unreachable; provincial / edge mode
5. PAPER — full fallback; later reconciled

The mode is **monotonic descent** during crisis; recovery is explicit.

## Crisis Communication Channels

- Primary: ALERT_WEBHOOK_URL (Slack/Discord/Telegram)
- Secondary: email
- Tertiary: SMS/USSD via telco adapter
- Quaternary: voice calls per on-call playbook

Each channel has a known degradation profile; the team rehearses the
ladder annually.

## Decision Authority in Crisis

- IC + ops chief authorise mode transitions.
- Clinical liaison must be present for any decision affecting clinical
  workflows.
- Regulator liaison engaged within an SLA per contract for SEV-1.

## Crisis Mode Audit

When the system enters CRISIS mode:

- A `crisis.entered` audit row is written at every operating level.
- Subsequent audit rows carry a `crisis_marker` so they can be later
  identified for reconciliation.
- On exit, a `crisis.exited` row is written.

## Recovery Discipline

- No bulk un-marking of crisis events; each is reviewed in reconciliation.
- Reconciliation events specific to crisis are governance-tracked under
  Phase 19.
- A post-crisis review identifies (a) what worked, (b) what failed, (c)
  doctrinal updates.

## Limitations

- This phase does not solve "what if the entire datacentre is destroyed".
  That is Tier-3 cold archive plus contingency at the sovereign-cloud /
  off-shore level.
- This phase does not solve "what if every operator is unavailable". That
  is operator continuity planning, run by the institution.
