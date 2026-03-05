
"use strict";

/*
==================================================
NHOP DEPUTY KERNEL
Operational Control Layer
==================================================
*/

let running = false;

/* ================================================
   INTERNAL METRICS
================================================ */

const metrics = {
  totalRequests: 0,
  avgLatency: 0,
  modules: new Set()
};

let latencySamples = [];

/* ================================================
   INITIALIZATION
================================================ */

async function initialize() {
  console.log("[DEPUTY] Kernel initialized");
}

/* ================================================
   PRE-BOOT VALIDATION
================================================ */

function preBootCheck() {
  console.log("[DEPUTY] Pre-boot check passed");
}

/* ================================================
   REQUEST OBSERVER
================================================ */

function observeRequest({ duration, status }) {

  metrics.totalRequests++;

  latencySamples.push(duration);

  if (latencySamples.length > 50)
    latencySamples.shift();

  metrics.avgLatency =
    latencySamples.reduce((a,b)=>a+b,0) /
    latencySamples.length;
}

/* ================================================
   ATTACH CONTEXT TO REQUEST
================================================ */

function attachContext(req) {
  req.deputy = {
    monitored: true
  };
}

/* ================================================
   MODULE TRACKING
================================================ */

function moduleRegistered(name) {
  metrics.modules.add(name);
}

/* ================================================
   OPERATIONS LOOP
================================================ */

function startOperationsLoop() {

  if (running) return;
  running = true;

  console.log("[DEPUTY] Operations loop started");

  setInterval(()=>{

    if(metrics.avgLatency > 2000){
      console.warn(
        "[DEPUTY WARNING] High latency:",
        metrics.avgLatency
      );
    }

  },5000);
}

/* ================================================
   SHUTDOWN
================================================ */

async function shutdown() {
  running = false;
  console.log("[DEPUTY] Shutdown complete");
}

/* ================================================
   EXPORT API
================================================ */

module.exports = {
  initialize,
  preBootCheck,
  observeRequest,
  attachContext,
  moduleRegistered,
  startOperationsLoop,
  shutdown
};
