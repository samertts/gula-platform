
// core/performance-guard.js
// Improved Guard: Manages load without triggering automatic shutdown

const os = require('os');

const CONFIG = {
    maxCpuMultiplier: 4.0,       // Allow higher load before throttling (1.5 -> 4.0)
    maxMemoryUsage: 0.95,       // Throttle if RAM usage > 90%
    maxQueue: 5000,             // Increase queue capacity (1000 -> 5000)
    throttleDelay: 1000         // Wait 1s before retrying tasks
};

let activeTasks = 0;

function getSystemMetrics() {
    const cpus = os.cpus().length;
    const load = os.loadavg()[0]; // 1-minute load average
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memUsage = (totalMem - freeMem) / totalMem;

    return {
        cpuUsage: load / cpus,
        memUsage: memUsage
    };
}

function allowExecution() {
    const metrics = getSystemMetrics();
   
    // Check CPU
    if (metrics.cpuUsage > CONFIG.maxCpuMultiplier) {
        console.warn(`[GUARD] High CPU Load: ${(metrics.cpuUsage * 100).toFixed(2)}%. Throttling.`);
        return false;
    }

    // Check RAM
    if (metrics.memUsage > CONFIG.maxMemoryUsage) {
        console.warn(`[GUARD] High RAM Usage: ${(metrics.memUsage * 100).toFixed(2)}%. Throttling.`);
        return false;
    }

    // Check Queue
    if (activeTasks > CONFIG.maxQueue) {
        console.warn(`[GUARD] Task Queue Full: ${activeTasks}. Throttling.`);
        return false;
    }

    return true;
}

async function guardedExecution(task) {
    // If system is overwhelmed, wait before retrying (Queueing strategy)
    while (!allowExecution()) {
        await new Promise(resolve => setTimeout(resolve, CONFIG.throttleDelay));
    }

    activeTasks++;
    try {
        return await task();
    } catch (error) {
        console.error("[GUARD] Task failed:", error);
        throw error;
    } finally {
        activeTasks--;
    }
}

module.exports = {
    guardedExecution,
    getSystemMetrics
};
