// modules/queue/queue.worker.js

const queue = require("./event.queue");
const auditService = require("../audit/audit.service");

console.log("NHOP_QUEUE_WORKER_STARTED");

async function processEvent(event) {
  try {
    if (event.type === "AUDIT_LOG") {
      await auditService.write(event.payload);
      console.log("Audit processed");
    }
  } catch (err) {
    console.error("Worker error:", err);
  }
}

async function processBatch() {
  while (queue.hasEvents()) {
    const ev = queue.getNextEvent();
    await processEvent(ev);
  }
}

function startWorker() {
  setInterval(processBatch, 1000);
}

startWorker();
