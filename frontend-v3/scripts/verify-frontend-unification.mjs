import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checks = [
  {
    file: "src/api/workspaceScopedReads.ts",
    fragments: [
      "patients.read",
      "orders.read",
      "/api/v1/clinical/patients",
      "/api/v1/clinical/orders",
      "DIRECT_REST_SCOPED_READS_BLOCKED",
    ],
    reason: "بوابة القراءة canonical أو ضابط منع legacy fallback غائب.",
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
    fragments: ["frontend-v2", "apps/gula-web-suite", "platform/apps/radiology", 'status: "bridge"'],
    reason: "سجل مصادر الواجهات الأمامية أو جسورها الانتقالية الآمنة غير مكتمل.",
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
  {
    file: "legacy-route-decisions.json",
    fragments: ["frontend-v2", "platform/apps/doctor", "platform/apps/radiology", "safe_bridge"],
    reason: "سجل قرار المسارات الانتقالية route-by-route غير مكتمل.",
  },
  {
    file: "ROUTE_BY_ROUTE_UNIFICATION.md",
    fragments: ["جرد قابل للتحقق آليًا", "safe_bridge", "مسار جديد بلا سجل"],
    reason: "وثيقة قرار المسارات التفصيلية مفقودة أو لا تصف ضابط التغطية.",
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

const catalogPath = resolve(root, "src/pages/migration/frontendSurfaceCatalog.ts");
if (existsSync(catalogPath) && readFileSync(catalogPath, "utf8").includes("pending_contract")) {
  failures.push("سجل مصادر الواجهات يحتوي حالة معلقة خارج جسر frontend-v3 الآمن.");
}

const decisionsPath = resolve(root, "legacy-route-decisions.json");
if (existsSync(decisionsPath)) {
  try {
    const { decisions } = JSON.parse(readFileSync(decisionsPath, "utf8"));
    const allowedDecisions = new Set(["decommissioned", "safe_bridge", "not_client_route"]);
    const decisionBySource = new Map();

    for (const entry of decisions ?? []) {
      if (!entry?.source || !allowedDecisions.has(entry.decision) || !entry.rationale || !Array.isArray(entry.routes) || !entry.routes.length) {
        failures.push("سجل قرار المسارات يحتوي إدخالًا ناقصًا أو قرارًا غير معتمد.");
        continue;
      }
      if (entry.decision === "safe_bridge" && !entry.v3Entry) {
        failures.push(`سجل قرار المسارات: ${entry.source} جسر آمن بلا مدخل frontend-v3.`);
      }
      if (new Set(entry.routes).size !== entry.routes.length) {
        failures.push(`سجل قرار المسارات: ${entry.source} يحتوي مسارًا مكررًا.`);
      }
      decisionBySource.set(entry.source, new Set(entry.routes));
    }

    for (const entry of decisions ?? []) {
      for (const sourceFile of entry.sourceFiles ?? []) {
        const sourcePath = resolve(root, "..", sourceFile);
        if (!existsSync(sourcePath)) {
          if (entry.decision === "decommissioned") continue;
          failures.push(`سجل قرار المسارات: ملف المصدر مفقود (${sourceFile}).`);
          continue;
        }
        const literalRoutes = [...readFileSync(sourcePath, "utf8").matchAll(/["'](\/[^"']*)["']/g)].map((match) => match[1]);
        const registered = decisionBySource.get(entry.source) ?? new Set();
        for (const route of new Set(literalRoutes)) {
          if (!registered.has(route)) {
            failures.push(`سجل قرار المسارات: ${entry.source} يحتوي ${route} بلا قرار موثق.`);
          }
        }
      }
    }
  } catch (error) {
    failures.push(`تعذر تحليل سجل قرار المسارات: ${error instanceof Error ? error.message : String(error)}`);
  }
}

if (failures.length) {
  console.error("فشل ضابط توحيد frontend-v3:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("نجح ضابط توحيد frontend-v3: الجسر والقراءات النطاقية ووثيقة الانتقال متسقة.");
