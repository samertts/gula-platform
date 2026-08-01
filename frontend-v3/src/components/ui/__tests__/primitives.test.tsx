import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>pending</Badge>);
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("applies default variant classes", () => {
    render(<Badge>default</Badge>);
    expect(screen.getByText("default")).toHaveClass("bg-primary");
  });

  it("applies success variant classes", () => {
    render(<Badge variant="success">ok</Badge>);
    expect(screen.getByText("ok")).toHaveClass("bg-emerald-100");
  });

  it("applies destructive variant classes", () => {
    render(<Badge variant="destructive">bad</Badge>);
    expect(screen.getByText("bad")).toHaveClass("bg-destructive");
  });

  it("merges custom className", () => {
    render(<Badge className="custom-klass">x</Badge>);
    expect(screen.getByText("x")).toHaveClass("custom-klass");
  });

  it("applies warning variant classes", () => {
    render(<Badge variant="warning">warn</Badge>);
    expect(screen.getByText("warn")).toHaveClass("bg-amber-100");
  });
});

describe("Button", () => {
  it("renders a button with children", () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("applies default variant classes", () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-primary");
  });

  it("applies outline variant classes", () => {
    render(<Button variant="outline">Cancel</Button>);
    expect(screen.getByRole("button")).toHaveClass("border-input");
  });

  it("applies size sm classes", () => {
    render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-8");
  });

  it("applies icon size classes", () => {
    render(<Button size="icon" aria-label="icon">I</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-9 w-9");
  });

  it("is disabled while loading", () => {
    render(<Button loading>Busy</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("is disabled when disabled prop set", () => {
    render(<Button disabled>No</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("passes through onClick", () => {
    let clicked = 0;
    render(<Button onClick={() => clicked++}>Click</Button>);
    screen.getByRole("button").click();
    expect(clicked).toBe(1);
  });

  it("merges custom className", () => {
    render(<Button className="w-full">Wide</Button>);
    expect(screen.getByRole("button")).toHaveClass("w-full");
  });
});

describe("Card", () => {
  it("renders children inside a card container", () => {
    render(<Card><p>body</p></Card>);
    expect(screen.getByText("body")).toBeInTheDocument();
  });

  it("applies card classes", () => {
    render(<Card>c</Card>);
    expect(screen.getByText("c")).toHaveClass("rounded-xl", "border");
  });

  it("renders full composition", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>,
    );
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
    expect(screen.getByText("Footer")).toBeInTheDocument();
  });

  it("merges className on CardTitle", () => {
    render(<CardTitle className="text-2xl">T</CardTitle>);
    expect(screen.getByText("T")).toHaveClass("text-2xl");
  });
});
