import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const read = (path) => readFile(resolve(repositoryRoot, path), "utf8");

const [snapshotText, gate, authorization, integration, routesSource, routeMapText, candidateMatrix] = await Promise.all([
  read("docs/contract-audit/generated/route-snapshots.json"),
  read("docs/contract-audit/FUNCTIONAL_REPLACEMENT_GATE.md"),
  read("docs/contract-audit/AUTHORIZATION_AND_TENANCY_AUDIT.md"),
  read("docs/contract-audit/INTEGRATION_BOUNDARY_AUDIT.md"),
  read("frontend-v3/src/routes/index.tsx"),
  read("docs/contract-audit/generated/frontend-route-contract-map.json"),
  read("docs/contract-audit/FRONTEND_CANDIDATE_CONTRACT_MATRIX.md"),
]);

const snapshot = JSON.parse(snapshotText);
const routes = snapshot.domains.flatMap((domain) => domain.endpoints ?? []);
const routeMap = JSON.parse(routeMapText);
const routedEntries = routesSource.split("\n").flatMap((line) => line.match(/\{\s*path:\s*"([^"]+)"/) ? [line] : []);

if (!Array.isArray(snapshot.domains) || snapshot.domains.length !== 7) {
  throw new Error("فشل تدقيق المخرجات: يجب أن تتضمن اللقطة المجالات السبعة المحددة.");
}

if (routes.length !== 306) {
  throw new Error(`فشل تدقيق المخرجات: العدد المستخرج للمسارات هو ${routes.length} بدل 306.`);
}

for (const route of routes) {
  const required = ["method", "path", "handler", "inputLocation", "responseShape", "requiresCurrentUser", "explicitPermissionGuard", "tenantContextEvidence", "authorizationStatus", "tenancyStatus", "negativeVerification", "functionalEligibility"];
  if (required.some((key) => !(key in route))) {
    throw new Error(`فشل تدقيق المخرجات: صف عقد ناقص الحقول الإلزامية (${route.path ?? "مسار مجهول"}).`);
  }
}

if (routes.some((route) => route.functionalEligibility !== "ممنوع من الربط الوظيفي" && route.functionalEligibility !== "مرشح لتدقيق يدوي لاحق؛ غير معتمد وظيفيًا")) {
  throw new Error("فشل تدقيق المخرجات: يحتوي مسار خلفي على حالة أهلية وظيفية غير معتمدة.");
}

for (const [name, content, phrases] of [
  ["قرار البوابة", gate, ["ممنوع", "متطلبات فتح البوابة", "الجسر الآمن", "FRONTEND_ROUTE_CONTRACT_MAP.md"]],
  ["تدقيق التفويض", authorization, ["اختبار رفض", "require_permission", "ممنوع"]],
  ["تدقيق التكامل", integration, ["GULA_BACKEND_SERVICE_TOKEN", "لا يدمج التدقيق المسارين تلقائيًا"]],
]) {
  if (phrases.some((phrase) => !content.includes(phrase))) {
    throw new Error(`فشل تدقيق المخرجات: ${name} لا يتضمن الحد الأدنى من قرار الحوكمة.`);
  }
}

if (routeMap.routeCount !== routedEntries.length || routeMap.entries?.length !== routedEntries.length) {
  throw new Error("فشل تدقيق المخرجات: خريطة بوابة الصفحات لا تطابق عدد المسارات المسجلة في frontend-v3.");
}

const allowedDecisions = new Set(["blocked_server_enforcement", "blocked_unbound", "auth_boundary", "safe_legacy_bridge", "navigation_redirect", "blocked_not_registered"]);
for (const entry of routeMap.entries) {
  if (!entry.path || !entry.contract || !entry.decision || !entry.reason || !entry.authorization || !entry.tenancy || !entry.negativeOutcome || !allowedDecisions.has(entry.decision)) {
    throw new Error(`فشل تدقيق المخرجات: يوجد مسار في خريطة البوابة بلا قرار مكتمل (${entry.path ?? "مجهول"}).`);
  }
}

const candidateReads = routeMap.entries.filter((entry) => ["orders.read", "patients.read"].includes(entry.contract));
if (candidateReads.length !== 2 || candidateReads.some((entry) => entry.decision !== "blocked_server_enforcement" || !entry.negativeOutcome.includes("server_enforcement_required"))) {
  throw new Error("فشل تدقيق المخرجات: يجب منع عقدي المرضى والطلبات حتى يثبت فرض الصلاحية الخادمي.");
}

for (const phrase of ["patients.read", "orders.read", "server_enforcement_required", "POST /authz/check", "قرار المنع"]) {
  if (!candidateMatrix.includes(phrase)) {
    throw new Error(`فشل تدقيق المخرجات: مصفوفة العقود المرشحة لا تتضمن الدليل الإلزامي (${phrase}).`);
  }
}

console.log(`تم التحقق من ${routes.length} مسارًا خلفيًا و${routeMap.entries.length} مدخل واجهة وسبعة مجالات وقرارات البوابة والتفويض والتكامل.`);
