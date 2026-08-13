import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDir, "../..");
const sourceRoot = "/home/ubuntu/gula-platform/backend/app";
const outputPath = path.join(repositoryRoot, "docs/contract-audit/generated/route-snapshots.json");
const markdownOutputPath = path.join(repositoryRoot, "docs/contract-audit/generated/ROUTE_CONTRACT_CATALOG.md");

const domains = [
  { domain: "radiology", file: "radiology/routes.py", prefix: "/radiology", testEvidence: "backend/tests/test_radiology_tenant_isolation.py — رفض المورد عند اختلاف المختبر" },
  { domain: "nursing", file: "nursing/routes.py", prefix: "/nursing", testEvidence: "غير موجود: لم يعثر الجرد النصي على اختبار رفض/عزل موجّه للتمريض" },
  { domain: "physician-care-continuum", file: "routes/care_continuum.py", prefix: "/care-continuum", testEvidence: "غير موجود: لم يعثر الجرد النصي على اختبار رفض/عزل موجّه للرعاية المستمرة" },
  { domain: "ehr", file: "routes/ehr.py", prefix: "/ehr", testEvidence: "غير موجود: لم يعثر الجرد النصي على اختبار رفض/عزل موجّه لمسارات EHR" },
  { domain: "clinical-orders", file: "routes/clinical_orders.py", prefix: "/clinical/orders", testEvidence: "غير موجود: لا يثبت مخزن الذاكرة عقد عزل قابلًا للاعتماد" },
  { domain: "clinical-documentation", file: "routes/clinical_documentation.py", prefix: "/clinical/documentation", testEvidence: "غير موجود: لا يثبت مخزن الذاكرة عقد عزل قابلًا للاعتماد" },
  { domain: "platform", file: "platform/routes.py", prefix: "/platform", testEvidence: "غير مطلوب للبيانات السريرية: الموجه وصفي عام فقط" },
];

