
"use strict";

/*
==================================================
NHOP EXTENSION QUARANTINE ENGINE (SOVEREIGN)
Kernel-authoritative self-healing isolation
==================================================
*/

const quarantined = new Map();

const MAX_RECOVERY_ATTEMPTS = 5;
const BASE_BACKOFF = 15000;

/* ------------------------------------------------
INTERNAL VALIDATION
------------------------------------------------ */
function assertKernel(kernel) {

    if (!kernel || typeof kernel.emitEvent !== "function")
        throw new Error(
            "[QUARANTINE] invalid kernel context"
        );
}

/* ------------------------------------------------
QUARANTINE
------------------------------------------------ */
function quarantineExtension(kernel, loader, name, reason) {

    assertKernel(kernel);

    if (quarantined.has(name))
        return;

    console.warn(
        `[QUARANTINE] Isolating extension → ${name}`
    );

    /* HARD ISOLATION */
    try {
        loader.unloadExtension?.(name);
    } catch {}

    quarantined.set(name, {
        name,
        reason,
        since: Date.now(),
        attempts: 0,
        nextAttempt: Date.now() + BASE_BACKOFF
    });

    kernel.emitEvent("kernel", "extension.quarantined", {
        name,
        reason
    });
}

/* ------------------------------------------------
RECOVERY ENGINE
------------------------------------------------ */
function attemptRecovery(kernel, loader) {

    assertKernel(kernel);

    const now = Date.now();

    for (const [name, q] of quarantined.entries()) {

        if (now < q.nextAttempt)
            continue;

        if (q.attempts >= MAX_RECOVERY_ATTEMPTS) {

            console.error(
                `[QUARANTINE] Permanent isolation → ${name}`
            );

            kernel.emitEvent(
                "kernel",
                "extension.permanently_disabled",
                { name }
            );

            quarantined.delete(name);
            continue;
        }

        q.attempts++;

        console.log(
            `[QUARANTINE] Recovery attempt ${q.attempts} → ${name}`
        );

        try {

            loader.reloadExtension(name);

            quarantined.delete(name);

            kernel.emitEvent(
                "kernel",
                "extension.recovered",
                { name }
            );

        } catch (err) {

            /* exponential backoff */
            q.nextAttempt =
                now + BASE_BACKOFF * (q.attempts + 1);

            console.warn(
                `[QUARANTINE] Recovery failed → ${name}`
            );
        }
    }
}

/* ------------------------------------------------
STATUS
------------------------------------------------ */
function getQuarantined() {
    return Array.from(quarantined.values());
}

module.exports = {
    quarantineExtension,
    attemptRecovery,
    getQuarantined
};
