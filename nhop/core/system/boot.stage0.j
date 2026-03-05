
"use strict";

/* Environment validation */

module.exports = function stage0(){

  console.log("🟢 Stage 0 — Environment");

  if(!process.version){
    throw new Error("Node environment invalid");
  }

  console.log("Node:", process.version);
};

