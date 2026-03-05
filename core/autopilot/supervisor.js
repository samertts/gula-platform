
/*
==========================================================
NHOP AUTOPILOT SUPERVISOR
Self-Healing Runtime Controller (FINAL)
==========================================================
*/

const { spawn } = require("child_process");
const os = require("os");
const path = require("path");
const net = require("net");

/* ======================================================
   CONFIG
====================================================== */

const ROOT = process.cwd();

const SERVICES = {
  backend: {
    cmd: "node",
    args: ["server.js"],
    cwd: ROOT,
    port: 3000
  },

  frontend: {
    cmd: "npm",
    args: ["run", "dev"],
    cwd: path.join(ROOT, "../nhop-frontend"),
    port: 5173
  }
};

const processes = {};
const restartCount = {};
const restartWindow = {};

const MAX_RESTARTS = 5;
const RESTART_DELAY = 3000;
const HEALTH_INTERVAL = 5000;

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
   PORT CHECK
====================================================== */

function isPortFree(port) {
  return new Promise(resolve => {
    const server = net.createServer();

    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close();
      resolve(true);
    });

    server.listen(port);
  });
}

/* ======================================================
   SYSTEM HEALTH (THROTTLED)
====================================================== */

let lastHealthLog = 0;

function systemHealth() {
  const now = Date.now();
  if (now - lastHealthLog < HEALTH_INTERVAL) return;

  lastHealthLog = now;

  const mem = process.memoryUsage();
  const load = os.loadavg()[0];

  log("INFO", "system.health", {
    cpuLoad: load,
    memoryMB: Math.round(mem.rss / 1024 / 1024)
  });

  if (load > os.cpus().length * 1.5) {
    log("WARN", "High system pressure detected");
  }
}

/* ======================================================
   START SERVICE
====================================================== */

async function startService(name) {

  const svc = SERVICES[name];
  if (!svc) return;

  const free = await isPortFree(svc.port);

  if (!free) {
    log("ERROR", `${name}.port_busy`, { port: svc.port });
    return;
  }

  log("INFO", `starting.${name}`);

  const child = spawn(svc.cmd, svc.args, {
    cwd: svc.cwd,
    shell: true
  });

  processes[name] = child;

  child.stdout.on("data", d =>
    process.stdout.write(`[${name}] ${d}`)
  );

  child.stderr.on("data", d =>
    process.stderr.write(`[${name}] ${d}`)
  );

  child.on("exit", code => {

    log("ERROR", `${name}.stopped`, { code });

    const now = Date.now();

    if (!restartWindow[name]) restartWindow[name] = now;

    if (now - restartWindow[name] > 60000) {
      restartCount[name] = 0;
      restartWindow[name] = now;
    }

    restartCount[name] = (restartCount[name] || 0) + 1;

    if (restartCount[name] > MAX_RESTARTS) {
      log("ERROR", `${name}.restart_limit_reached`);
      return;
    }

    setTimeout(() => {
      log("WARN", `restarting.${name}`);
      startService(name);
    }, RESTART_DELAY);
  });
}

/* ======================================================
   WATCHDOG LOOP
====================================================== */

function watchdog() {
  setInterval(systemHealth, 2000);
}

/* ======================================================
   SHUTDOWN
====================================================== */

function shutdown() {

  log("WARN", "Supervisor shutting down");

  Object.values(processes).forEach(p => {
    try { p.kill("SIGINT"); } catch {}
  });

  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

/* ======================================================
   BOOT
====================================================== */

async function boot() {

  log("INFO", "NHOP Supervisor booting");

  await startService("backend");
  await startService("frontend");

  watchdog();

  log("INFO", "Supervisor active");
}

boot();
