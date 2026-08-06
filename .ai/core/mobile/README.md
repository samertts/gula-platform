---
id: MOBILE-000001
type: mobile
title: "Mobile Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 70%
tags: [mobile, flutter, android, ios, bridge]
---

# Mobile Knowledge — Bridge Reference

## Stack
- Flutter (cross-platform)
- Android + iOS + Desktop targets
- GitHub Actions CI/CD for builds

## CI/CD Workflows
- `mobile-android.yml` — Android build (12KB)
- `mobile-ios.yml` — iOS build (11KB)
- `mobile-flutter-desktop.yml` — Desktop build (11KB)

## Build Actions
- `.github/actions/build-android/action.yml` — Android composite action
- `.github/actions/build-ios/action.yml` — iOS composite action
- `.github/actions/build-flutter/action.yml` — Flutter composite action

## Key Features
- Offline-first capability
- Push notifications
- Biometric authentication
- Role-based mobile access

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — Mobile decisions
- `docs/mobile/` — Mobile documentation (if exists)
