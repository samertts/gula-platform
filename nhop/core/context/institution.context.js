
"use strict";

/*
====================================================
NHOP Institution Context
Multi-Institution Isolation Layer
Kernel Compatible Edition (Final)
====================================================
*/

const crypto = require("crypto");

/*
----------------------------------------------------
INTERNAL STATE
----------------------------------------------------
*/

let currentInstitution = {
    id: "default",
    name: "NHOP Default Institution",
    permissions: ["*"],
    createdAt: new Date().toISOString()
};

/*
----------------------------------------------------
HELPERS
----------------------------------------------------
*/

function generateRequestId() {
    return crypto.randomUUID();
}

/*
----------------------------------------------------
PUBLIC API
----------------------------------------------------
*/

function getInstitution() {
    return currentInstitution;
}

function setInstitution(data = {}) {
    currentInstitution = {
        id: data.id || "default",
        name: data.name || "NHOP Default Institution",
        permissions: data.permissions || ["*"],
        createdAt: currentInstitution.createdAt
    };
}

/*
----------------------------------------------------
EXPRESS MIDDLEWARE
----------------------------------------------------
*/

function institutionMiddleware(req, res, next) {

    try {
        // attach unique request id
        req.requestId = generateRequestId();

        // attach institution context
        req.institution = {
            ...currentInstitution,
            requestId: req.requestId
        };

        next();

    } catch (err) {
        // fail-safe (never break request pipeline)
        console.error("Institution middleware failure:", err.message);
        next();
    }
}

/*
----------------------------------------------------
EXPORT CONTRACT ADAPTER
IMPORTANT:
server.js expects `.middleware`
----------------------------------------------------
*/

module.exports = Object.freeze({

    // core api
    getInstitution,
    setInstitution,

    // internal name (backward compatibility)
    institutionMiddleware,

    // kernel expected interface ✅
    middleware: institutionMiddleware

});
