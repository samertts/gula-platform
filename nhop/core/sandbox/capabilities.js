
"use strict";

/*
==================================================
NHOP CAPABILITY SYSTEM
Provides restricted powers to modules
==================================================
*/

function createCapabilities(router, runtime, logger){

  return Object.freeze({

    router: Object.freeze(router),

    ledger: Object.freeze({
      commit: runtime.commitLedgerEvent?.bind(runtime)
    }),

    audit: Object.freeze({
      log: runtime.auditEvent?.bind(runtime)
    }),

    log: Object.freeze({
      info: logger.info,
      warn: logger.warn,
      error: logger.error
    }),

    time: () => new Date().toISOString()

  });
}

module.exports = createCapabilities;
