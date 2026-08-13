import { readFile, readdir } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const root = resolve(scriptDir, "..");
const clientRoot = join(root, "client/src");
const policyPath = join(root, "surface_contract_policy.md");
const matrixPath = join(root, "ui_action_contract_matrix.md");
const ledgerPath = join(root, "refresh_surface_contract_ledger.md");
const registryPath = join(root, "scripts/backend-contract-registry.json");
const excludedPaths = new Set([
  "_core/hooks/useAuth.ts",
  "lib/trpc.ts",
  "main.tsx",
  "components/AIChatBox.tsx",
  "pages/ComponentShowcase.tsx",
  "pages/NotFound.tsx",
]);
const directNetworkCalls = /\bfetch\s*\(|\baxios(?:\.[A-Za-z]+)?\s*\(|\buseMutation\b|\.mutate(?:Async)?\s*\(|\bXMLHttpRequest\b/;
const trpcCallPattern = /\btrpc\.([A-Za-z][\w.]*)\.(useQuery|useMutation|mutate|query)\b/g;
const safeClientProcedures = new Set(["integration.connectionStatus"]);

function hasOperationalClientCall(source) {
  if (directNetworkCalls.test(source)) return true;
  return [...source.matchAll(trpcCallPattern)].some((match) => !safeClientProcedures.has(match[1]));
}

async function collectSurfaceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const absolute = join(directory, entry.name);
    const filePath = relative(clientRoot, absolute);
    if (entry.isDirectory()) {
      if (filePath !== "components/ui" && filePath !== "_core") files.push(...await collectSurfaceFiles(absolute));
    } else if ((entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) && !entry.name.endsWith(".test.ts") && !excludedPaths.has(filePath)) {
      files.push({ filePath, absolute });
    }
  }
  return files;
}

function declaredContractIds(source) {
  return [...source.matchAll(/(?:data-contract-id|contractId)\s*(?:=|:)\s*\{?\s*["']([^"']+)["']/g)].map((match) => match[1]);
}

function hasPermissionMarker(source, permission) {
  return source.includes(`data-permission=\"${permission}\"`) || source.includes(`requiredPermission: \"${permission}\"`) || source.includes(`requiredPermission: '${permission}'`);
}

function hasWorkspaceMarker(source) {
  return source.includes('data-workspace-context="required"') || source.includes('workspaceContext: "required"') || source.includes("workspaceContext: 'required'");
}

const [policy, matrix, ledger, registrySource, files] = await Promise.all([
  readFile(policyPath, "utf8"),
  readFile(matrixPath, "utf8"),
  readFile(ledgerPath, "utf8"),
  readFile(registryPath, "utf8"),
  collectSurfaceFiles(clientRoot),
]);
const registry = JSON.parse(registrySource);
const contractsById = new Map(registry.contracts.map((contract) => [contract.id, contract]));
const sources = await Promise.all(files.map(async ({ filePath, absolute }) => ({ filePath, source: await readFile(absolute, "utf8") })));
const violations = [];

if (!policy.includes("لا يجوز") || !policy.includes("لا تُستخدم لإيحاء") || !policy.includes("سجل العقود")) {
  violations.push("سياسة الربط لا تتضمن قواعد منع التشغيل وسجل العقود.");
}
if (!matrix.includes("حالة العقد") || !matrix.includes("معرف العقد الأساسي") || !matrix.includes("العقود التابعة الموثقة") || !matrix.includes("صلاحية الخلفية") || !matrix.includes("يتطلب سياق منشأة") || !matrix.includes("مراجع API داخل المعالج") || !matrix.includes("ملخص التغطية")) {
  violations.push("مصفوفة الإجراءات لا تتضمن تتبع المعالج ومعرف العقد والصلاحية وسياق المنشأة وملخص التغطية.");
}
if (!ledger.includes("حالة منع صريحة") && !ledger.includes("حالة عدم ربط")) {
  violations.push("سجل الصفحات لا يوثق حالة منع أو عدم ربط بوضوح.");
}
if (registry.contracts.length < 20 || registry.contracts.some((contract) => !contract.id || !contract.path || !contract.permission || typeof contract.requiresWorkspaceContext !== "boolean" || !Array.isArray(contract.operationKinds) || contract.operationKinds.length === 0 || !Array.isArray(contract.clientMethods) || contract.clientMethods.length === 0)) {
  violations.push("سجل العقود ناقص أو لا يحدد المسار والصلاحية وسياق مساحة العمل ونوع العملية واسم عملية العميل لكل عقد.");
}

const matrixRows = matrix.split("\n").filter((line) => line.startsWith("| `"));
for (const row of matrixRows) {
  if (row.includes("عقد مرجعي محتمل")) violations.push("المصفوفة تحتوي مطابقة ضمنية على مستوى الملف بدل تتبع المعالج.");
  if (row.includes("مطابق: المعالج يستدعي") && row.includes("| `—` | `—` |")) {
    violations.push("صف مطابق في المصفوفة يفتقد معرف العقد أو الصلاحية أو سياق المنشأة.");
  }
  if (row.includes("غير مطابق: استدعاء المعالج") && !row.includes("يبقى غير تشغيلي حتى توثيق عقد واحد")) {
    violations.push("إجراء تشغيلي بلا عقد محدد لا يعلن بوضوح بقاءه غير تشغيلي.");
  }
  if (row.includes("غير مطابق: استدعاء المعالج")) {
    violations.push("توجد عملية تشغيلية في المصفوفة بلا مسار معالج إلى عقد وصلاحية وسياق منشأة موثقين.");
  }
}

for (const { filePath, source } of sources) {
  const ids = declaredContractIds(source);
  for (const id of ids) {
    if (!contractsById.has(id)) violations.push(`${filePath}: معرف عقد غير موجود في السجل (${id}).`);
  }
  if (!hasOperationalClientCall(source)) continue;
  if (ids.length === 0) {
    violations.push(`${filePath}: استدعاء تشغيلي بلا data-contract-id أو contractId مسجل.`);
    continue;
  }
  for (const id of ids) {
    const contract = contractsById.get(id);
    if (!contract) continue;
    if (!hasPermissionMarker(source, contract.permission)) violations.push(`${filePath}: العقد ${id} بلا مؤشر صلاحية خلفية صريح (${contract.permission})؛ لا تكفي حراسة المسار أو الصلاحية المحلية العامة.`);
    if (contract.requiresWorkspaceContext && !hasWorkspaceMarker(source)) violations.push(`${filePath}: العقد ${id} يتطلب مؤشر سياق مساحة العمل.`);
  }
}

if (violations.length > 0) throw new Error(`فشل ضابط العقود:\n- ${violations.join("\n- ")}`);

console.log(`✓ تم التحقق من ${sources.length} سطح عميل وسجل ${registry.contracts.length} عقدًا: لا توجد استدعاءات تشغيلية غير مسجلة، وكل صف تشغيلي في المصفوفة يتبع المعالج إلى عقد وصلاحية وسياق أو يعلن بقاءه غير تشغيلي.`);
