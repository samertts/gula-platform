import { describe, expect, it } from "vitest";
import {
  OperationalReadBlockedError,
  OperationalWriteBlockedError,
  assertFrontendReadIsAllowed,
  assertFrontendWriteIsAllowed,
} from "./client";

describe("workspace API contract gates", () => {
  it("allows backend workspace discovery and detail reads", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/niam/workspaces")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/niam/workspaces/abc")).not.toThrow();
  });

  it("allows only server-authoritative workspace switching", () => {
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/workspaces/abc/switch")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("patch", "/niam/workspaces/abc")).toThrow(OperationalWriteBlockedError);
    expect(() => assertFrontendWriteIsAllowed("delete", "/niam/workspaces/abc")).toThrow(OperationalWriteBlockedError);
  });

  it("allows membership discovery and approved lifecycle mutations", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/niam/memberships/me")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/applications")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/applications/app-1/approve")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/invitations")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/invitations/inv-1/accept")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/member-1/suspend")).not.toThrow();
  });

  it("blocks client-side membership status or direct role-like mutations", () => {
    expect(() => assertFrontendWriteIsAllowed("patch", "/niam/memberships/member-1")).toThrow(OperationalWriteBlockedError);
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/memberships/member-1/status")).toThrow(OperationalWriteBlockedError);
    expect(() => assertFrontendWriteIsAllowed("delete", "/niam/memberships/member-1")).toThrow(OperationalWriteBlockedError);
  });

  it("continues to block direct clinical reads", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/patients")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/lims/orders")).toThrow(OperationalReadBlockedError);
  });
});
