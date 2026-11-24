# Language Pack Rollback Guide

## Lifecycle states

`NOT_INSTALLED`, `AVAILABLE`, `QUEUED`, `DOWNLOADING`, `VERIFYING`, `INSTALLING`, `READY`, `UPDATE_AVAILABLE`, `FAILED`, `ROLLBACK_REQUIRED`, `DISABLED`.

`READY` is reached only after verification and installation. No state may bypass verification.

## Automatic failure behavior

- A failed verification before installation leaves the current active version untouched.
- The active version is changed only after all files are written and fsynced.
- If an update fails, the previously active pack remains active and its files are not deleted.
- A first-time installation failure sets state to `FAILED`.

## Manual rollback

`PackManager.rollback(language_id)` activates the stored `previous_version` and sets state to `READY`. Use it only when the operator intends to revert to the version that preceded the current active version.

```python
from app.localization.language_registry import LanguageRegistry
from app.localization.pack_manager import PackManager

manager = PackManager(root, LanguageRegistry.load())
print(manager.active_version("fa"), manager._language_state("fa").get("previous_version"))
manager.rollback("fa")
```

## Disabling a language

1. Set `is_active: false` in `shared/guls/language_registry.json` for a blocked language, or disable distribution for a withdrawn pack.
2. Leave installed files intact for audit and rollback.
3. Preference validation then resolves to English.

Never edit an installed catalog in place. Never delete a previous version before the replacement has been proven stable.

## Recovery checklist

1. Confirm `GULS_PACK_PUBLIC_KEY_PATH` points to the trusted key.
2. Confirm `GULS_ALLOW_SYNTHETIC_PACKS=0`.
3. Inspect lifecycle state and versions.
4. Roll back or reinstall a signed known-good pack.
5. Confirm the effective language through `PUT /api/v1/users/me/preferences/language`.
6. Record the incident and approval evidence.

## Test evidence

`test_update_and_rollback_preserve_previous_pack` verifies that a failed update leaves the previously active version ready. `test_downgrade_is_rejected` verifies that older packs cannot be activated. `test_explicit_state_transition_is_validated` verifies the state machine.
