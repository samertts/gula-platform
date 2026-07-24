import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { patientsApi } from "@/api/endpoints";
import { Card, CardContent, Input, Badge, DataTable } from "@/components/ui";
import { Search } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Patient } from "@/types";
import { formatDate, getGenderLabel } from "@/lib/utils";

export function PatientsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["patients", search],
    queryFn: () => patientsApi.list({ search, limit: 50 }),
  });

  const columns: ColumnDef<Patient>[] = [
    { accessorKey: "full_name", header: t("patient.fullName") },
    { accessorKey: "phone", header: t("patient.phone") },
    {
      accessorKey: "gender",
      header: t("patient.gender"),
      cell: ({ row }) => <Badge variant="secondary">{getGenderLabel(row.original.gender)}</Badge>,
    },
    {
      accessorKey: "date_of_birth",
      header: t("patient.birthDate"),
      cell: ({ row }) => formatDate(row.original.birth_date),
    },
    { accessorKey: "national_id", header: t("patient.nationalId") },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("patient.title")}</h1>
          <p className="text-muted-foreground">{t("patient.subtitle")}</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.items || (data as any)?.patients || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={t("patient.search")}
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