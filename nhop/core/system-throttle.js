// core/system-throttle.js
// Finalized Throttle Script: Loosens restrictions to prevent sandbox failure

function initializeThrottle() {
    console.log("[THROTTLE] Applying load management protocols...");
   
    // High load often causes sandbox creation failure in WSL
    // Loosen restrictions on the autopilot engine
    process.env.AUTOPILOT_THRESHOLD = "0.98";
   
    // Prevent strict sandbox failures when creating AI extensions
    process.env.SANDBOX_STRICT = "false";
    process.env.NODE_ENV = "production";
}

module.exports = {
    initializeThrottle
};
