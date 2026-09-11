import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FileText } from "lucide-react";

const tabs = [
  { id: "encounter-management", label: "encounter-management", icon: FileText },
] as const;

type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success", completed: "success", approved: "success",
    pending: "warning", draft: "default", rejected: "destructive",
    inactive: "default", expired: "warning", revoked: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function CapabilitiesEncounterManagementPage() {
  const [activeTab, setActiveTab] = useState<TabId>("encounter-management");
  const col = createColumnHelper<Record<string, unknown>>();

  // NR-054: this page used to call GET /encounter-management, a router under
  // app/capabilities/ that factory.py never includes — the request answered 404.
  // The canonical owner of an encounter is the national data platform:
  // app/routes/national_data.py::list_canonical_encounters, which is registered,
  // scoped to the caller's lab_id, and gated server-side on `patients:read`.
  const encounterManagement = useQuery({
    queryKey: ["canonicalEncounters"],
    queryFn: () => api.get("/national-data/encounters").then((r) => r.data),
  });

  // Columns follow CanonicalEncounter.query_all, which is the actual response
  // contract. The generated scaffold asked for `name` and `created_at`; the
  // canonical record has neither, so both rendered blank and "Invalid Date".
  const encounterManagementCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("encounter_type", { header: "النوع" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("reason_description", { header: "السبب" }),
    col.accessor("period_start", {
      header: "تاريخ البدء",
      cell: ({ getValue }) => {
        const raw = getValue() as string | null;
        return raw ? new Date(raw).toLocaleDateString("ar-IQ") : "—";
      },
    }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    "encounter-management": { columns: encounterManagementCols, data: (encounterManagement.data ?? []) as Record<string, unknown>[], loading: encounterManagement.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="إدارة الزيارات" description="إدارة إدارة الزيارات" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
