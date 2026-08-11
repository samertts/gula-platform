import { describe, expect, it } from "vitest";
import { assignUserRole, createLaboratory, getAdminDirectory } from "./admin-service";

const laboratoryActor = {
  id: 99,
  role: "lab_staff",
  institutionId: 7,
  laboratoryId: 2,
};

describe("administrative service authorization", () => {
  it("rejects a non-administrator before any directory query is attempted", async () => {
    await expect(getAdminDirectory(laboratoryActor)).rejects.toMatchObject({ code: "FORBIDDEN" });
  });

  it("rejects role assignment and laboratory creation by non-administrators", async () => {
    await expect(assignUserRole(laboratoryActor, { userId: 15, role: "physician" })).rejects.toMatchObject({ code: "FORBIDDEN" });
    await expect(createLaboratory(laboratoryActor, { code: "LAB-01", nameAr: "مختبر", nameEn: "Laboratory" })).rejects.toMatchObject({ code: "FORBIDDEN" });
  });
});
