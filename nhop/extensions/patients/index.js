"use strict";

/*
==========================================================
NHOP PATIENTS EXTENSION (replaces old module)
Full patient management with auth protection
==========================================================
*/

const crypto = require("crypto");
const db     = require("../../core/database/db");

module.exports.register = async function (capabilities) {
  const { router, logger } = capabilities;

  logger.info("Patients Extension booting");

  function auth(...roles) {
    return (req, res, next) => {
      if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
      global.requireAuth(roles.length ? roles : undefined)(req, res, next);
    };
  }

  /* GET /patients - list (protected) */
  router.get("/patients", auth("admin", "lab_staff", "doctor"), async (req, res) => {
    try {
      const { q, page = 1, limit = 50 } = req.query;
      const offset = (Number(page) - 1) * Number(limit);
      const params = [];
      let where = "WHERE 1=1";

      if (q) {
        params.push(`%${q}%`);
        where += ` AND (name ILIKE $${params.length} OR national_id ILIKE $${params.length} OR phone ILIKE $${params.length})`;
      }

      params.push(Number(limit), offset);
      const result = await db.query(
        `SELECT * FROM patients ${where} ORDER BY created_at DESC LIMIT $${params.length - 1} OFFSET $${params.length}`,
        params
      );

      res.json({ ok: true, patients: result.rows });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* POST /patients - create (protected) */
  router.post("/patients", auth("admin", "lab_staff", "doctor"), async (req, res) => {
    try {
      const { name, national_id, birth_date, gender, phone, address, blood_type, notes } = req.body;

      if (!name) return res.status(400).json({ error: "name_required" });

      const result = await db.query(
        `INSERT INTO patients(name, national_id, birth_date, gender, phone, address, blood_type, notes)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *`,
        [name, national_id || null, birth_date || null, gender || null,
         phone || null, address || null, blood_type || null, notes || null]
      );

      res.status(201).json({ ok: true, patient: result.rows[0] });
    } catch (err) {
      if (err.code === "23505") return res.status(409).json({ error: "national_id_already_exists" });
      res.status(500).json({ error: err.message });
    }
  });

  /* GET /patients/:id - single patient */
  router.get("/patients/:id", auth("admin", "lab_staff", "doctor"), async (req, res) => {
    try {
      const result = await db.query("SELECT * FROM patients WHERE id=$1", [req.params.id]);
      if (!result.rows.length) return res.status(404).json({ error: "not_found" });
      res.json({ ok: true, patient: result.rows[0] });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* PATCH /patients/:id - update */
  router.patch("/patients/:id", auth("admin", "lab_staff", "doctor"), async (req, res) => {
    try {
      const { name, national_id, birth_date, gender, phone, address, blood_type, notes } = req.body;
      const result = await db.query(
        `UPDATE patients
         SET name=COALESCE($1,name), national_id=COALESCE($2,national_id),
             birth_date=COALESCE($3,birth_date), gender=COALESCE($4,gender),
             phone=COALESCE($5,phone), address=COALESCE($6,address),
             blood_type=COALESCE($7,blood_type), notes=COALESCE($8,notes),
             updated_at=NOW()
         WHERE id=$9 RETURNING *`,
        [name||null, national_id||null, birth_date||null, gender||null,
         phone||null, address||null, blood_type||null, notes||null, req.params.id]
      );
      if (!result.rows.length) return res.status(404).json({ error: "not_found" });
      res.json({ ok: true, patient: result.rows[0] });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* POST /patients/:id/link-user - link patient to user account */
  router.post("/patients/:id/link-user", auth("admin"), async (req, res) => {
    try {
      const { user_id } = req.body;
      if (!user_id) return res.status(400).json({ error: "user_id_required" });

      /* verify user exists and is patient/citizen */
      const userRes = await db.query("SELECT id, role FROM users WHERE id=$1", [user_id]);
      if (!userRes.rows.length) return res.status(404).json({ error: "user_not_found" });

      const result = await db.query(
        "UPDATE patients SET user_id=$1, updated_at=NOW() WHERE id=$2 RETURNING *",
        [user_id, req.params.id]
      );

      if (!result.rows.length) return res.status(404).json({ error: "patient_not_found" });

      /* also update user role to 'patient' if not already */
      if (!["patient", "citizen"].includes(userRes.rows[0].role)) {
        await db.query("UPDATE users SET role='patient' WHERE id=$1", [user_id]);
      }

      res.json({ ok: true, patient: result.rows[0] });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  logger.info("Patients Extension fully activated");
};
