const db = require("../../../db/database");
const audit = require("../../audit.service");
exports.create = async (data) => {
  const { national_id, full_name, gender, birth_date, phone } = data;

  const result = await db.query(
    `INSERT INTO patients
     (national_id, full_name, gender, birth_date, phone)
     VALUES ($1,$2,$3,$4,$5)
     RETURNING *`,
    [national_id, full_name, gender, birth_date, phone]
  );

  return result.rows[0];
};
const patient = result.rows[0];

await audit.log({
  entity_type: "patient",
  entity_id: patient.uuid,
  action: "CREATE",
  metadata: patient
});

return patient;
