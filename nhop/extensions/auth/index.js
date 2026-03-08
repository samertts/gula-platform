"use strict";

/*
==========================================================
NHOP AUTH EXTENSION
JWT-based authentication with role management
Roles: admin | lab_staff | doctor | patient | citizen
==========================================================
*/

const bcrypt  = require("bcryptjs");
const jwt     = require("jsonwebtoken");
const crypto  = require("crypto");
const db      = require("../../core/database/db");

/* --- Require JWT_SECRET from env; never fall back to a weak default --- */
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET || JWT_SECRET.length < 32) {
  console.error("[AUTH] FATAL: JWT_SECRET env var is missing or too short (min 32 chars). Server cannot start.");
  process.exit(1);
}
const JWT_EXPIRES     = process.env.JWT_EXPIRES     || "8h";
const REFRESH_EXPIRES = process.env.REFRESH_EXPIRES || "30d";

/* -------------------------------------------------------
   In-memory rate limiter (no external dep required)
   Limits: 10 attempts per IP per 15 minutes on auth routes
------------------------------------------------------- */
const rateLimitStore = new Map(); // ip -> { count, resetAt }
const RATE_LIMIT_MAX      = 10;
const RATE_LIMIT_WINDOW   = 15 * 60 * 1000; // 15 min

function rateLimit(req, res, next) {
  const ip  = req.ip || "unknown";
  const now = Date.now();
  const rec = rateLimitStore.get(ip);

  if (!rec || now > rec.resetAt) {
    rateLimitStore.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW });
    return next();
  }

  rec.count++;
  if (rec.count > RATE_LIMIT_MAX) {
    const retryAfter = Math.ceil((rec.resetAt - now) / 1000);
    res.setHeader("Retry-After", retryAfter);
    return res.status(429).json({
      error: "too_many_requests",
      retry_after_seconds: retryAfter
    });
  }
  next();
}

/* Cleanup stale rate-limit entries every 30 minutes */
setInterval(() => {
  const now = Date.now();
  for (const [ip, rec] of rateLimitStore) {
    if (now > rec.resetAt) rateLimitStore.delete(ip);
  }
}, 30 * 60 * 1000);

/* -------------------------------------------------------
   Token Helpers
------------------------------------------------------- */

function signAccess(payload) {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES });
}

function signRefresh(userId) {
  const token = crypto.randomBytes(40).toString("hex");
  return token;
}

async function storeRefreshToken(userId, rawToken) {
  const hash    = crypto.createHash("sha256").update(rawToken).digest("hex");
  const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  await db.query(
    "INSERT INTO refresh_tokens(user_id, token_hash, expires_at) VALUES ($1,$2,$3)",
    [userId, hash, expires]
  );
}

/* -------------------------------------------------------
   Auth Middleware (exported for use by other extensions)
------------------------------------------------------- */

function requireAuth(roles = []) {
  return (req, res, next) => {
    const header = req.headers["authorization"] || "";
    const token  = header.startsWith("Bearer ") ? header.slice(7) : null;

    if (!token) {
      return res.status(401).json({ error: "authentication_required" });
    }

    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      req.user = decoded;

      if (roles.length && !roles.includes(decoded.role)) {
        return res.status(403).json({ error: "insufficient_permissions", required: roles });
      }

      next();
    } catch {
      return res.status(401).json({ error: "token_invalid_or_expired" });
    }
  };
}

/* expose globally so other extensions can use it */
global.requireAuth = requireAuth;

/* -------------------------------------------------------
   EXTENSION REGISTER
------------------------------------------------------- */

