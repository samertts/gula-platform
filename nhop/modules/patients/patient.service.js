const client = require("../../db/database");

async function createPatient(data) {
  const { national_id, full_name, gender, birth_date, phone } = data;

  const result = await client.query(
    `INSERT INTO patients
    (national_id, full_name, gender, birth_date, phone)
    VALUES ($1,$2,$3,$4,$5)
    RETURNING *`,
    [national_id, full_name, gender, birth_date, phone]
  );

  return result.rows[0];
}

module.exports = { createPatient };
