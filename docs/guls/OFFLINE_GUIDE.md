# Offline Language Pack Guide

## Availability model

Installed packs are local data. The runtime reads catalogs from `GULS_LOCAL_PACK_ROOT/packs/{language_id}/{version}/catalogs/`. The delivery API is not consulted during normal rendering. If the API is unavailable, English and already-installed languages continue to work.

## Download behavior

1. The user explicitly selects a language.
2. English remains the effective language while the pack is downloaded, verified, and installed.
3. Download progress is tracked as bytes and a 0–1 fraction.
4. Interrupted downloads remain resumable; partial data is never installed.
5. Data saver, metered network, roaming, and available-storage checks are enforced before authorization.
6. Short-lived content URLs expire after 300 seconds.

## Offline installation

For a pre-approved offline artifact:

1. Copy the signed `.zip` to the target environment through an approved channel.
2. Configure `GULS_PACK_PUBLIC_KEY_PATH` with the trusted public key.
3. Set `GULS_ALLOW_SYNTHETIC_PACKS=0` in production.
4. Call `PackManager.install(language_id, pack_bytes)` from a trusted maintenance job.
5. Confirm lifecycle state is `READY` and `active_version` is expected.

No network access is required by the verifier or installer.

## Platform notes

- Backend/local filesystem: implemented and tested in this change.
- Web: Service Worker/IndexedDB pack caching is not implemented in this change. Existing `vite-plugin-pwa` can host a future adapter; no offline cache claim is made.
- Android/iOS/desktop: no dynamic-pack storage is implemented in this change. Existing Android string resources remain static.

## Failure behavior

| Condition | Result |
|---|---|
| Partial download | `DOWNLOADING`, resumable; effective language remains English |
| Verification failure | `FAILED` (or previous active version retained on update failure) |
| Delivery API offline | Already installed languages continue; new selections remain English |
| Missing translation key | English fallback; empty display if absent in English; never raw key |

## Data hygiene

Packs contain no patient data. Download metadata must not include PHI. Content responses use `Cache-Control: no-store`.
