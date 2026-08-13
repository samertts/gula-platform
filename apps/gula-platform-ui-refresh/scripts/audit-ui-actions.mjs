import { readFile, stat, writeFile } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");
const sourceRoot = join(repoRoot, "frontend-v3/src");
const routesPath = join(sourceRoot, "routes/index.tsx");
const registryPath = join(appRoot, "scripts/backend-contract-registry.json");
const outputPath = join(appRoot, "ui_action_contract_matrix.md");

function clean(value) {
  return value.replace(/<[^>]+>/g, " ").replace(/\{[^}]+\}/g, " ").replace(/\s+/g, " ").trim().slice(0, 90) || "عنصر دون نص ثابت";
}

function lineOf(source, offset) {
  return source.slice(0, offset).split("\n").length;
}

function markdown(value) {
  return String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function resolveImport(fromFile, importPath) {
  if (!importPath.startsWith("@/") && !importPath.startsWith(".")) return null;
  const base = importPath.startsWith("@/") ? join(sourceRoot, importPath.slice(2)) : resolve(dirname(fromFile), importPath);
  const candidates = [base, `${base}.tsx`, `${base}.ts`, join(base, "index.tsx"), join(base, "index.ts")];
  for (const candidate of candidates) {
    try {
      if ((await stat(candidate)).isFile()) return candidate.includes("/components/ui/") ? null : candidate;
    } catch {
      // تجربة امتداد بديل.
    }
  }
  return null;
}

async function componentTree(entry) {
  const files = new Map();
  async function visit(file) {
    if (files.has(file) || files.size > 80) return;
    const source = await readFile(file, "utf8");
    files.set(file, source);
    const imports = [...source.matchAll(/(?:from\s+|import\s*\()(["'])([^"']+)\1/g)].map((match) => match[2]);
    for (const importPath of imports) {
      const dependency = await resolveImport(file, importPath);
      if (dependency) await visit(dependency);
    }
  }
  await visit(entry);
  return files;
}

function attr(attrs, name) {
  return attrs.match(new RegExp(`(?:^|\\s)${name}\\s*=\\s*["']([^"']+)["']`))?.[1] ?? "";
}

function category(tag, label, handler, attrs) {
  const text = `${label} ${handler} ${attrs}`.toLowerCase();
  if (/بحث|filter|search|استعلام/.test(text)) return "بحث أو تصفية";
  if (/إضافة|إنشاء|حفظ|تعديل|حذف|add|create|save|delete|update/.test(text)) return "إضافة أو تعديل";
  if (/تصدير|تنزيل|طباعة|export|download|print/.test(text)) return "تصدير أو تنزيل";
  if (/كلمة المرور|موافقة|صلاحية|هوية|تسجيل الدخول|أمان|verify|auth|security/.test(text)) return "أمان أو وصول";
  if (["a", "Link"].includes(tag) || /navigate|setlocation/.test(text)) return "تنقل";
  if (["Input", "input", "Select", "select", "Textarea", "textarea"].includes(tag)) return "إدخال أو اختيار";
  if (tag === "form") return "إرسال نموذج";
  return "إجراء واجهة";
}

function isLocalUiHandler(handler) {
  return /^(?:\([^)]*\)|[A-Za-z_$][\w$]*)?\s*=>\s*(?:set[A-Z]|navigate|setLocation)|^(?:set[A-Z]|navigate|setLocation)/.test(handler);
}

function extractBraced(source, openingIndex) {
  if (source[openingIndex] !== "{") return null;
  let depth = 0;
  let quote = null;
  for (let index = openingIndex; index < source.length; index += 1) {
    const character = source[index];
    if (quote) {
      if (character === quote && source[index - 1] !== "\\") quote = null;
    } else if (character === "\"" || character === "'" || character === "`") {
      quote = character;
    } else if (character === "{") {
      depth += 1;
    } else if (character === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(openingIndex + 1, index);
    }
  }
  return null;
}

function eventHandler(attrs) {
  const match = /\bon(?:Click|Submit|Change)\s*=\s*\{/.exec(attrs);
  if (!match) return "—";
  return extractBraced(attrs, match.index + match[0].length - 1)?.trim() || "—";
}

function openingElements(source) {
  const tagPattern = /<(Button|button|form|Input|input|Select|select|Textarea|textarea|a|Link)\b/g;
  const elements = [];
  for (const match of source.matchAll(tagPattern)) {
    const index = match.index;
    let cursor = index + match[0].length;
    let quote = null;
    let braces = 0;
    for (; cursor < source.length; cursor += 1) {
      const character = source[cursor];
      if (quote) {
        if (character === quote && source[cursor - 1] !== "\\") quote = null;
      } else if (character === "\"" || character === "'" || character === "`") {
        quote = character;
      } else if (character === "{") {
        braces += 1;
      } else if (character === "}") {
        braces = Math.max(0, braces - 1);
      } else if (character === ">" && braces === 0) {
        elements.push({ tag: match[1], attrs: source.slice(index + match[0].length, cursor), index, end: cursor + 1 });
        break;
      }
    }
  }
  return elements;
}

function apiReferences(code) {
  return [...new Set([...code.matchAll(/\b([A-Za-z][A-Za-z0-9]*Api\.[A-Za-z][A-Za-z0-9]*)\s*\(/g)].map((match) => match[1]))];
}

function apiBindings(source) {
  const bindings = new Map();
  const directBinding = /\b(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*[^;\n]{0,240}?\b([A-Za-z][A-Za-z0-9]*Api\.[A-Za-z][A-Za-z0-9]*)\b/g;
  for (const match of source.matchAll(directBinding)) bindings.set(match[1], match[2]);
  return bindings;
}

function handlerSource(source, handler) {
  if (handler === "—") return { state: "بلا معالج", code: "" };
  if (isLocalUiHandler(handler)) return { state: "إجراء محلي", code: handler };
  if (handler.includes("=>")) return { state: "معالج مضمن", code: handler };
  const name = handler.match(/^[A-Za-z_$][\w$]*/)?.[0];
  if (!name) return { state: "تعذر تحليل المعالج", code: "" };
  const escapedName = escapeRegExp(name);
  const patterns = [
    new RegExp(`\\b(?:const|let)\\s+${escapedName}\\s*=\\s*(?:async\\s*)?(?:\\([^)]*\\)|[A-Za-z_$][\\w$]*)\\s*=>\\s*`, "m"),
    new RegExp(`\\bconst\\s+${escapedName}\\s*=\\s*useCallback\\(\\s*(?:async\\s*)?(?:\\([^)]*\\)|[A-Za-z_$][\\w$]*)\\s*=>\\s*`, "m"),
    new RegExp(`\\bfunction\\s+${escapedName}\\s*\\([^)]*\\)\\s*`, "m"),
  ];
  for (const pattern of patterns) {
    const match = pattern.exec(source);
    if (!match) continue;
    const start = match.index + match[0].length;
    if (source[start] === "{") return { state: "معالج مسمى", code: extractBraced(source, start) ?? "" };
    return { state: "معالج مسمى", code: source.slice(start, source.indexOf(";", start) > 0 ? source.indexOf(";", start) : start + 400) };
  }
  return { state: "معالج غير متتبع", code: "" };
}

function referencedOperations(source, code) {
  const references = new Set(apiReferences(code));
  const bindings = apiBindings(source);
  for (const match of code.matchAll(/\b([A-Za-z_$][\w$]*)\.(?:mutate(?:Async)?|refetch|query|execute)\b/g)) {
    const boundReference = bindings.get(match[1]);
    if (boundReference) references.add(boundReference);
  }
  return [...references];
}

function operationKind(apiReference) {
  const method = apiReference.split(".").at(-1)?.toLowerCase() ?? "";
  if (/(check|verif|validate)/.test(method)) return "check";
  if (/lookup/.test(method)) return "lookup";
  if (/search/.test(method)) return "search";
  if (/execute/.test(method)) return "execute";
  if (/(list|get|search|find|query|fetch|load|detail|metrics|status|download|export)/.test(method)) return "read";
  if (/(create|add|save|update|delete|remove|submit|send|message|register|login|logout)/.test(method)) return "write";
  return null;
}

function contractForReference(apiReference, registry) {
  const [apiClient, clientMethod] = apiReference.split(".");
  const kind = operationKind(apiReference);
  if (!kind) return null;
  const candidates = registry.contracts.filter((contract) => contract.aliases.includes(apiClient) && contract.operationKinds.includes(kind) && contract.clientMethods.includes(clientMethod));
  return candidates.length === 1 ? candidates[0] : null;
}

function traceAction(source, handler, registry) {
  const trace = handlerSource(source, handler);
  const references = referencedOperations(source, trace.code);
  const contracts = [...new Map(references.map((reference) => {
    const contract = contractForReference(reference, registry);
    return contract ? [contract.id, contract] : null;
  }).filter(Boolean)).values()];
  const unresolved = references.filter((reference) => !contractForReference(reference, registry));
  return { ...trace, references, contracts, unresolved };
}

function linkedContract(trace) {
  return trace.references.length > 0 && trace.unresolved.length === 0 && trace.contracts.length > 0 ? trace.contracts[0] : null;
}

function contractStatus(trace, contract) {
  if (contract && trace.contracts.length === 1) return "مطابق: المعالج يستدعي عقدًا مسجلًا واحدًا";
  if (contract) return "مطابق: المعالج يستدعي عقدًا أساسيًا وعقودًا تابعة مسجلة";
  if (trace.references.length > 0) return "غير مطابق: استدعاء المعالج لا يملك عقدًا واحدًا مسجلًا";
  if (trace.state === "إجراء محلي") return "محلي غير تشغيلي؛ لا يحتاج عقد مورد";
  if (trace.state === "بلا معالج") return "لا يوجد معالج محلي مباشر؛ لا يُفترض تنفيذ عقد من هذا العنصر";
  if (trace.state === "معالج غير متتبع" || trace.state === "تعذر تحليل المعالج") return "غير متتبع؛ يبقى الإجراء غير تشغيلي حتى توثيق المعالج";
  return "لا يستدعي المعالج موردًا؛ لا يحتاج عقد مورد";
}

function permissionValue(contract) {
  return contract?.permission ?? "—";
}

function workspaceValue(contract) {
  if (!contract) return "—";
  return contract.requiresWorkspaceContext ? "نعم" : "لا";
}

function actionDecision(trace, contract) {
  if (contract) return "ربط مرجعي محدد؛ لا يفعّل في النموذج قبل اختبار عقد الخادم والحالات";
  if (trace.references.length > 0) return "يبقى غير تشغيلي حتى توثيق عقد واحد للمعالج وصلاحيته وسياقه";
  if (trace.state === "معالج غير متتبع" || trace.state === "تعذر تحليل المعالج") return "يبقى غير تشغيلي حتى استكمال دليل تتبع المعالج";
  return "لا يوجد تنفيذ لمورد خلفي من هذا العنصر";
}

function summarize(rows, key) {
  return [...rows.reduce((map, row) => map.set(row[key], (map.get(row[key]) ?? 0) + 1), new Map()).entries()]
    .sort(([left], [right]) => left.localeCompare(right));
}

const routesSource = await readFile(routesPath, "utf8");
const registry = JSON.parse(await readFile(registryPath, "utf8"));
const imports = new Map(
  [...routesSource.matchAll(/const\s+(\w+)\s*=\s*lazy\(\(\)\s*=>\s*import\("@\/(.+?)"/g)]
    .map(([, symbol, file]) => [symbol, join(sourceRoot, `${file}.tsx`)]),
);
const routeExpression = /^\s*\{\s*path:\s*"([^"]+)".*?<LazyPage><(\w+)/gm;
const rows = [];

for (const routeMatch of routesSource.matchAll(routeExpression)) {
  const [, route, component] = routeMatch;
  const routeGuarded = routeMatch[0].includes("RoleGuard");
  const entry = imports.get(component);
  if (!entry) continue;
  let files;
  try {
    files = await componentTree(entry);
  } catch (error) {
    console.warn(`تعذر فهرسة ${route}: ${error instanceof Error ? error.message : String(error)}`);
    continue;
  }
  for (const [file, source] of files) {
    for (const element of openingElements(source)) {
      const { tag, attrs, index } = element;
      const handler = eventHandler(attrs);
      const content = source.slice(element.end, element.end + 240).split(`</${tag}>`)[0];
      const label = attr(attrs, "aria-label") || attr(attrs, "title") || attr(attrs, "placeholder") || attr(attrs, "name") || attr(attrs, "id") || (tag === "form" ? "نموذج إدخال" : clean(content));
      const trace = traceAction(source, handler, registry);
      const contract = linkedContract(trace);
      const localScope = source.slice(Math.max(0, index - 700), Math.min(source.length, index + 900));
      const protection = /hasPermission|permissions|requireRole|ProtectedRoute|useAuth|can[A-Z]/.test(localScope)
        ? "إشارة حماية محلية؛ لا تغني عن تفويض الخادم"
        : routeGuarded
          ? "حارس مسار ظاهر؛ لا يغني عن تفويض الخادم"
          : "لا توجد حراسة محلية مثبتة";
      rows.push({
        route,
        file,
        tag,
        label,
        handler,
        handlerState: trace.state,
        handlerTrace: trace.references.join("، ") || "—",
        category: category(tag, label, handler, attrs),
        contractStatus: contractStatus(trace, contract),
        contractId: contract?.id ?? "—",
        relatedContractIds: contract ? trace.contracts.slice(1).map((item) => item.id).join("، ") || "—" : "—",
        permission: permissionValue(contract),
        workspace: workspaceValue(contract),
        protection,
        decision: actionDecision(trace, contract),
        line: lineOf(source, index),
        unboundOperational: trace.references.length > 0 && !contract,
      });
    }
  }
}

rows.sort((left, right) => left.route.localeCompare(right.route) || left.file.localeCompare(right.file) || left.line - right.line);
const unboundOperational = rows.filter((row) => row.unboundOperational).length;
const linked = rows.filter((row) => row.contractId !== "—").length;
const lines = [
  "# مصفوفة إجراءات واجهة GULA v3 وعقودها",
  "",
  "> أُنشئت آليًا من الصفحات المحملة عبر خريطة المسارات ومن مكوّناتها المحلية المتداخلة. تتبع كل خانة مرتبطة الاستدعاء من معالج العنصر نفسه إلى عقد واحد في سجل الخلفية؛ ولا يعد أي صف جاهزًا لتشغيل طبي قبل اختبار عقد الخادم والصلاحية والسياق والحالات.",
  "",
  `- **العناصر المرئية المفهرسة:** ${rows.length}`,
  `- **إجراءات ذات عقد محدد من المعالج:** ${linked}`,
  `- **إجراءات تشغيلية بلا مطابقة معالج→عقد:** ${unboundOperational}`,
  `- **عقود الخلفية المرجعية المسجلة:** ${registry.contracts.length}`,
  "",
  "## ملخص التغطية حسب الفئة",
  "",
  "| الفئة | العدد |",
  "|---|---:|",
  ...summarize(rows, "category").map(([name, count]) => `| ${markdown(name)} | ${count} |`),
  "",
  "## ملخص التغطية حسب الصلاحية الخلفية المرجعية",
  "",
  "| الصلاحية الخلفية المرجعية | العدد |",
  "|---|---:|",
  ...summarize(rows, "permission").map(([name, count]) => `| ${markdown(name)} | ${count} |`),
  "",
  "## ملخص التغطية حسب حماية الواجهة",
  "",
  "| حماية الواجهة | العدد |",
  "|---|---:|",
  ...summarize(rows, "protection").map(([name, count]) => `| ${markdown(name)} | ${count} |`),
  "",
  "| المسار | الملف والموقع | العنصر | النص أو الوصف | المعالج | حالة تتبع المعالج | مراجع API داخل المعالج | الفئة | حالة العقد | معرف العقد الأساسي | العقود التابعة الموثقة | صلاحية الخلفية | يتطلب سياق منشأة | حماية الواجهة | قرار العرض |",
  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
  ...rows.map((row) => `| \`${markdown(row.route)}\` | \`${markdown(relative(sourceRoot, row.file))}:${row.line}\` | ${markdown(row.tag)} | ${markdown(row.label)} | \`${markdown(row.handler)}\` | ${markdown(row.handlerState)} | \`${markdown(row.handlerTrace)}\` | ${markdown(row.category)} | ${markdown(row.contractStatus)} | \`${markdown(row.contractId)}\` | \`${markdown(row.relatedContractIds)}\` | ${markdown(row.permission)} | ${markdown(row.workspace)} | ${markdown(row.protection)} | ${markdown(row.decision)} |`),
  "",
  "## قواعد التفسير",
  "",
  "1. تتضمن الفهرسة المكونات المحلية المستوردة من كل صفحة، وليس ملف الصفحة وحده. ولا تدخل مكتبات الواجهة الخارجية في عدّ الإجراءات الخاصة بالمنتج.",
  "2. لا يُستنتج العقد من اسم API موجود في الملف: يقرأ المولد جسم معالج العنصر أو المعالج المضمن ثم يطابق استدعاءه مع اسم عميل مسجل ونوع عملية مسجل.",
  "3. يحدد كل صف مطابق عقدًا أساسيًا واحدًا. ويعرض حقل «العقود التابعة الموثقة» أي استدعاءات متسلسلة يطلقها المعالج نفسه، فلا تختفي من الدليل ولا تُعامل كصالحيات ضمنية. يبقى أي استدعاء غير مسجل غير تشغيلي.",
  "4. حقلا «معرف العقد الأساسي» و«صلاحية الخلفية» يستندان مباشرة إلى سجل العقود، بينما يبين حقل «يتطلب سياق منشأة» القيمة المناظرة لـ `requiresWorkspaceContext`.",
  "5. لا تكفي حماية الواجهة أو حارس المسار لتفعيل الإجراء؛ يظل تفويض الخادم وسياق المنشأة مصدر القرار النهائي.",
  "",
];

await writeFile(outputPath, lines.join("\n"), "utf8");
console.log(`مصفوفة الإجراءات مكتملة: ${rows.length} عنصرًا عبر المكونات المتداخلة → ${relative(process.cwd(), outputPath)}`);