function parseModels(source) {
  const models = {};
  const matcher = /^class\s+(\w+)\(BaseModel\):\n([\s\S]*?)(?=^class\s+|^#\s*={5,}|\Z)/gm;
  for (const match of source.matchAll(matcher)) {
    const [, name, body] = match;
    const fields = [];
    for (const field of body.matchAll(/^ {4}(\w+):\s*([^\n=]+?)(?:\s*=\s*([^\n]+))?$/gm)) {
      fields.push({ name: field[1], type: field[2].trim(), default: field[3]?.trim() ?? null });
    }
    models[name] = fields;
  }
  return models;
}

function inferResponse(functionBody) {
  if (/return\s+_paginated_response\(/.test(functionBody)) return "كائن ترقيم صفحات من _paginated_response";
  if (/return\s+\{\s*["']items["']/.test(functionBody)) return "كائن JSON يتضمن items وtotal (وقد يتضمن skip وlimit)";
  if (/return\s+_to_dict\(/.test(functionBody) || /return\s+_model_to_dict\(/.test(functionBody)) return "قاموس تسلسلي ديناميكي من نموذج/ORM";
  if (/return\s+svc\./.test(functionBody) || /return\s+\w+Service\./.test(functionBody)) return "نتيجة خدمة ديناميكية؛ لا يعلن الموجه نموذج استجابة";
  if (/return\s+\{/.test(functionBody)) return "كائن JSON مضمّن في التنفيذ";
  return "غير معلن في الموجه؛ يتطلب تتبع الخدمة";
}

function parseRoutes(source, domain) {
  const endpoints = [];
  const decoratorMatcher = /^@router\.(get|post|put|patch|delete)\(\s*["']([^"']*)["']/gm;
  for (const decorator of source.matchAll(decoratorMatcher)) {
    const [, method, routePath] = decorator;
    const handlerSearchStart = decorator.index + decorator[0].length;
    const functionMatcher = /^(?:async\s+)?def\s+(\w+)\(([\s\S]*?)\)\s*(?:->\s*[^:]+)?:/m;
    const functionMatch = functionMatcher.exec(source.slice(handlerSearchStart));
    if (!functionMatch) continue;
    const [, handler, signature] = functionMatch;
    const functionStart = handlerSearchStart + functionMatch.index;
    const functionBodyStart = functionStart + functionMatch[0].length;
    const nextDecorator = source.slice(functionBodyStart).search(/^@router\.(get|post|put|patch|delete)\(/m);
    const functionBody = source.slice(functionBodyStart, nextDecorator === -1 ? undefined : functionBodyStart + nextDecorator);
    const routeDeclaration = source.slice(decorator.index, functionStart);
    const inputMatch = signature.match(/^\s*(?:data|body|payload|request):\s*(\w+)/m);
    const tenantContextEvidence = /current_user\.lab_id|_lab_id\(/.test(functionBody)
      ? "مباشر في دالة الموجه"
      : /\bcurrent_user\b/.test(functionBody)
        ? "يمرر المستخدم إلى مساعد/خدمة؛ يلزم تتبع إضافي"
        : "لا يظهر في دالة الموجه";
    endpoints.push({
      method: method.toUpperCase(),
      path: `${domain.prefix}${routePath}`.replace(/\/\/+/, "/"),
      handler,
      inputModel: inputMatch?.[1] ?? null,
      inputLocation: inputMatch ? "جسم الطلب" : "استعلام/مسار/لا يوجد جسم طلب معلن",
      responseShape: inferResponse(functionBody),
      requiresCurrentUser: /Depends\(get_current_user\)/.test(signature) || /Depends\(get_current_user\)/.test(routeDeclaration),
      tenantContextEvidence,
      tenantReference: tenantContextEvidence !== "لا يظهر في دالة الموجه",
      explicitPermissionGuard: /require_permission\(|require_role\(/.test(routeDeclaration) || /require_permission\(|require_role\(/.test(functionBody),
    });
  }
  return endpoints;
}

const snapshotDomains = domains.map((domain) => {
  const filename = path.join(sourceRoot, domain.file);
  const source = fs.readFileSync(filename, "utf8");
  const endpoints = parseRoutes(source, domain).map((endpoint) => {
    const exposure = exposureStatus(domain, endpoint);
    const hasExplicitAuthorization = endpoint.requiresCurrentUser && endpoint.explicitPermissionGuard;
    const hasDirectTenancyEvidence = endpoint.tenantContextEvidence === "مباشر في دالة الموجه";
    const hasIsolationTest = !domain.testEvidence.startsWith("غير موجود") && !domain.testEvidence.startsWith("غير مطلوب") && !domain.testEvidence.includes("لا يثبت");
    return {
      ...endpoint,
      authorizationStatus: hasExplicitAuthorization ? "دليل ثابت ظاهر؛ لا يعد تحققًا تشغيليًا" : "محجوب: لا يظهر حارس هوية وصلاحية دقيقان معًا",
      tenancyStatus: hasDirectTenancyEvidence ? "دليل ثابت مباشر؛ لا يعد تحققًا تشغيليًا" : "محجوب: لا يظهر عزل منشأة مباشر في دالة الموجه",
      negativeVerification: hasIsolationTest
        ? `دليل اختبار مُكتشف: ${domain.testEvidence}؛ لم يعتمد التنفيذ التشغيلي في هذه البيئة.`
        : `محجوب: ${domain.testEvidence}`,
      functionalEligibility: exposure.includes("مرشح") ? "مرشح لتدقيق يدوي لاحق؛ غير معتمد وظيفيًا" : "ممنوع من الربط الوظيفي",
    };
  });
  return {
    domain: domain.domain,
    source: `backend/app/${domain.file}`,
    testEvidence: domain.testEvidence,
    inputModels: parseModels(source),
    endpoints,
  };
});

const snapshot = {
  generatedAt: new Date().toISOString(),
  generator: "scripts/contract-audit/extract-route-snapshots.mjs",
  limitations: [
    "استخراج ثابت من ملفات الراوتر؛ لا يثبت تسجيل المسار في مصنع التطبيق أو سلوك الخدمة النهائي.",
    "شكل الاستجابة مستنتج من دالة الراوتر ولا يمثل مخطط OpenAPI معتمدًا.",
    "عدم وجود explicitPermissionGuard في اللقطة لا ينفي تفويضًا منفذًا في طبقة أدنى، لكنه لا يكفي لاعتماد واجهة تشغيلية.",
  ],
  domains: snapshotDomains,
};

for (const domain of snapshotDomains) {
  const source = fs.readFileSync(path.join(sourceRoot, domains.find((candidate) => candidate.domain === domain.domain).file), "utf8");
  const declaredRoutes = (source.match(/^@router\.(get|post|put|patch|delete)\(/gm) ?? []).length;
  if (domain.endpoints.length !== declaredRoutes) {
    throw new Error(`Route extraction mismatch for ${domain.domain}: extracted ${domain.endpoints.length}, declared ${declaredRoutes}`);
  }
}

function escapeCell(value) {
  return String(value).replaceAll("|", "\\|").replaceAll("\n", "<br>");
}

function exposureStatus(domain, endpoint) {
  if (domain.domain === "platform") return "وصفي عام فقط؛ لا يحمل تدفقًا سريريًا";
  if (["clinical-orders", "clinical-documentation"].includes(domain.domain)) return "ممنوع: مخزن ذاكرة/نطاق غير مثبت";
  if (domain.domain === "ehr") return "ممنوع: تسجيل الموجه غير مثبت وصلاحية دقيقة غير موثقة";
  if (!endpoint.explicitPermissionGuard) return "ممنوع: لا يوجد حارس صلاحية دقيق ظاهر في الموجه";
  if (!endpoint.tenantReference) return "ممنوع: لا يظهر مرجع سياق منشأة في دالة الموجه";
  return "مرشح للتدقيق اليدوي؛ ليس موافقة تشغيلية";
}

const markdown = [
  "# كتالوج المسارات المستخرج آليًا",
  "",
  "**مولّد آليًا من:** `scripts/contract-audit/extract-route-snapshots.mjs`. يُعاد توليده بالأمر `node scripts/contract-audit/extract-route-snapshots.mjs` ولا يغيّر قرار الحوكمة وحده.",
  "",
  "> يعرض هذا الملف شكلًا مستنتجًا من دوال الموجه، لا مخطط OpenAPI معتمدًا. وتظل حالة التعرض **ممنوعة** ما لم تثبت مرحلة التفويض والعزل عقدًا محددًا.",
  "",
];

for (const domain of snapshotDomains) {
  markdown.push(`## ${domain.domain}`, "", `المصدر: \`${domain.source}\`.`, "");
  markdown.push("| الطريقة | المسار | المعالج | المصدر | نموذج الإدخال/موضعه | شكل الاستجابة المستنتج | حالة التفويض | حالة العزل | نتيجة الرفض/الاختبار | أهلية الربط |", "|---|---|---|---|---|---|---|---|---|---|");
  for (const endpoint of domain.endpoints) {
    const input = endpoint.inputModel ? `${endpoint.inputModel} — جسم الطلب` : endpoint.inputLocation;
    const sourceLink = `[${domain.source}](../../../${domain.source})`;
    markdown.push(`| ${endpoint.method} | \`${endpoint.path}\` | \`${endpoint.handler}\` | ${sourceLink} | ${escapeCell(input)} | ${escapeCell(endpoint.responseShape)} | ${escapeCell(endpoint.authorizationStatus)} | ${escapeCell(endpoint.tenancyStatus)} | ${escapeCell(endpoint.negativeVerification)} | ${escapeCell(endpoint.functionalEligibility)} |`);
  }
  const usedModels = [...new Set(domain.endpoints.map((endpoint) => endpoint.inputModel).filter(Boolean))];
  if (usedModels.length) {
    markdown.push("", "### نماذج الإدخال المستخدمة", "", "| النموذج | الحقول المستخرجة |", "|---|---|");
    for (const modelName of usedModels) {
      const fields = domain.inputModels[modelName] ?? [];
      const summary = fields.length ? fields.map((field) => `\`${field.name}\`: ${field.type}${field.default ? ` = ${field.default}` : ""}`).join("<br>") : "لم يستخرج النموذج من هذا الملف";
      markdown.push(`| \`${modelName}\` | ${escapeCell(summary)} |`);
    }
  }
  markdown.push("");
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(snapshot, null, 2)}\n`);
fs.writeFileSync(markdownOutputPath, `${markdown.join("\n")}\n`);
console.log(`Generated ${outputPath} and ${markdownOutputPath} with ${snapshotDomains.reduce((sum, domain) => sum + domain.endpoints.length, 0)} routes.`);
