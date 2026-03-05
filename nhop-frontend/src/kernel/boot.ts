
/*
==========================================================
NHOP UI KERNEL BOOTLOADER — FINAL HARDENED EDITION
Sovereign Frontend Runtime
==========================================================
*/

import { initEventBus } from "./event-bus";
import { initCache } from "./cache-manager";
import { loadModule } from "./module-loader";
import { prefetchOnUserIntent } from "./prefetch-strategy";
import { connectSSE } from "../shared/services/sse";

/* ======================================================
   GLOBAL RUNTIME STATE
====================================================== */

const runtime = {
  started: false,
  bootTime: 0,
  eventBus: null as any
};

/* ======================================================
   SAFE DOM READY (memory safe)
====================================================== */

function domReady(): Promise<void> {
  return new Promise((resolve) => {

    if (
      document.readyState === "complete" ||
      document.readyState === "interactive"
    ) {
      resolve();
      return;
    }

    document.addEventListener(
      "DOMContentLoaded",
      () => resolve(),
      { once: true }
    );
  });
}

/* ======================================================
   EVENT BUS HARDENING
====================================================== */

function secureEventBus(eventBus:any){

  const originalPublish = eventBus.publish.bind(eventBus);

  eventBus.publish = (event:string, payload:any)=>{

    if(
      !event.startsWith("server:") &&
      !event.startsWith("ui:") &&
      !event.startsWith("module:")
    ){
      console.warn("[EVENT BLOCKED]",event);
      return;
    }

    originalPublish(event,payload);
  };

  return eventBus;
}

/* ======================================================
   SSE SAFE CONNECT (single instance)
====================================================== */

let sseConnected = false;

function safeConnectSSE(eventBus:any){

  if(sseConnected){
    console.log("[SSE] already connected");
    return;
  }

  /* prevent multi-tab flood */
  if(localStorage.getItem("nhop_sse_lock")){
    console.log("[SSE] secondary tab detected — disabled");
    return;
  }

  localStorage.setItem("nhop_sse_lock","1");

  connectSSE(eventBus);
  sseConnected = true;
}

/* ======================================================
   FAILOVER UI
====================================================== */

function renderBootFailure(root:HTMLElement){

  root.innerHTML = `
    <div style="
      font-family:sans-serif;
      padding:40px;
      text-align:center">
      <h2>System failed to start</h2>
      <p>Please refresh or contact administrator</p>
    </div>
  `;
}

/* ======================================================
   BOOT SEQUENCE
====================================================== */

export async function bootNHOP(){

  if(runtime.started){
    console.warn("NHOP already booted");
    return;
  }

  console.log("🚀 NHOP UI Boot Starting...");
  runtime.bootTime = performance.now();

  /* -----------------------------
     1. WAIT DOM
  ----------------------------- */

  await domReady();

  const root = document.getElementById("app");

  if(!root){
    throw new Error("#app container missing in index.html");
  }

  /* -----------------------------
     2. EVENT BUS INIT
  ----------------------------- */

  let eventBus = initEventBus();
  eventBus = secureEventBus(eventBus);

  runtime.eventBus = eventBus;

  console.log("✅ Event Bus Ready");

  /* -----------------------------
     3. CACHE INIT
  ----------------------------- */

  try{
    await initCache();
    console.log("✅ Cache initialized");
  }catch(err){
    console.warn("Cache disabled",err);
  }

  /* -----------------------------
     4. SSE REALTIME
  ----------------------------- */

  try{
    safeConnectSSE(eventBus);
    console.log("✅ SSE connected");
  }catch(err){
    console.warn("SSE unavailable",err);
  }

  /* -----------------------------
     5. LOAD SHELL MODULE
  ----------------------------- */

  let shell:any;

  try{
    shell = await loadModule("shell");
  }catch(err){
    console.error("Shell load failed",err);
    renderBootFailure(root);
    return;
  }

  if(!shell?.render){
    renderBootFailure(root);
    throw new Error("Shell module missing render()");
  }

  shell.render(root,{ eventBus });

  console.log("✅ Shell rendered");

  /* -----------------------------
     6. PREFETCH ENGINE
  ----------------------------- */

  prefetchOnUserIntent(eventBus);

  console.log("✅ Prefetch active");

  /* -----------------------------
     7. GLOBAL EVENT HOOKS
  ----------------------------- */

  eventBus.subscribe("server:health",(data:any)=>{
    console.log("[HEALTH]",data);
  });

  eventBus.subscribe("server:error",(err:any)=>{
    console.warn("[SERVER ERROR]",err);
  });

  /* -----------------------------
     8. BOOT TELEMETRY
  ----------------------------- */

  runtime.started = true;

  const bootDuration =
    Math.round(performance.now() - runtime.bootTime);

  console.log(`🔥 NHOP UI Ready (${bootDuration}ms)`);

  eventBus.publish("ui:booted",{
    duration: bootDuration,
    ts: Date.now()
  });
}

/* ======================================================
   AUTO START
====================================================== */

bootNHOP().catch((err)=>{
  console.error("BOOT FAILURE",err);
});
