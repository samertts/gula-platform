# 09 — Failure Scenarios & Response Playbooks

Each scenario lists: detection signals, automated response, human
runbook, escalation, and post-incident actions. Every action in this
chapter has a corresponding pre-authorised runbook artefact in
`runbooks/` (signed; runtime verifies signature before execution).

## 9.1 Full national network outage

**Scope:** all RSN ↔ NFT links down; RSNs may also be partitioned from
each other.

### Detection
- NFT heartbeat loss across ≥ 50% of RSNs simultaneously.
- Ministry SoC alert + carrier acknowledgement.

### Automated response
- Each RSN flips to safe-mode (see `05-offline-sync.md` §5.6).
- MCOM auto-raised to **2** (advisory). MCOM-3+ requires human authority.
- AI advisories suspended.
- Background analytics paused.
- Sovereign Gateway public APIs serve a "degraded operations" banner;
  GULA shows read-only state for clinical surfaces.
- Outbound notifications throttled to P0/P1 only.

### Human runbook
- Ministry duty officer notified (P0 page).
- Each regional director confirms RSN health locally.
- Paper-fallback is **not** activated unless MCOM-4 declared.
- Hourly status broadcast on out-of-band radio + sat link.

### Recovery
- Carriers restore links incrementally; RSNs re-anchor time, pull
  policy bundle, replay events, validate audit chain checkpoints.
- Reconciliation order: audit chain → MPI updates → encounter/referral
  → orders/results → analytics.
- All locally accepted writes during outage are visible nationally
  within 4 h of restored links (SLO).

### Post-incident
- Verify audit chain across the partition window; sign-off by
  ministry CISO.
- Quantify time-violation rate during outage (target H2 < 2%).

---

## 9.2 Partial node failure (single RSN node down)

### Detection
- Patroni leader lost / replica lost.
- App-pool unhealthy in cluster.
- NATS RAFT quorum at risk.

### Automated response
- Patroni promotes sync replica; old leader fenced.
- App pool re-balances; failed node cordoned.
- NATS RAFT continues if quorum survives.
- Auto-repair engine attempts pool recycle, GC, reconnects.

### Human runbook
- On-call SRE diagnoses hardware (NIC / NVMe / PSU).
- Replace node from hot spares; rebuild & rejoin.
- Post-rejoin verify replication caught up; verify audit chain
  unbroken.

### Escalation
- If two of three DB nodes down → P0; consider degraded read-only
  mode while rebuilding.

---

## 9.3 Complete RSN loss (datacentre destroyed)

### Detection
- Loss of all heartbeats from RSN.
- Physical confirmation from regional authority.

### Automated response
- NFT flags affected `region_id` as `OFFLINE`.
- Adjacent RSNs accept emergency proposals for the offline region's
  patients (cross-region read-only by default; emergency writes
  permitted under MCOM-3 grant).
- Federation re-routes referrals away from the offline region.

### Human runbook
- Activate DR-warm MSBC for the region (target RTO ≤ 4 h to
  read-only, ≤ 24 h to full service).
- Restore from the most recent peer event log + cold archive (audit
  chain rebuilt from local WORM tape if surviving; otherwise from
  national chain checkpoints + adjacent RSN logs).
- All restored encounters are flagged `restored=true` on a
  `restoration_manifest` for clinical review.

### Escalation
- Ministry crisis cell convened.
- Public communications coordinated through Ministry comms.

---

## 9.4 MCOM-3 (mass casualty)

### Detection
- Manual declaration by regional director or ministry duty officer.
- Auto-trigger: ≥ N MCI calls within window OR explicit civil
  defence declaration.

### Automated response
- Switch triage protocol to START/SALT field triage.
- Re-route ambulances to designated mass-casualty hubs.
- Lock non-clinical write surfaces (billing, registration cleanup,
  admin operations).
- Reserve 50% of P0/P1 reservation pool to MCI flows.
- Hold AI advisories; pre-approved automation only.

### Human runbook
- ED commanders activate triage tags, surge staffing, and pre-printed
  mass-casualty bundles.
- Hospital incident command system (HICS) invoked.
- Inter-region transfers prioritised; NFT brokers acceptance.

### Escalation to MCOM-4
- See §9.5.

### De-escalation
- Regional director + ministry duty officer signature required.
- 60 min lock-window prevents flapping.

---

## 9.5 MCOM-4 (catastrophic / national emergency)

### Detection
- Ministry declaration. Cabinet-level signature.

### Automated response
- Broadcast policy switch to "freeze bundle".
- Sever non-essential federation; RSNs operate fully autonomously.
- AI advisories disabled regardless of promotion status.
- Public projection stream throttled; only ministry-approved feeds
  remain.
- Paper-fallback bundle pushed to printers; sealed packets opened on
  facility command order.
- All write APIs except a P0 safe-list disabled (vitals, declared
  death, transfers, MCI assignments).

### Human runbook
- Twice-daily ministry briefings; hourly RSN status reports.
- Field clinicians use paper; data entry catch-up batched after
  de-escalation, with a `data_provenance=paper_backfill` tag.

### Recovery
- Down-transition staged: 4 → 3 (re-enable referral writes), 3 → 2
  (re-enable scheduling), 2 → 1.
