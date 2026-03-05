const db = require("../../db/database");
const { generateTrackingId } = require("../core/id.generator");
const audit = require("../audit/audit.service");
const queue = require("../queue/event.queue");
// CREATE PATIENT
exports.create = async (req, res) => {
  try {
    const {
      national_id,
      full_name,
      gender,
      birth_date,
      phone
    } = req.body;

    const trackingId = generateTrackingId();

    const query = `
      INSERT INTO patients
      (national_id, full_name, gender, birth_date, phone, national_tracking_id)
      VALUES ($1,$2,$3,$4,$5,$6)
      RETURNING *;
    `;

    const values = [
      national_id,
      full_name,
      gender,
      birth_date,
      phone,
      trackingId
    ];

    const result = await db.query(query, values);
queue.push({
  entity: "patient",
  entity_id: result.rows[0].uuid,
  action: "CREATE",
  payload: result.rows[0]
});
// Audit 
audit.log({
  entity: "patient",
  entity_id: result.rows[0].uuid,
  action: "CREATE",
  payload: result.rows[0]
});
    res.status(201).json({
      message: "Patient created successfully",
      data: result.rows[0]
    });

  } catch (err) {
    console.error("Create patient error:", err);
    res.status(500).json({
      error: "Failed to create patient"
    });
  }
};
