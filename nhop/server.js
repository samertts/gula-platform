// Top of server.js
const throttle = require('./core/system-throttle');
throttle.initializeThrottle();

"use strict";



/*
==========================================================
NHOP SOVEREIGN SERVER — EXTENSION KERNEL FINAL
Kernel never changes — Extensions evolve
==========================================================
*/

const express = require("express");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

/* ======================================================
   CONFIG
====================================================== */

const PORT = process.env.PORT || 3000;
const APP_NAME = "NHOP";

/* modules + extensions (FINAL ARCHITECTURE) */
const MODULE_DIRS = [
  path.join(__dirname, "modules"),
  path.join(__dirname, "extensions")
];

/* ======================================================
   LOGGER (IMMUTABLE)
====================================================== */

const logger = Object.freeze({
  log(level, message, meta = {}) {
    console.log(JSON.stringify({
      level,
      time: new Date().toISOString(),
      message,
      ...meta
    }));
  },
  info(m,meta){this.log("INFO",m,meta);},
  warn(m,meta){this.log("WARN",m,meta);},
  error(m,meta){this.log("ERROR",m,meta);}
});

/* ======================================================
   SAFE MIDDLEWARE GUARD
====================================================== */

function safeMiddleware(mw,name){
  if(typeof mw !== "function"){
    throw new Error(`${name} is not middleware`);
  }
  return mw;
}

/* ======================================================
   LOAD CORE KERNELS
====================================================== */

const loadShield = require("./core/security/load.shield");
const runtime = require("./core/runtime/runtime.kernel");
const deputyKernel = require("./core/runtime/deputy.kernel");
const selfHeal = require("./core/healing/self.heal");
const institutionContext = require("./core/context/institution.context");
const policyMiddleware = require("./core/policy/policy.middleware");
const autopilot = require("./core/autopilot/autopilot.kernel");

const ledgerContext = require("./core/ledger/ledger.context");
const createCapabilities = require("./core/sandbox/capabilities");
const createSecureRouter = require("./core/sandbox/secure.router");

/* expose runtime authority */
global.runtimeKernel = runtime;

/* ======================================================
   GLOBAL ERROR SHIELD
====================================================== */

selfHeal.globalErrorShield();
selfHeal.retryFailedModules();

/* ======================================================
   EXPRESS INIT
====================================================== */

const app = express();

app.disable("x-powered-by");
app.set("trust proxy", true);

/* ======================================================
   CORS — allow frontend dev server and production origin
====================================================== */
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "http://localhost:5173,http://localhost:3001").split(",");

app.use((req, res, next) => {
  const origin = req.headers.origin;
  /* Only whitelist explicit origins — never wildcard with credentials */
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Request-ID");
  res.setHeader("Access-Control-Max-Age", "86400");
  if (req.method === "OPTIONS") return res.status(204).end();
  next();
});

/* ======================================================
   SECURITY HEADERS
====================================================== */
app.use((_req, res, next) => {
  res.setHeader("X-Content-Type-Options",  "nosniff");
  res.setHeader("X-Frame-Options",         "DENY");
  res.setHeader("X-XSS-Protection",        "1; mode=block");
  res.setHeader("Referrer-Policy",         "strict-origin-when-cross-origin");
  res.setHeader("Permissions-Policy",      "camera=(), microphone=(), geolocation=()");
  next();
});

app.use(express.json({ limit: "1mb" }));

/* ======================================================
   BACKPRESSURE PROTECTION
====================================================== */

let activeRequests = 0;
const MAX_CONCURRENT = 500;

app.use((req,res,next)=>{

  if(activeRequests > MAX_CONCURRENT){
    return res.status(503).json({error:"Server busy"});
  }

  activeRequests++;
  res.on("finish",()=>activeRequests--);

  next();
});

/* ======================================================
   REQUEST FORENSICS CONTEXT
====================================================== */

app.use((req,res,next)=>{

  req.requestId = crypto.randomUUID();
  req.startTime = Date.now();

  ledgerContext.startRequest?.(req.requestId);

  res.setTimeout(15000,()=>{
    logger.warn("Request timeout",{requestId:req.requestId});
    res.status(408).end();
  });

  res.on("finish",()=>{
    deputyKernel.observeRequest?.({
      requestId:req.requestId,
      duration:Date.now()-req.startTime,
      status:res.statusCode
    });
  });

  next();
});

/* ======================================================
   SECURITY STACK (ORDER CRITICAL)
====================================================== */

app.use(safeMiddleware(loadShield.shieldMiddleware,"loadShield"));
app.use(safeMiddleware(institutionContext.middleware,"institutionContext"));

