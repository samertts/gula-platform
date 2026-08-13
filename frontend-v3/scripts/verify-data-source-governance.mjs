import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildDataSourceInventory } from "./data-source-inventory.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFile(resolve(root, path), "utf8");
const failures = [];

async function assertContains(path, snippets) {
  const source = await read(path);
  for (const snippet of snippets) {
    if (!source.includes(snippet)) failures.push(`${path}: missing ${snippet}`);
  }
  return source;
}

const decisions = JSON.parse(await read("data-source-decisions.json"));
const savedInventory = JSON.parse(await read("data-source-inventory.json"));
const generatedInventory = await buildDataSourceInventory();

if (JSON.stringify(savedInventory) !== JSON.stringify(generatedInventory)) {
  failures.push("data-source-inventory.json: stale or incomplete inventory; run pnpm generate:data-source-inventory");
}

if (generatedInventory.surfaces.length === 0) {
  failures.push("data-source-inventory.json: no data surfaces were discovered");
}

for (const surface of generatedInventory.surfaces) {
  if (!generatedInventory.allowedClassifications.includes(surface.classification)) {
    failures.push(`${surface.source}: missing an allowed explicit classification`);
  }

  if (surface.kinds.includes("demo-surface")) {
    const source = await read(surface.source);
    if (surface.classification !== "demo-only") {
      failures.push(`${surface.source}: demo surface must be classified demo-only`);
    }
    if (/data-contract-status=["']operational["']/.test(source)) {
      failures.push(`${surface.source}: demo surface must not claim operational data`);
    }
  }
}

for (const required of [
  "src/pages/patients/PatientsPage.tsx",
  "src/pages/orders/OrdersPage.tsx",
  "src/pages/ehr/EhrPage.tsx",
  "src/pages/results/ResultsPage.tsx",
  "src/pages/samples/SamplesPage.tsx",
]) {
  if (!generatedInventory.surfaces.some((surface) => surface.source === required)) {
    failures.push(`data-source-inventory.json: missing controlled surface ${required}`);
  }
}

if (decisions.visibleOperationalWrites.length !== 12) {
  failures.push("data-source-decisions.json: visible operational write inventory must contain 12 decisions");
}

for (const item of decisions.visibleOperationalWrites) {
  const source = await read(item.source);
  if (!source.includes(item.operation.replace("POST ", ""))) {
    failures.push(`${item.source}: missing inventoried operation ${item.operation}`);
  }
}

for (const path of ["src/pages/ehr/EhrPage.tsx", "src/pages/results/ResultsPage.tsx", "src/pages/samples/SamplesPage.tsx"]) {
  await assertContains(path, ["LegacyRouteBridge"]);
}

await assertContains("src/api/client.ts", [
  "OperationalWriteBlockedError",
  "OperationalReadBlockedError",
  "assertFrontendWriteIsAllowed",
  "assertFrontendReadIsAllowed",
  "IDENTITY_AND_DECISION_ALLOWLIST",
  "INITIALIZATION_READ_ALLOWLIST",
  "this.instance.interceptors.request.use",
]);

const hooks = await read("src/hooks/useApi.ts");
for (const hook of decisions.unusedClinicalMutationHooks) {
  if (!hooks.includes(`function ${hook}`)) failures.push(`src/hooks/useApi.ts: missing declared hook ${hook}`);
}

for (const page of ["src/pages/patients/PatientsPage.tsx", "src/pages/orders/OrdersPage.tsx"]) {
  await assertContains(page, ["workspaceScopedReads", "data-contract-id", "data-workspace-context"]);
}

if (failures.length > 0) {
  console.error("فشل تدقيق مصادر البيانات في frontend-v3:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`نجح تدقيق مصادر البيانات: ${generatedInventory.surfaces.length} سطحًا مصنفًا صراحةً، وأسـطح القراءة السريرية محكومة، وكل الكتابات المرئية مصنفة ومحجوبة مركزيًا.`);
