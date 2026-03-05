
"use strict";

const validateKernelStructure =
  require("./kernel.loader");

module.exports = function stage1(root){

  console.log("🟢 Stage 1 — Kernel Integrity");

  validateKernelStructure(root);
};
