"use strict";

const policyEngine =
  require("./policy.engine");

async function policyMiddleware(req, res, next) {

  const result =
    await policyEngine.evaluate(req);

  if (!result.allowed) {
    return res.status(403).json({
      error: "Policy violation",
      reason: result.reason
    });
  }

  next();
}

module.exports = policyMiddleware;
