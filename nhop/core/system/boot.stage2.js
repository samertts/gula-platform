
"use strict";

const fs = require("fs");

module.exports = function stage2(){

  console.log("🟢 Stage 2 — System Readiness");

  const requiredDirs = [
    "core",
    "modules"
  ];

  for(const dir of requiredDirs){
    if(!fs.existsSync(dir)){
      throw new Error(`Missing directory: ${dir}`);
    }
  }
};
