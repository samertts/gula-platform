"use strict";

const express = require("express");
const router = express.Router();
const crypto = require("crypto");
const db = require("../../core/database/db");

/* =========================
   GET ALL PATIENTS
========================= */
router.get("/", async (req, res, next) => {
  try {
    const result = await db.query(
      "SELECT * FROM patients ORDER BY created_at DESC"
    );

    res.json(result.rows);
  } catch (err) {
    next(err);
  }
});

/* =========================
   CREATE PATIENT
========================= */
router.post("/", async (req, res, next) => {
  try {
    const { name, age } = req.body;

    if (!name || !age) {
      return res.status(400).json({
        error: "name and age required",
      });
    }

    const id = crypto.randomUUID();

    await db.query(
      `INSERT INTO patients(id, name, age)
       VALUES ($1,$2,$3)`,
      [id, name, age]
    );

    res.status(201).json({
      id,
      name,
      age,
    });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
