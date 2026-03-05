
"use strict";

/*
NHOP AUTOPILOT KERNEL (HARDENED VERSION)
Adaptive Self Optimization Engine
Safe for Production
*/

const os = require("os");
const { monitorEventLoopDelay } = require("perf_hooks");

const loopMonitor = monitorEventLoopDelay({ resolution: 20 });
loopMonitor.enable();

let intervalHandle = null;

const state = Object.seal({
  mode: "conservative",
  lastCheck: Date.now(),
  eventLoopDelay: 0
});

/* ---------------- SYSTEM METRICS ---------------- */

function systemLoad() {
  const cpuCount = os.cpus().length;

  const avg = os.loadavg()[0];

  // fallback for Windows or unsupported env
  if (avg === 0) {
    const usage = process.cpuUsage();
    return (usage.user + usage.system) / 1e6 / cpuCount;
  }

  return avg / cpuCount;
}

function memoryPressure() {
  const mem = process.memoryUsage();
  return mem.heapUsed / mem.heapTotal;
}

function eventLoopPressure() {
  const delay = loopMonitor.mean / 1e6; // ns → ms
  state.eventLoopDelay = delay;
  return delay;
}

/* ---------------- DECISION ENGINE ---------------- */

function decideMode() {
  const load = systemLoad();
  const mem = memoryPressure();
  const loop = eventLoopPressure();

  if (load > 0.7 || mem > 0.80 || loop > 50) {
    state.mode = "aggressive";
  } else {
    state.mode = "conservative";
  }

  state.lastCheck = Date.now();
}

/* ---------------- ACTIONS ---------------- */

function safeGC(force = false) {
  if (typeof global.gc !== "function") return;

  if (force || state.eventLoopDelay < 20) {
    try {
      global.gc();
    } catch {}
  }
}

function conservativeActions() {
  safeGC(false);
}

function aggressiveActions() {
  console.warn("[AUTOPILOT] High system pressure detected");

  safeGC(true);

  if (global.runtimeKernel &&
      typeof global.runtimeKernel.shedLoad === "function") {
    try {
      global.runtimeKernel.shedLoad();
    } catch (e) {
      console.error("[AUTOPILOT] shedLoad failed:", e.message);
    }
  }
}

/* ---------------- MAIN LOOP ---------------- */

function autopilotCycle() {
  try {
    decideMode();

    if (state.mode === "aggressive") {
      aggressiveActions();
    } else {
      conservativeActions();
    }

  } catch (err) {
    console.error("[AUTOPILOT ERROR]", err);
  }
}

/* ---------------- PUBLIC API ---------------- */

function startAutopilot(interval = 5000) {
  if (intervalHandle) return;

  console.log("Autopilot Engine Started");

  intervalHandle = setInterval(autopilotCycle, interval);
  intervalHandle.unref(); // prevents blocking shutdown
}

function stopAutopilot() {
  if (intervalHandle) {
    clearInterval(intervalHandle);
    intervalHandle = null;
  }
}

module.exports = {
  startAutopilot,
  stopAutopilot,
  state
};
