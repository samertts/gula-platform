import { readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const root = resolve(scriptDir, "..");
const sourceRoot = resolve(root, "src");
const outputPath = resolve(root, "data-source-inventory.json");

const CONTROLLED_SURFACES = {
  "src/pages/patients/PatientsPage.tsx": "contract-bound",
  "src/pages/orders/OrdersPage.tsx": "contract-bound",
  "src/pages/ehr/EhrPage.tsx": "safe_bridge",
  "src/pages/results/ResultsPage.tsx": "safe_bridge",
  "src/pages/samples/SamplesPage.tsx": "safe_bridge",
};

const DEMO_SURFACES = new Set([
  "src/contexts/AuthContext.tsx",
  "src/layouts/DashboardLayout.tsx",
  "src/layouts/Sidebar.tsx",
]);

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(async (entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  }));
  return files.flat();
}

function sourceKinds(source, relativePath) {
  const kinds = [];
  if (relativePath === "src/api/endpoints.ts") kinds.push("endpoint-catalog");
  if (/from\s+["']@\/api\/endpoints["']/.test(source)) kinds.push("endpoint-import");
  if (/\buseQuery\s*\(/.test(source)) kinds.push("react-query-read");
  if (/\buseMutation\s*\(/.test(source)) kinds.push("react-query-mutation");
  if (/\bworkspaceScopedReads\b/.test(source)) kinds.push("workspace-scoped-read");
  if (/\bapi\.(?:get|post|put|patch|delete)\s*\(/.test(source)) kinds.push("direct-api-client");
  if (/\bLegacyRouteBridge\b/.test(source)) kinds.push("safe-bridge-marker");
  if (/\bdemoAccess\b|\bdemo_mode\b|\bdemoMode\b/.test(source)) kinds.push("demo-surface");
  return kinds;
}

function classify(relativePath, kinds) {
  if (CONTROLLED_SURFACES[relativePath]) return CONTROLLED_SURFACES[relativePath];
  if (DEMO_SURFACES.has(relativePath) || kinds.includes("demo-surface")) return "demo-only";
  return "unbound";
}

export async function buildDataSourceInventory() {
  const all = await walk(sourceRoot);
  const entries = [];

  for (const path of all) {
    if (!/\.(?:ts|tsx)$/.test(path) || /\.(?:test|spec)\.(?:ts|tsx)$/.test(path)) continue;
    const source = await readFile(path, "utf8");
    const rel = relative(root, path).replaceAll("\\", "/");
    const kinds = sourceKinds(source, rel);
    if (kinds.length === 0) continue;

    entries.push({
      source: rel,
      kinds: kinds.sort(),
      classification: classify(rel, kinds),
      status: classify(rel, kinds) === "contract-bound" ? "blocked-until-server-enforcement" : "non-operational",
    });
  }

  return {
    version: 1,
    generatedBy: "scripts/data-source-inventory.mjs",
    sourceRoot: "src",
    allowedClassifications: ["contract-bound", "safe_bridge", "unbound", "demo-only"],
    surfaces: entries.sort((a, b) => a.source.localeCompare(b.source)),
  };
}

export async function writeDataSourceInventory() {
  const inventory = await buildDataSourceInventory();
  await writeFile(outputPath, `${JSON.stringify(inventory, null, 2)}\n`);
  return inventory;
}

const directExecution = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (directExecution) {
  const inventory = await writeDataSourceInventory();
  console.log(`تم توليد جرد مصادر البيانات: ${inventory.surfaces.length} سطحًا.`);
}
