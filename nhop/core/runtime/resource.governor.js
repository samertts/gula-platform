"use strict";

/*
 NHOP RESOURCE GOVERNOR
 Controls CPU and memory usage per module
*/

const os = require("os");

const MODULE_LIMITS = {
    maxExecutionTimeMs: 1500,
    maxMemoryMB: 80
};

const runningModules = new Map();

function startTracking(moduleName) {
    runningModules.set(moduleName, {
        startTime: Date.now(),
        startMemory: process.memoryUsage().heapUsed
    });
}

function stopTracking(moduleName) {
    runningModules.delete(moduleName);
}

function checkLimits(moduleName) {
    const info = runningModules.get(moduleName);
    if (!info) return true;

    const elapsed = Date.now() - info.startTime;

    const memoryNow =
        (process.memoryUsage().heapUsed - info.startMemory) /
        1024 /
        1024;

    if (elapsed > MODULE_LIMITS.maxExecutionTimeMs) {
        console.warn("[GOVERNOR] Execution timeout:", moduleName);
        return false;
    }

    if (memoryNow > MODULE_LIMITS.maxMemoryMB) {
        console.warn("[GOVERNOR] Memory limit exceeded:", moduleName);
        return false;
    }

    return true;
}

function monitorLoop() {
    setInterval(() => {
        for (const [name] of runningModules.entries()) {
            const ok = checkLimits(name);

            if (!ok) {
                console.error("[GOVERNOR] Module isolated:", name);
                runningModules.delete(name);
            }
        }
    }, 1000);
}

module.exports = {
    startTracking,
    stopTracking,
    monitorLoop
};
