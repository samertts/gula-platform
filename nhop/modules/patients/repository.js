const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: process.env.DB_PORT || 5432,
  user: process.env.DB_USER || "postgres",
  password: process.env.DB_PASSWORD || "postgres",
  database: process.env.DB_NAME || "nhop"
});

async function createPatient(patient) {
  const query = `
    INSERT INTO patients(id, name, age, created_at)
    VALUES($1,$2,$3,NOW())
    RETURNING *;
  `;

  const result = await pool.query(query, [
    patient.id,
    patient.name,
    patient.age
  ]);

  return result.rows[0];
}

async function getAllPatients() {
  const result = await pool.query(
    "SELECT * FROM patients ORDER BY created_at DESC"
  );
  return result.rows;
}

module.exports = {
  createPatient,
  getAllPatients
};
