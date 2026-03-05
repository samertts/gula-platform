"use strict";

const identityEngine =
  require("./identity.engine");

async function trustMiddleware(req, res, next) {

  const userId = req.headers["x-user-id"];
  const signature = req.headers["x-signature"];

  if (!userId || !signature) {
    return res.status(401).json({
      error: "Missing digital identity"
    });
  }

  const identity =
    identityEngine.getIdentity(userId);

  if (!identity) {
    return res.status(403).json({
      error: "Unknown identity"
    });
  }

  const valid =
    identityEngine.verify(
      identity.publicKey,
      req.body || {},
      signature
    );

  if (!valid) {
    return res.status(403).json({
      error: "Invalid signature"
    });
  }

  req.identity = {
    userId: identity.userId,
    role: identity.role
  };

  next();
}

module.exports = trustMiddleware;
