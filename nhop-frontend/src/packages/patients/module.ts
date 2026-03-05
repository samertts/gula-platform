
import type { NHOPModule } from "../../kernel/module-types";

const PatientsModule: NHOPModule = {

  id: "patients",
  title: "Patients",

  mount(root: HTMLElement) {

    root.innerHTML = `
      <h1>Patients Module</h1>
      <p>Clinical system ready 🧬</p>

      <button id="add">
        Add Patient
      </button>
    `;

    document
      .getElementById("add")
      ?.addEventListener("click", () => {

        alert("Patient workflow placeholder");

      });
  },

  unmount() {
    console.log("Patients module unloaded");
  }

};

export default PatientsModule;

import { loadModule } from "../../kernel/module-loader";

let current: any = null;

export async function navigate(route: string) {

  const view = document.getElementById("app-view");
  if (!view) return;

  if (current?.unmount) {
    current.unmount();
  }

  view.innerHTML = "Loading...";

  current = await loadModule(route);

  await current.mount(view, {});
}


