

"use strict";

const os = require("os");

function getHealth(runtime, registeredModules) {
  const memory = process.memoryUsage();

  return {
    status: "ok",
    runtime: "active",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),

    system: {
      platform: os.platform(),
      cpuCount: os.cpus().length,
      loadAvg: os.loadavg()
    },

    memory: {
      rss: memory.rss,
      heapUsed: memory.heapUsed,
      heapTotal: memory.heapTotal,
      external: memory.external
    },

    modules: registeredModules.length
  };
}

module.exports = {
  getHealth
};
