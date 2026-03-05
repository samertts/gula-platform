"use strict";

const vm = require("vm");
const fs = require("fs");
const path = require("path");

/*
 NHOP EXECUTION SANDBOX
 Isolates modules from core system
*/

const sandboxRegistry = new Map();

function createSandbox(modulePath) {
    const code = fs.readFileSync(modulePath, "utf8");

    const sandbox = {
        console,
        setTimeout,
        setInterval,
        clearTimeout,
        clearInterval,

        module: { exports: {} },
        exports: {},

        SAFE_API: {
            log: (...args) => {
                console.log("[SANDBOX]", ...args);
            }
        }
    };

    const context = vm.createContext(sandbox, {
        name: "NHOP_SANDBOX",
        codeGeneration: { strings: false, wasm: false }
    });

    try {
        const script = new vm.Script(code, {
            filename: modulePath,
            timeout: 2000
        });

        script.runInContext(context);

        sandboxRegistry.set(modulePath, {
            status: "running",
            startedAt: Date.now()
        });

        return sandbox.module.exports;

    } catch (err) {
        console.error("[SANDBOX ERROR]", modulePath, err.message);

        sandboxRegistry.set(modulePath, {
            status: "failed",
            error: err.message
        });

        return null;
    }
}

function loadModuleSafe(modulePath) {
    const absolute = path.resolve(modulePath);

    if (!fs.existsSync(absolute)) {
        console.warn("[SANDBOX] module missing:", absolute);
        return null;
    }

    return createSandbox(absolute);
}

function getSandboxStatus() {
    return Array.from(sandboxRegistry.entries());
}

module.exports = {
    loadModuleSafe,
    getSandboxStatus
};
