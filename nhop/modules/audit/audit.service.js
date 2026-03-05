const db = require("../../db/database");

async function write(data) {
  const query = `
    INSERT INTO audit_logs
    (entity_type, entity_id, action, metadata)
    VALUES ($1,$2,$3,$4)
  `;

  const values = [
    data.entity,
    data.entity_id,
    data.action,
    data.payload
  ];

  await db.query(query, values);
}

module.exports = {
  write
};
