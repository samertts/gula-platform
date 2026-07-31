import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi, adminLogLevelApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Select } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Search, Plus, ShieldCheck, ShieldOff, Settings2 } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Lab } from "@/types";

export function AdminLabsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-labs", search],
    queryFn: () => adminApi.labs({ limit: 50 }),
  });

  const columns: ColumnDef<Lab>[] = [
    { accessorKey: "name", header: "اسم المختبر" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    { accessorKey: "license_number", header: "رقم الترخيص" },
    { accessorKey: "director_name", header: "المدير" },
    {
      accessorKey: "is_active",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? "نشط" : "غير نشط"}
        </Badge>
      ),
    },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة المختبرات"
        description="إدارة ومراقبة المختبرات المسجلة على المنصة"
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            إضافة مختبر
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.labs ?? []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="بحث عن مختبر..." value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-users", search],
    queryFn: () => adminApi.users({ limit: 50 }),
  });

  const columns: ColumnDef<any>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "email", header: "البريد الإلكتروني" },
    { accessorKey: "role", header: "الدور" },
    { accessorKey: "lab_name", header: "المختبر" },
    {
      accessorKey: "is_active",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? "نشط" : "غير نشط"}
        </Badge>
      ),
    },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة المستخدمين"
        description="إدارة المستخدمين والصلاحيات"
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            إضافة مستخدم
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.users ?? []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="بحث عن مستخدم..." value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function AdminAuditPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => adminApi.auditLogs({ limit: 50 }),
  });

  const columns: ColumnDef<any>[] = [
    { accessorKey: "action", header: "الإجراء" },
    { accessorKey: "entity_type", header: "الكيان" },
    { accessorKey: "entity_id", header: "رقم الكيان" },
    { accessorKey: "user_name", header: "المستخدم" },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="سجل التدقيق" description="سجل جميع العمليات على المنصة" />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.logs ?? []}
            loading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}

interface PendingLab {
  id: number;
  name: string;
  city: string | null;
  phone: string | null;
  created_at: string | null;
  admin_email: string | null;
  admin_name: string | null;
}

