const crypto = require("crypto");

const VALID_KEYS = new Set([
  process.env.API_KEY || "sovereign-dev-key"
]);

function apiGuard(req, res, next) {

  const key = req.headers["x-api-key"];

  if (!key || !VALID_KEYS.has(key)) {
    return res.status(403).json({
      error: "Sovereign access denied"
    });
  }

  req.requestSignature = crypto.randomUUID();

  next();
}

module.exports = apiGuard;
