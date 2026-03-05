const express = require("express");
const router = express.Router();

const controller = require("./patient.controller");

// Create patient
router.post("/", controller.create);

module.exports = router;
