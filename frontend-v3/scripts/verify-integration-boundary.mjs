import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFile(resolve(root, path), "utf8");

const [client, scopedReads, viteConfig, refreshEntry] = await Promise.all([
  read("src/api/client.ts"),
  read("src/api/workspaceScopedReads.ts"),
  read("vite.config.ts"),
  read("../apps/gula-platform-ui-refresh/client/src/main.tsx"),
]);

const expectations = [
  [client, /VITE_API_BASE_URL \?\? "\/api"/, "عميل frontend-v3 يجب أن يعرّف قاعدة REST العامة /api."],
  [client, /withCredentials: true/, "عميل frontend-v3 يجب أن يرسل بيانات اعتماد الجلسة مع REST."],
  [scopedReads, /api\.get<unknown>\("\/authz\/me"\)/, "بوابة القراءة يجب أن تثبت سياق المنشأة عبر REST."],
  [scopedReads, /api\.post<unknown>\("\/authz\/check"/, "بوابة القراءة يجب أن تطلب قرار التفويض عبر REST."],
  [viteConfig, /'\/api':\s*\{\s*target: 'http:\/\/localhost:8000'/s, "وكيل التطوير يجب أن يوجه REST إلى الخلفية المرجعية."],
  [refreshEntry, /url: "\/api\/trpc"/, "تطبيق ui-refresh يجب أن يبقي tRPC على مساره الخادمي المستقل."],
];

for (const [content, pattern, message] of expectations) {
  if (!pattern.test(content)) {
    throw new Error(`فشل ضابط حدود التكامل: ${message}`);
  }
}

for (const [name, content] of [["client", client], ["workspaceScopedReads", scopedReads]]) {
  if (/GULA_BACKEND_SERVICE_TOKEN|GULA_BACKEND_BASE_URL|\/api\/trpc/.test(content)) {
    throw new Error(`فشل ضابط حدود التكامل: لا يجوز أن يكشف ${name} أسرار الجسر الخادمي أو مسار tRPC.`);
  }
}

console.log("تم التحقق من حدود REST المباشر وجسر tRPC الخادمي دون كشف أسرار.");
