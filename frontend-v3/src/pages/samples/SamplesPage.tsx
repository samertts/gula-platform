import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search);
  const { data, isLoading } = useQuery({
    queryKey: ["samples", debouncedSearch],
    queryFn: () => samplesApi.list({ limit: 50 }),
  });

  const columns: ColumnDef<Sample>[] = [
    { accessorKey: "barcode", header: t("sample.barcode") },
    { accessorKey: "patient_name", header: t("order.patientName") },
    { accessorKey: "sample_type", header: t("sample.sampleType") },
    {
      accessorKey: "status",
      header: t("sample.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    { accessorKey: "notes", header: t("sample.notes") },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("sample.title")} description={t("sample.subtitle")} />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.samples || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder={t("sample.search")} value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}