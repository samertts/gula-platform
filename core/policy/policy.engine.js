"use strict";

/*
 NHOP SOVEREIGN POLICY ENGINE
 Dynamic runtime governance
*/

const institutionContext =
  require("../context/institution.context");

const policies = [];

function register(policy) {
  policies.push(policy);
}

async function evaluate(req) {

  const ctx = institutionContext.getContext();

  for (const policy of policies) {

    const result = await policy({
      request: req,
      context: ctx
    });

    if (result && result.allow === false) {
      return {
        allowed: false,
        reason: result.reason || "Blocked by policy"
      };
    }
  }

  return { allowed: true };
}

/* ======================
   DEFAULT POLICIES
====================== */

/* Block unknown institutions */
register(({ context }) => {
  if (!context || !context.institutionId) {
    return {
      allow: false,
      reason: "Institution missing"
    };
  }
});

/* Example load protection */
register(() => {
  if (process.memoryUsage().heapUsed > 300 * 1024 * 1024) {
    return {
      allow: false,
      reason: "System under pressure"
    };
  }
});

module.exports = {
  register,
  evaluate
};
