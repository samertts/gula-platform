import { useQuery } from "@tanstack/react-query";
import { qcApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { QualityControl } from "@/types";
import { ShieldCheck, FlaskConical } from "lucide-react";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  passed: "success",
  failed: "destructive",
  warning: "warning",
  pending: "secondary",
};

export function QCPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["qc"],
    queryFn: () => qcApi.list({ limit: 50 }),
  });

  const columns: ColumnDef<QualityControl>[] = [
    { accessorKey: "test_code", header: "رمز الفحص" },
    { accessorKey: "lot_number", header: "رقم التشغيلة" },
    { accessorKey: "measured_value", header: "القيمة" },
    { accessorKey: "expected_value", header: "القيمة المستهدفة" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const items = (data as any)?.qc_results || (data as any)?.items || [];

  return (
    <div className="space-y-6">
      <PageHeader title="مراقبة الجودة" description="فحوصات مراقبة الجودة الداخلية" />
      <Card>
        <CardContent className="pt-6">
          {items.length === 0 ? (
            <EmptyState icon={ShieldCheck} title="لا توجد نتائج جودة" description="سيتم عرض نتائج مراقبة الجودة هنا" />
          ) : (
            <DataTable columns={columns} data={items} loading={isLoading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
