---
id: RUNBOOK-000006
type: runbook
title: production
version: "1.0"
created: "2026-08-05"
status: verified
kind: production
---

# RUNBOOK-000006: production

## Purpose
Operate the production procedure reliably and repeatably.

## Prerequisites
- Access to the environment and its health endpoints
- Verified snapshot or backup when applicable

## Procedure
1. Verify the deployed version and environment
2. Confirm all health components pass
3. Check secrets, certificates, and expiry dates
4. Review recent logs for anomalies
5. Confirm backup freshness
6. Document the production state

## Context
Executed refactor mission 'Record knowledge from a completed engineering mission' end-to-end through the Orchestrator pipeline (status complete)

## Success Criteria
All health components pass; service state matches the runbook goal.
