# 08 — Minimal Sovereign Build Core (MSBC)

## 8.1 Purpose

The MSBC is the smallest deployable unit that:

- Hosts a single Regional Sovereign Node (RSN) end-to-end.
- Meets H1–H5 (P99 < 2 s, < 2% time violations, < 3% bypass, 72 h
  offline survival, full auditability).
- Can be air-shipped, racked, and brought online by a small team
  (≤ 6 engineers) within 96 hours.

It is the reference design for region-1 first roll-out and for
disaster-displaced "rapid RSN" deployments.

## 8.2 Bill of materials (per MSBC)

| Layer | Item | Spec | Qty |
|-------|------|------|-----|
| Compute | App nodes (mixed clinical + critical + governance) | 32-core EPYC, 256 GB RAM, dual 25 GbE, 2× 3.84 TB NVMe (mirrored) | 6 |
| Compute | DB nodes (PG primary + sync replica + async) | 32-core EPYC, 512 GB RAM, dual 25 GbE, 4× 7.68 TB NVMe (RAID-10) | 3 |
| Compute | NATS / Redis nodes | 16-core, 64 GB, 2× 1.92 TB NVMe | 3 |
| Compute | Audit archiver | 16-core, 128 GB, 8× 16 TB HDD (WORM-locked) + 2× 3.84 TB NVMe | 1 |
| Network | ToR switches, 25/100 GbE | redundant pair | 2 |
| Network | Out-of-band (OOB) | redundant | 1 |
| Security | HSM (sovereign root) | FIPS 140-2 L3 | 2 |
| Time | GPS receiver + Rb oscillator + chrony peers | multi-constellation | 2 |
| Power | UPS + ATS | N+1 | — |
| Cooling | rack-level | N+1 | — |
| Peripheral | Air-gapped backup tape library | LTO-9 WORM | 1 |
| Peripheral | Sealed offline media for paper-fallback | printed forms, sealed | quarterly refresh |

Approx footprint: 1 rack + 1 OOB rack + HSM cabinet.

## 8.3 Software stack

- OS: hardened Linux (sovereign distribution; CIS L1+).
- Containers: containerd + Kubernetes (k0s for simplicity) — single
  cluster spanning the 6 app nodes; PG/NATS/Redis run on dedicated
  bare-metal nodes outside Kubernetes (with NodePort in-cluster only
  for app discovery).
- Service mesh: Cilium + SPIRE.
- Storage: local NVMe via Patroni for PG; MinIO (erasure-coded) for
  objects.
- Observability: Prometheus + Loki + Tempo + Alertmanager (regional
  scope; Mimir long-term off-region).
- Secrets: Vault, HSM-sealed.
- Policy: OPA + Cedar; bundle pulled from `policy-authority` mirror.

## 8.4 Services to deploy

Critical Plane: `triage-engine`, `emergency-router`, `dispatch-bridge`,
`mcom-controller`, `priority-scheduler`, `decision-stabilizer`,
`time-authority-agent`.

Clinical Plane: `mpi`, `emr-core`, `referral-engine`,
`encounter-orchestrator`, `order-engine`, `result-engine`,
`consent-service`, `notification-fabric`.

Governance Plane (regional mirror): `policy-mirror`, `time-authority-agent`,
`audit-ledger`, `ai-governance` (read-only mirror; can run shadow
inferences locally during partition only on previously-signed-off
models), `clinical-governance` (read-only rule mirror), `integrity-engine`,
`validation-engine` (sampling; review queue can be local; final
clinical board decisions go to NFT after heal).

Cross-cutting: Sovereign Gateway (regional ingress), `sndhs-sdk`
(library — no service), Contract Registry mirror.

## 8.5 Deployment order

