"use strict";

function register(app, logger) {
  const router = require("./routes");

  if (!router) {
    throw new Error("Patients routes not found");
  }

  app.use("/patients", router);

  if (logger) {
    logger.info("Patients module registered");
  }
}

module.exports = { register };