- Backfill of paper records audited; legal officer signs off
  reconciliation.

---

## 9.6 Data conflict (sync irreconcilable)

### Detection
- `manual-merge` queue grows beyond SLO.
- Conflicting authoritative writes on the same entity from two RSNs
  during a custody-handoff window.

### Automated response
- Entity locked read-only across all replicas.
- `gov.integrity.discrepancy.detected` event raised.
- All dependent decisions paused (e.g., a referral whose owning
  encounter is in conflict cannot transition).

### Human runbook
- Medical-records officer reviews both timelines via the manual-merge
  UI.
- Two-person rule for severity ≥ S2.
- Resolution emits a `sync.merge.applied` event and clears the lock.

### Post-incident
- Root cause logged in policy authority; resolver tuned if pattern
  recurs.

---

## 9.7 Human misuse (bypass, fraud, coercion)

### Detection
- Bypass-pattern score above threshold (`14-integrity.md`).
- Phantom/ghost actions detected.
- Anomalous override frequency.

### Automated response
- User enters **restricted mode**: write actions require co-signature
  by a peer of equal/higher role.
- Compliance and the user's supervisor notified.
- Writes performed during the suspect window are marked `under_review`
  in their audit annotation.

### Human runbook
- Compliance interview within 5 working days.
- If confirmed: account suspension; clinical care continuity preserved
  (records re-assigned to peer).
- If false positive: clear flag; tune detection threshold.

### Escalation
- Pattern across multiple users → criminal investigation referral.

---

## 9.8 Compromised credential / endpoint

### Detection
- IdP signal (impossible travel, anomalous device).
- Endpoint EDR alert.
- Anomalous query patterns.

### Automated response
- Session revoked; all decision tokens for that principal blacklisted.
- Device attestation revoked if rooted in TPM.
- Recent writes by the principal flagged `under_review`.
- Two-person rule applied retroactively for the suspect window (writes
  not yet propagated externally are quarantined).

### Human runbook
- Security IR team isolates the device.
- Re-issue credentials after attestation refresh.
- Compliance reviews the under_review writes; clears or rolls back.

---

## 9.9 Audit chain break

### Detection
- Verifier walks chain → discontinuity found.

### Automated response
- Writes on the affected segment paused.
- P0 alert.
- Chain break event recorded (in a separate, sealed channel).

### Human runbook
- Root cause: storage corruption, clock injection, malicious
  intervention.
- Restore from WORM mirror; re-anchor checkpoints to known-good
  national chain.
- Forensic analysis with auditors; report to ministry CISO.

### Recovery gating
- Writes resume only after dual sign-off (CISO + ministry duty
  officer).

---

## 9.10 Time authority desync

### Detection
- Drift > 100 ms vs national authority for > 30 s.
- GPS lock lost AND uplink lost (rb oscillator drifts predictably).

### Automated response
- `time_quality` flips to `DRIFTED` then `LOCAL_FALLBACK`.
- Writes accepted but tagged; UIs display a banner.
- Critical-plane decisions continue using monotonic clock; wall-clock
  features (e.g., billing windows) defer.

### Human runbook
- SRE swaps GPS antenna / receiver; verifies oscillator stability.
- Policy authority signs an exception for the affected window; all
  affected events are revalidated post-recovery.

---

## 9.11 AI regression / drift

### Detection
- Drift detector window crosses threshold.
- Latency anomaly.
- Clinical board flag.

### Automated response
- Two-of-three signals → AI circuit opens; advisory invisible.
- Shadow runs continue from frozen snapshot for analysis.

### Human runbook
- AI governance team reviews shadow vs ground-truth.
- Re-promote only after Clinical Board sign-off.

---

## 9.12 Storage corruption

### Detection
- Page checksum failures, replication mismatches.

### Automated response
- Affected partition isolated; reads served from healthy replica.

### Human runbook
- Restore partition from WAL + base backup; verify against event log.
- Run consistency-check sample.

---

## 9.13 Supply-chain compromise (signed image revoked)

### Detection
- Cosign verify failure at admission.
- Out-of-band notification from upstream.

### Automated response
- Affected pods drained; replaced with last-known-good image.
- Policy bundle marks the image hash as quarantined.

### Human runbook
- Build, sign, deploy a new image with the patched dependency.
- Rotate any keys handled by the compromised binary.

---

## 9.14 Escalation tree

```
Frontline operator / SRE
    │ unhandled in 15 min P0 / 1 h P1
    ▼
On-call regional engineer
    │ unhandled in 30 min P0 / 4 h P1
    ▼
Regional director + Ministry SoC duty engineer
    │ unhandled in 60 min P0 / 24 h P1
    ▼
Ministry CISO + duty cabinet officer
    │ unresolved or political/cross-border impact
    ▼
Minister of Health
```

Every escalation step writes to `gov.escalation.*` events for
auditability.

## 9.15 Communication runbook

- Internal: SoC dashboard + radio backup + signed status feed.
- Public: Ministry comms; SNDHS does not publish patient-impacting
  status itself.
- Clinical: facility intranet + SMS via notification fabric (P0
  channel), with paper backup for MCOM-3+.
