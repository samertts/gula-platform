#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const vercelPath = path.join(root, "vercel.json");
const vercel = JSON.parse(fs.readFileSync(vercelPath, "utf8"));
const text = fs.readFileSync(vercelPath, "utf8");
const failures = [];

if (text.includes('"destination": "https://api.gula-platform.org')) {
  failures.push("vercel.json contains a hard-coded production API rewrite");
}

const rewrites = vercel.rewrites ?? [];
for (const rewrite of rewrites) {
  const destination = String(rewrite.destination ?? "");
  if (/api\.gula-platform\.org/i.test(destination)) {
    failures.push(`rewrite destination points to production: ${destination}`);
  }
}

const clientPath = path.join(root, "frontend-v3", "src", "api", "client.ts");
const client = fs.readFileSync(clientPath, "utf8");
if (!client.includes("VITE_API_BASE_URL")) {
  failures.push("frontend API client does not use VITE_API_BASE_URL");
}
if (client.includes("https://api.gula-platform.org")) {
  failures.push("frontend API client contains a hard-coded production API URL");
}

const requiredDocs = [
  "docs/STAGING_RUNBOOK.md",
  "docs/VERCEL_ENVIRONMENT_ISOLATION_AR.md",
];
for (const relative of requiredDocs) {
  if (!fs.existsSync(path.join(root, relative))) {
    failures.push(`missing environment isolation documentation: ${relative}`);
  }
}

if (failures.length) {
  console.error("Vercel API isolation check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Vercel API isolation check passed: no hard-coded production API rewrite or client URL detected.");
