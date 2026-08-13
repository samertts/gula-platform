import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const routesSourcePath = resolve(repositoryRoot, "frontend-v3/src/routes/index.tsx");
const outputDirectory = resolve(repositoryRoot, "docs/contract-audit/generated");
const source = await readFile(routesSourcePath, "utf8");

const routeLines = source.split("\n").flatMap((line, lineIndex) => {
  const match = line.match(/\{\s*path:\s*"([^"]+)"/);
  return match ? [{ path: match[1], line: lineIndex + 1, source: line.trim() }] : [];
});

const occurrences = new Map();
const registered = routeLines.map((route) => {
  const occurrence = (occurrences.get(route.path) ?? 0) + 1;
  occurrences.set(route.path, occurrence);
  const id = `${route.path}#${occurrence}`;

  if (route.path === "patients") {
    return {
      ...route,
      id,
      contract: "patients.read",
      decision: "blocked_server_enforcement",
      reason: "بوابة الواجهة تمنع القراءة؛ موجه البيانات لا يثبت فرض صلاحية دقيقة داخل الخادم.",
      authorization: "محجوب: فحص المتصفح ليس بديلًا عن حارس خادمي مفروض في مسار البيانات.",
      tenancy: "لا ينفذ طلب بيانات؛ يوجد دليل lab_id جزئي لا يكفي وحده للتفعيل.",
      negativeOutcome: "منع آمن: server_enforcement_required؛ لا يُرسل طلب REST للمرضى.",
    };
  }
  if (route.path === "orders") {
    return {
      ...route,
      id,
      contract: "orders.read",
      decision: "blocked_server_enforcement",
      reason: "بوابة الواجهة تمنع القراءة؛ موجه البيانات لا يثبت فرض صلاحية دقيقة داخل الخادم.",
      authorization: "محجوب: فحص المتصفح ليس بديلًا عن حارس خادمي مفروض في مسار البيانات.",
      tenancy: "لا ينفذ طلب بيانات؛ يوجد دليل lab_id جزئي لا يكفي وحده للتفعيل.",
      negativeOutcome: "منع آمن: server_enforcement_required؛ لا يُرسل طلب REST للطلبات.",
    };
  }
  if (route.path === "reports") {
    return {
      ...route,
      id,
      contract: "غير مرتبط",
      decision: "blocked_unbound",
      reason: "تعرض الصفحة حالة خالية آمنة ولا يوجد عقد تقارير معتمد.",
      authorization: "محجوب: لا يوجد إذن خادمي موثق.",
      tenancy: "محجوب: لا يوجد دليل نطاق منشأة.",
      negativeOutcome: "رفض آمن: لا يجري طلب شبكة ولا تُعرض مؤشرات أو تنزيلات.",
    };
  }
  if (["login", "register"].includes(route.path)) {
    return {
      ...route,
      id,
      contract: "حد المصادقة",
      decision: "auth_boundary",
      reason: "لا تمثل الصفحة قراءة أو كتابة لبيانات سريرية.",
      authorization: "خارج بوابة العقود السريرية.",
      tenancy: "لا ينطبق قبل إنشاء الجلسة.",
      negativeOutcome: "لا يسمح المسار بالوصول إلى البيانات السريرية.",
    };
  }
  if (route.path === "*" && route.source.includes("LegacyRouteBridge")) {
    return {
      ...route,
      id,
      contract: "جسر انتقال",
      decision: "safe_legacy_bridge",
      reason: "يعيد التوجيه إلى واجهة v3 آمنة أو حالة منع دون استدعاء بيانات تشغيلية.",
      authorization: "لا يمنح الجسر صلاحية تشغيلية.",
      tenancy: "لا يمرر الجسر بيانات نطاقية.",
      negativeOutcome: "رفض آمن أو تحويل إلى مسار v3؛ لا يستدعي بيانات تشغيلية.",
    };
  }
  if (route.path === "*" || route.source.includes("<Navigate")) {
    return {
      ...route,
      id,
      contract: "لا ينطبق",
      decision: "navigation_redirect",
      reason: "المسار يعيد التوجيه ولا ينفذ تدفق بيانات تشغيليًا.",
      authorization: "لا ينطبق على مسار تحويل.",
      tenancy: "لا ينطبق على مسار تحويل.",
      negativeOutcome: "لا يتصل المسار بالخلفية.",
    };
  }
  return {
    ...route,
    id,
    contract: "غير مسجل",
    decision: "blocked_not_registered",
    reason: "لا يوجد عقد قراءة أو كتابة موثق ومفروض في بوابة الاستبدال الحالية.",
    authorization: "محجوب: لا يوجد إذن خادمي موثق ومفروض.",
    tenancy: "محجوب: لا يوجد دليل عزل منشأة/مورد كافٍ.",
    negativeOutcome: "منع صريح: لا يعد المسار مكافئًا وظيفيًا ولا يفعّل تدفقًا تشغيليًا.",
  };
});

const payload = {
  source: "frontend-v3/src/routes/index.tsx",
  routeCount: registered.length,
  entries: registered,
};
const escapeCell = (value) => String(value).replaceAll("|", "\\|");
const markdown = [
  "# خريطة عقود مسارات frontend-v3",
  "",
  "هذه خريطة مولدة من تعريف المسارات المركزي. لكل مدخل مسار قرار عقد أو منع صريح؛ ولا تعني حالة المنع وجود قدرة تشغيلية.",
  "",
  "| المعرّف | المسار | العقد/الحد | القرار | التفويض | العزل/السياق | نتيجة الرفض |",
  "|---|---|---|---|---|---|",
  ...registered.map((entry) => `| ${escapeCell(entry.id)} | ${escapeCell(entry.path)} | ${escapeCell(entry.contract)} | ${escapeCell(entry.decision)} | ${escapeCell(entry.authorization)} | ${escapeCell(entry.tenancy)} | ${escapeCell(entry.negativeOutcome)} |`),
  "",
  `> عدد المداخل المسجلة: **${registered.length}**. أعد توليد هذه الوثيقة بواسطة \`pnpm generate:route-gate\` من داخل \`frontend-v3\`.`,
].join("\n");

await mkdir(outputDirectory, { recursive: true });
await Promise.all([
  writeFile(resolve(outputDirectory, "frontend-route-contract-map.json"), `${JSON.stringify(payload, null, 2)}\n`),
  writeFile(resolve(outputDirectory, "FRONTEND_ROUTE_CONTRACT_MAP.md"), `${markdown}\n`),
]);

console.log(`تم توليد خريطة بوابة لـ ${registered.length} مدخل مسار في frontend-v3.`);
