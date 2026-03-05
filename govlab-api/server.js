const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

let patients = [];

app.get("/", (req, res) => {
  res.send("GovLab API running");
});

app.post("/patients", (req, res) => {
  const patient = { id: Date.now(), ...req.body };
  patients.push(patient);
  res.json(patient);
});

app.get("/patients", (req, res) => {
  res.json(patients);
});

app.listen(3000, () => {
  console.log("API running on port 3000");
});
