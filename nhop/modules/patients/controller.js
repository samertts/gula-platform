const { v4: uuidv4 } = require("uuid");
const repo = require("./repository");

function validate(body) {
  if (!body.name) throw new Error("name required");
  if (!body.age) throw new Error("age required");
  if (typeof body.age !== "number") throw new Error("age must be number");
}

async function create(req, res, next) {
  try {
    validate(req.body);

    const patient = {
      id: uuidv4(),
      name: req.body.name,
      age: req.body.age
    };

    const saved = await repo.createPatient(patient);

    res.json({
      status: "success",
      data: saved
    });
  } catch (err) {
    next(err);
  }
}

async function list(req, res, next) {
  try {
    const patients = await repo.getAllPatients();
    res.json(patients);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  create,
  list
};
