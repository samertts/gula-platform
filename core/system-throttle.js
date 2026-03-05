
"use strict";

/*
==================================================
NHOP ADAPTIVE RUNTIME GOVERNOR (SOVEREIGN)
Kernel-aware self regulating controller
==================================================
*/

let governorRunning = false;
let monitorTimer = null;

const state = {
    pressure: "normal",
    lastLatency: 0,
    sandboxStrict: false,
    safeMode: false
};

/* ------------------------------------------------
BASE ENV
------------------------------------------------ */
function applyBaseTuning() {

    process.env.AUTOPILOT_THRESHOLD ??= "0.98";
    process.env.SANDBOX_STRICT ??= "false";

    syncState();
}

/* ------------------------------------------------
STATE SYNC
------------------------------------------------ */
function syncState() {
    state.sandboxStrict =
        process.env.SANDBOX_STRICT === "true";
}

/* ------------------------------------------------
PRESSURE MODEL
------------------------------------------------ */
function evaluatePressure(metrics = {}) {

    const latency = metrics.avgLatency || 0;
    const errors = metrics.errorRate || 0;
    const memory = process.memoryUsage().heapUsed;

    state.lastLatency = latency;

    if (errors > 0.2 || memory > 800_000_000)
        state.pressure = "critical";
    else if (latency > 900)
        state.pressure = "high";
    else
        state.pressure = "normal";
}

/* ------------------------------------------------
ADAPTIVE RESPONSE
------------------------------------------------ */
function applyAdaptiveRules() {

    switch (state.pressure) {

        case "critical":
            enableSafeMode();
            break;

        case "high":
            process.env.AUTOPILOT_THRESHOLD = "0.8";
            break;

        default:
            disableSafeMode();
            process.env.AUTOPILOT_THRESHOLD = "0.98";
    }

    syncState();
}

/* ------------------------------------------------
SAFE MODE
------------------------------------------------ */
function enableSafeMode() {

    if (state.safeMode) return;

    state.safeMode = true;

    process.env.SANDBOX_STRICT = "false";

    console.warn(
        "[GOVERNOR] SAFE MODE ACTIVATED"
    );
}

function disableSafeMode() {

    if (!state.safeMode) return;

    state.safeMode = false;

    console.log(
        "[GOVERNOR] SAFE MODE DISABLED"
    );
}

/* ------------------------------------------------
KERNEL BINDING
------------------------------------------------ */
function attachKernel(kernel) {

    if (!kernel?.onEvent) {
        console.warn("[GOVERNOR] Kernel not attached");
        return;
    }

    kernel.onEvent("sandbox.failure", () => {
        state.pressure = "critical";
        enableSafeMode();
    });

    kernel.onEvent("extension.crash", () => {
        console.warn("[GOVERNOR] Extension crash detected");
    });

    console.log("[GOVERNOR] Kernel linked");
}

/* ------------------------------------------------
MONITOR LOOP
------------------------------------------------ */
function startMonitor(deputy) {

    monitorTimer = setInterval(() => {

        const metrics = deputy?.metrics || {};

        evaluatePressure(metrics);
        applyAdaptiveRules();

    }, 4000);
}

/* ------------------------------------------------
START
------------------------------------------------ */
function startGovernor({ deputy, kernel } = {}) {

    if (governorRunning) return;

    governorRunning = true;

    console.log("[GOVERNOR] Starting...");

    applyBaseTuning();
    attachKernel(kernel);
    startMonitor(deputy);

    console.log("[GOVERNOR] ACTIVE");
}

/* ------------------------------------------------
STOP (VERY IMPORTANT)
------------------------------------------------ */
function stopGovernor() {

    if (monitorTimer)
        clearInterval(monitorTimer);

    governorRunning = false;

    console.log("[GOVERNOR] stopped");
}

/* ------------------------------------------------
STATUS
------------------------------------------------ */
function getStatus() {
    return {
        ...state,
        env: {
            AUTOPILOT_THRESHOLD:
                process.env.AUTOPILOT_THRESHOLD,
            SANDBOX_STRICT:
                process.env.SANDBOX_STRICT
        }
    };
}

module.exports = {
    startGovernor,
    stopGovernor,
    getStatus
};
