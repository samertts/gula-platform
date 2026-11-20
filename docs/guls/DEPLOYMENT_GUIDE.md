# GULS Deployment Guide

## Scope

This guide covers application configuration for the GULS additive foundation. It does not authorize production deployment. No production database, CDN, or deployment was accessed by this program.

## Required configuration

| Variable | Purpose | Production value |
|---|---|---|
| `GULS_REGISTRY_PATH` | Optional registry override | Usually unset; default is `shared/guls/language_registry.json` |
| `GULS_PACK_PUBLIC_KEY_PATH` | Trusted Ed25519 public key | Path to protected key file |
| `GULS_PACK_PUBLIC_KEY_B64` | Alternative inline public key | Use only from secret manager |
| `GULS_LOCAL_PACK_ROOT` | Local pack/state directory | Writable persistent path per instance or shared volume |
| `GULS_PACK_DIST_ROOT` | Directory of signed `.zip` artifacts | Read-only mount or release artifact location |
| `GULS_ALLOW_SYNTHETIC_PACKS` | Enables `synthetic_test_only` packs | Must be `0` in production |

## Wiring

`backend/app/factory.py` includes `app.routes.localization.router`, which mounts:

- `/api/v1/localization/*`
- `/api/v1/users/me/preferences/language`

## Release steps

1. Verify registry and pack JSON schemas.
2. Build packs with `tools/guls_sign_pack.py` using a protected private key.
3. Run backend localization tests and frontend GULS tests.
4. Confirm no `synthetic_test_only` artifact is in the production distribution root.
5. Deploy code and configuration.
6. Call `GET /api/v1/localization/languages` and verify lifecycle states.
7. Confirm a synthetic pack is rejected in production configuration.
8. Confirm English remains effective when a non-ready language is selected.

## Operational checks

- Monitor state transitions through `GET /api/v1/localization/downloads/{download_id}` and local state.
- Keep `GULS_LOCAL_PACK_ROOT` backed up if rollback capability is required.
- Do not modify installed catalogs manually.
- Rotate signing keys by publishing a new key ID and re-signing packs; the registry/pack manifest records the signer key ID. See `SIGNING_KEY_MANAGEMENT.md` for generation, protection, rotation, and revocation procedure.

## Unsupported in this release

- Web Service Worker/IndexedDB pack caching.
- Mobile/desktop dynamic pack storage.
- Font deployment and licensing verification.
- Production clinical translations.
