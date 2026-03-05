
"use strict";

/*
==================================================
NHOP KERNEL AWARENESS (SOVEREIGN EDITION)
Temporal + Behavioral system intelligence
==================================================
*/

const extensions = new Map();

const STATES = {
    HEALTHY: "healthy",
    UNSTABLE: "unstable",
    DEGRADED: "degraded",
    QUARANTINED: "quarantined"
};

/* ------------------------------------------------
PROFILE
------------------------------------------------ */
function ensureProfile(name) {

    if (!extensions.has(name)) {

        extensions.set(name, {
            name,
            starts: 0,
            failures: [],
            events: 0,
            state: STATES.HEALTHY,
            healthScore: 100,
            lastSeen: Date.now()
        });
    }

    return extensions.get(name);
}

/* ------------------------------------------------
TIME WINDOW HELPERS
------------------------------------------------ */
function recentFailures(profile, windowMs = 30000) {

    const now = Date.now();

    return profile.failures.filter(
        t => now - t < windowMs
    ).length;
}

/* ------------------------------------------------
HEALTH MODEL
------------------------------------------------ */
function recalcHealth(profile) {

    const recent = recentFailures(profile);

    let score = 100 - (recent * 15);

    const mem = process.memoryUsage().heapUsed;

    if (mem > 700_000_000)
        score -= 10;

    profile.healthScore = Math.max(0, score);

    updateState(profile);
}

/* ------------------------------------------------
STATE MACHINE
------------------------------------------------ */
function updateState(profile) {

    if (profile.healthScore < 30)
        profile.state = STATES.QUARANTINED;
    else if (profile.healthScore < 50)
        profile.state = STATES.DEGRADED;
    else if (profile.healthScore < 80)
        profile.state = STATES.UNSTABLE;
    else
        profile.state = STATES.HEALTHY;
}

/* ------------------------------------------------
EVENTS
------------------------------------------------ */
function recordStart(name) {

    const p = ensureProfile(name);
    p.starts++;
    p.lastSeen = Date.now();
}

function recordFailure(name) {

    const p = ensureProfile(name);

    p.failures.push(Date.now());
    p.lastSeen = Date.now();

    recalcHealth(p);
}

function recordEvent(name) {

    const p = ensureProfile(name);
    p.events++;
    p.lastSeen = Date.now();
}

/* ------------------------------------------------
SYSTEM HEALTH
------------------------------------------------ */
function systemHealth() {

    let total = 0;
    let count = 0;

    for (const p of extensions.values()) {
        total += p.healthScore;
        count++;
    }

    return count ? total / count : 100;
}

/* ------------------------------------------------
ANOMALY DETECTOR
------------------------------------------------ */
function detectAnomalies() {

    const alerts = [];

    for (const p of extensions.values()) {

        if (p.state === STATES.QUARANTINED)
            alerts.push({
                type: "quarantine_required",
                extension: p.name
            });

        if (recentFailures(p) > 5)
            alerts.push({
                type: "failure_storm",
                extension: p.name
            });
    }

    return alerts;
}

/* ------------------------------------------------
API
------------------------------------------------ */
module.exports = {

    STATES,

    recordStart,
    recordFailure,
    recordEvent,

    systemHealth,
    detectAnomalies,

    getProfiles: () =>
        Array.from(extensions.values())
};
