
"use strict";

/*
=========================================
NHOP SANDBOX FACTORY
Creates safe execution environment
=========================================
*/

const express = require("express");

function createSandbox(logger) {

    const router = express.Router();

    return {
        router,

        expose(path, handler) {
            if (typeof handler !== "function") {
                throw new Error("Sandbox handler must be function");
            }

            router.use(path, handler);
        }
    };
}

module.exports = createSandbox;

core/sandbox/capabilities.js

"use strict";

const createSandbox = require("./sandbox.factory");

function buildCapabilities(app, logger) {

    const sandbox = createSandbox(logger);

    return {
        logger,
        router: sandbox.router,
        sandbox
    };
}

module.exports = buildCapabilities;
