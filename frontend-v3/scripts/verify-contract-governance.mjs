import { access, readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const refreshedAppRoot = join(repositoryRoot, "apps", "gula-platform-ui-refresh");

const requiredContracts = [
  { id: "patients.read", permission: "patients:read", workspace: true },
  { id: "orders.read", permission: "orders:read", workspace: true },
];

async function readRequired(path, label) {
  try {
    await access(path);
  } catch {
    throw new Error(`${label}: الملف المطلوب غير موجود (${path}).`);
  }
  return readFile(path, "utf8");
}

const [registrySource, scopedReads, patientPage, ordersPage, policy, matrix, ledger] = await Promise.all([
  readRequired(join(refreshedAppRoot, "scripts", "backend-contract-registry.json"), "سجل العقود"),
  readRequired(join(frontendRoot, "src", "api", "workspaceScopedReads.ts"), "بوابة القراءات النطاقية"),
  readRequired(join(frontendRoot, "src", "pages", "patients", "PatientsPage.tsx"), "صفحة المرضى"),
  readRequired(join(frontendRoot, "src", "pages", "orders", "OrdersPage.tsx"), "صفحة الطلبات"),
  readRequired(join(refreshedAppRoot, "surface_contract_policy.md"), "سياسة ربط العقود"),
  readRequired(join(refreshedAppRoot, "ui_action_contract_matrix.md"), "مصفوفة الإجراءات"),
  readRequired(join(refreshedAppRoot, "refresh_surface_contract_ledger.md"), "سجل الأسطح"),
]);

const registry = JSON.parse(registrySource);
const violations = [];
const contractsById = new Map(registry.contracts.map((contract) => [contract.id, contract]));

for (const expected of requiredContracts) {
  const contract = contractsById.get(expected.id);
  if (!contract) {
    violations.push(`العقد ${expected.id} غير مسجل في سجل العقود المرجعي.`);
    continue;
  }
  if (contract.permission !== expected.permission || contract.requiresWorkspaceContext !== expected.workspace) {
    violations.push(`العقد ${expected.id} لا يطابق الصلاحية أو شرط سياق المنشأة المعتمد.`);
  }
}

for (const requiredFragment of [
  'api.get<unknown>("/authz/me")',
  'api.post<unknown>("/authz/check"',
  'resource_attrs: { lab_id: scope.labId }',
  'await requireVerifiedWorkspacePermission(SCOPED_READ_CONTRACTS.patients.permission)',
  'await requireVerifiedWorkspacePermission(SCOPED_READ_CONTRACTS.orders.permission)',
]) {
  if (!scopedReads.includes(requiredFragment)) {
    violations.push(`بوابة القراءات النطاقية تفتقد الفرض المطلوب: ${requiredFragment}`);
  }
}

for (const [label, source, contractId, permission] of [
  ["صفحة المرضى", patientPage, "patients.read", "patients:read"],
  ["صفحة الطلبات", ordersPage, "orders.read", "orders:read"],
]) {
  if (!source.includes('data-workspace-context="required"') || !source.includes(contractId) || !source.includes(permission)) {
    violations.push(`${label} لا تعلن العقد أو الصلاحية أو سياق المنشأة صراحة.`);
  }
}

if (!policy.includes("لا يجوز") || !policy.includes("سجل العقود المرجعي") || !matrix.includes("معرف العقد الأساسي") || !ledger.includes("patients.read") || !ledger.includes("orders.read")) {
  violations.push("أدلة حوكمة الواجهة المنقولة ناقصة أو لا توثق عقود المرضى والطلبات المعتمدة.");
}

if (violations.length) {
  throw new Error(`فشل ضابط عقود frontend-v3:\n- ${violations.join("\n- ")}`);
}

console.log("✓ تم التحقق من عقود المرضى والطلبات النطاقية، والصلاحيات، وسياق المنشأة، وأدلة الحوكمة المرجعية.");
