import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checks = [
  {
    file: "src/api/workspaceScopedReads.ts",
    fragments: ["patients.read", "orders.read", "authz/me"],
    reason: "بوابة القراءة النطاقية الموحدة غائبة أو لا توثق عقدي المرضى والطلبات.",
  },
  {
    file: "src/pages/patients/PatientsPage.tsx",
    fragments: ["workspaceScopedReads"],
    reason: "صفحة المرضى لا تستخدم بوابة القراءة النطاقية الموحدة.",
  },
  {
    file: "src/pages/orders/OrdersPage.tsx",
    fragments: ["workspaceScopedReads"],
    reason: "صفحة الطلبات لا تستخدم بوابة القراءة النطاقية الموحدة.",
  },
  {
    file: "src/routes/index.tsx",
    fragments: ["LegacyRouteBridge", 'path: "*"'],
    reason: "جدول المسارات لا يسجل جسر التوافق الانتقالي.",
  },
  {
    file: "src/pages/migration/frontendSurfaceCatalog.ts",
    fragments: ["frontend-v2", "apps/gula-web-suite", "platform/apps/radiology", "pending_contract"],
    reason: "سجل مصادر الواجهات الأمامية أو حالات انتقالها غير مكتمل.",
  },
  {
    file: "src/pages/migration/LegacyRouteBridge.tsx",
    fragments: ["specialtyEntrypoints", "resolveLegacyRoute"],
    reason: "جسر توافق واجهات الإصدار الثاني والتطبيقات التخصصية غير مكتمل.",
  },
  {
    file: "FRONTEND_UNIFICATION.md",
    fragments: ["السطح الأمامي المرجعي", "طبقة القراءة الموحدة", "التدفقات السريرية الفرعية"],
    reason: "وثيقة توحيد الواجهة لا تصف النطاق وحالات الانتقال بصورة كافية.",
  },
];

const failures = [];
for (const check of checks) {
  const path = resolve(root, check.file);
  if (!existsSync(path)) {
    failures.push(`${check.file}: الملف مفقود. ${check.reason}`);
    continue;
  }

  const content = readFileSync(path, "utf8");
  const missing = check.fragments.filter((fragment) => !content.includes(fragment));
  if (missing.length) {
    failures.push(`${check.file}: مكونات مفقودة (${missing.join(", ")}). ${check.reason}`);
  }
}

if (failures.length) {
  console.error("فشل ضابط توحيد frontend-v3:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("نجح ضابط توحيد frontend-v3: الجسر والقراءات النطاقية ووثيقة الانتقال متسقة.");
