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
  [scopedReads, /\/api\/v1\/clinical\/patients/, "بوابة القراءة يجب أن تستخدم مسار patients.read canonical."],
  [scopedReads, /\/api\/v1\/clinical\/orders/, "بوابة القراءة يجب أن تستخدم مسار orders.read canonical."],
  [scopedReads, /contract_version: "1\.0"/, "بوابة القراءة يجب أن تتحقق من envelope versioned."],
  [scopedReads, /workspace_context/, "بوابة القراءة يجب أن تتحقق من سياق مساحة العمل الخادمي."],
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

console.log("تم التحقق من حدود REST المباشر والبوابة السريرية canonical وجسر tRPC الخادمي دون كشف أسرار.");
