import { readFile, readdir, writeFile } from "node:fs/promises";
import { join, relative } from "node:path";

const repoRoot = "/home/ubuntu/gula-platform";
const routesPath = join(repoRoot, "frontend-v3/src/routes/index.tsx");
const outputPath = "/home/ubuntu/gula-platform-ui-refresh/ui_route_action_catalog.md";

async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const target = join(directory, entry.name);
    if (entry.isDirectory()) return listFiles(target);
    return [target];
  }));
  return nested.flat();
}

function count(source, expression) {
  return [...source.matchAll(expression)].length;
}

const routesSource = await readFile(routesPath, "utf8");
const imports = new Map(
  [...routesSource.matchAll(/const\s+(\w+)\s*=\s*lazy\(\(\)\s*=>\s*import\("@\/(.+?)"\)/g)]
    .map(([, symbol, file]) => [symbol, `frontend-v3/src/${file}.tsx`]),
);

const routeRows = [];
const routeExpression = /^\s*\{\s*path:\s*"([^"]+)".*?<LazyPage><(\w+)/gm;
for (const match of routesSource.matchAll(routeExpression)) {
  const [, path, component] = match;
  const file = imports.get(component);
  if (!file) {
    routeRows.push({ path, component, file: "—", api: "غير محدد", state: "غير محدد", actions: "غير محدد", note: "يتطلب مراجعة يدوية" });
    continue;
  }
  let source = "";
  try {
    source = await readFile(join(repoRoot, file), "utf8");
  } catch {
    routeRows.push({ path, component, file, api: "غير مقروء", state: "غير محدد", actions: "غير محدد", note: "تعذرت قراءة الملف" });
    continue;
  }
  const api = [...new Set([...source.matchAll(/\b([A-Za-z][A-Za-z0-9]*Api\.[A-Za-z][A-Za-z0-9]*)\b/g)].map((result) => result[1]))];
  const states = ["isLoading", "isError", "error", "EmptyState", "Loading", "Skeleton"].filter((term) => source.includes(term));
  const buttons = count(source, /<(?:Button|button)\b/g);
  const handlers = count(source, /\bonClick\s*=/g);
  const mutations = count(source, /\buseMutation\b/g);
  const note = api.length === 0 && buttons > 0
    ? "إجراءات مرئية بلا مرجع API محلي واضح"
    : api.length === 0
      ? "سطح قالب أو عرض ساكن محتمل"
      : handlers > mutations && buttons > 0
        ? "يتطلب تحققًا يدويًا من معالجات الإجراءات"
        : "يحتاج مواءمة مع عقد الخلفية";
  routeRows.push({
    path,
    component,
    file,
    api: api.join("، ") || "—",
    state: states.join("، ") || "—",
    actions: `أزرار: ${buttons}؛ onClick: ${handlers}؛ mutations: ${mutations}`,
    note,
  });
}

routeRows.sort((left, right) => left.path.localeCompare(right.path));
const lines = [
  "# كتالوج مسارات وإجراءات واجهة GULA v3",
  "",
  "> أُنشئ آليًا من مسارات الواجهة وملفات الصفحات. «مرجع API محلي» دليل فهرسة فقط؛ لا يثبت بمفرده أن مسار الخلفية منفذ أو أن التفويض الخادمي يتحقق منه.",
  "",
  `**عدد المسارات المفهرسة:** ${routeRows.length}`,
  "",
  "| المسار | المكوّن | الملف | مراجع API محلية | مؤشرات الحالة | الإجراءات المرئية | التصنيف الأولي |",
  "|---|---|---|---|---|---|---|",
  ...routeRows.map((row) => "| `" + row.path + "` | `" + row.component + "` | `" + row.file.replace("frontend-v3/src/", "") + "` | " + row.api + " | " + row.state + " | " + row.actions + " | " + row.note + " |"),
  "",
  "## حدود الكتالوج",
  "",
  "يسجل الكتالوج استدعاءات تحمل لاحقة `Api` ومعالجات وأزرارًا في ملف الصفحة نفسه. ولا يكشف الاستدعاءات المارة عبر مكوّنات فرعية أو hooks، لذلك تراجع الأسطح المصنفة عالية المخاطر يدويًا مقابل عقد الخلفية وسجل الصلاحيات قبل تغيير سلوك المستخدم.",
  "",
];

await writeFile(outputPath, lines.join("\n"), "utf8");
console.log(`كتالوج الواجهة مكتمل: ${routeRows.length} مسارًا → ${relative(process.cwd(), outputPath)}`);
