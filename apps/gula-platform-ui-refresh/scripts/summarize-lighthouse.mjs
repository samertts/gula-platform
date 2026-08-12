import { readFile, writeFile } from "node:fs/promises";

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  throw new Error("Usage: node scripts/summarize-lighthouse.mjs <input.json> <output.md>");
}

const report = JSON.parse(await readFile(inputPath, "utf8"));
const score = report.categories?.accessibility?.score;
const audits = Object.values(report.audits ?? {});
const failed = audits.filter((audit) => audit.scoreDisplayMode === "binary" && audit.score === 0);
const manual = audits.filter((audit) => audit.scoreDisplayMode === "manual");

const lines = [
  "# تدقيق إمكانية الوصول",
  "",
  `- **المصدر:** \`${report.finalUrl ?? report.requestedUrl ?? "غير معروف"}\``,
  `- **النتيجة الآلية (Lighthouse):** ${typeof score === "number" ? Math.round(score * 100) : "غير متاحة"}/100`,
  `- **مخالفات آلية فاشلة:** ${failed.length}`,
  `- **فحوص تتطلب مراجعة يدوية:** ${manual.length}`,
  "",
  "## المخالفات الآلية",
  "",
];

if (failed.length === 0) {
  lines.push("لا توجد مخالفات ثنائية فاشلة ضمن فئة الوصول التي فحصها التقرير.");
} else {
  for (const audit of failed) {
    lines.push(`### ${audit.title ?? audit.id}`, "", audit.description ?? "لا يوجد وصف.", "");
    const nodes = audit.details?.items ?? [];
    if (nodes.length > 0) {
      lines.push("| العنصر | الملخص |", "|---|---|");
      for (const node of nodes.slice(0, 10)) {
        lines.push(`| \`${String(node.node?.selector ?? "غير محدد").replaceAll("|", "\\|")}\` | ${String(node.node?.explanation ?? "").replaceAll("|", "\\|")} |`);
      }
      lines.push("");
    }
  }
}

lines.push("## عناصر المراجعة اليدوية", "", "تتطلب قابلية استخدام لوحة المفاتيح، ترتيب التركيز، وضوح التركيز، جودة النصوص البديلة، وفهم الرسائل العربية مراجعة تشغيلية بالإضافة إلى التدقيق الآلي.", "");
await writeFile(outputPath, lines.join("\n"), "utf8");
