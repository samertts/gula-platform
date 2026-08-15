import { readdir, stat } from "node:fs/promises";
import { basename, join, resolve } from "node:path";

const distDir = resolve(process.argv[2] || "dist");
const budgets = {
  totalBytes: 2_500_000,
  entryJsBytes: 400_000,
  cssBytes: 180_000,
};

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await collectFiles(path)));
    else files.push(path);
  }
  return files;
}

function kib(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`;
}

const files = await collectFiles(distDir);
const sizes = await Promise.all(files.map(async (path) => ({ path, bytes: (await stat(path)).size })));
const assetSizes = sizes.filter(({ path }) => path.includes(`${join("dist", "assets")}`) || path.includes(`${join("dist", "assets")}`.replaceAll("\\", "/")));
const totalBytes = sizes.reduce((sum, item) => sum + item.bytes, 0);
const entry = assetSizes.find(({ path }) => /^index-[^/]+\.js$/.test(basename(path)));
const cssBytes = assetSizes.filter(({ path }) => path.endsWith(".css")).reduce((sum, item) => sum + item.bytes, 0);

const violations = [];
if (totalBytes > budgets.totalBytes) violations.push(`total dist ${kib(totalBytes)} > ${kib(budgets.totalBytes)}`);
if (!entry) violations.push("could not identify the hashed index entry JavaScript asset");
else if (entry.bytes > budgets.entryJsBytes) violations.push(`index entry ${kib(entry.bytes)} > ${kib(budgets.entryJsBytes)}`);
if (cssBytes > budgets.cssBytes) violations.push(`CSS assets ${kib(cssBytes)} > ${kib(budgets.cssBytes)}`);

console.log(JSON.stringify({
  distDir,
  budgets,
  measured: {
    fileCount: sizes.length,
    totalBytes,
    total: kib(totalBytes),
    entryJs: entry ? { file: basename(entry.path), bytes: entry.bytes, size: kib(entry.bytes) } : null,
    css: { bytes: cssBytes, size: kib(cssBytes) },
  },
  violations,
}, null, 2));

if (violations.length > 0) process.exit(1);
