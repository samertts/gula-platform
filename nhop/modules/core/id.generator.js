const crypto = require("crypto");

exports.generateTrackingId = () => {
  const year = new Date().getFullYear();

  const random = crypto
    .randomBytes(4)
    .toString("hex")
    .toUpperCase();

  return `NHOP-${year}-${random}`;
};
