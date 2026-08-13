import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, Badge, DataTable, Input } from "@/components/ui";
import { EmptyState } from "@/components/ui/EmptyState";
import { WorkspaceReadBlockedError, workspaceScopedReads } from "@/api/workspaceScopedReads";
import { Search, ShieldAlert } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabOrder } from "@/types";
import { formatDate } from "@/lib/utils";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  pending: "warning",
  completed: "success",
  validated: "default",
  cancelled: "destructive",
  in_progress: "secondary",
};

export function OrdersPage() {
  const [search, setSearch] = useState("");
  const query = useQuery({
    queryKey: ["orders", "orders.read", search],
    queryFn: () => workspaceScopedReads.listOrders({ search, limit: 50 }),
    retry: false,
  });
  const blockedMessage = query.error instanceof WorkspaceReadBlockedError ? query.error.message : null;

  const columns: ColumnDef<LabOrder>[] = [
    { accessorKey: "order_id", header: "رقم الطلب" },
    { accessorKey: "patient_name", header: "اسم المريض" },
    { accessorKey: "doctor_name", header: "اسم الطبيب" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "results_count",
      header: "عدد الفحوصات",
      cell: ({ row }) => row.original.results_count ?? "-",
    },
    {
      accessorKey: "created_at",
      header: "تاريخ الإنشاء",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  return (
    <div
      className="space-y-6"
      data-contract-id="orders.read"
      data-permission="orders:read"
      data-workspace-context="required"
    >
      <div>
        <h1 className="text-2xl font-bold">الطلبات</h1>
        <p className="text-muted-foreground">إدارة طلبات الفحوصات المخبرية</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          {blockedMessage ? (
            <EmptyState
              icon={ShieldAlert}
              title="قراءة الطلبات غير متاحة لهذه الجلسة"
              description={blockedMessage}
            />
          ) : <DataTable
            columns={columns}
            data={query.data ?? []}
            loading={query.isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="بحث عن طلب..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="ps-9 w-80"
                />
              </div>
            }
          />}
        </CardContent>
      </Card>
    </div>
  );
}
