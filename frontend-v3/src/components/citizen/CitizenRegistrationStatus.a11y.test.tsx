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
});
