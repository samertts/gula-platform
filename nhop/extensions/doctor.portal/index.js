"use strict";

/*
==========================================================
NHOP DOCTOR PORTAL EXTENSION
Features for medical doctors:
  - Patient management
  - Lab order creation
  - Result viewing with AI support
  - Patient history
==========================================================
*/

const db = require("../../core/database/db");

module.exports.register = async function (capabilities) {
  const { router, logger, events } = capabilities;

  logger.info("Doctor Portal Extension booting");

  const auth = () => {
    if (!global.requireAuth) throw new Error("auth_not_loaded");
    return global.requireAuth(["doctor", "admin"]);
  };

  /* =======================================================
     PATIENT SEARCH & MANAGEMENT
  ======================================================= */

  /* GET /doctor/patients - search patients */
  router.get("/doctor/patients", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin"])(req, res, async () => {
      try {
        const { q, page = 1, limit = 20 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);
        const params = [];
        let where = "WHERE 1=1";

        if (q) {
          params.push(`%${q}%`);
          where += ` AND (p.name ILIKE $${params.length} OR p.national_id ILIKE $${params.length} OR p.phone ILIKE $${params.length})`;
        }

        params.push(Number(limit), offset);

        const result = await db.query(
          `SELECT p.*,
                  (SELECT COUNT(*) FROM lab_orders lo WHERE lo.patient_id=p.id) AS total_orders,
                  (SELECT MAX(lo.created_at) FROM lab_orders lo WHERE lo.patient_id=p.id) AS last_order_date
           FROM patients p
           ${where}
           ORDER BY p.created_at DESC
           LIMIT $${params.length - 1} OFFSET $${params.length}`,
          params
        );

        res.json({ ok: true, patients: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* POST /doctor/patients - create patient */
  router.post("/doctor/patients", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin", "lab_staff"])(req, res, async () => {
      try {
        const { name, national_id, birth_date, gender, phone, address, blood_type, notes } = req.body;

        if (!name) {
          return res.status(400).json({ error: "patient_name_required" });
        }

        const result = await db.query(
          `INSERT INTO patients(name, national_id, birth_date, gender, phone, address, blood_type, notes)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
           RETURNING *`,
          [name, national_id || null, birth_date || null, gender || null,
           phone || null, address || null, blood_type || null, notes || null]
        );

        if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "patient_created", entityType: "patient", entityId: result.rows[0].id, ip: req.ip });

        res.status(201).json({ ok: true, patient: result.rows[0] });
      } catch (err) {
        if (err.code === "23505") return res.status(409).json({ error: "national_id_already_exists" });
        res.status(500).json({ error: "patient_creation_failed" });
      }
    });
  });

  /* GET /doctor/patients/:id - patient full profile */
  router.get("/doctor/patients/:id", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin", "lab_staff"])(req, res, async () => {
      try {
        const patRes = await db.query("SELECT * FROM patients WHERE id=$1", [req.params.id]);
        if (!patRes.rows.length) {
          return res.status(404).json({ error: "patient_not_found" });
        }

        /* recent orders */
        const orders = await db.query(
          `SELECT lo.*, u.name AS doctor_name
           FROM lab_orders lo
           LEFT JOIN users u ON u.id = lo.doctor_id
           WHERE lo.patient_id=$1
           ORDER BY lo.created_at DESC
           LIMIT 10`,
          [req.params.id]
        );

        /* recent abnormal results */
        const abnormals = await db.query(
          `SELECT tr.value, tr.abnormal_flag, tr.created_at,
                  tc.name_ar, tc.name_en, tc.unit, tc.normal_range_min, tc.normal_range_max
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           WHERE tr.patient_id=$1 AND tr.is_abnormal=TRUE
           ORDER BY tr.created_at DESC
           LIMIT 20`,
          [req.params.id]
        );

        res.json({
          ok: true,
          patient:          patRes.rows[0],
          recent_orders:    orders.rows,
          abnormal_results: abnormals.rows
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     DOCTOR DASHBOARD
  ======================================================= */

  /* GET /doctor/dashboard - doctor's own stats */
  router.get("/doctor/dashboard", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin"])(req, res, async () => {
      try {
        const doctorId = req.user.role === "doctor" ? req.user.id : null;
        const params   = doctorId ? [doctorId] : [];
        const filter   = doctorId ? "WHERE lo.doctor_id=$1" : "";

        const [orders, recent] = await Promise.all([
          db.query(
            `SELECT status, COUNT(*) as count FROM lab_orders lo
             ${filter}
             GROUP BY status`,
            params
          ),
          db.query(
            `SELECT lo.id, lo.status, lo.priority, lo.created_at,
                    p.name AS patient_name, p.national_id
             FROM lab_orders lo
             JOIN patients p ON p.id = lo.patient_id
             ${filter}
             ORDER BY lo.created_at DESC
             LIMIT 10`,
            params
          )
        ]);

        const orderStats = {};
        for (const r of orders.rows) orderStats[r.status] = parseInt(r.count);

        res.json({
          ok: true,
          doctor: req.user.name,
          orders: orderStats,
          recent_orders: recent.rows
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     RESULT HISTORY FOR A PATIENT
  ======================================================= */

  /* GET /doctor/patients/:id/results - full result history */
  router.get("/doctor/patients/:id/results", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin"])(req, res, async () => {
      try {
        const { test_code, from_date, to_date, page = 1, limit = 50 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);
        const params = [req.params.id];
        let where = "WHERE tr.patient_id=$1 AND tr.status IN ('approved','released')";

        if (test_code) {
          params.push(test_code);
          where += ` AND tc.code=$${params.length}`;
        }
        if (from_date) {
          params.push(from_date);
          where += ` AND tr.created_at >= $${params.length}`;
        }
        if (to_date) {
          params.push(to_date);
          where += ` AND tr.created_at <= $${params.length}`;
        }

        params.push(Number(limit), offset);

        const result = await db.query(
          `SELECT tr.id, tr.value, tr.value_numeric, tr.unit, tr.is_abnormal,
                  tr.abnormal_flag, tr.created_at,
                  tc.name_ar, tc.name_en, tc.code, tc.category,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           ${where}
           ORDER BY tr.created_at DESC
           LIMIT $${params.length - 1} OFFSET $${params.length}`,
          params
        );

        res.json({ ok: true, results: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     AI-ENHANCED RESULT ANALYSIS
  ======================================================= */

  /* POST /doctor/analyze/:patientId - AI analysis for patient */
  router.post("/doctor/analyze/:patientId", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "admin"])(req, res, async () => {
      try {
        /* Verify patient exists */
        const patCheck = await db.query("SELECT id FROM patients WHERE id=$1", [req.params.patientId]);
        if (!patCheck.rows.length) {
          return res.status(404).json({ error: "patient_not_found" });
        }

        /* Doctors can only analyze patients they have ordered tests for (unless admin) */
        if (req.user.role === "doctor") {
          const access = await db.query(
            "SELECT 1 FROM lab_orders WHERE patient_id=$1 AND doctor_id=$2 LIMIT 1",
            [req.params.patientId, req.user.id]
          );
          if (!access.rows.length) {
            return res.status(403).json({ error: "access_denied_no_orders_for_this_patient" });
          }
        }

        /* get latest results for patient */
        const results = await db.query(
          `SELECT tr.value_numeric AS value, tc.code AS test, tc.name_ar,
                  tc.normal_range_min, tc.normal_range_max, tr.is_abnormal
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           WHERE tr.patient_id=$1 AND tr.status IN ('approved','released')
           ORDER BY tr.created_at DESC`,
          [req.params.patientId]
        );

        /* build analysis payload */
        const labValues = {};
        for (const r of results.rows) {
          if (r.value !== null && !labValues[r.test]) {
            labValues[r.test] = r.value;
          }
        }

        /* basic rule-based analysis */
        const flags = [];
        const recommendations = [];
        let riskLevel = "low";

        if (labValues.GLU > 200) {
          flags.push({ test: "GLU", message: "ارتفاع السكر - يحتمل سكري غير منضبط", severity: "high" });
          recommendations.push("مراجعة وضع السكر وإعادة قياس HBA1C");
          riskLevel = "high";
        } else if (labValues.GLU > 126) {
          flags.push({ test: "GLU", message: "سكر مرتفع - مراقبة مطلوبة", severity: "medium" });
          riskLevel = "medium";
        }

        if (labValues.WBC > 12) {
          flags.push({ test: "WBC", message: "كريات بيضاء مرتفعة - احتمال عدوى أو التهاب", severity: "medium" });
          recommendations.push("فحص مزرعة دم إن استدعى الأمر");
          if (riskLevel !== "high") riskLevel = "medium";
        }

        if (labValues.HGB < 12) {
          flags.push({ test: "HGB", message: "هيموجلوبين منخفض - فقر دم محتمل", severity: "medium" });
          recommendations.push("فحص الحديد وفيريتين وB12");
        }

        if (labValues.CREA > 1.3) {
          flags.push({ test: "CREA", message: "كرياتينين مرتفع - مراقبة وظائف الكلى", severity: "medium" });
          recommendations.push("متابعة مع أخصائي الكلى");
          if (riskLevel !== "high") riskLevel = "medium";
        }

        if (labValues.CHOL > 240) {
          flags.push({ test: "CHOL", message: "كولسترول مرتفع - خطر قلبي وعائي", severity: "medium" });
          recommendations.push("نظام غذائي ونمط حياة صحي، مراجعة العلاج");
        }

        if (labValues.TSH > 4.5) {
          flags.push({ test: "TSH", message: "TSH مرتفع - خمول الغدة الدرقية محتمل", severity: "medium" });
          recommendations.push("متابعة T3 وT4 مع استشارة الغدد الصماء");
        }

        if (labValues.VITD < 20) {
          flags.push({ test: "VITD", message: "نقص فيتامين د", severity: "low" });
          recommendations.push("مكملات فيتامين د والتعرض للشمس");
        }

        const abnormalsCount = results.rows.filter(r => r.is_abnormal).length;

        res.json({
          ok: true,
          patient_id: req.params.patientId,
          analysis: {
            risk_level:      riskLevel,
            abnormal_count:  abnormalsCount,
            total_tests:     results.rows.length,
            flags,
            recommendations,
            disclaimer:      "هذا التحليل مساعد للطبيب وليس تشخيصاً طبياً نهائياً"
          },
          lab_values: labValues
        });

      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  logger.info("Doctor Portal Extension fully activated");
};
