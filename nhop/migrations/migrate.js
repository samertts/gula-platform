"use strict";
/**
 * NHOP Database Migration Runner
 * Run: node migrations/migrate.js
 */

const fs = require("fs");
const path = require("path");
const db = require("../core/database/db");

async function run() {
  const files = fs.readdirSync(__dirname)
    .filter(f => f.endsWith(".sql"))
    .sort();

  for (const file of files) {
    const sql = fs.readFileSync(path.join(__dirname, file), "utf8");
    console.log(`Running migration: ${file}`);
    try {
      await db.query(sql);
      console.log(`✓ ${file} done`);
    } catch (err) {
      console.error(`✗ ${file} failed:`, err.message);
      process.exit(1);
    }
  }

  console.log("All migrations complete.");
  process.exit(0);
}

run();
