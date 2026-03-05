const registry = new Map();

export async function loadModule(name:string){

  if(registry.has(name))
    return registry.get(name);

  const mod = await import(
    /* @vite-ignore */
    `/packages/module-${name}/index.ts`
  );

  const sandbox = Object.freeze({
    register: mod.register
  });

  registry.set(name,sandbox);

  return sandbox;
}