app.use(
  safeMiddleware(
    typeof policyMiddleware === "function"
      ? policyMiddleware
      : policyMiddleware.middleware,
    "policyMiddleware"
  )
);

/* ======================================================
   LEDGER + DEPUTY CONTEXT
====================================================== */

app.use((req,res,next)=>{
  runtime.attachLedgerContext?.(req);
  deputyKernel.attachContext?.(req);
  next();
});

/* ======================================================
   EXTENSION + MODULE LOADER
====================================================== */

const registeredUnits = [];

async function discoverUnits(){

  logger.info("Extension discovery started");

  for(const baseDir of MODULE_DIRS){

    if(!fs.existsSync(baseDir)) continue;

    for(const dir of fs.readdirSync(baseDir)){

      const entry =
        path.join(baseDir,dir,"index.js");

      if(!fs.existsSync(entry)) continue;

      try{

        delete require.cache[
          require.resolve(entry)
        ];

        const code = fs.readFileSync(entry);

        const hash = crypto
          .createHash("sha256")
          .update(code)
          .digest("hex");

        /* sandbox per extension */
        const sandbox = runtime.createSandbox?.(dir);
        if(!sandbox)
          throw new Error("Sandbox creation failed");

        const secureRouter =
          createSecureRouter(app,dir);

        const capabilities =
          createCapabilities(
            secureRouter,
            sandbox,
            logger
          );

        const extension = require(entry);

        if(typeof extension.register !== "function")
          throw new Error("register() missing");

        await extension.register(capabilities);

        registeredUnits.push({dir,hash});

        deputyKernel.moduleRegistered?.(dir);

        logger.info("Extension loaded",{dir,hash});

      }catch(err){

        logger.error("Extension failure",{
          extension:dir,
          error:err.message
        });
      }
    }
  }
}

/* ======================================================
   HEALTH ENDPOINT
====================================================== */

app.get("/health",(req,res)=>{
  res.json({
    status:"ok",
    app:APP_NAME,
    extensions:registeredUnits.length,
    time:new Date().toISOString()
  });
});

/* ======================================================
   404
====================================================== */

app.use((req,res)=>{
  res.status(404).json({
    error:"Route not found",
    requestId:req.requestId
  });
});

/* ======================================================
   GLOBAL ERROR HANDLER
====================================================== */

app.use((err,req,res,next)=>{

  logger.error("Unhandled request error",{
    error:err.message,
    requestId:req.requestId
  });

  runtime.auditEvent?.("SERVER_ERROR",{
    requestId:req.requestId,
    error:err.message
  });

  res.status(500).json({
    error:"Internal server error",
    requestId:req.requestId
  });
});

/* ======================================================
   BOOT VALIDATION
====================================================== */

function validateBoot(){

  if(!runtime) throw new Error("Runtime missing");
  if(!loadShield) throw new Error("Security missing");
  if(!deputyKernel) throw new Error("Deputy missing");

  deputyKernel.preBootCheck?.();

  Object.freeze(runtime);
  Object.freeze(deputyKernel);

  logger.info("Boot validation passed");
}

/* ======================================================
   START SERVER
====================================================== */

let autopilotHandle=null;

async function startServer(){

  try{

    validateBoot();

    await runtime.initialize?.();
    await deputyKernel.initialize?.();

    await discoverUnits();

    const server = app.listen(PORT,()=>{

      logger.info("Server running",{port:PORT});

      autopilotHandle =
        autopilot.startAutopilot?.();

      deputyKernel.startOperationsLoop?.();
    });

    setupShutdown(server);

  }catch(err){

    logger.error("Startup failed",{error:err.message});
    process.exit(1);
  }
}

/* ======================================================
   SHUTDOWN
====================================================== */

function setupShutdown(server){

  async function shutdown(signal){

    logger.warn("Shutdown",{signal});

    if(autopilotHandle)
      clearInterval(autopilotHandle);

    await deputyKernel.shutdown?.();
    await runtime.shutdown?.();

    server.close(()=>{
      logger.info("HTTP closed");
      process.exit(0);
    });

    setTimeout(()=>process.exit(1),10000);
  }

  process.on("SIGINT",shutdown);
  process.on("SIGTERM",shutdown);
}

/* ======================================================
   SAFETY NET
====================================================== */

process.on("unhandledRejection",e=>{
  logger.error("Unhandled rejection",{error:e.message});
});

process.on("uncaughtException",e=>{
  logger.error("Uncaught exception",{error:e.message});
});

/* ======================================================
   START
====================================================== */

startServer();
