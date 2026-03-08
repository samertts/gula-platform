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

  /* GET /lab/catalog - list all active tests (requires auth) */
  router.get("/lab/catalog", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff", "doctor", "patient", "citizen"])(req, res, async () => {
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
        res.status(500).json({ error: "catalog_fetch_failed" });
      }
    });
  });

  /* GET /lab/catalog/categories - list categories (requires auth) */
  router.get("/lab/catalog/categories", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff", "doctor", "patient", "citizen"])(req, res, async () => {
      try {
        const result = await db.query(
          "SELECT DISTINCT category FROM test_catalog WHERE is_active=TRUE ORDER BY category"
        );
        res.json({ ok: true, categories: result.rows.map(r => r.category) });
      } catch (err) {
        res.status(500).json({ error: "categories_fetch_failed" });
      }
    });
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
        const rawPage  = Math.max(1, Number(req.query.page)  || 1);
        const rawLimit = Math.min(100, Math.max(1, Number(req.query.limit) || 30));
        const offset   = (rawPage - 1) * rawLimit;
        const params = [];
        const { status, patient_id } = req.query;
        let where = "WHERE 1=1";

        if (status)     { params.push(status);     where += ` AND lo.status=$${params.length}`; }
        if (patient_id) { params.push(patient_id); where += ` AND lo.patient_id=$${params.length}`; }

        /* doctors see only their own orders */
        if (req.user.role === "doctor") {
          params.push(req.user.id);
          where += ` AND lo.doctor_id=$${params.length}`;
        }

        params.push(rawLimit, offset);

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
        const { status } = req.query;
        const rawPage  = Math.max(1, Number(req.query.page)  || 1);
        const rawLimit = Math.min(100, Math.max(1, Number(req.query.limit) || 30));
        const offset   = (rawPage - 1) * rawLimit;
        const params = [];
        let where = "WHERE 1=1";

        if (status) {
          params.push(status);
          where += ` AND s.status=$${params.length}`;
        }

        params.push(rawLimit, offset);

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

  /* POST /lab/results - enter test results (wrapped in DB transaction) */
  router.post("/lab/results", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      const { sample_id, results } = req.body;
      /* results: [{test_catalog_id, value, notes}] */

      if (!sample_id || !results?.length) {
        return res.status(400).json({ error: "sample_id and results[] required" });
      }

      /* Validate max batch size */
      if (results.length > 50) {
        return res.status(400).json({ error: "max_50_results_per_request" });
      }

      const client = await db.pool.connect();
      try {
        await client.query("BEGIN");

        /* get sample — lock row for this transaction */
        const sampleRes = await client.query("SELECT * FROM samples WHERE id=$1 FOR UPDATE", [sample_id]);
        if (!sampleRes.rows.length) {
          await client.query("ROLLBACK");
          return res.status(404).json({ error: "sample_not_found" });
        }
        const sample = sampleRes.rows[0];

        if (!["received", "processing"].includes(sample.status)) {
          await client.query("ROLLBACK");
          return res.status(409).json({ error: "sample_not_in_valid_state_for_results", state: sample.status });
        }

        const inserted = [];

        for (const r of results) {
          const { test_catalog_id, value, notes } = r;
          if (!test_catalog_id || value === undefined || value === null || value === "") continue;

          const catRes = await client.query(
            "SELECT unit, normal_range_min, normal_range_max FROM test_catalog WHERE id=$1",
            [test_catalog_id]
          );
          if (!catRes.rows.length) continue;
          const cat = catRes.rows[0];

          const flag   = getAbnormalFlag(value, cat.normal_range_min, cat.normal_range_max);
          const numVal = parseFloat(value);

          const itemRes = await client.query(
            `SELECT id FROM lab_order_items WHERE order_id=$1 AND test_catalog_id=$2`,
            [sample.order_id, test_catalog_id]
          );
          const orderItemId = itemRes.rows[0]?.id || null;

          const ins = await client.query(
            `INSERT INTO test_results
               (sample_id, order_item_id, test_catalog_id, patient_id, value, value_numeric,
                unit, status, is_abnormal, abnormal_flag, tech_id, notes)
             VALUES ($1,$2,$3,$4,$5,$6,$7,'resulted',$8,$9,$10,$11)
             ON CONFLICT DO NOTHING
             RETURNING *`,
            [sample_id, orderItemId, test_catalog_id, sample.patient_id,
             String(value), isNaN(numVal) ? null : numVal,
             cat.unit, !!flag, flag, req.user.id, notes || null]
          );

          if (ins.rows.length) {
            inserted.push(ins.rows[0]);
            if (orderItemId) {
              await client.query("UPDATE lab_order_items SET status='resulted' WHERE id=$1", [orderItemId]);
            }
          }
        }

        await client.query(
          "UPDATE samples SET status='processing', updated_at=NOW() WHERE id=$1",
          [sample_id]
        );

        await client.query("COMMIT");

        logger.info("Results entered", { sampleId: sample_id, count: inserted.length, tech: req.user.id });

        if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "results_entered", entityType: "sample", entityId: sample_id, details: { count: inserted.length }, ip: req.ip });

        res.status(201).json({ ok: true, results: inserted });

      } catch (err) {
        await client.query("ROLLBACK").catch(() => {});
        logger.error("Result entry failed — rolled back", { error: err.message });
        res.status(500).json({ error: "result_entry_failed" });
      } finally {
        client.release();
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

        if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "result_approved", entityType: "test_result", entityId: req.params.id, ip: req.ip });

        res.json({ ok: true, result: result.rows[0] });
      } catch (err) {
        res.status(500).json({ error: "approval_failed" });
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

        if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "order_released", entityType: "lab_order", entityId: req.params.id, ip: req.ip });

        res.json({ ok: true, message: "results_released_to_patient" });
      } catch (err) {
        res.status(500).json({ error: "release_failed" });
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

  /* =======================================================
     WORK QUEUE — what needs to be done right now
  ======================================================= */

  /* GET /lab/work-queue - pending tasks for lab staff */
  router.get("/lab/work-queue", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff"])(req, res, async () => {
      try {
        const [toCollect, toReceive, toResult, toApprove, toRelease] = await Promise.all([
          /* samples needing collection */
          db.query(
            `SELECT s.id, s.barcode, s.sample_type, s.created_at,
                    p.name AS patient_name, lo.priority
             FROM samples s
             JOIN patients p ON p.id = s.patient_id
             JOIN lab_orders lo ON lo.id = s.order_id
             WHERE s.status='ordered'
             ORDER BY CASE lo.priority WHEN 'stat' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END, s.created_at ASC
             LIMIT 20`
          ),
          /* samples received, need lab processing */
          db.query(
            `SELECT s.id, s.barcode, s.sample_type, s.received_at,
                    p.name AS patient_name, lo.priority
             FROM samples s
             JOIN patients p ON p.id = s.patient_id
             JOIN lab_orders lo ON lo.id = s.order_id
             WHERE s.status='received'
             ORDER BY CASE lo.priority WHEN 'stat' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END
             LIMIT 20`
          ),
          /* results to be entered */
          db.query(
            `SELECT s.id, s.barcode, s.sample_type, s.received_at,
                    p.name AS patient_name, lo.priority,
                    COUNT(loi.id) AS test_count
             FROM samples s
             JOIN patients p ON p.id = s.patient_id
             JOIN lab_orders lo ON lo.id = s.order_id
             JOIN lab_order_items loi ON loi.order_id = lo.id AND loi.status = 'pending'
             WHERE s.status IN ('received','processing')
             GROUP BY s.id, p.name, lo.priority
             ORDER BY CASE lo.priority WHEN 'stat' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END
             LIMIT 20`
          ),
          /* results needing approval */
          db.query(
            `SELECT tr.id, tr.value, tr.is_abnormal, tr.abnormal_flag,
                    tr.created_at, tc.name_ar, tc.code,
                    p.name AS patient_name, lo.priority
             FROM test_results tr
             JOIN test_catalog tc ON tc.id = tr.test_catalog_id
             JOIN samples s ON s.id = tr.sample_id
             JOIN lab_orders lo ON lo.id = s.order_id
             JOIN patients p ON p.id = tr.patient_id
             WHERE tr.status='resulted'
             ORDER BY tr.is_abnormal DESC,
               CASE lo.priority WHEN 'stat' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END
             LIMIT 30`
          ),
          /* orders with all results approved, ready to release */
          db.query(
            `SELECT lo.id, lo.priority, lo.updated_at,
                    p.name AS patient_name,
                    COUNT(tr.id) AS result_count
             FROM lab_orders lo
             JOIN patients p ON p.id = lo.patient_id
             JOIN samples s ON s.order_id = lo.id
             JOIN test_results tr ON tr.sample_id = s.id AND tr.status='approved'
             WHERE lo.status='processing'
             GROUP BY lo.id, p.name
             HAVING COUNT(tr.id) > 0
             ORDER BY CASE lo.priority WHEN 'stat' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END
             LIMIT 20`
          )
        ]);

        res.json({
          ok: true,
          queue: {
            to_collect:  toCollect.rows,
            to_process:  toReceive.rows,
            enter_results: toResult.rows,
            to_approve:  toApprove.rows,
            to_release:  toRelease.rows,
          },
          counts: {
            to_collect:    toCollect.rows.length,
            to_process:    toReceive.rows.length,
            enter_results: toResult.rows.length,
            to_approve:    toApprove.rows.length,
            to_release:    toRelease.rows.length,
          }
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     PENDING RESULTS APPROVAL (for one order)
  ======================================================= */

  /* GET /lab/orders/:id/pending-results - get results needing approval */
  router.get("/lab/orders/:id/pending-results", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff"])(req, res, async () => {
      try {
        const results = await db.query(
          `SELECT tr.id, tr.value, tr.value_numeric, tr.unit, tr.status,
                  tr.is_abnormal, tr.abnormal_flag, tr.notes, tr.created_at,
                  tc.name_ar, tc.name_en, tc.code,
                  tc.normal_range_min, tc.normal_range_max, tc.normal_range_text,
                  u.name AS tech_name
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           JOIN samples s ON s.id = tr.sample_id
           LEFT JOIN users u ON u.id = tr.tech_id
           WHERE s.order_id=$1 AND tr.status='resulted'
           ORDER BY tr.is_abnormal DESC, tc.category, tc.name_ar`,
          [req.params.id]
        );

        res.json({ ok: true, results: results.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* POST /lab/orders/:id/approve-all - bulk approve all resulted results */
  router.post("/lab/orders/:id/approve-all", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["lab_staff", "admin"])(req, res, async () => {
      try {
        const result = await db.query(
          `UPDATE test_results
           SET status='approved', approved_by=$1, approved_at=NOW(), updated_at=NOW()
           WHERE sample_id IN (SELECT id FROM samples WHERE order_id=$2)
             AND status='resulted'
           RETURNING id`,
          [req.user.id, req.params.id]
        );

        res.json({ ok: true, approved: result.rows.length });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     CRITICAL VALUE DETECTION
  ======================================================= */

  /* GET /lab/critical-values - results with critical values (needs urgent attention) */
  router.get("/lab/critical-values", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff", "doctor"])(req, res, async () => {
      try {
        /* critical thresholds */
        const CRITICAL = {
          GLU:   { high: 400 },
          HGB:   { low: 7 },
          PLT:   { low: 50 },
          WBC:   { high: 30 },
          K:     { low: 2.5, high: 6.5 },
          NA:    { low: 120, high: 160 },
          CREA:  { high: 10 },
          INR:   { high: 5 },
        };

        /* get recent abnormal results and check against critical thresholds */
        const result = await db.query(
          `SELECT tr.id, tr.value_numeric, tr.is_abnormal, tr.created_at,
                  tr.status, tc.code, tc.name_ar, tc.unit,
                  p.name AS patient_name, p.phone AS patient_phone,
                  lo.id AS order_id, lo.priority,
                  u_doc.name AS doctor_name
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           JOIN samples s ON s.id = tr.sample_id
           JOIN lab_orders lo ON lo.id = s.order_id
           JOIN patients p ON p.id = tr.patient_id
           LEFT JOIN users u_doc ON u_doc.id = lo.doctor_id
           WHERE tr.status IN ('resulted','approved')
             AND tr.created_at > NOW() - INTERVAL '24 hours'
             AND tr.value_numeric IS NOT NULL
           ORDER BY tr.created_at DESC
           LIMIT 200`
        );

        /* filter to critical values only */
        const critical = result.rows.filter(r => {
          const thres = CRITICAL[r.code];
          if (!thres) return false;
          if (thres.high && r.value_numeric > thres.high) return true;
          if (thres.low  && r.value_numeric < thres.low)  return true;
          return false;
        }).map(r => {
          const thres = CRITICAL[r.code] || {};
          return {
            ...r,
            critical_type: (thres.high && r.value_numeric > thres.high) ? "critically_high" : "critically_low"
          };
        });

        res.json({
          ok: true,
          critical_values: critical,
          count: critical.length
        });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  /* =======================================================
     TAT (Turnaround Time) REPORT
  ======================================================= */

  /* GET /lab/tat-report - turnaround time analytics */
  router.get("/lab/tat-report", async (req, res) => {
    if (!global.requireAuth) return res.status(503).json({ error: "auth_not_loaded" });
    global.requireAuth(["admin", "lab_staff"])(req, res, async () => {
      try {
        const result = await db.query(
          `SELECT tc.category,
                  COUNT(*) AS total,
                  ROUND(AVG(EXTRACT(EPOCH FROM (tr.created_at - lo.created_at))/3600)::numeric, 1) AS avg_hours,
                  ROUND(MAX(EXTRACT(EPOCH FROM (tr.created_at - lo.created_at))/3600)::numeric, 1) AS max_hours,
                  COUNT(CASE WHEN EXTRACT(EPOCH FROM (tr.created_at - lo.created_at))/3600 > tc.turnaround_hours THEN 1 END) AS breached
           FROM test_results tr
           JOIN test_catalog tc ON tc.id = tr.test_catalog_id
           JOIN samples s ON s.id = tr.sample_id
           JOIN lab_orders lo ON lo.id = s.order_id
           WHERE tr.created_at > NOW() - INTERVAL '30 days'
           GROUP BY tc.category
           ORDER BY avg_hours DESC`
        );

        res.json({ ok: true, tat: result.rows });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  });

  logger.info("Lab Workflow Extension fully activated");
};
