"use strict";

/*
 NHOP Self-Healing Engine
 Prevents server crashes and isolates failing modules
*/

const path = require("path");

const failedModules = new Map();

function safeRequire(modulePath) {
  try {
    delete require.cache[require.resolve(modulePath)];
    const mod = require(modulePath);

    failedModules.delete(modulePath);

    console.log("[HEAL] module loaded:", modulePath);

    return mod;
  } catch (err) {
    console.error("[HEAL] module failed:", modulePath);
    console.error(err.message);

    failedModules.set(modulePath, {
      error: err.message,
      time: new Date().toISOString()
    });

    return null;
  }
}

function retryFailedModules(interval = 10000) {
  setInterval(() => {
    if (failedModules.size === 0) return;

    console.log("[HEAL] retrying failed modules...");

    for (const [modulePath] of failedModules.entries()) {
      safeRequire(modulePath);
    }
  }, interval);
}

function globalErrorShield() {
  process.on("uncaughtException", (err) => {
    console.error("[HEAL] Uncaught Exception:", err.message);
  });

  process.on("unhandledRejection", (reason) => {
    console.error("[HEAL] Unhandled Rejection:", reason);
  });
}

module.exports = {
  safeRequire,
  retryFailedModules,
  globalErrorShield
};
