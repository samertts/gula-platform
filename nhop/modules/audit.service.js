const db = require("../db/database");

exports.log = async ({ entity_type, entity_id, action, metadata }) => {
  await db.query(
    `INSERT INTO audit_logs
     (entity_type, entity_id, action, metadata)
     VALUES ($1,$2,$3,$4)`,
    [entity_type, entity_id, action, metadata]
  );
};
