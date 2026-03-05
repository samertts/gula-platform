
"use strict";

/*
==================================================
NHOP UNIFIED BOOT SYSTEM — FINAL EDITION
Controlled System Startup Layer
==================================================
*/

const path = require("path");

/* ==================================================
   SAFE EXECUTOR
================================================== */

function runSafe(name, fn){

  try{
    console.log(`🟢 ${name}`);
    fn();
  }
  catch(err){
    console.error(`❌ Boot failure at ${name}`);
    console.error(err.message);
    process.exit(1);
  }
}

/* ==================================================
   STAGE 0 — ENVIRONMENT
================================================== */

runSafe("Stage 0 — Environment", ()=>{

  if(!process.version)
    throw new Error("Node runtime unavailable");

  console.log("Node:", process.version);
});

/* ==================================================
   STAGE 1 — KERNEL VALIDATION
================================================== */

runSafe("Stage 1 — Kernel Integrity", ()=>{

  const validateKernelStructure =
    require("./core/system/kernel.loader");

  validateKernelStructure(__dirname);
});

/* ==================================================
   STAGE 2 — SYSTEM READINESS
================================================== */

runSafe("Stage 2 — System Readiness", ()=>{

  const fs = require("fs");

  ["core","modules"].forEach(dir=>{
    if(!fs.existsSync(path.join(__dirname,dir))){
      throw new Error(`Missing directory: ${dir}`);
    }
  });
});

/* ==================================================
   STAGE 3 — SERVER START
================================================== */

runSafe("Stage 3 — Server Launch", ()=>{

  require("./server.js");
});

console.log("\n✅ NHOP Boot Complete\n");
