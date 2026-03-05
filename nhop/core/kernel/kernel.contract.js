
"use strict";

/*
==================================================
NHOP KERNEL CONTRACT (SOVEREIGN EDITION)
Secure communication backbone
==================================================
*/

const EventEmitter = require("events");

class KernelContract extends EventEmitter {

    constructor() {
        super();

        /* internal registries */
        this._services = new Map();
        this._extensions = new Map();
        this._permissions = new Map();
    }

    /* ==================================================
       SERVICE REGISTRATION (Kernel Only)
    ================================================== */
    registerService(name, service) {

        if (this._services.has(name))
            throw new Error(`Service already exists: ${name}`);

        this._services.set(name, Object.freeze(service));

        console.log("[KERNEL] Service registered:", name);
    }

    /* ==================================================
       PERMISSION SYSTEM
    ================================================== */
    grantPermissions(extension, permissions = []) {
        this._permissions.set(extension, new Set(permissions));
    }

    _assertPermission(extension, service) {

        const perms = this._permissions.get(extension);

        if (!perms || !perms.has(service)) {
            throw new Error(
                `Access denied: ${extension} → ${service}`
            );
        }
    }

    /* ==================================================
       CONTROLLED SERVICE ACCESS
    ================================================== */
    getService(extension, name) {

        this._assertPermission(extension, name);

        if (!this._services.has(name))
            throw new Error(`Unknown service: ${name}`);

        return this._services.get(name);
    }

    /* ==================================================
       EXTENSION REGISTRATION
    ================================================== */
    registerExtension(name, api) {

        if (this._extensions.has(name))
            throw new Error(`Extension already loaded: ${name}`);

        this._extensions.set(name, Object.freeze(api));

        console.log("[KERNEL] Extension online:", name);
    }

    /* ==================================================
       SAFE EVENT BUS (Namespaced)
    ================================================== */
    emitEvent(extension, event, payload) {

        const namespaced = `${extension}:${event}`;
        this.emit(namespaced, payload);
    }

    onEvent(extension, event, handler) {

        const namespaced = `${extension}:${event}`;
        this.on(namespaced, handler);
    }

    /* ==================================================
       SYSTEM LIFECYCLE
    ================================================== */
    async shutdown() {

        console.log("[KERNEL] Graceful shutdown");

        for (const [name, ext] of this._extensions.entries()) {
            if (typeof ext.shutdown === "function") {
                await ext.shutdown();
            }
        }
    }
}

/* singleton */
module.exports = new KernelContract();
