
/*
==================================================
NHOP FRONTEND ENTRYPOINT
==================================================
*/

import { bootNHOP } from "@kernel/boot";

console.log("🚀 Starting NHOP UI Runtime...");

bootNHOP().catch((err) => {
  console.error("NHOP BOOT FAILURE:", err);
});

import { createPatient } from "./api/patients.api";

createPatient("Test Patient").then(console.log);
