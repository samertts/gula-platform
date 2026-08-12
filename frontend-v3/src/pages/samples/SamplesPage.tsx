import { useQuery } from "@tanstack/react-query";
import { samplesApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Sample } from "@/types";
import { useDebounce } from "@/hooks/useDebounce";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  collected: "secondary",
  received: "default",
  processing: "warning",
  analyzed: "success",
  rejected: "destructive",
};

export function SamplesPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search);
  const { data, isLoading } = useQuery({
    queryKey: ["samples", debouncedSearch],
    queryFn: () => samplesApi.list({ limit: 50 }),
  });

  const columns: ColumnDef<Sample>[] = [
    { accessorKey: "barcode", header: "الباركود" },
    { accessorKey: "patient_name", header: "اسم المريض" },
    { accessorKey: "sample_type", header: "نوع العينة" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    { accessorKey: "notes", header: "ملاحظات" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="العينات" description="إدارة عينات الفحوصات المخبرية" />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.items || (data as any)?.samples || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="بحث عن عينة..." value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}
