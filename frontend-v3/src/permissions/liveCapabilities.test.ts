import { describe, expect, it } from "vitest";
import { hasReflectedPermission } from "./liveCapabilities";

describe("live reflected capabilities", () => {
  it("denies when the server reflection is empty", () => {
    expect(hasReflectedPermission({}, ["patients:read"])).toBe(false);
  });

  it("allows a capability reflected for any organization context", () => {
    expect(
      hasReflectedPermission(
        {
          organizationA: ["patients:read"],
          organizationB: ["reports:read"],
        },
        ["patients:read"],
      ),
    ).toBe(true);
  });

  it("does not treat a missing capability as an allow", () => {
    expect(hasReflectedPermission({ organizationA: ["reports:read"] }, ["patients:read"])).toBe(false);
  });

  it("keeps an empty requirement list neutral", () => {
    expect(hasReflectedPermission({}, [])).toBe(true);
  });
});
