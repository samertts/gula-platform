import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { edgeApi } from "@/api/endpoints";
import {
  Card, CardHeader, CardTitle, CardContent,
  Badge, Button, Input, DataTable,
} from "@/components/ui";
import {
  PageHeader, LoadingSpinner, ErrorDisplay, EmptyState,
} from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { EdgeDevice, EdgeTask } from "@/types";
import { Server, Terminal, Radio, Activity, Shield, ShieldOff } from "lucide-react";

const deviceStatusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  active: "success",
  quarantined: "warning",
  revoked: "destructive",
};

const taskStatusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  pending: "secondary",
  running: "warning",
  completed: "success",
  failed: "destructive",
  cancelled: "outline",
};

function EdgeDevices() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["edge-devices"],
    queryFn: () => edgeApi.listDevices(),
  });

  const quarantine = useMutation({
    mutationFn: (deviceId: string) => edgeApi.quarantineDevice(deviceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["edge-devices"] }),
  });

  const revoke = useMutation({
    mutationFn: (deviceId: string) => edgeApi.revokeDevice(deviceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["edge-devices"] }),
  });

  const reinstate = useMutation({
    mutationFn: (deviceId: string) => edgeApi.reinstateDevice(deviceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["edge-devices"] }),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const devices: EdgeDevice[] = data?.devices ?? [];
  const filtered = devices.filter(
    (d) =>
      !search ||
      d.device_id.toLowerCase().includes(search.toLowerCase()) ||
      (d.display_name || "").toLowerCase().includes(search.toLowerCase()),
  );

  const columns: ColumnDef<EdgeDevice>[] = [
    { accessorKey: "device_id", header: "معرف الجهاز" },
    {
      accessorKey: "display_name",
      header: "الاسم",
      cell: ({ row }) => row.original.display_name || "—",
    },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => {
        const labels: Record<string, string> = {
          active: "نشط", quarantined: "محجور", revoked: "ملغى",
        };
        return (
          <Badge variant={deviceStatusVariant[row.original.status] || "secondary"}>
            {labels[row.original.status] || row.original.status}
          </Badge>
        );
      },
    },
    {
      accessorKey: "last_seen_at",
      header: "آخر ظهور",
      cell: ({ row }) => row.original.last_seen_at || "—",
    },
    {
      accessorKey: "agent_version",
      header: "الإصدار",
      cell: ({ row }) => row.original.agent_version || "—",
    },
    {
      id: "actions",
      header: "الإجراءات",
      cell: ({ row }) => {
        const d = row.original;
        return (
          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
            {d.status === "active" && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => quarantine.mutate(d.device_id)}
                  loading={quarantine.isPending}
                >
                  <Shield className="h-3 w-3" /> حجر
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => revoke.mutate(d.device_id)}
                  loading={revoke.isPending}
                >
                  <ShieldOff className="h-3 w-3" /> إلغاء
                </Button>
              </>
            )}
            {(d.status === "quarantined" || d.status === "revoked") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => reinstate.mutate(d.device_id)}
                loading={reinstate.isPending}
              >
                <Activity className="h-3 w-3" /> إعادة تفعيل
              </Button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <Card>
      <CardContent className="pt-6">
        {devices.length === 0 ? (
          <EmptyState icon={Radio} title="لا توجد أجهزة" description="لم يتم تسجيل أي أجهزة حافة بعد" />
        ) : filtered.length === 0 ? (
          <EmptyState icon={Radio} title="لا توجد نتائج" description="لا توجد أجهزة تطابق بحثك" />
        ) : (
          <DataTable
            columns={columns}
            data={filtered}
            toolbar={
              <Input
                placeholder="بحث عن جهاز..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-xs"
              />
            }
          />
        )}
      </CardContent>
    </Card>
  );
}

function EdgeTasks() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["edge-tasks"],
    queryFn: () => edgeApi.listTasks(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const tasks: EdgeTask[] = data?.tasks ?? [];

  const statusLabels: Record<string, string> = {
    pending: "معلق", running: "قيد التنفيذ", completed: "مكتمل", failed: "فشل", cancelled: "ملغي",
  };

  const columns: ColumnDef<EdgeTask>[] = [
    { accessorKey: "task_uid", header: "رمز المهمة" },
    { accessorKey: "kind", header: "النوع" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={taskStatusVariant[row.original.status] || "secondary"}>
          {statusLabels[row.original.status] || row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "device_id",
      header: "الجهاز المستهدف",
      cell: ({ row }) => row.original.device_id || "—",
    },
    { accessorKey: "created_at", header: "تاريخ الإنشاء" },
  ];

  return (
    <Card>
      <CardContent className="pt-6">
        {tasks.length === 0 ? (
          <EmptyState icon={Terminal} title="لا توجد مهام" description="لم يتم إنشاء أي مهام بعد" />
        ) : (
          <DataTable columns={columns} data={tasks} />
        )}
      </CardContent>
    </Card>
  );
}

function EdgeFleetSummary() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["edge-fleet-summary"],
    queryFn: () => edgeApi.fleetSummary(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const s = (data as Record<string, any>) || {};

  const cards = [
    { title: "إجمالي الأجهزة", value: s.devices_total ?? 0, icon: Server, color: "text-blue-600" },
    { title: "الأجهزة النشطة", value: s.online_devices ?? 0, icon: Radio, color: "text-emerald-600" },
    { title: "المهام المعلقة", value: s.pending_tasks ?? 0, icon: Terminal, color: "text-amber-600" },
    { title: "المهام المكتملة", value: s.tasks_completed_total ?? 0, icon: Activity, color: "text-violet-600" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-5 w-5 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{card.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function EdgePage() {
  const [activeTab, setActiveTab] = useState<"devices" | "tasks" | "fleet">("devices");

  return (
    <div className="space-y-6">
      <PageHeader title="منصة الحافة" description="إدارة أجهزة الحافة والمهام عن بُعد" />

      <div className="flex gap-2 border-b pb-2">
        <Button
          variant={activeTab === "devices" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("devices")}
        >
          <Server className="h-4 w-4" /> الأجهزة
        </Button>
        <Button
          variant={activeTab === "tasks" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("tasks")}
        >
          <Terminal className="h-4 w-4" /> المهام
        </Button>
        <Button
          variant={activeTab === "fleet" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("fleet")}
        >
          <Activity className="h-4 w-4" /> ملخص الأسطول
        </Button>
      </div>

      {activeTab === "devices" && <EdgeDevices />}
      {activeTab === "tasks" && <EdgeTasks />}
      {activeTab === "fleet" && <EdgeFleetSummary />}
    </div>
  );
}