module.exports.register = async function (capabilities) {
  const { router, logger } = capabilities;

  logger.info("Auth Extension booting");

  /* -------------------------------------------------------
     REGISTER
     POST /auth/register
  ------------------------------------------------------- */
  router.post("/auth/register", rateLimit, async (req, res) => {
    try {
      const { name, email, password, phone, role = "citizen", national_id } = req.body;

      if (!name || !email || !password) {
        return res.status(400).json({ error: "name, email, and password are required" });
      }

      const validRoles = ["patient", "citizen"];
      if (!validRoles.includes(role)) {
        return res.status(400).json({ error: "self_registration_only_patient_or_citizen" });
      }

      const existing = await db.query("SELECT id FROM users WHERE email=$1", [email]);
      if (existing.rows.length) {
        return res.status(409).json({ error: "email_already_registered" });
      }

      const hash = await bcrypt.hash(password, 12);

      const result = await db.query(
        `INSERT INTO users(name, email, password_hash, phone, role, national_id)
         VALUES ($1,$2,$3,$4,$5,$6) RETURNING id, name, email, role`,
        [name, email.toLowerCase(), hash, phone || null, role, national_id || null]
      );

      const user = result.rows[0];

      /* if patient role, create patient record */
      if (role === "patient") {
        await db.query(
          `INSERT INTO patients(user_id, name, phone, national_id)
           VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING`,
          [user.id, name, phone || null, national_id || null]
        );
      }

      const access  = signAccess({ id: user.id, email: user.email, role: user.role, name: user.name });
      const refresh = signRefresh(user.id);
      await storeRefreshToken(user.id, refresh);

      res.status(201).json({
        ok: true,
        user: { id: user.id, name: user.name, email: user.email, role: user.role },
        access_token:  access,
        refresh_token: refresh
      });

    } catch (err) {
      logger.error("Register failed", { error: err.message });
      res.status(500).json({ error: "registration_failed" });
    }
  });

  /* -------------------------------------------------------
     LOGIN
     POST /auth/login
  ------------------------------------------------------- */
  router.post("/auth/login", rateLimit, async (req, res) => {
    try {
      const { email, password } = req.body;

      if (!email || !password) {
        return res.status(400).json({ error: "email_and_password_required" });
      }

      const result = await db.query(
        "SELECT id, name, email, password_hash, role, is_active FROM users WHERE email=$1",
        [email.toLowerCase().trim()]
      );

      const user = result.rows[0];

      if (!user) {
        /* Audit failed attempt — use setTimeout to avoid timing-based enumeration */
        setTimeout(() => {
          if (global.auditLog) global.auditLog({ action: "login_failed", details: { email }, ip: req.ip });
        }, 0);
        return res.status(401).json({ error: "invalid_credentials" });
      }

      if (!user.is_active) {
        if (global.auditLog) global.auditLog({ userId: user.id, userName: user.name, userRole: user.role, action: "login_failed_disabled", ip: req.ip });
        return res.status(403).json({ error: "account_disabled" });
      }

      const valid = await bcrypt.compare(password, user.password_hash);
      if (!valid) {
        if (global.auditLog) global.auditLog({ userId: user.id, userName: user.name, userRole: user.role, action: "login_failed_wrong_password", ip: req.ip });
        return res.status(401).json({ error: "invalid_credentials" });
      }

      const access  = signAccess({ id: user.id, email: user.email, role: user.role, name: user.name });
      const refresh = signRefresh(user.id);
      await storeRefreshToken(user.id, refresh);

      if (global.auditLog) global.auditLog({ userId: user.id, userName: user.name, userRole: user.role, action: "login", ip: req.ip });

      res.json({
        ok: true,
        user: { id: user.id, name: user.name, email: user.email, role: user.role },
        access_token:  access,
        refresh_token: refresh
      });

    } catch (err) {
      logger.error("Login failed", { error: err.message });
      res.status(500).json({ error: "login_failed" });
    }
  });

  /* -------------------------------------------------------
     REFRESH TOKEN
     POST /auth/refresh
  ------------------------------------------------------- */
  router.post("/auth/refresh", async (req, res) => {
    try {
      const { refresh_token } = req.body;
      if (!refresh_token) {
        return res.status(400).json({ error: "refresh_token_required" });
      }

      const hash = crypto.createHash("sha256").update(refresh_token).digest("hex");

      const result = await db.query(
        `SELECT rt.user_id, u.name, u.email, u.role, u.is_active
         FROM refresh_tokens rt
         JOIN users u ON u.id = rt.user_id
         WHERE rt.token_hash=$1 AND rt.expires_at > NOW()`,
        [hash]
      );

      if (!result.rows.length) {
        return res.status(401).json({ error: "invalid_or_expired_refresh_token" });
      }

      const user = result.rows[0];
      if (!user.is_active) {
        return res.status(403).json({ error: "account_disabled" });
      }

      const access = signAccess({ id: user.user_id, email: user.email, role: user.role, name: user.name });

      res.json({ ok: true, access_token: access });

    } catch (err) {
      res.status(500).json({ error: "refresh_failed" });
    }
  });

  /* -------------------------------------------------------
     LOGOUT
     POST /auth/logout
  ------------------------------------------------------- */
  router.post("/auth/logout", requireAuth(), async (req, res) => {
    try {
      const { refresh_token } = req.body;
      if (refresh_token) {
        const hash = crypto.createHash("sha256").update(refresh_token).digest("hex");
        await db.query("DELETE FROM refresh_tokens WHERE token_hash=$1", [hash]);
      }
      res.json({ ok: true, message: "logged_out" });
    } catch {
      res.json({ ok: true });
    }
  });

  /* -------------------------------------------------------
     GET CURRENT USER
     GET /auth/me
  ------------------------------------------------------- */
  router.get("/auth/me", requireAuth(), async (req, res) => {
    try {
      const result = await db.query(
        "SELECT id, name, email, role, phone, national_id, created_at FROM users WHERE id=$1",
        [req.user.id]
      );
      if (!result.rows.length) {
        return res.status(404).json({ error: "user_not_found" });
      }
      res.json({ ok: true, user: result.rows[0] });
    } catch (err) {
      res.status(500).json({ error: "fetch_failed" });
    }
  });

  /* -------------------------------------------------------
     ADMIN: CREATE USER (lab_staff, doctor, admin)
     POST /auth/users
  ------------------------------------------------------- */
  router.post("/auth/users", requireAuth(["admin"]), async (req, res) => {
    try {
      const { name, email, password, role, phone, national_id } = req.body;

      if (!name || !email || !password || !role) {
        return res.status(400).json({ error: "name, email, password, role are required" });
      }

      const validRoles = ["admin", "lab_staff", "doctor", "patient", "citizen"];
      if (!validRoles.includes(role)) {
        return res.status(400).json({ error: "invalid_role" });
      }

      const existing = await db.query("SELECT id FROM users WHERE email=$1", [email]);
      if (existing.rows.length) {
        return res.status(409).json({ error: "email_already_exists" });
      }

      const hash = await bcrypt.hash(password, 12);

      const result = await db.query(
        `INSERT INTO users(name, email, password_hash, phone, role, national_id)
         VALUES ($1,$2,$3,$4,$5,$6) RETURNING id, name, email, role`,
        [name, email.toLowerCase(), hash, phone || null, role, national_id || null]
      );

      res.status(201).json({ ok: true, user: result.rows[0] });

    } catch (err) {
      logger.error("Create user failed", { error: err.message });
      res.status(500).json({ error: "create_failed" });
    }
  });

  /* -------------------------------------------------------
     ADMIN: LIST USERS
     GET /auth/users
  ------------------------------------------------------- */
  router.get("/auth/users", requireAuth(["admin"]), async (req, res) => {
    try {
      const { role, page = 1, limit = 50 } = req.query;
      const offset = (Number(page) - 1) * Number(limit);

      let query  = "SELECT id, name, email, role, phone, national_id, is_active, created_at FROM users";
      const params = [];

      if (role) {
        params.push(role);
        query += ` WHERE role=$${params.length}`;
      }

      query += ` ORDER BY created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
      params.push(Number(limit), offset);

      const result = await db.query(query, params);
      res.json({ ok: true, users: result.rows });

    } catch (err) {
      res.status(500).json({ error: "fetch_failed" });
    }
  });

  /* -------------------------------------------------------
     ADMIN: TOGGLE USER STATUS
     PATCH /auth/users/:id/status
  ------------------------------------------------------- */
  router.patch("/auth/users/:id/status", requireAuth(["admin"]), async (req, res) => {
    try {
      const { is_active } = req.body;
      await db.query(
        "UPDATE users SET is_active=$1, updated_at=NOW() WHERE id=$2",
        [!!is_active, req.params.id]
      );
      res.json({ ok: true });
    } catch {
      res.status(500).json({ error: "update_failed" });
    }
  });

  /* -------------------------------------------------------
     CHANGE PASSWORD
     POST /auth/change-password
  ------------------------------------------------------- */
  router.post("/auth/change-password", requireAuth(), async (req, res) => {
    try {
      const { current_password, new_password } = req.body;

      if (!current_password || !new_password) {
        return res.status(400).json({ error: "current_password and new_password required" });
      }

      /* Require min 8 chars + at least 1 digit + 1 uppercase */
      if (new_password.length < 8) {
        return res.status(400).json({ error: "password_must_be_at_least_8_chars" });
      }
      if (!/[0-9]/.test(new_password)) {
        return res.status(400).json({ error: "password_must_contain_a_digit" });
      }
      if (!/[A-Z]/.test(new_password)) {
        return res.status(400).json({ error: "password_must_contain_an_uppercase_letter" });
      }

      const result = await db.query("SELECT password_hash FROM users WHERE id=$1", [req.user.id]);
      if (!result.rows.length) return res.status(404).json({ error: "user_not_found" });

      const valid = await bcrypt.compare(current_password, result.rows[0].password_hash);
      if (!valid) return res.status(401).json({ error: "current_password_incorrect" });

      const newHash = await bcrypt.hash(new_password, 12);
      await db.query("UPDATE users SET password_hash=$1, updated_at=NOW() WHERE id=$2", [newHash, req.user.id]);

      /* invalidate all refresh tokens */
      await db.query("DELETE FROM refresh_tokens WHERE user_id=$1", [req.user.id]);

      if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "password_changed", ip: req.ip });

      res.json({ ok: true, message: "password_changed_successfully" });
    } catch (err) {
      logger.error("Change password failed", { error: err.message });
      res.status(500).json({ error: "change_failed" });
    }
  });

  /* -------------------------------------------------------
     UPDATE PROFILE
     PATCH /auth/me
  ------------------------------------------------------- */
  router.patch("/auth/me", requireAuth(), async (req, res) => {
    try {
      const { name, phone } = req.body;
      const result = await db.query(
        "UPDATE users SET name=COALESCE($1,name), phone=COALESCE($2,phone), updated_at=NOW() WHERE id=$3 RETURNING id,name,email,role,phone",
        [name || null, phone || null, req.user.id]
      );
      res.json({ ok: true, user: result.rows[0] });
    } catch (err) {
      res.status(500).json({ error: "update_failed" });
    }
  });

  /* -------------------------------------------------------
     ADMIN: RESET USER PASSWORD
     POST /auth/users/:id/reset-password
  ------------------------------------------------------- */
  router.post("/auth/users/:id/reset-password", requireAuth(["admin"]), async (req, res) => {
    try {
      const { new_password } = req.body;
      if (!new_password || new_password.length < 8) {
        return res.status(400).json({ error: "new_password_min_8_chars" });
      }

      const hash = await bcrypt.hash(new_password, 12);
      await db.query(
        "UPDATE users SET password_hash=$1, updated_at=NOW() WHERE id=$2",
        [hash, req.params.id]
      );
      await db.query("DELETE FROM refresh_tokens WHERE user_id=$1", [req.params.id]);

      if (global.auditLog) global.auditLog({ userId: req.user.id, userName: req.user.name, userRole: req.user.role, action: "admin_password_reset", entityType: "user", entityId: req.params.id, ip: req.ip });

      res.json({ ok: true, message: "password_reset_done" });
    } catch (err) {
      res.status(500).json({ error: "reset_failed" });
    }
  });

  /* -------------------------------------------------------
     AUDIT LOGS TABLE — lazy create on boot
  ------------------------------------------------------- */
  db.query(`
    CREATE TABLE IF NOT EXISTS audit_logs (
      id          BIGSERIAL PRIMARY KEY,
      user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
      user_name   TEXT,
      user_role   TEXT,
      action      TEXT NOT NULL,
      entity_type TEXT,
      entity_id   TEXT,
      details     JSONB DEFAULT '{}',
      ip          TEXT,
      created_at  TIMESTAMPTZ DEFAULT NOW()
    )
  `).catch(err => logger.warn("audit_logs table warning", { err: err.message }));

  /* -------------------------------------------------------
     AUDIT HELPER — global for all extensions
  ------------------------------------------------------- */
  global.auditLog = async function({ userId, userName, userRole, action, entityType, entityId, details, ip }) {
    try {
      await db.query(
        `INSERT INTO audit_logs (user_id, user_name, user_role, action, entity_type, entity_id, details, ip)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
        [userId||null, userName||null, userRole||null, action, entityType||null,
         entityId ? String(entityId) : null, details ? JSON.stringify(details) : '{}', ip||null]
      );
    } catch (err) {
      logger.warn("auditLog write failed", { err: err.message });
    }
  };

  /* -------------------------------------------------------
     ADMIN: GET AUDIT LOGS
     GET /auth/audit-logs?page=1&limit=50&action=login&user_id=5
  ------------------------------------------------------- */
  router.get("/auth/audit-logs", requireAuth(["admin"]), async (req, res) => {
    try {
      const { page = 1, limit = 50, action, user_id } = req.query;
      const offset = (Number(page) - 1) * Number(limit);
      const conditions = [];
      const values = [];
      let idx = 1;

      if (action) { conditions.push(`action ILIKE $${idx++}`); values.push(`%${action}%`); }
      if (user_id) { conditions.push(`user_id = $${idx++}`); values.push(Number(user_id)); }

      const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";

      const [data, count] = await Promise.all([
        db.query(
          `SELECT id, user_id, user_name, user_role, action, entity_type, entity_id, details, ip, created_at
           FROM audit_logs ${where}
           ORDER BY created_at DESC
           LIMIT $${idx} OFFSET $${idx + 1}`,
          [...values, Number(limit), offset]
        ),
        db.query(`SELECT COUNT(*) FROM audit_logs ${where}`, values)
      ]);

      res.json({ ok: true, logs: data.rows, total: Number(count.rows[0].count), page: Number(page), limit: Number(limit) });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  /* hook audit into login */
  const _origLogin = router.stack.find(l => l.route && l.route.path === "/auth/login");
  /* Audit is written inside login handler via global.auditLog after this point */

  logger.info("Auth Extension fully activated");
};
