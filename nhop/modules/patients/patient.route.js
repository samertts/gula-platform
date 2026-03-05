const express = require("express");
const router = express.Router();
const patientController = require("./controllers/patient.controller");

router.post("/", patientController.createPatient);

module.exports = router;
