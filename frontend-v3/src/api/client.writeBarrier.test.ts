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
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/auth/login")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/auth/refresh")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/auth/logout")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/auth/logout-all")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("get", "/patients")).not.toThrow();
  });

  it("يسمح بعقود device-integration المحاكية فقط ويرفض مسارًا غير مصنف", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/summary")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/devices/VITAL-001?limit=20")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/connectors?limit=20")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/protocol-profiles")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/simulators")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/monitoring")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/device-integration/monitoring/alerts?status=open")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/devices/VITAL-001/probe")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/devices")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/connectors")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/connectors/CONN-HL7-001/status")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/connectors/CONN-HL7-001/simulate")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/protocol-profiles")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/monitoring/metrics")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/monitoring/alerts/42/acknowledge")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/device-integration/devices/VITAL-001/raw-command")).toThrow(OperationalWriteBlockedError);
  });

  it("يسمح فقط بمسارات account-request المصنفة ويمنع المسارات غير المحددة", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/niam/account-requests/")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/account-requests/request-1/review")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/account-requests/request-1/verification/start")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/account-requests/accounts/account-1/suspend")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/account-requests/request-1/internal-bypass")).toThrow(OperationalWriteBlockedError);
  });

  it("يرفض قراءة REST غير مصنفة ويحصر الاستثناء في تهيئة الجلسة العامة", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/patients")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/r/public-token")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/session")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/setup/status")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/niam/sessions/account/account-1")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/sessions/session-1/terminate")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/sessions/account/account-1/terminate-all")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/sessions/account/account-1/delete-all")).toThrow(OperationalWriteBlockedError);
  });
});
