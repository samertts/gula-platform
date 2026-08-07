"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44.

Source: `backend/app/national/workflow_runtime/application/service.py`
(moved by `git mv` in Commit 3.6).

This file was the finding's evidence: **0 bytes** at archive time. Every
`/national/workflows/*` handler's `_get_service()` lazy import
(`WorkflowRuntimeService`) therefore raised ImportError, making the entire
wired surface return HTTP 500. Archived per ADR-028 (archive-first, reversible
via a single `git revert`). Canonical provider:
`backend/app/workflows` + `backend/app/identity/workflows/routes.py`.
"""
