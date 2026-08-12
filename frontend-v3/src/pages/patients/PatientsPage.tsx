import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, Input, Badge, DataTable } from "@/components/ui";
import { EmptyState } from "@/components/ui/EmptyState";
import { WorkspaceReadBlockedError, workspaceScopedReads } from "@/api/workspaceScopedReads";
import { Search, ShieldAlert } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Patient } from "@/types";
import { formatDate, getGenderLabel } from "@/lib/utils";

export function PatientsPage() {
  const [search, setSearch] = useState("");
  const columns: ColumnDef<Patient>[] = [
    { accessorKey: "full_name", header: "الاسم" },
    { accessorKey: "phone", header: "الهاتف" },
    {
      accessorKey: "gender",
      header: "الجنس",
      cell: ({ row }) => <Badge variant="secondary">{getGenderLabel(row.original.gender)}</Badge>,
    },
    {
      accessorKey: "date_of_birth",
      header: "تاريخ الميلاد",
      cell: ({ row }) => formatDate(row.original.birth_date),
    },
    { accessorKey: "national_id", header: "الرقم الوطني" },
    { accessorKey: "lab_id", header: "رقم المختبر" },
  ];

  const query = useQuery({
    queryKey: ["patients", "patients.read", search],
    queryFn: () => workspaceScopedReads.listPatients({ search, limit: 50 }),
    retry: false,
  });
  const blockedMessage = query.error instanceof WorkspaceReadBlockedError ? query.error.message : null;

  return (
    <div
      className="space-y-6"
      data-contract-id="patients.read"
      data-permission="patients:read"
      data-workspace-context="required"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">المرضى</h1>
          <p className="text-muted-foreground">إدارة سجلات المرضى</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          {blockedMessage ? (
            <EmptyState
              icon={ShieldAlert}
              title="قراءة المرضى غير متاحة لهذه الجلسة"
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
                  placeholder="بحث عن مريض..."
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
