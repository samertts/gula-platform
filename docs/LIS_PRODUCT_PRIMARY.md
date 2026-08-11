# GULA LIS — Primary Product Contract

## Purpose

GULA Platform is now organized around one primary product: **GULA LIS**, a Laboratory Information System for medical laboratories and the clinical teams that depend on them. The product is Arabic-first, supports English, and treats Arabic RTL as a complete interface direction rather than a translation-only feature.

GULA LIS is not a collection of disconnected applications. It is one product delivered through adaptive clients: GULA Web, GULA Android, and GULA iOS. Each client shares the account, organization context, workspace discovery, permission catalog, clinical state machines, audit policy, and API contracts. A desktop client is optional and must be justified by a documented operational requirement.

## Primary operating scope

The first complete operating workspace is **Laboratory Workspace**. Its workflow is intentionally explicit:

| Area | Primary responsibility |
|---|---|
| Identity and context | Unified account, role, institution, laboratory, language, and workspace access |
| Patients | Patient identity, medical record context, scoped search, and controlled updates |
| Lab orders | Order creation, tests, priority, status transitions, and physician ownership |
| Specimens | Collection, receipt, barcode chain of custody, verification, processing, rejection, and completion |
| Results | Entry only after sample verification, review by an authorized senior role, and controlled release |
| Safety | Critical alerts, targeted notifications, inbox, tasks, approvals, messages, and audit events |
| Management | Laboratory and user administration, reports, and organization-scoped analytics |

## Roles and authorization

The product recognizes five primary roles: patient, laboratory staff, physician, institution administrator, and system administrator. The server must evaluate **role + workspace + permission + organization context** for every protected operation. UI visibility is not a security boundary.

Authorization decisions must reject cross-organization access, cross-laboratory access where a laboratory scope is assigned, patient access outside the linked account, and physician access to orders not owned by that physician. Denied operations produce an audit record with the actor, entity, action, reason, and outcome.

## Clinical safety contract

Clinical writes are versioned and must reject stale versions. State transitions are finite and explicit. A result cannot be entered unless its sample is verified or in the allowed processing state. Results cannot be approved without an authorized reviewing role, and released results cannot be overwritten. Invalid transitions are hard failures and are recorded as denied or failed audit events.

## Shared GULA App Shell

The App Shell is built once and reused by every workspace. It contains the unified account identity, organization context, workspace switcher, language switcher, global search, inbox, tasks, notifications, privacy, security, and settings. Laboratory Workspace is the first operational workspace; future clinical workspaces must plug into this shell without creating separate accounts or conflicting permission models.

## Web and repository relationship

The managed web project under `/home/ubuntu/gula-web-suite` is the active product surface for the GULA LIS web experience. This repository remains the canonical platform repository for backend services, shared contracts, native mobile clients, infrastructure, and product documentation. Changes that affect roles, permissions, clinical states, data contracts, or public product positioning must be reflected in both locations before a release candidate is approved.

The public domain `https://www.gula-platform.org/` should be updated from the approved managed web checkpoint through the platform's publishing flow. The source repository can be synchronized independently, but production publication must remain an explicit release action with a reviewed checkpoint.

## Release acceptance

A release candidate is not considered LIS-ready unless it has passing type checks and unit tests, a reviewed migration, server-side authorization coverage, audit coverage for protected writes, Arabic and English UI verification, RTL verification, and an explicit separation between real operational data and empty states. No patient data, test results, reviews, or testimonials may be fabricated for demonstration.
