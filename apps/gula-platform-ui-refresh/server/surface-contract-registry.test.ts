import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const registryPath = join(process.cwd(), "scripts/backend-contract-registry.json");
const matrixPath = join(process.cwd(), "ui_action_contract_matrix.md");

describe("سجل عقود الواجهة", () => {
  it("يوثق معرفًا ومسارًا وصلاحية وسياقًا لكل عقد مرجعي", async () => {
    const registry = JSON.parse(await readFile(registryPath, "utf8")) as {
      contracts: Array<{ id: string; method: string; path: string; permission: string; requiresWorkspaceContext: boolean; aliases: string[]; operationKinds: string[]; clientMethods: string[] }>;
    };

    expect(registry.contracts.length).toBeGreaterThanOrEqual(10);
    expect(new Set(registry.contracts.map((contract) => contract.id)).size).toBe(registry.contracts.length);
    for (const contract of registry.contracts) {
      expect(contract.id).toMatch(/^[a-z0-9.-]+$/);
      expect(contract.method).toMatch(/^(GET|POST)$/);
      expect(contract.path).toMatch(/^\//);
      expect(contract.permission.trim().length).toBeGreaterThan(0);
      expect(typeof contract.requiresWorkspaceContext).toBe("boolean");
      expect(contract.aliases.length).toBeGreaterThan(0);
      expect(contract.operationKinds.length).toBeGreaterThan(0);
      expect(contract.operationKinds.every((kind) => ["read", "write", "lookup", "check", "search", "execute"].includes(kind))).toBe(true);
      expect(contract.clientMethods.length).toBeGreaterThan(0);
    }
  });

  it("يوثق في المصفوفة سلسلة المعالج إلى عقد واحد أو قرار عدم التشغيل الصريح", async () => {
    const matrix = await readFile(matrixPath, "utf8");
    const rows = matrix.split("\n").filter((line) => line.startsWith("| `"));

    expect(matrix).toContain("مراجع API داخل المعالج");
    expect(matrix).toContain("معرف العقد الأساسي");
    expect(matrix).toContain("العقود التابعة الموثقة");
    expect(matrix).not.toContain("عقد مرجعي محتمل");
    for (const row of rows.filter((line) => line.includes("غير مطابق: استدعاء المعالج"))) {
      expect(row).toContain("يبقى غير تشغيلي حتى توثيق عقد واحد");
    }
    for (const row of rows.filter((line) => line.includes("مطابق: المعالج يستدعي"))) {
      expect(row).not.toContain("| `—` | `—` |");
    }
  });
});
