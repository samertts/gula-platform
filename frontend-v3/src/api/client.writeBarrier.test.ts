import { describe, expect, it } from "vitest";
import {
  OperationalReadBlockedError,
  OperationalWriteBlockedError,
  assertFrontendReadIsAllowed,
  assertFrontendWriteIsAllowed,
} from "./client";

describe("حاجز الكتابات التشغيلية في frontend-v3", () => {
  it("يرفض كتابة مريض سريرية حتى لو احتوت طبقة endpoints على دالة قديمة", () => {
    expect(() => assertFrontendWriteIsAllowed("post", "/patients")).toThrow(OperationalWriteBlockedError);
  });

  it("يرفض تغييرات حالة الأجهزة والإشعارات والإدارة غير المتعاقد عليها", () => {
    for (const [method, url] of [
      ["post", "/edge/devices/device-1/quarantine"],
      ["post", "/notifications/send-status"],
      ["post", "/niam/governance/authorities"],
      ["put", "/test-results/42/verify"],
    ]) {
      expect(() => assertFrontendWriteIsAllowed(method, url)).toThrow(OperationalWriteBlockedError);
    }
  });

  it("يسمح فقط باستثناءات الهوية والتحقق الضيقة اللازمة لبدء جلسة أو فحص قرار قراءة", () => {
    expect(() => assertFrontendWriteIsAllowed("post", "/login")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/authz/check")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("get", "/patients")).not.toThrow();
  });

  it("يرفض قراءة REST غير مصنفة ويحصر الاستثناء في تهيئة الجلسة العامة", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/patients")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/r/public-token")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/session")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/setup/status")).not.toThrow();
  });
});
