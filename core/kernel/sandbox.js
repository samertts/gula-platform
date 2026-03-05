
/*
==========================================================
NHOP MEDICAL SANDBOX ENGINE
Process Isolation + Self-Healing Runtime
FINAL PRODUCTION VERSION
==========================================================
*/

const { fork } = require("child_process");
const path = require("path");
const os = require("os");

/* ======================================================
   CONFIG
====================================================== */

const RESTART_DELAY = 3000;
const MAX_RESTARTS = 5;
const HEALTH_INTERVAL = 10000;
const MESSAGE_TIMEOUT = 15000;

/* ======================================================
   STATE
====================================================== */

const sandboxes = new Map();
const restartCounter = new Map();
const pendingRequests = new Map();

/* ======================================================
   LOGGER
====================================================== */

function log(level, message, extra = {}) {
  console.log(JSON.stringify({
    level,
    time: new Date().toISOString(),
    message,
    ...extra
  }));
}

/* ======================================================
   VALIDATION
====================================================== */

function resolveEntry(entryFile) {
  const full = path.resolve(entryFile);

  if (!require("fs").existsSync(full)) {
    throw new Error(`Sandbox entry not found: ${full}`);
  }

  return full;
}

/* ======================================================
   HEALTH MONITOR
====================================================== */

function monitorHealth(name, child) {

  const timer = setInterval(() => {

    if (!child.connected) {
      clearInterval(timer);
      return;
    }

    const mem = process.memoryUsage().rss / 1024 / 1024;
    const load = os.loadavg()[0];

    log("INFO", "sandbox.health", {
      module: name,
      systemLoad: load.toFixed(2),
      memoryMB: Math.round(mem)
    });

  }, HEALTH_INTERVAL);

  child.on("exit", () => clearInterval(timer));
}

/* ======================================================
   CREATE SANDBOX
====================================================== */

function createSandbox(name, entryFile) {

  if (sandboxes.has(name)) {
    log("WARN", "sandbox.already_running", { name });
    return sandboxes.get(name);
  }

  const resolvedEntry = resolveEntry(entryFile);

  log("INFO", "sandbox.starting", { name });

  const child = fork(resolvedEntry, [], {
    stdio: ["pipe", "pipe", "pipe", "ipc"],
    env: {
      ...process.env,
      NHOP_SANDBOX: "true",
      MODULE_NAME: name
    }
  });

  sandboxes.set(name, child);
  restartCounter.set(name, restartCounter.get(name) || 0);

  monitorHealth(name, child);

  /* -----------------------------
     STDOUT PIPE
  ----------------------------- */

  child.stdout?.on("data", data => {
    log("INFO", "sandbox.stdout", {
      module: name,
      output: data.toString().trim()
    });
  });

  child.stderr?.on("data", data => {
    log("ERROR", "sandbox.stderr", {
      module: name,
      error: data.toString().trim()
    });
  });

  /* -----------------------------
     MESSAGE CHANNEL
  ----------------------------- */

  child.on("message", msg => {

    if (msg?.requestId && pendingRequests.has(msg.requestId)) {
      const resolver = pendingRequests.get(msg.requestId);
      pendingRequests.delete(msg.requestId);
      resolver.resolve(msg);
      return;
    }

    log("INFO", "sandbox.message", {
      module: name,
      msg
    });
  });

  /* -----------------------------
     EXIT HANDLER
  ----------------------------- */

  child.on("exit", code => {

    sandboxes.delete(name);

    log("ERROR", "sandbox.exited", {
      module: name,
      code
    });

    const count = (restartCounter.get(name) || 0) + 1;
    restartCounter.set(name, count);

    if (count > MAX_RESTARTS) {
      log("ERROR", "sandbox.restart_limit_reached", { name });
      return;
    }

    setTimeout(() => {
      log("WARN", "sandbox.restarting", { name });
      createSandbox(name, resolvedEntry);
    }, RESTART_DELAY);
  });

  log("INFO", "sandbox.started", { name });

  return child;
}

/* ======================================================
   SEND MESSAGE (ASYNC RPC)
====================================================== */

function sendToSandbox(name, payload) {

  const sb = sandboxes.get(name);

  if (!sb) {
    throw new Error(`Sandbox ${name} not running`);
  }

  const requestId =
    Date.now() + "-" + Math.random().toString(36).slice(2);

  payload.requestId = requestId;

  return new Promise((resolve, reject) => {

    pendingRequests.set(requestId, { resolve, reject });

    sb.send(payload);

    setTimeout(() => {
      if (pendingRequests.has(requestId)) {
        pendingRequests.delete(requestId);
        reject(new Error("Sandbox response timeout"));
      }
    }, MESSAGE_TIMEOUT);
  });
}

/* ======================================================
   STOP SANDBOX
====================================================== */

function stopSandbox(name) {

  const sb = sandboxes.get(name);
  if (!sb) return;

  log("WARN", "sandbox.stopping", { name });

  try {
    sb.kill("SIGINT");
  } catch {}

  sandboxes.delete(name);
}

/* ======================================================
   STOP ALL
====================================================== */

function stopAllSandboxes() {

  for (const name of sandboxes.keys()) {
    stopSandbox(name);
  }
}

/* ======================================================
   LIST
====================================================== */

function listSandboxes() {
  return Array.from(sandboxes.keys());
}

/* ======================================================
   SAFE SHUTDOWN
====================================================== */

process.on("SIGINT", () => {
  log("WARN", "sandbox.global_shutdown");
  stopAllSandboxes();
  process.exit(0);
});

process.on("SIGTERM", () => {
  log("WARN", "sandbox.global_shutdown");
  stopAllSandboxes();
  process.exit(0);
});

/* ======================================================
   EXPORTS
====================================================== */

module.exports = {
  createSandbox,
  sendToSandbox,
  stopSandbox,
  stopAllSandboxes,
  listSandboxes
};
