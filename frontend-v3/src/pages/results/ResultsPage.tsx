import { useQuery } from "@tanstack/react-query";
import { resultsApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input } from "@/components/ui";
import { Search } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabResult } from "@/types";

const flagVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  normal: "success",
  high: "warning",
  low: "warning",
  critical_high: "destructive",
  critical_low: "destructive",
};

export function ResultsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["results", search],
    queryFn: () => resultsApi.list({ limit: 50 }),
  });

  const columns: ColumnDef<LabResult>[] = [
    { accessorKey: "id", header: "معرف النتيجة" },
    { accessorKey: "order_id", header: "رقم الطلب" },
    { accessorKey: "test_name", header: "اسم الفحص" },
    { accessorKey: "value", header: "القيمة", cell: ({ row }) => row.original.value ?? row.original.value_text ?? "-" },
    {
      accessorKey: "flag",
      header: "الحالة",
      cell: ({ row }) => {
        const flag = row.original.flag;
        return flag ? (
          <Badge variant={flagVariant[flag] || "secondary"}>{flag}</Badge>
        ) : (
          <Badge variant="outline">-</Badge>
        );
      },
    },
    {
      accessorKey: "created_at",
      header: "تاريخ الإنشاء",
      cell: ({ row }) => row.original.created_at ?? "-",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">النتائج</h1>
        <p className="text-muted-foreground">نتائج الفحوصات المخبرية</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.results || data?.items || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="بحث عن نتيجة..."
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
