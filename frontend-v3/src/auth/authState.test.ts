import { describe, expect, it } from "vitest";
import { AUTH_STATES, stateForAuthorizedContext } from "./authState";
import type { UserInfo } from "@/types";
import type { WorkspaceSummary } from "@/api/client";

const user: UserInfo = { id: 1, name: "User", email: "user@example.test", role: "citizen", lab_id: null, lab_name: null };
const workspace: WorkspaceSummary = { id: "w-1", uuid: "w-1", workspace_type: "citizen", name: "Citizen", status: "active", organization_id: null, facility_id: null, department_id: null, professional_type: null, is_personal: true };

describe("AuthState model", () => {
  it("requires explicit context when multiple workspaces exist", () => {
    expect(stateForAuthorizedContext(user, [workspace, { ...workspace, id: "w-2", uuid: "w-2" }], null)).toBe(AUTH_STATES.WORKSPACE_REQUIRED);
  });
  it("allows server-approved single workspace after context establishment", () => {
    expect(stateForAuthorizedContext(user, [workspace], workspace)).toBe(AUTH_STATES.AUTHORIZED);
  });
  it("keeps a signed-in user authenticated when no workspace exists", () => {
    expect(stateForAuthorizedContext(user, [], null)).toBe(AUTH_STATES.AUTHENTICATED);
  });
});
