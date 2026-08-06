# DOMAIN_CONTRACTS.md

> **PROGRAM-STABLE-004** — Cross-Domain Contracts (Phase 4).
> Generated: 2026-08-06T04:28:40+00:00

## The Rule

Direct access between Domains is forbidden. A Domain never imports another Domain's modules and never reads another Domain's database. The ONLY legal communication channels are versioned contracts.

## Allowed Channels

| Channel | Kind | Used for |
|---|---|---|
| Public REST APIs | rest | Synchronous request/response |
| FHIR APIs | fhir | FHIR R4 resource exchange |
| HL7 | hl7 | HL7 messaging with national/legacy systems |
| Events | event | Asynchronous decoupled notification |
| Contracts | contract | Documented, versioned service agreements |

## Contract Rules

1. Every contract is **versioned** (SemVer).
2. Every contract is **documented** (documentation_url is mandatory).
3. Every contract is **tested** (endpoint is wired to a tested surface).
4. Every contract spans **two distinct Domains** (provider + consumer).
5. A contract may be consumed only while **published**.
6. **Backward compatibility is never broken** — a breaking change requires a MAJOR version and explicit certification.

## Cross-Domain Gateway

`CrossDomainGateway` is the single enforcement point. A consumer without a published contract to the provider over the requested channel is denied.

## Contract Enforcement

The `ContractRegistry` rejects unversioned, undocumented, untested, or self-referential contracts at registration time. The lifecycle audit records every contract change.

## Registry

No cross-domain contracts are published yet. Every current integration travels through Shared Core (FHIR Engine, Event Bus, API Gateway). New contracts must follow the rules above.

## Isolation Statement

The isolation scan confirms **zero cross-domain imports** and **zero cross-domain table overlaps** across all 11 Domains.
