import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "documents", label: "المستندات", icon: FileText },
  { id: "versions", label: "versions", icon: Activity },
  { id: "signatures", label: "signatures", icon: List },
  { id: "qrcode", label: "qrcode", icon: ClipboardList },
  { id: "attachments", label: "attachments", icon: BookOpen },
  { id: "history", label: "history", icon:  FolderOpen },
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

export default function NationalDocumentPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("documents");
  const col = createColumnHelper<Record<string, unknown>>();

  const documents = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "documents"],
    queryFn: () => api.get("/national/documents").then((r) => r.data),
  });
  const versions = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "versions"],
    queryFn: () => api.get("/national/documents//versions").then((r) => r.data),
  });
  const signatures = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "signatures"],
    queryFn: () => api.get("/national/documents//signatures").then((r) => r.data),
  });
  const qrcode = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "qrcode"],
    queryFn: () => api.get("/national/documents//qrcode").then((r) => r.data),
  });
  const attachments = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "attachments"],
    queryFn: () => api.get("/national/documents//attachments").then((r) => r.data),
  });
  const history = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "history"],
    queryFn: () => api.get("/national/documents//history").then((r) => r.data),
  });

  const documentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const versionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const signaturesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const qrcodeCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const attachmentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const historyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    documents: { columns: documentsCols, data: (documents.data ?? []) as Record<string, unknown>[], loading: documents.isLoading },
    versions: { columns: versionsCols, data: (versions.data ?? []) as Record<string, unknown>[], loading: versions.isLoading },
    signatures: { columns: signaturesCols, data: (signatures.data ?? []) as Record<string, unknown>[], loading: signatures.isLoading },
    qrcode: { columns: qrcodeCols, data: (qrcode.data ?? []) as Record<string, unknown>[], loading: qrcode.isLoading },
    attachments: { columns: attachmentsCols, data: (attachments.data ?? []) as Record<string, unknown>[], loading: attachments.isLoading },
    history: { columns: historyCols, data: (history.data ?? []) as Record<string, unknown>[], loading: history.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الوثائق الوطنية" description="إدارة الوثائق الوطنية" />
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
