import { existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { hasPermission } from "./index";

describe("single frontend permission catalogue", () => {
  it("keeps the active catalogue as the only local role-permission table", () => {
    expect(hasPermission("citizen", "citizen:workspace")).toBe(true);
    expect(existsSync(join(process.cwd(), "src", "permissions", "rbac.ts"))).toBe(false);
  });
});
