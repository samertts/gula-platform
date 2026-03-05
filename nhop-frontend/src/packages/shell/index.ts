
/*
==================================================
NHOP UI SHELL
Root Application Layout
==================================================
*/

import { loadModule } from "../../kernel/module-loader";

type Ctx = {
  eventBus?: any;
};

export async function render(root: HTMLElement, ctx: Ctx) {

  root.innerHTML = `
    <div id="nhop-shell" style="
      font-family: system-ui;
      background:#0f172a;
      color:white;
      min-height:100vh;
      display:flex;
      flex-direction:column;
    ">

      <header style="
        padding:16px 24px;
        background:#020617;
        border-bottom:1px solid #1e293b;
        display:flex;
        gap:12px;
      ">
        <button data-route="dashboard">Dashboard</button>
      </header>

      <main id="nhop-view" style="
        flex:1;
        padding:24px;
      ">
        Loading module...
      </main>

    </div>
  `;

  const view = document.getElementById("nhop-view")!;

  async function navigate(name: string) {
    view.innerHTML = "Loading...";
    const mod = await loadModule(name);

    if (mod?.render) {
      mod.render(view, ctx);
    } else {
      view.innerHTML = "Module has no render()";
    }
  }

  document.querySelectorAll("[data-route]").forEach(btn => {
    btn.addEventListener("click", e => {
      const route =
        (e.currentTarget as HTMLElement).dataset.route;

      if (route) navigate(route);
    });
  });

  // first screen
  await navigate("dashboard");

  console.log("✅ NHOP Shell Ready");
}


/*
==================================================
DASHBOARD MODULE
==================================================
*/

export function render(root: HTMLElement) {

  root.innerHTML = `
    <div style="
      background:#1e293b;
      padding:24px;
      border-radius:12px;
    ">
      <h2>📊 NHOP Dashboard</h2>
      <p>Kernel + Shell + Module Loader working ✅</p>
    </div>
  `;

  console.log("Dashboard loaded");
}
