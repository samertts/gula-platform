"use strict";

/*
==========================================================
NHOP LAB WORKFLOW EXTENSION
Complete laboratory workflow management:
  - Test catalog
  - Lab orders
  - Sample tracking
  - Result entry
  - Result approval & release
  - Reports
==========================================================
*/

const crypto = require("crypto");
const db     = require("../../core/database/db");

/* -------------------------------------------------------
   Barcode generator
------------------------------------------------------- */
function generateBarcode(prefix = "NHOP") {
  const ts  = Date.now().toString(36).toUpperCase();
  const rnd = crypto.randomBytes(3).toString("hex").toUpperCase();
  return `${prefix}-${ts}-${rnd}`;
}

/* -------------------------------------------------------
   Abnormal flag helper
------------------------------------------------------- */
function getAbnormalFlag(value, min, max) {
  const num = parseFloat(value);
  if (isNaN(num)) return null;
  if (min !== null && num < min) return "L";
  if (max !== null && num > max) return "H";
  return null;
}

module.exports.register = async function (capabilities) {
  const { router, logger, events } = capabilities;

  logger.info("Lab Workflow Extension booting");

  /* =======================================================
     TEST CATALOG
  ======================================================= */

  /* GET /lab/catalog - list all active tests */
  router.get("/lab/catalog", async (req, res) => {
    try {
      const { category } = req.query;
      let query  = "SELECT * FROM test_catalog WHERE is_active=TRUE";
      const params = [];

      if (category) {
        params.push(category);
        query += ` AND category=$${params.length}`;
      }

      query += " ORDER BY category, name_ar";
      const result = await db.query(query, params);
      res.json({ ok: true, tests: result.rows });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* GET /lab/catalog/categories - list categories */
  router.get("/lab/catalog/categories", async (req, res) => {
    try {
      const result = await db.query(
        "SELECT DISTINCT category FROM test_catalog WHERE is_active=TRUE ORDER BY category"
      );
      res.json({ ok: true, categories: result.rows.map(r => r.category) });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* POST /lab/catalog - add test (admin only) */
  router.post("/lab/catalog", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin"])(req, res, async () => {
      try {
        const { code, name_ar, name_en, category, sample_type, unit,
                normal_range_min, normal_range_max, normal_range_text, price, turnaround_hours } = req.body;

        if (!code || !name_ar || !name_en || !category) {
          return res.status(400).json({ error: "code, name_ar, name_en, category are required" });
        }

        const result = await db.query(
          `INSERT INTO test_catalog(code,name_ar,name_en,category,sample_type,unit,
             normal_range_min,normal_range_max,normal_range_text,price,turnaround_hours)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
           RETURNING *`,
          [code, name_ar, name_en, category, sample_type || "blood", unit || null,
           normal_range_min || null, normal_range_max || null, normal_range_text || null,
           price || 0, turnaround_hours || 24]
        );

        res.status(201).json({ ok: true, test: result.rows[0] });
      } catch (err) {
        if (err.code === "23505") return res.status(409).json({ error: "test_code_already_exists" });
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     LAB ORDERS
  ======================================================= */

  /* POST /lab/orders - create order (doctor or lab_staff) */
  router.post("/lab/orders", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["doctor", "lab_staff", "admin"])(req, res, async () => {
      try {
        const { patient_id, test_ids, clinical_notes, priority = "normal" } = req.body;

        if (!patient_id || !test_ids?.length) {
          return res.status(400).json({ error: "patient_id and test_ids[] required" });
        }

        /* validate patient */
        const pat = await db.query("SELECT id FROM patients WHERE id=$1", [patient_id]);
        if (!pat.rows.length) {
          return res.status(404).json({ error: "patient_not_found" });
        }

        /* create order */
        const orderRes = await db.query(
          `INSERT INTO lab_orders(patient_id, doctor_id, clinical_notes, priority, status)
           VALUES ($1,$2,$3,$4,'pending') RETURNING *`,
          [patient_id, req.user.id, clinical_notes || null, priority]
        );
        const order = orderRes.rows[0];

        /* validate tests exist */
        const testRes = await db.query(
          "SELECT id, sample_type FROM test_catalog WHERE id = ANY($1) AND is_active=TRUE",
          [test_ids]
        );
        if (!testRes.rows.length) {
          return res.status(404).json({ error: "no_valid_tests_found" });
        }

        /* create order items */
        for (const test of testRes.rows) {
          await db.query(
            "INSERT INTO lab_order_items(order_id, test_catalog_id) VALUES ($1,$2)",
            [order.id, test.id]
          );
        }

        /* group by sample type and create samples */
        const sampleTypes = [...new Set(testRes.rows.map(t => t.sample_type))];
        for (const stype of sampleTypes) {
          await db.query(
            `INSERT INTO samples(order_id, patient_id, sample_type, barcode, status)
             VALUES ($1,$2,$3,$4,'ordered')`,
            [order.id, patient_id, stype, generateBarcode()]
          );
        }

        logger.info("Lab order created", { orderId: order.id, patientId: patient_id });

        events?.publish?.("lab.order.created", { orderId: order.id, patientId: patient_id });

        res.status(201).json({ ok: true, order });

      } catch (err) {
        logger.error("Create order failed", { error: err.message });
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* GET /lab/orders - list orders */
  router.get("/lab/orders", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff", "doctor"])(req, res, async () => {
      try {
        const { status, patient_id, page = 1, limit = 30 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);
        const params = [];
        let where = "WHERE 1=1";

        if (status)     { params.push(status);     where += ` AND lo.status=$${params.length}`; }
        if (patient_id) { params.push(patient_id); where += ` AND lo.patient_id=$${params.length}`; }

        /* doctors see only their own orders */
        if (req.user.role === "doctor") {
          params.push(req.user.id);
          where += ` AND lo.doctor_id=$${params.length}`;
        }

        params.push(Number(limit), offset);

        const result = await db.query(
          `SELECT lo.*, p.name AS patient_name, p.national_id AS patient_national_id,
                  u.name AS doctor_name
           FROM lab_orders lo
           JOIN patients p ON p.id = lo.patient_id
           LEFT JOIN users u ON u.id = lo.doctor_id
           ${where}
           ORDER BY lo.created_at DESC
           LIMIT $${params.length - 1} OFFSET $${params.length}`,
          params
        );

        res.json({ ok: true, orders: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* GET /lab/orders/:id - get single order with items */
  router.get("/lab/orders/:id", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff", "doctor", "patient", "citizen"])(req, res, async () => {
      try {
        const orderRes = await db.query(
          `SELECT lo.*, p.name AS patient_name, p.national_id AS patient_national_id,
                  u.name AS doctor_name
           FROM lab_orders lo
           JOIN patients p ON p.id = lo.patient_id
           LEFT JOIN users u ON u.id = lo.doctor_id
           WHERE lo.id=$1`,
          [req.params.id]
        );

        if (!orderRes.rows.length) {
          return res.status(404).json({ error: "order_not_found" });
        }

        const order = orderRes.rows[0];

        /* patients can only see their own orders */
        if (["patient", "citizen"].includes(req.user.role)) {
          const pat = await db.query("SELECT id FROM patients WHERE user_id=$1", [req.user.id]);
          if (!pat.rows.length || pat.rows[0].id !== order.patient_id) {
            return res.status(403).json({ error: "access_denied" });
          }
        }

        /* get items */
        const items = await db.query(
          `SELECT loi.*, tc.name_ar, tc.name_en, tc.code, tc.unit,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text
           FROM lab_order_items loi
           JOIN test_catalog tc ON tc.id = loi.test_catalog_id
           WHERE loi.order_id=$1`,
          [req.params.id]
        );

        /* get samples */
        const samples = await db.query(
          "SELECT * FROM samples WHERE order_id=$1",
          [req.params.id]
        );

        /* get results */
        const results = await db.query(
          `SELECT tr.*, tc.name_ar, tc.name_en, tc.code,
                  u.name AS tech_name
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           LEFT JOIN users u ON u.id = tr.tech_id
           WHERE tr.sample_id = ANY(SELECT id FROM samples WHERE order_id=$1)
           ORDER BY tc.category, tc.name_ar`,
          [req.params.id]
        );

        res.json({
          ok: true,
          order,
          items: items.rows,
          samples: samples.rows,
          results: results.rows
        });

      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     SAMPLE MANAGEMENT
  ======================================================= */

  /* GET /lab/samples - list samples */
  router.get("/lab/samples", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff"])(req, res, async () => {
      try {
        const { status, page = 1, limit = 30 } = req.query;
        const offset = (Number(page) - 1) * Number(limit);
        const params = [];
        let where = "WHERE 1=1";

        if (status) {
          params.push(status);
          where += ` AND s.status=$${params.length}`;
        }

        params.push(Number(limit), offset);

        const result = await db.query(
          `SELECT s.*, p.name AS patient_name, p.national_id AS patient_national_id
           FROM samples s
           JOIN patients p ON p.id = s.patient_id
           ${where}
           ORDER BY s.created_at DESC
           LIMIT $${params.length - 1} OFFSET $${params.length}`,
          params
        );

        res.json({ ok: true, samples: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* PATCH /lab/samples/:id/collect - mark sample as collected */
  router.patch("/lab/samples/:id/collect", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const result = await db.query(
          `UPDATE samples SET status='collected', collected_at=NOW(), collector_id=$1, updated_at=NOW()
           WHERE id=$2 AND status='ordered' RETURNING *`,
          [req.user.id, req.params.id]
        );

        if (!result.rows.length) {
          return res.status(404).json({ error: "sample_not_found_or_already_collected" });
        }

        /* update order status */
        await db.query(
          `UPDATE lab_orders SET status='received', updated_at=NOW()
           WHERE id=$1 AND status='pending'`,
          [result.rows[0].order_id]
        );

        events?.publish?.("sample.collected", { sampleId: req.params.id });

        res.json({ ok: true, sample: result.rows[0] });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* PATCH /lab/samples/:id/receive - receive in lab */
  router.patch("/lab/samples/:id/receive", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const result = await db.query(
          `UPDATE samples SET status='received', received_at=NOW(), updated_at=NOW()
           WHERE id=$1 AND status='collected' RETURNING *`,
          [req.params.id]
        );

        if (!result.rows.length) {
          return res.status(404).json({ error: "sample_not_found_or_not_in_collected_state" });
        }

        /* update order items to processing */
        await db.query(
          `UPDATE lab_order_items SET status='collected'
           WHERE order_id=$1`,
          [result.rows[0].order_id]
        );

        await db.query(
          `UPDATE lab_orders SET status='processing', updated_at=NOW() WHERE id=$1`,
          [result.rows[0].order_id]
        );

        res.json({ ok: true, sample: result.rows[0] });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* PATCH /lab/samples/:id/reject - reject sample */
  router.patch("/lab/samples/:id/reject", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const { reason } = req.body;
        const result = await db.query(
          `UPDATE samples SET status='rejected', rejection_reason=$1, updated_at=NOW()
           WHERE id=$2 RETURNING *`,
          [reason || "No reason given", req.params.id]
        );

        if (!result.rows.length) {
          return res.status(404).json({ error: "sample_not_found" });
        }

        res.json({ ok: true, sample: result.rows[0] });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     RESULT ENTRY
  ======================================================= */

  /* POST /lab/results - enter test results */
  router.post("/lab/results", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const { sample_id, results } = req.body;
        /* results: [{test_catalog_id, value, notes}] */

        if (!sample_id || !results?.length) {
          return res.status(400).json({ error: "sample_id and results[] required" });
        }

        /* get sample */
        const sampleRes = await db.query("SELECT * FROM samples WHERE id=$1", [sample_id]);
        if (!sampleRes.rows.length) {
          return res.status(404).json({ error: "sample_not_found" });
        }
        const sample = sampleRes.rows[0];

        const inserted = [];

        for (const r of results) {
          const { test_catalog_id, value, notes } = r;

          /* get catalog info for range check */
          const catRes = await db.query(
            "SELECT unit, normal_range_min, normal_range_max FROM test_catalog WHERE id=$1",
            [test_catalog_id]
          );
          if (!catRes.rows.length) continue;
          const cat = catRes.rows[0];

          const flag    = getAbnormalFlag(value, cat.normal_range_min, cat.normal_range_max);
          const numVal  = parseFloat(value);

          /* get order_item_id */
          const itemRes = await db.query(
            `SELECT id FROM lab_order_items WHERE order_id=$1 AND test_catalog_id=$2`,
            [sample.order_id, test_catalog_id]
          );
          const orderItemId = itemRes.rows[0]?.id || null;

          const res2 = await db.query(
            `INSERT INTO test_results
               (sample_id, order_item_id, test_catalog_id, patient_id, value, value_numeric,
                unit, status, is_abnormal, abnormal_flag, tech_id, notes)
             VALUES ($1,$2,$3,$4,$5,$6,$7,'resulted',$8,$9,$10,$11)
             ON CONFLICT DO NOTHING
             RETURNING *`,
            [sample_id, orderItemId, test_catalog_id, sample.patient_id,
             value, isNaN(numVal) ? null : numVal,
             cat.unit, !!flag, flag, req.user.id, notes || null]
          );

          if (res2.rows.length) {
            inserted.push(res2.rows[0]);

            /* update order item status */
            if (orderItemId) {
              await db.query(
                "UPDATE lab_order_items SET status='resulted' WHERE id=$1",
                [orderItemId]
              );
            }
          }
        }

        /* update sample status */
        await db.query(
          "UPDATE samples SET status='processing', updated_at=NOW() WHERE id=$1",
          [sample_id]
        );

        logger.info("Results entered", { sampleId: sample_id, count: inserted.length });

        res.status(201).json({ ok: true, results: inserted });

      } catch (err) {
        logger.error("Result entry failed", { error: err.message });
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* PATCH /lab/results/:id/approve - approve result */
  router.patch("/lab/results/:id/approve", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const { notes } = req.body;

        const result = await db.query(
          `UPDATE test_results
           SET status='approved', approved_by=$1, approved_at=NOW(), updated_at=NOW(),
               notes=COALESCE($2, notes)
           WHERE id=$3 AND status='resulted'
           RETURNING *`,
          [req.user.id, notes || null, req.params.id]
        );

        if (!result.rows.length) {
          return res.status(404).json({ error: "result_not_found_or_not_in_resulted_state" });
        }

        res.json({ ok: true, result: result.rows[0] });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* POST /lab/results/:id/release - release result to patient */
  router.post("/lab/orders/:id/release", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        /* release all approved results for an order */
        await db.query(
          `UPDATE test_results SET status='released', updated_at=NOW()
           WHERE sample_id IN (SELECT id FROM samples WHERE order_id=$1)
             AND status='approved'`,
          [req.params.id]
        );

        /* mark order complete */
        await db.query(
          "UPDATE lab_orders SET status='completed', updated_at=NOW() WHERE id=$1",
          [req.params.id]
        );

        /* update all items */
        await db.query(
          "UPDATE lab_order_items SET status='approved' WHERE order_id=$1",
          [req.params.id]
        );

        /* get order info to publish event */
        const orderRes = await db.query(
          "SELECT patient_id FROM lab_orders WHERE id=$1",
          [req.params.id]
        );

        if (orderRes.rows.length) {
          events?.publish?.("lab.result.created", {
            orderId:   req.params.id,
            patientId: orderRes.rows[0].patient_id
          });
        }

        res.json({ ok: true, message: "results_released_to_patient" });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     REPORTS
  ======================================================= */

  /* GET /lab/reports/:orderId - get full report */
  router.get("/lab/reports/:orderId", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth()(req, res, async () => {
      try {
        const { orderId } = req.params;

        /* get order */
        const orderRes = await db.query(
          `SELECT lo.*, p.name AS patient_name, p.national_id, p.birth_date, p.gender,
                  u.name AS doctor_name
           FROM lab_orders lo
           JOIN patients p ON p.id = lo.patient_id
           LEFT JOIN users u ON u.id = lo.doctor_id
           WHERE lo.id=$1`,
          [orderId]
        );

        if (!orderRes.rows.length) {
          return res.status(404).json({ error: "order_not_found" });
        }

        const order = orderRes.rows[0];

        /* access control: patients only see released orders */
        if (["patient", "citizen"].includes(req.user.role)) {
          const pat = await db.query("SELECT id FROM patients WHERE user_id=$1", [req.user.id]);
          const patId = pat.rows[0]?.id;
          if (patId !== order.patient_id) {
            return res.status(403).json({ error: "access_denied" });
          }
          if (order.status !== "completed") {
            return res.status(403).json({ error: "results_not_released_yet" });
          }
        }

        /* get results grouped by category */
        const results = await db.query(
          `SELECT tr.*, tc.name_ar, tc.name_en, tc.code, tc.category,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text,
                  approver.name AS approved_by_name,
                  tech.name AS tech_name
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           LEFT JOIN users approver ON approver.id = tr.approved_by
           LEFT JOIN users tech ON tech.id = tr.tech_id
           WHERE tr.sample_id IN (SELECT id FROM samples WHERE order_id=$1)
           ORDER BY tc.category, tc.name_ar`,
          [orderId]
        );

        /* group by category */
        const grouped = {};
        for (const r of results.rows) {
          if (!grouped[r.category]) grouped[r.category] = [];
          grouped[r.category].push(r);
        }

        const report = {
          report_id:    `RPT-${orderId.slice(0, 8).toUpperCase()}`,
          generated_at: new Date().toISOString(),
          order: {
            id:            order.id,
            status:        order.status,
            priority:      order.priority,
            clinical_notes: order.clinical_notes,
            created_at:   order.created_at
          },
          patient: {
            name:       order.patient_name,
            national_id: order.national_id,
            birth_date:  order.birth_date,
            gender:      order.gender
          },
          doctor:   order.doctor_name || "N/A",
          results:  grouped,
          abnormal_count: results.rows.filter(r => r.is_abnormal).length,
          total_tests:    results.rows.length
        };

        res.json({ ok: true, report });

      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     DASHBOARD STATS (lab staff)
  ======================================================= */

  /* GET /lab/stats - lab dashboard stats */
  router.get("/lab/stats", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff"])(req, res, async () => {
      try {
        const [orders, samples, results] = await Promise.all([
          db.query(
            `SELECT status, COUNT(*) as count FROM lab_orders
             WHERE created_at > NOW() - INTERVAL '7 days'
             GROUP BY status`
          ),
          db.query(
            `SELECT status, COUNT(*) as count FROM samples
             WHERE created_at > NOW() - INTERVAL '7 days'
             GROUP BY status`
          ),
          db.query(
            `SELECT COUNT(*) as total,
                    COUNT(CASE WHEN is_abnormal=TRUE THEN 1 END) as abnormal
             FROM test_results
             WHERE created_at > NOW() - INTERVAL '7 days'`
          )
        ]);

        const orderStats  = {};
        for (const r of orders.rows) orderStats[r.status] = parseInt(r.count);

        const sampleStats = {};
        for (const r of samples.rows) sampleStats[r.status] = parseInt(r.count);

        res.json({
          ok: true,
          period: "last_7_days",
          orders:  orderStats,
          samples: sampleStats,
          results: {
            total:    parseInt(results.rows[0]?.total || 0),
            abnormal: parseInt(results.rows[0]?.abnormal || 0)
          }
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  logger.info("Lab Workflow Extension fully activated");
};
