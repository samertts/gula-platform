"use strict";

/*
==========================================================
NHOP PATIENT & CITIZEN PORTAL EXTENSION
Self-service features for patients and citizens:
  - View own lab results
  - Track sample status
  - Download reports
  - Health history summary
==========================================================
*/

const db = require("../../core/database/db");

module.exports.register = async function (capabilities) {
  const { router, logger } = capabilities;

  logger.info("Patient Portal Extension booting");

  /* -------------------------------------------------------
     Helper: get patient record for logged-in user
  ------------------------------------------------------- */
  async function getMyPatient(userId) {
    const r = await db.query("SELECT * FROM patients WHERE user_id=$1", [userId]);
    return r.rows[0] || null;
  }

  /* =======================================================
     PROFILE
  ======================================================= */

  /* GET /portal/me - get my patient profile */
  router.get("/portal/me", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);

        if (!patient) {
          return res.status(404).json({
            error: "patient_profile_not_found",
            hint: "Your account is not linked to a patient record yet"
          });
        }

        res.json({ ok: true, patient });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* PATCH /portal/me - update my profile */
  router.patch("/portal/me", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        const { phone, address, blood_type } = req.body;

        await db.query(
          `UPDATE patients
           SET phone=COALESCE($1,phone), address=COALESCE($2,address),
               blood_type=COALESCE($3,blood_type), updated_at=NOW()
           WHERE id=$4`,
          [phone || null, address || null, blood_type || null, patient.id]
        );

        const updated = await db.query("SELECT * FROM patients WHERE id=$1", [patient.id]);
        res.json({ ok: true, patient: updated.rows[0] });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     MY ORDERS & SAMPLES
  ======================================================= */

  /* GET /portal/orders - my lab orders */
  router.get("/portal/orders", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        const { page = 1, limit = 20 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);

        const result = await db.query(
          `SELECT lo.id, lo.status, lo.priority, lo.created_at, lo.updated_at,
                  u.name AS doctor_name,
                  COUNT(loi.id) AS test_count,
                  COUNT(CASE WHEN loi.status='approved' OR loi.status='resulted' THEN 1 END) AS completed_tests
           FROM lab_orders lo
           LEFT JOIN users u ON u.id = lo.doctor_id
           LEFT JOIN lab_order_items loi ON loi.order_id = lo.id
           WHERE lo.patient_id=$1
           GROUP BY lo.id, u.name
           ORDER BY lo.created_at DESC
           LIMIT $2 OFFSET $3`,
          [patient.id, Number(limit), offset]
        );

        res.json({ ok: true, orders: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* GET /portal/orders/:id/status - track sample status */
  router.get("/portal/orders/:id/status", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        const orderRes = await db.query(
          "SELECT * FROM lab_orders WHERE id=$1 AND patient_id=$2",
          [req.params.id, patient.id]
        );

        if (!orderRes.rows.length) {
          return res.status(404).json({ error: "order_not_found" });
        }

        const order = orderRes.rows[0];

        const samples = await db.query(
          "SELECT id, sample_type, barcode, status, collected_at, received_at FROM samples WHERE order_id=$1",
          [req.params.id]
        );

        const items = await db.query(
          `SELECT loi.status, tc.name_ar, tc.name_en
           FROM lab_order_items loi
           JOIN test_catalog tc ON tc.id = loi.test_catalog_id
           WHERE loi.order_id=$1`,
          [req.params.id]
        );

        /* status timeline */
        const timeline = buildTimeline(order, samples.rows);

        res.json({
          ok: true,
          order: {
            id:         order.id,
            status:     order.status,
            priority:   order.priority,
            created_at: order.created_at
          },
          samples:  samples.rows,
          tests:    items.rows,
          timeline,
          is_ready: order.status === "completed"
        });

      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  function buildTimeline(order, samples) {
    const steps = [
      {
        step:   "order_placed",
        label:  "تم إنشاء الطلب",
        done:   true,
        time:   order.created_at
      },
      {
        step:   "sample_collected",
        label:  "تم أخذ العينة",
        done:   samples.some(s => s.status !== "ordered"),
        time:   samples[0]?.collected_at || null
      },
      {
        step:   "sample_received",
        label:  "استلام العينة في المختبر",
        done:   samples.some(s => ["received","processing","completed"].includes(s.status)),
        time:   samples[0]?.received_at || null
      },
      {
        step:   "processing",
        label:  "جاري تحليل العينات",
        done:   ["processing","completed"].includes(order.status),
        time:   null
      },
      {
        step:   "completed",
        label:  "النتائج جاهزة",
        done:   order.status === "completed",
        time:   order.status === "completed" ? order.updated_at : null
      }
    ];
    return steps;
  }

  /* =======================================================
     MY RESULTS
  ======================================================= */

  /* GET /portal/results - my released results */
  router.get("/portal/results", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        const { page = 1, limit = 30 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);

        const result = await db.query(
          `SELECT tr.id, tr.value, tr.unit, tr.is_abnormal, tr.abnormal_flag,
                  tr.created_at, tr.status,
                  tc.name_ar, tc.name_en, tc.code, tc.category,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text,
                  lo.id AS order_id
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           JOIN samples s ON s.id = tr.sample_id
           JOIN lab_orders lo ON lo.id = s.order_id
           WHERE tr.patient_id=$1 AND tr.status='released'
           ORDER BY tr.created_at DESC
           LIMIT $2 OFFSET $3`,
          [patient.id, Number(limit), offset]
        );

        res.json({ ok: true, results: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* GET /portal/report/:orderId - my full report */
  router.get("/portal/report/:orderId", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        /* verify order belongs to this patient and is completed */
        const orderRes = await db.query(
          "SELECT * FROM lab_orders WHERE id=$1 AND patient_id=$2 AND status='completed'",
          [req.params.orderId, patient.id]
        );

        if (!orderRes.rows.length) {
          return res.status(404).json({
            error: "report_not_available",
            hint: "Order not found or results not released yet"
          });
        }

        const order = orderRes.rows[0];

        /* get results */
        const results = await db.query(
          `SELECT tr.value, tr.unit, tr.is_abnormal, tr.abnormal_flag, tr.created_at,
                  tc.name_ar, tc.name_en, tc.code, tc.category,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           WHERE tr.sample_id IN (SELECT id FROM samples WHERE order_id=$1)
             AND tr.status='released'
           ORDER BY tc.category, tc.name_ar`,
          [req.params.orderId]
        );

        /* group by category */
        const grouped = {};
        for (const r of results.rows) {
          if (!grouped[r.category]) grouped[r.category] = [];
          grouped[r.category].push(r);
        }

        const report = {
          report_id:      `RPT-${order.id.slice(0, 8).toUpperCase()}`,
          generated_at:   new Date().toISOString(),
          patient: {
            name:       patient.name,
            national_id: patient.national_id,
            birth_date:  patient.birth_date,
            gender:      patient.gender
          },
          order_date:     order.created_at,
          results_by_category: grouped,
          abnormal_count: results.rows.filter(r => r.is_abnormal).length,
          total_tests:    results.rows.length,
          disclaimer:     "هذه النتائج للمراجعة الطبية فقط. استشر طبيبك للتفسير الصحيح."
        };

        res.json({ ok: true, report });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     HEALTH SUMMARY
  ======================================================= */

  /* GET /portal/health-summary - personal health trends */
  router.get("/portal/health-summary", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["patient", "citizen"])(req, res, async () => {
      try {
        const patient = await getMyPatient(req.user.id);
        if (!patient) {
          return res.status(404).json({ error: "patient_profile_not_found" });
        }

        /* get all released results */
        const results = await db.query(
          `SELECT tr.value_numeric, tr.is_abnormal, tr.created_at,
                  tc.code, tc.name_ar, tc.unit,
                  tc.normal_range_min, tc.normal_range_max
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           WHERE tr.patient_id=$1 AND tr.status='released' AND tr.value_numeric IS NOT NULL
           ORDER BY tc.code, tr.created_at ASC`,
          [patient.id]
        );

        /* group by test code for trends */
        const trends = {};
        for (const r of results.rows) {
          if (!trends[r.code]) {
            trends[r.code] = {
              name_ar:           r.name_ar,
              unit:              r.unit,
              normal_range_min:  r.normal_range_min,
              normal_range_max:  r.normal_range_max,
              values:            []
            };
          }
          trends[r.code].values.push({
            value: r.value_numeric,
            date:  r.created_at,
            is_abnormal: r.is_abnormal
          });
        }

        /* summary counts */
        const totalResults  = results.rows.length;
        const abnormalCount = results.rows.filter(r => r.is_abnormal).length;

        res.json({
          ok: true,
          patient: { name: patient.name },
          summary: {
            total_results:    totalResults,
            abnormal_results: abnormalCount,
            tests_tracked:    Object.keys(trends).length
          },
          trends
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  logger.info("Patient Portal Extension fully activated");
};
