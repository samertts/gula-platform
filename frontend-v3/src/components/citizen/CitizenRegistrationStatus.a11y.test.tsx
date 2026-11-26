import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
import {
  CitizenRegistrationStatus,
  SYNTHETIC_REGISTRATION_STATUS,
} from "./CitizenRegistrationStatus";

describe("Citizen registration status (synthetic RTL surface)", () => {
  it("renders an Arabic RTL status without claiming government verification", async () => {
    const { container } = render(
      <CitizenRegistrationStatus status={SYNTHETIC_REGISTRATION_STATUS} />,
    );

    const region = container.querySelector("section");
    expect(region).toHaveAttribute("dir", "rtl");
    expect(region).toHaveAttribute("lang", "ar");
    expect(
      screen.getByRole("heading", { name: "حالة طلب إنشاء الحساب" }),
    ).toBeInTheDocument();
    expect(screen.getByText("قيد المراجعة الحضورية")).toBeInTheDocument();
    expect(screen.getByText("مراجعة حضورية مطلوبة")).toBeInTheDocument();
    expect(
      screen.getByText(/بيانات تجريبية داخل بيئة معزولة/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/تم التحقق من الهوية الحكومية/)).not.toBeInTheDocument();

    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("keeps medical access explicitly disabled for an incomplete lifecycle", () => {
    render(<CitizenRegistrationStatus status={SYNTHETIC_REGISTRATION_STATUS} />);

    const medicalAccess = screen.getByText("الوصول للبيانات الطبية: غير مفعّل");
    expect(medicalAccess.closest("[role='status']")).not.toBeNull();
    const nextStep = screen.getByText(/الخطوة التالية: انتظار مراجعة مختصة/);
    expect(nextStep).toHaveAttribute("role", "status");
    expect(nextStep).toHaveAttribute("aria-live", "polite");
  });

  it("falls back to English LTR labels without inventing a translation", async () => {
    const { container } = render(
      <CitizenRegistrationStatus status={SYNTHETIC_REGISTRATION_STATUS} locale="en" />,
    );
    const region = container.querySelector("section");
    expect(region).toHaveAttribute("dir", "ltr");
    expect(region).toHaveAttribute("lang", "en");
    expect(screen.getByRole("heading", { name: "Account registration status" })).toBeInTheDocument();
    expect(screen.getByText("Pending in-person review")).toBeInTheDocument();
    expect(screen.getByText(/Synthetic data in an isolated environment/)).toBeInTheDocument();

    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("shows an unknown lifecycle token verbatim instead of a misleading label", () => {
    render(
      <CitizenRegistrationStatus
        status={{ ...SYNTHETIC_REGISTRATION_STATUS, lifecycle_state: "FUTURE_STATE_TOKEN" }}
        locale="en"
      />,
    );
    expect(screen.getByText("FUTURE_STATE_TOKEN")).toBeInTheDocument();
  });

  it("never presents a verified badge without official verification", () => {
    render(
      <CitizenRegistrationStatus
        status={{
          ...SYNTHETIC_REGISTRATION_STATUS,
          verification_state: "VERIFIED",
          official_verification: false,
        }}
      />,
    );
    expect(screen.queryByText(/موثّق/)).not.toBeInTheDocument();
    expect(screen.getByText(/التحقق الحكومي الرسمي: غير متاح/)).toBeInTheDocument();
    expect(screen.getByText("الوصول للبيانات الطبية: غير مفعّل")).toBeInTheDocument();
  });

  it("never renders a verified claim even if a caller asserts official verification", () => {
    render(
      <CitizenRegistrationStatus
        status={{
          ...SYNTHETIC_REGISTRATION_STATUS,
          verification_state: "VERIFIED",
          official_verification: true,
        }}
        locale="en"
      />,
    );
    expect(screen.queryByText(/Verification state: VERIFIED/)).not.toBeInTheDocument();
    expect(screen.getByText("Official government verification: unavailable")).toBeInTheDocument();
  });

  it("shows only allowlisted non-assertive official states", () => {
    render(
      <CitizenRegistrationStatus
        status={{
          ...SYNTHETIC_REGISTRATION_STATUS,
          verification_state: "PENDING_REVIEW",
          official_verification: true,
        }}
        locale="en"
      />,
    );
    expect(screen.getByText("Verification state: PENDING_REVIEW")).toBeInTheDocument();
  });
});
