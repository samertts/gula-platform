"use strict";

/*
 NHOP Adaptive Load Shield
 Lightweight runtime protection layer
*/

const os = require("os");

const state = {
  requests: 0,
  lastReset: Date.now(),
  rps: 0
};

const LIMITS = {
  SOFT_RPS: 50,
  HARD_RPS: 120
};

function calculateRPS() {
  const now = Date.now();
  const diff = (now - state.lastReset) / 1000;

  if (diff >= 1) {
    state.rps = Math.round(state.requests / diff);
    state.requests = 0;
    state.lastReset = now;
  }
}

setInterval(calculateRPS, 500);

function shieldMiddleware(req, res, next) {
  state.requests++;

  const load = os.loadavg()[0];

  /* HARD PROTECTION */
  if (state.rps > LIMITS.HARD_RPS || load > 2.5) {
    return res.status(503).json({
      error: "System busy",
      protection: "HARD_SHIELD"
    });
  }

  /* SOFT PROTECTION */
  if (state.rps > LIMITS.SOFT_RPS) {
    setTimeout(() => next(), 50);
    return;
  }

  next();
}

function getStatus() {
  return {
    rps: state.rps,
    cpuLoad: os.loadavg()[0],
    memoryFree: os.freemem()
  };
}

module.exports = {
  shieldMiddleware,
  getStatus
};
