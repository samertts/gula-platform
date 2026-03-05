

"use strict";

/*
==================================================
NHOP SANDBOX FACTORY (FINAL STABLE VERSION)
Isolated Extension Runtime
Compatible with existing server.js
==================================================
*/

const vm = require("vm");
const path = require("path");

/* ---------------------------------------------
   SAFE CAPABILITIES LOADING
--------------------------------------------- */

let CAPABILITIES = {};

try {
    CAPABILITIES = require("./capabilities");
} catch (err) {
    console.warn("[SANDBOX] capabilities not found, using empty set");
}

/* ---------------------------------------------
   BLOCKED MODULES (Security Policy)
--------------------------------------------- */

const BLOCKED_MODULES = new Set([
    "fs",
    "child_process",
    "cluster",
    "worker_threads",
    "vm"
]);

/* ---------------------------------------------
   SAFE REQUIRE WRAPPER
--------------------------------------------- */

function safeRequire(requester) {

    return function (mod) {

        if (BLOCKED_MODULES.has(mod)) {
            throw new Error(
                `[SANDBOX SECURITY] Module blocked: ${mod}`
            );
        }

        try {
            return require(mod);
        } catch (err) {
            throw new Error(
                `[SANDBOX REQUIRE ERROR] ${requester}: ${err.message}`
            );
        }
    };
}

/* ---------------------------------------------
   CREATE SANDBOX
--------------------------------------------- */

function createSandbox(extensionName = "unknown") {

    try {

        /* sandbox global scope */
        const sandboxGlobal = {

            console,

            Buffer,

            setTimeout,
            setInterval,
            clearTimeout,
            clearInterval,

            CAPABILITIES,

            EXTENSION: extensionName,

            global: {},

            require: safeRequire(extensionName)
        };

        /* isolate context */
        const context = vm.createContext(
            sandboxGlobal,
            {
                name: `NHOP_SANDBOX_${extensionName}`,
                codeGeneration: {
                    strings: true,
                    wasm: false
                }
            }
        );

        /* -----------------------------------------
           EXECUTION ENGINE
        ----------------------------------------- */

        function run(code, filename = "extension.js") {

            if (!code || typeof code !== "string") {
                throw new Error(
                    "[SANDBOX] invalid code input"
                );
            }

            const script = new vm.Script(code, {
                filename,
                displayErrors: true,
                timeout: 5000
            });

            return script.runInContext(context, {
                timeout: 5000
            });
        }

        /* -----------------------------------------
           SUCCESS OBJECT
        ----------------------------------------- */

        return {
            name: extensionName,
            context,
            run
        };

    } catch (err) {

        console.error("\n========== SANDBOX CREATION FAILED ==========");
        console.error("Extension:", extensionName);
        console.error(err.stack);
        console.error("=============================================\n");

        return null;
    }
}

/* ---------------------------------------------
   EXPORT (IMPORTANT — DO NOT CHANGE)
--------------------------------------------- */

module.exports = createSandbox;
