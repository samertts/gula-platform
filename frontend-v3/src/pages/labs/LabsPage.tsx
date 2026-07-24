import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Lab } from "@/types";

export function LabsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["labs", search],
    queryFn: () => adminApi.labs({ limit: 50 }),
  });

  const columns: ColumnDef<Lab>[] = [
    { accessorKey: "name", header: t("lab.name") },
    { accessorKey: "city", header: t("lab.city") },
    { accessorKey: "phone", header: t("lab.phone") },
    { accessorKey: "license_number", header: t("lab.licenseNumber") },
    { accessorKey: "director_name", header: t("lab.directorName") },
    {
      accessorKey: "is_active",
      header: t("lab.status"),
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? t("lab.active") : t("lab.inactive")}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("lab.title")}
        description={t("lab.subtitle")}
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            {t("lab.newLab")}
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.labs || (data as any)?.items || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder={t("lab.search")} value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}