export function AdminPendingLabsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-pending-labs"],
    queryFn: () => adminApi.pendingLabs({ limit: 50 }),
  });

  const activate = useMutation({
    mutationFn: (id: number) => adminApi.activateLab(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-pending-labs"] }),
  });

  const columns: ColumnDef<PendingLab>[] = [
    { accessorKey: "name", header: "اسم المختبر" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    { accessorKey: "admin_name", header: "مدير المختبر" },
    { accessorKey: "admin_email", header: "بريد المدير" },
    {
      accessorKey: "created_at",
      header: "تاريخ التسجيل",
      cell: ({ row }) => (row.original.created_at ? new Date(row.original.created_at).toLocaleDateString("ar-IQ") : "—"),
    },
    {
      id: "actions",
      header: "إجراء",
      cell: ({ row }) => (
        <Button
          size="sm"
          onClick={() => activate.mutate(row.original.id)}
          disabled={activate.isPending}
        >
          <ShieldCheck className="h-4 w-4" />
          تفعيل
        </Button>
      ),
    },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="طلبات انضمام المختبرات"
        description="مراجعة وتفعيل طلبات تسجيل المختبرات الجديدة"
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data?.pending_labs ?? []}
            loading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function AdminControlPage() {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const [logLevel, setLogLevel] = useState("INFO");

  const { data: killSwitch, isLoading: ksLoading } = useQuery({
    queryKey: ["admin-kill-switch"],
    queryFn: () => adminApi.killSwitchStatus(),
    refetchInterval: 15_000,
  });

  const { data: controlStats } = useQuery({
    queryKey: ["admin-control-layer"],
    queryFn: () => adminApi.controlLayerStats(),
  });

  const { data: currentLevel, refetch: refetchLevel } = useQuery({
    queryKey: ["admin-log-level"],
    queryFn: () => adminLogLevelApi.get(),
  });

  const activate = useMutation({
    mutationFn: () => adminApi.killSwitchActivate(reason || "تفعيل يدوي من لوحة التحكم"),
    onSuccess: () => {
      setReason("");
      queryClient.invalidateQueries({ queryKey: ["admin-kill-switch"] });
    },
  });

  const deactivate = useMutation({
    mutationFn: () => adminApi.killSwitchDeactivate(reason || "عودة الخدمة إلى الوضع الطبيعي"),
    onSuccess: () => {
      setReason("");
      queryClient.invalidateQueries({ queryKey: ["admin-kill-switch"] });
    },
  });

  const setLevel = useMutation({
    mutationFn: () => adminLogLevelApi.set(logLevel),
    onSuccess: () => refetchLevel(),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="التحكم والسيطرة"
        description="مفتاح الإيقاف الطارئ وطبقة التحكم وسجل المستوى"
      />

      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <ShieldCheck className="h-4 w-4" /> مفتاح الإيقاف الطارئ
            </div>
            {ksLoading ? (
              <Badge variant="secondary">جاري التحميل…</Badge>
            ) : killSwitch?.active ? (
              <Badge variant="destructive">مفعّل</Badge>
            ) : (
              <Badge variant="success">غير مفعّل</Badge>
            )}
          </div>
          {killSwitch?.active && (
            <div className="text-xs text-gray-500 space-y-1">
              <div>السبب: {killSwitch.reason ?? "—"}</div>
              <div>بواسطة: {killSwitch.activated_by ?? "—"}</div>
              {killSwitch.activated_at ? (
                <div>التاريخ: {new Date(killSwitch.activated_at).toLocaleString("ar-IQ")}</div>
              ) : null}
            </div>
          )}
          <Input
            placeholder="سبب التفعيل/التعطيل (اختياري)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="flex gap-2">
            <Button
              variant="destructive"
              onClick={() => activate.mutate()}
              disabled={activate.isPending || killSwitch?.active}
            >
              <ShieldOff className="h-4 w-4" />
              تفعيل الإيقاف
            </Button>
            <Button
              variant="outline"
              onClick={() => deactivate.mutate()}
              disabled={deactivate.isPending || !killSwitch?.active}
            >
              <ShieldCheck className="h-4 w-4" />
              رفع الإيقاف
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-500">طلبات محظورة</div>
            <div className="mt-1 text-2xl font-bold text-red-600">{controlStats?.policy.blocked_total ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-500">طلبات مسموحة</div>
            <div className="mt-1 text-2xl font-bold">{controlStats?.policy.allowed_total ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-500">طبقة التحكم</div>
            <div className="mt-1 text-2xl font-bold">
              {controlStats?.policy.enabled ? "مفعّلة" : "معطّلة"}
            </div>
            <div className="text-xs text-gray-400">البيئة: {controlStats?.policy.env ?? "—"}</div>
          </CardContent>
        </Card>
      </div>

      {controlStats && Object.keys(controlStats.auto_repair).length > 0 && (
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="text-sm font-medium">إجراءات الإصلاح التلقائي</div>
            {Object.entries(controlStats.auto_repair).map(([name, info]) => (
              <div key={name} className="flex items-center justify-between text-xs">
                <span className="font-mono">{name}</span>
                <span className={info.triggered ? "text-red-600" : "text-gray-500"}>
                  {info.triggered ? `آخر تنفيذ: ${info.last_at ?? "—"}` : "لم يتم تشغيله"}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Settings2 className="h-4 w-4" /> مستوى السجل
          </div>
          <div className="flex items-end gap-2">
            <Select
              value={logLevel}
              options={["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].map((lvl) => ({ value: lvl, label: lvl }))}
              onChange={(e) => setLogLevel(e.target.value)}
              className="w-48"
            />
            <Button variant="outline" onClick={() => setLevel.mutate()} disabled={setLevel.isPending}>
              تطبيق
            </Button>
          </div>
          {currentLevel ? (
            <div className="text-xs text-gray-500">
              المستوى الحالي: {currentLevel.root_level} (فعّال: {currentLevel.effective_level})
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
