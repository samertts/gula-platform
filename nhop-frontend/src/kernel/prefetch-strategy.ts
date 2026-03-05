

/*
==========================================================
NHOP INTENT-DRIVEN PREFETCH ENGINE
Hybrid Kernel + User Behavior Intelligence
==========================================================
*/

type EventBus = {
  publish: (event: string, data?: any) => void;
  subscribe: (event: string, cb: (data?: any) => void) => void;
};

const seenModules = new Set<string>();

/* ======================================================
   PREFETCH CORE
====================================================== */

async function prefetchModule(name: string) {
  if (!name || seenModules.has(name)) return;

  seenModules.add(name);

  console.log(`⚡ Prefetching module: ${name}`);

  try {
    await import(`../modules/${name}/index`);
  } catch (err) {
    console.warn("Prefetch failed:", name, err);
  }
}

/* ======================================================
   USER INTENT DETECTOR (DOM → SIGNALS)
====================================================== */

function attachIntentListeners(eventBus: EventBus) {

  // Hover intent (strong predictor)
  document.addEventListener("pointerenter", (e) => {
    const el = (e.target as HTMLElement)?.closest("[data-module]");
    if (!el) return;

    const module = el.getAttribute("data-module");
    eventBus.publish("intent:hover", { module });
  }, true);

  // Click intent (certainty)
  document.addEventListener("click", (e) => {
    const el = (e.target as HTMLElement)?.closest("[data-module]");
    if (!el) return;

    const module = el.getAttribute("data-module");
    eventBus.publish("intent:click", { module });
  });

  // Idle intent (CPU free)
  requestIdleCallback(() => {
    eventBus.publish("intent:idle");
  });
}

/* ======================================================
   STRATEGY BRAIN
====================================================== */

export function prefetchOnUserIntent(eventBus: EventBus) {

  console.log("🧠 Intent Prefetch Engine online");

  attachIntentListeners(eventBus);

  /* hover = preload */
  eventBus.subscribe("intent:hover", ({ module }) => {
    prefetchModule(module);
  });

  /* click = guaranteed load */
  eventBus.subscribe("intent:click", ({ module }) => {
    prefetchModule(module);
  });

  /* idle = warm critical modules */
  eventBus.subscribe("intent:idle", () => {
    ["dashboard", "patients"].forEach(prefetchModule);
  });
}
