
"use strict";

/*
==================================================
NHOP MIDDLEWARE VALIDATOR
Detect invalid Express middleware before boot
==================================================
*/

const path = require("path");

const MIDDLEWARES = [

  {
    name: "loadShield",
    file: "core/security/load.shield.js",
    export: "shieldMiddleware"
  },

  {
    name: "institutionContext",
    file: "core/context/institution.context.js",
    export: "middleware"
  },

  {
    name: "policyMiddleware",
    file: "core/policy/policy.middleware.js",
    export: null // exported directly
  }

];

function validate(rootDir){

  console.log("🔍 Validating middleware...\n");

  const errors = [];

  for(const mw of MIDDLEWARES){

    try{

      const mod = require(
        path.join(rootDir, mw.file)
      );

      const fn = mw.export
        ? mod[mw.export]
        : mod;

      if(typeof fn !== "function"){
        errors.push(
          `${mw.name} is not a middleware function`
        );
      }

    }catch(err){

      errors.push(
        `${mw.name} failed to load: ${err.message}`
      );
    }
  }

  if(errors.length){

    console.error("❌ Middleware validation failed\n");

    errors.forEach(e=>console.error(" •",e));

    console.error("\nBoot stopped for safety.\n");

    process.exit(1);
  }

  console.log("✅ Middleware validation passed\n");
}

module.exports = validate;
