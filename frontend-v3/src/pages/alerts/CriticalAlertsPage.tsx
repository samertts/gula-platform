import { useQuery } from "@tanstack/react-query";
import { criticalAlertsApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { CriticalAlert } from "@/types";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

export function CriticalAlertsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["critical-alerts"],
    queryFn: () => criticalAlertsApi.list({}),
  });

  const columns: ColumnDef<CriticalAlert>[] = [
    { accessorKey: "order_id", header: "رقم الطلب" },
    {
      accessorKey: "critical_tests",
      header: "الفحوصات الحرجة",
      cell: ({ row }) => (row.original.critical_tests || []).join(", "),
    },
    { accessorKey: "token_prefix", header: "رمز" },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const alerts = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="التنبيهات الحرجة"
        description="نتائج المختبر الحرجة التي تتطلب متابعة فورية"
        actions={
          alerts.length > 0 ? (
            <Badge variant="destructive" className="text-sm px-3 py-1">
              <AlertTriangle className="h-4 w-4 ms-1" />
              {alerts.length} تنبيه
            </Badge>
          ) : undefined
        }
      />
      <Card>
        <CardContent className="pt-6">
          {alerts.length === 0 ? (
            <EmptyState icon={CheckCircle2} title="لا توجد تنبيهات حرجة" description="جميع النتائج ضمن الحدود الطبيعية" />
          ) : (
            <DataTable columns={columns} data={alerts} loading={isLoading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
