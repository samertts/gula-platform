
"use strict";

const path = require("path");

const stage0 = require("./boot.stage0");
const stage1 = require("./boot.stage1");
const stage2 = require("./boot.stage2");

module.exports = function boot(){

  console.log("\n🚀 NHOP BOOT SEQUENCE\n");

  stage0();
  stage1(path.resolve(__dirname,"../../"));
  stage2();

  console.log("\n✅ Boot sequence completed\n");
};