```
Day 0  — Power, network, OOB up. Time authority up. HSM initialised.
Day 1  — DB cluster bootstrapped; Patroni quorum verified.
         NATS + Redis bootstrapped.
Day 2  — Service mesh + SPIRE; identities issued.
         Vault sealed/unsealed via HSM. Policy mirror loaded.
Day 3  — Critical Plane deployed; smoke + chaos.
         Clinical Plane deployed; smoke + chaos.
Day 4  — Governance mirror deployed; audit chain initialised.
         Sovereign Gateway up; gateway key issued by Ministry root.
         End-to-end synthetic patient journey passes.
Day 5  — DR drill: kill primary DB; verify failover < 30 s.
         Partition drill: cut uplink; verify 4 h offline ops.
         Audit chain verifier passes.
Day 6  — MoH acceptance test (synthetic + 1 day shadow on real load).
         Cutover in shadow mode (T-shadow, 2 weeks).
Day 20+ — Production cutover after sign-off.
```

## 8.6 Configuration baselines (excerpt)

- `policy_freeze_after_hours = 72` (after which RSN flips to freeze
  bundle and demands refresh).
- `time_drift_safe_mode_ms = 500`.
- `db_pool_per_app = (16 + 32)`; with 6 app nodes × 2 services that
  hit DB, total ≤ 0.6 × `max_connections`.
- `nats_max_payload = 1 MiB`; clinical-event soft cap 64 KiB.
- `priority_reservation = { P0: 0.30, P1: 0.30, P2: 0.30, P3: 0.10 }`.
- `mcom_default_level = 1`; safe-mode override to 2.
- `audit_chain_checkpoint_interval_minutes = 60`.

## 8.7 Acceptance gates

The MSBC passes only if **all** the following pass on the deployed
hardware:

| Gate | Test | Threshold |
|------|------|-----------|
| G1 | Synthetic golden-path: dispatch → vitals → triage → orders → admit | P99 ≤ 1.6 s end-to-end |
| G2 | Critical-encounter declaration + bundle apply | P99 ≤ 800 ms |
| G3 | Triage assess | P99 ≤ 80 ms |
| G4 | Sustained load 10× baseline TPS | < 2% time violations, P0 SLOs intact |
| G5 | Network partition for 72 h (synthetic load) | All P0/P1 functions operational; audit chain intact |
| G6 | Heal & sync after 72 h partition | Reconciliation completes ≤ 2 h; manual queue ≤ 1% of mutations |
| G7 | DR: lose primary DB | Failover ≤ 30 s; no committed write lost |
| G8 | DR: lose entire RSN | Rebuild from peer event log ≤ 4 h |
| G9 | Security: red-team scenario set | Zero P0 escalations, zero plaintext PHI off-rack |
| G10 | TLA+ model checks | All specs PASS |
| G11 | Clinical war-game (`15-wargames.md` set A) | Pass criteria all met |

Failure of any gate blocks production cutover.

## 8.8 Cost & supportability constraints

- Total MSBC cost cap (compute + storage + network + HSM + tape): set
  by Ministry procurement — the design is to fit within an envelope
  that allows two MSBCs per region (primary + DR-warm).
- Spares kit shipped with each MSBC: SSDs (10%), NICs, PSUs, HSM
  spare, two laptops with sealed offline runbooks.
- 24×7 on-site engineering presence for 90 days post-cutover; 24×7
  remote thereafter; quarterly on-site DR drills.

## 8.9 What MSBC explicitly does NOT include

- National federation tier (NFT) — that is its own separate build.
- Cross-region MPI federation — accessed via NFT; MSBC ships with the
  client and a regional MPI sufficient for autonomy.
- Public health analytics aggregation — handled at NFT.
- AI training infrastructure — done off-region; only inference (frozen
  artefacts) runs in-region.

## 8.10 Day-2 operations (per MSBC)

- Quarterly rotation of HSM operators; biennial root rotation.
- Monthly chaos suite + restore drill.
- Weekly audit-chain verifier across the entire chain.
- Monthly safe-mode rehearsal (cut external time + policy uplinks for
  2 hours).
- Quarterly war-game replay (`15-wargames.md`).
- Continuous policy bundle pull; canary on non-production region first.
