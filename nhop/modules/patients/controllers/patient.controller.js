const patientService = require("../services/patient.service");

exports.createPatient = async (req, res) => {
  try {
    const patient = await patientService.create(req.body);
    res.json(patient);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error creating patient");
  }
};
