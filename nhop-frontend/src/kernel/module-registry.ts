import type { NHOPModule } from "./module-types";

type Loader = () => Promise<{ default: NHOPModule }>;

const registry: Record<string, Loader> = {};

export function registerModule(
  name: string,
  loader: Loader
) {
  registry[name] = loader;
}

export async function loadRegisteredModule(
  name: string
): Promise<NHOPModule> {

  const loader = registry[name];

  if (!loader) {
    throw new Error(`Module "${name}" not registered`);
  }

  const mod = await loader();

  return mod.default;
}
