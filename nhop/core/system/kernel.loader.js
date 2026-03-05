
"use strict";

/*
==================================================
NHOP AUTO KERNEL LOADER — FINAL EDITION
Full Dependency + Integrity Validator
==================================================
*/

const fs = require("fs");
const path = require("path");

/* ==================================================
   REQUIRED KERNEL MAP
================================================== */

const REQUIRED_KERNELS = {
  "core/runtime/runtime.kernel.js": [],
  "core/runtime/deputy.kernel.js": [
    "initialize",
    "shutdown"
  ],
  "core/ledger/ledger.context.js": [
    "startRequest",
    "verify"
  ],
  "core/sandbox/capabilities.js": [],
  "core/sandbox/secure.router.js": []
};

/* ==================================================
   SAFE REQUIRE
================================================== */

function safeRequire(fullPath){

  try{
    delete require.cache[require.resolve(fullPath)];
    return require(fullPath);
  }
  catch(err){
    return { __error: err };
  }
}

/* ==================================================
   VALIDATION ENGINE
================================================== */

function validateKernelStructure(rootDir){

  const errors = [];
  const loaded = [];

  console.log("\n🔍 NHOP Kernel Validation Starting...\n");

  for(const file in REQUIRED_KERNELS){

    const fullPath = path.join(rootDir, file);

    /* ---- existence check ---- */

    if(!fs.existsSync(fullPath)){
      errors.push(`Missing file: ${file}`);
      continue;
    }

    /* ---- load test ---- */

    const mod = safeRequire(fullPath);

    if(mod.__error){
      errors.push(
        `Load failure (${file}): ${mod.__error.message}`
      );
      continue;
    }

    /* ---- export validation ---- */

    const requiredExports = REQUIRED_KERNELS[file];

    for(const fn of requiredExports){
      if(typeof mod[fn] !== "function"){
        errors.push(
          `Invalid export in ${file}: missing "${fn}()"`
        );
      }
    }

    loaded.push(file);
  }

  /* ==================================================
     RESULT
  ================================================== */

  if(errors.length){

    console.error("\n❌ KERNEL VALIDATION FAILED\n");

    errors.forEach(e=>console.error(" •", e));

    console.error("\nSystem halted for safety.\n");

    process.exit(1);
  }

  console.log("✅ Kernel validation passed");
  console.log("Loaded kernels:", loaded.length,"\n");
}

/* ==================================================
   EXPORT
================================================== */

module.exports = validateKernelStructure;
