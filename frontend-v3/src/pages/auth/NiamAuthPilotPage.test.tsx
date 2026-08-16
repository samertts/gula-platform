import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NiamAuthPilotPage } from "./NiamAuthPilotPage";

describe("NiamAuthPilotPage", () => {
  it("stays disabled unless the explicit staging feature flag is enabled", () => {
    render(<NiamAuthPilotPage />);
    expect(screen.getByRole("heading", { name: "بوابة NIAM التجريبية غير مفعّلة" })).toBeInTheDocument();
    expect(screen.getByText(/لا تغيّر مصادقة المنصة الأساسية/)).toBeInTheDocument();
  });
});
