import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable } from "@/components/ui/DataTable";
import type { ColumnDef } from "@tanstack/react-table";

interface Row {
  id: number;
  name: string;
}

const columns: ColumnDef<Row>[] = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "name", header: "Name" },
];

const rows: Row[] = [
  { id: 1, name: "Ali" },
  { id: 2, name: "Sana" },
  { id: 3, name: "Omar" },
];

describe("DataTable", () => {
  it("renders header and rows", () => {
    render(<DataTable columns={columns} data={rows} />);
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Ali")).toBeInTheDocument();
    expect(screen.getByText("Sana")).toBeInTheDocument();
  });

  it("renders toolbar", () => {
    render(<DataTable columns={columns} data={rows} toolbar={<button>Action</button>} />);
    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(<DataTable columns={columns} data={[]} loading />);
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument();
  });

  it("shows error state with retry", () => {
    const onRetry = vi.fn();
    render(<DataTable columns={columns} data={[]} error={new Error("boom")} onRetry={onRetry} />);
    expect(screen.getByText("تعذر تحميل البيانات")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("shows empty state", () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText("لا توجد بيانات")).toBeInTheDocument();
  });

  it("sorts by clicking a sortable column header", () => {
    render(<DataTable columns={columns} data={rows} />);
    const nameHeader = screen.getByText("Name");
    fireEvent.click(nameHeader);
    const firstDataRow = screen.getAllByRole("row")[1];
    expect(firstDataRow).toHaveTextContent("Ali");
    fireEvent.click(nameHeader);
    const firstDataRowDesc = screen.getAllByRole("row")[1];
    expect(firstDataRowDesc).toHaveTextContent("Sana");
  });

  it("calls onRowClick when a row is clicked", () => {
    const onRowClick = vi.fn();
    render(<DataTable columns={columns} data={rows} onRowClick={onRowClick} />);
    fireEvent.click(screen.getByText("Sana"));
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it("paginates beyond pageSize", () => {
    const manyRows: Row[] = Array.from({ length: 25 }, (_, i) => ({ id: i, name: `R${i}` }));
    render(<DataTable columns={columns} data={manyRows} />);
    expect(screen.getByText("R0")).toBeInTheDocument();
    expect(screen.queryByText("R15")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "التالي" }));
    expect(screen.getByText("R15")).toBeInTheDocument();
  });
});
