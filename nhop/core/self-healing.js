// core/self-healing.js

const fs = require("fs");

function safeExecute(fn, fallback = null) {
  return async (...args) => {
    try {
      return await fn(...args);
    } catch (err) {
      console.error("SELF_HEALING_ERROR:", err.message);

      if (fallback) {
        try {
          return await fallback(err, ...args);
        } catch (e) {
          console.error("FALLBACK_FAILED:", e.message);
        }
      }

      return null;
    }
  };
}

function protectProcess() {

  process.on("uncaughtException", (err) => {
    console.error("UNCAUGHT_EXCEPTION:", err);
  });

  process.on("unhandledRejection", (err) => {
    console.error("UNHANDLED_REJECTION:", err);
  });

}

module.exports = {
  safeExecute,
  protectProcess
};
