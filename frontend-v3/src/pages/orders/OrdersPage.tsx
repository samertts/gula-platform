import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ordersApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input } from "@/components/ui";
import { Search } from "lucide-react";
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
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["orders", search],
    queryFn: () => ordersApi.list({ search, limit: 50 }),
  });

  const columns: ColumnDef<LabOrder>[] = [
    { accessorKey: "order_id", header: t("order.orderId") },
    { accessorKey: "patient_name", header: t("order.patientName") },
    { accessorKey: "doctor_name", header: t("order.doctorName") },
    {
      accessorKey: "status",
      header: t("order.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "results_count",
      header: t("order.testsCount"),
      cell: ({ row }) => row.original.results_count ?? "-",
    },
    {
      accessorKey: "created_at",
      header: t("order.createdAt"),
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("order.title")}</h1>
        <p className="text-muted-foreground">{t("order.subtitle")}</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={t("order.search")}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="ps-9 w-80"
                />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}