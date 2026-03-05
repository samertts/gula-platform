import { loadModule } from "../../kernel/module-loader";

const viewId = "app-view";

export async function navigate(route: string) {

  const view = document.getElementById(viewId);
  if (!view) return;

  view.innerHTML = "Loading...";

  const module = await loadModule(route);

  if (module?.render) {
    module.render(view, {});
  }
}
