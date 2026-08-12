import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { hospitalApi } from "@/api/endpoints";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Input,
  Button,
  DataTable,
  Select,
  Dialog,
} from "@/components/ui";
import {
  PageHeader,
  LoadingSpinner,
  EmptyState,
  ErrorDisplay,
} from "@/components/shared/PageComponents";
import { Building2, DoorOpen, Bed, Plus, Search, Hospital } from "lucide-react";
import { toast } from "@/hooks/useToast";

interface Hospital {
  id: number;
  code: string;
  name: string;
  name_ar?: string;
  hospital_type: string;
  license_number?: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  city?: string;
  province?: string;
  country?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface Department {
  id: number;
  hospital_id: number;
  parent_id?: number;
  code: string;
  name: string;
  name_ar?: string;
  department_type?: string;
  phone?: string;
  is_active: boolean;
}

interface Unit {
  id: number;
  hospital_id: number;
  code: string;
  name: string;
  name_ar?: string;
  unit_type: string;
  is_active: boolean;
}

interface OccupancyData {
  total: number;
  available: number;
  occupied: number;
  reserved: number;
  maintenance: number;
  cleaning: number;
  occupancy_rate: number;
}

type Tab = "hospitals" | "departments" | "occupancy";

const TABS: { key: Tab; label: string; icon: typeof Hospital }[] = [
  { key: "hospitals", label: "المستشفيات", icon: Hospital },
  { key: "departments", label: "الأقسام والوحدات", icon: DoorOpen },
  { key: "occupancy", label: "إشغال الأسرة", icon: Bed },
];

export function HospitalPage() {
  const [activeTab, setActiveTab] = useState<Tab>("hospitals");

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة المستشفيات"
        description="إدارة المستشفيات والأقسام والوحدات وإشغال الأسرة"
      />

      <div className="flex gap-1 rounded-lg border p-1 bg-muted/30 w-fit">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === key
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "hospitals" && <HospitalsList />}
      {activeTab === "departments" && <DepartmentsAndUnits />}
      {activeTab === "occupancy" && <BedOccupancy />}
    </div>
  );
}

function HospitalsList() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    name_ar: "",
    hospital_type: "general",
    phone: "",
    email: "",
    city: "",
    address: "",
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["hospitals"],
    queryFn: () => hospitalApi.list({ limit: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => hospitalApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hospitals"] });
      setDialogOpen(false);
      setFormData({ code: "", name: "", name_ar: "", hospital_type: "general", phone: "", email: "", city: "", address: "" });
      toast({ variant: "success", title: "تمت الإضافة", description: "تم إضافة المستشفى بنجاح" });
    },
    onError: (err: Error) => {
      toast({ variant: "destructive", title: "خطأ", description: err.message });
    },
  });

  const hospitals: Hospital[] = (data as { items?: Hospital[] })?.items ?? [];

  const filtered = search
    ? hospitals.filter(
        (h) =>
          h.name.toLowerCase().includes(search.toLowerCase()) ||
          h.code.toLowerCase().includes(search.toLowerCase()) ||
          (h.city && h.city.toLowerCase().includes(search.toLowerCase())),
      )
    : hospitals;

  const columns: ColumnDef<Hospital>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "code", header: "الكود" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    {
      accessorKey: "hospital_type",
      header: "النوع",
      cell: ({ row }) => {
        const types: Record<string, string> = { general: "عام", specialized: "تخصصي", teaching: "تعليمي", private: "خاص" };
        return types[row.original.hospital_type] ?? row.original.hospital_type;
      },
    },
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

  if (error) return <ErrorDisplay error={(error as Error).message} onRetry={() => refetch()} />;

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={filtered}
            loading={isLoading}
            toolbar={
              <div className="flex items-center gap-3 w-full">
                <div className="relative flex-1">
                  <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="بحث عن مستشفى..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="ps-9 w-80"
                  />
                </div>
                <Button onClick={() => setDialogOpen(true)}>
                  <Plus className="h-4 w-4" />
                  إضافة مستشفى
                </Button>
              </div>
            }
          />
        </CardContent>
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="إضافة مستشفى جديد"
        footer={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              إلغاء
            </Button>
            <Button
              onClick={() => createMutation.mutate(formData as unknown as Record<string, unknown>)}
              loading={createMutation.isPending}
            >
              حفظ
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">الكود *</label>
            <Input
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              placeholder="HOSP001"
            />
          </div>
          <div>
            <label className="text-sm font-medium">الاسم *</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="اسم المستشفى"
            />
          </div>
          <div>
            <label className="text-sm font-medium">الاسم (عربي)</label>
            <Input
              value={formData.name_ar}
              onChange={(e) => setFormData({ ...formData, name_ar: e.target.value })}
              placeholder="اسم المستشفى بالعربية"
            />
          </div>
          <div>
            <label className="text-sm font-medium">النوع *</label>
            <Select
              value={formData.hospital_type}
              onChange={(e) => setFormData({ ...formData, hospital_type: e.target.value })}
              options={[
                { value: "general", label: "عام" },
                { value: "specialized", label: "تخصصي" },
                { value: "teaching", label: "تعليمي" },
                { value: "private", label: "خاص" },
              ]}
            />
          </div>
          <div>
            <label className="text-sm font-medium">الهاتف</label>
            <Input
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="رقم الهاتف"
            />
          </div>
          <div>
            <label className="text-sm font-medium">البريد الإلكتروني</label>
            <Input
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="email@hospital.com"
            />
          </div>
          <div>
            <label className="text-sm font-medium">المدينة</label>
            <Input
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              placeholder="المدينة"
            />
          </div>
        </div>
      </Dialog>
    </div>
  );
}

function DepartmentsAndUnits() {
  const queryClient = useQueryClient();
  const [selectedHospitalId, setSelectedHospitalId] = useState("");
  const [deptDialogOpen, setDeptDialogOpen] = useState(false);
  const [deptForm, setDeptForm] = useState({ code: "", name: "", name_ar: "", department_type: "", phone: "" });
  const [showUnits, setShowUnits] = useState(false);

  const { data: hospitalsData } = useQuery({
    queryKey: ["hospitals"],
    queryFn: () => hospitalApi.list({ limit: 200 }),
  });

  const hospitals: Hospital[] = (hospitalsData as { items?: Hospital[] })?.items ?? [];
  const hospitalId = selectedHospitalId ? Number(selectedHospitalId) : null;

  const { data: deptsData, isLoading: deptsLoading, error: deptsError, refetch: refetchDepts } = useQuery({
    queryKey: ["hospital-departments", hospitalId],
    queryFn: () => hospitalApi.listDepartments(hospitalId!),
    enabled: !!hospitalId,
  });

  const { data: unitsData, isLoading: unitsLoading } = useQuery({
    queryKey: ["hospital-units", hospitalId],
    queryFn: () => hospitalApi.listUnits(hospitalId!),
    enabled: !!hospitalId && showUnits,
  });

  const departments: Department[] = (deptsData as unknown as Department[]) ?? [];
  const units: Unit[] = (unitsData as unknown as Unit[]) ?? [];

  const createDeptMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => hospitalApi.createDepartment(hospitalId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hospital-departments", hospitalId] });
      setDeptDialogOpen(false);
      setDeptForm({ code: "", name: "", name_ar: "", department_type: "", phone: "" });
      toast({ variant: "success", title: "تمت الإضافة", description: "تم إضافة القسم بنجاح" });
    },
    onError: (err: Error) => {
      toast({ variant: "destructive", title: "خطأ", description: err.message });
    },
  });

  const deptColumns: ColumnDef<Department>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "code", header: "الكود" },
    {
      accessorKey: "department_type",
      header: "النوع",
      cell: ({ row }) => row.original.department_type || "—",
    },
    { accessorKey: "phone", header: "الهاتف" },
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

  const unitColumns: ColumnDef<Unit>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "code", header: "الكود" },
    { accessorKey: "unit_type", header: "نوع الوحدة" },
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

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-80">
          <Select
            value={selectedHospitalId}
            onChange={(e) => {
              setSelectedHospitalId(e.target.value);
              setShowUnits(false);
            }}
            placeholder="اختر مستشفى..."
            options={hospitals.map((h) => ({ value: String(h.id), label: h.name }))}
          />
        </div>
      </div>

      {!hospitalId && (
        <EmptyState
          icon={Building2}
          title="اختر مستشفى"
          description="يرجى اختيار مستشفى لعرض الأقسام والوحدات"
        />
      )}

      {hospitalId && (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <DoorOpen className="h-5 w-5" />
                  الأقسام
                </CardTitle>
                <Button size="sm" onClick={() => setDeptDialogOpen(true)}>
                  <Plus className="h-4 w-4" />
                  إضافة قسم
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {deptsLoading && <LoadingSpinner />}
              {deptsError && <ErrorDisplay error={(deptsError as Error).message} onRetry={() => refetchDepts()} />}
              {!deptsLoading && !deptsError && departments.length === 0 && (
                <EmptyState
                  icon={DoorOpen}
                  title="لا توجد أقسام"
                  description="لم يتم إضافة أقسام بعد لهذا المستشفى"
                />
              )}
              {!deptsLoading && !deptsError && departments.length > 0 && (
                <DataTable columns={deptColumns} data={departments} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  الوحدات
                </CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowUnits(!showUnits)}
                >
                  {showUnits ? "إخفاء" : "عرض"}
                </Button>
              </div>
            </CardHeader>
            {showUnits && (
              <CardContent>
                {unitsLoading && <LoadingSpinner />}
                {!unitsLoading && units.length === 0 && (
                  <EmptyState
                    icon={Building2}
                    title="لا توجد وحدات"
                    description="لم يتم إضافة وحدات بعد لهذا المستشفى"
                  />
                )}
                {!unitsLoading && units.length > 0 && (
                  <DataTable columns={unitColumns} data={units} />
                )}
              </CardContent>
            )}
          </Card>

          <Dialog
            open={deptDialogOpen}
            onClose={() => setDeptDialogOpen(false)}
            title="إضافة قسم جديد"
            footer={
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setDeptDialogOpen(false)}>
                  إلغاء
                </Button>
                <Button
                  onClick={() => createDeptMutation.mutate(deptForm as unknown as Record<string, unknown>)}
                  loading={createDeptMutation.isPending}
                >
                  حفظ
                </Button>
              </div>
            }
          >
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">الكود *</label>
                <Input
                  value={deptForm.code}
                  onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value })}
                  placeholder="DEPT001"
                />
              </div>
              <div>
                <label className="text-sm font-medium">الاسم *</label>
                <Input
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  placeholder="اسم القسم"
                />
              </div>
              <div>
                <label className="text-sm font-medium">الاسم (عربي)</label>
                <Input
                  value={deptForm.name_ar}
                  onChange={(e) => setDeptForm({ ...deptForm, name_ar: e.target.value })}
                  placeholder="اسم القسم بالعربية"
                />
              </div>
              <div>
                <label className="text-sm font-medium">نوع القسم</label>
                <Input
                  value={deptForm.department_type}
                  onChange={(e) => setDeptForm({ ...deptForm, department_type: e.target.value })}
                  placeholder="مثال: طوارئ، جراحة..."
                />
              </div>
              <div>
                <label className="text-sm font-medium">الهاتف</label>
                <Input
                  value={deptForm.phone}
                  onChange={(e) => setDeptForm({ ...deptForm, phone: e.target.value })}
                  placeholder="رقم الهاتف"
                />
              </div>
            </div>
          </Dialog>
        </>
      )}
    </div>
  );
}

function BedOccupancy() {
  const [selectedHospitalId, setSelectedHospitalId] = useState("");

  const { data: hospitalsData } = useQuery({
    queryKey: ["hospitals"],
    queryFn: () => hospitalApi.list({ limit: 200 }),
  });

  const hospitals: Hospital[] = (hospitalsData as { items?: Hospital[] })?.items ?? [];
  const hospitalId = selectedHospitalId ? Number(selectedHospitalId) : null;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["hospital-occupancy", hospitalId],
    queryFn: () => hospitalApi.occupancy({ hospital_id: hospitalId }),
    enabled: !!hospitalId,
  });

  const occupancy = data as OccupancyData | undefined;

  return (
    <div className="space-y-4">
      <div className="w-80">
        <Select
          value={selectedHospitalId}
          onChange={(e) => setSelectedHospitalId(e.target.value)}
          placeholder="اختر مستشفى..."
          options={hospitals.map((h) => ({ value: String(h.id), label: h.name }))}
        />
      </div>

      {!hospitalId && (
        <EmptyState
          icon={Bed}
          title="اختر مستشفى"
          description="يرجى اختيار مستشفى لعرض إشغال الأسرة"
        />
      )}

      {hospitalId && isLoading && <LoadingSpinner />}

      {hospitalId && error && (
        <ErrorDisplay error={(error as Error).message} onRetry={() => refetch()} />
      )}

      {hospitalId && occupancy && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">إجمالي الأسرة</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{occupancy.total}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">مشغول</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-amber-600">{occupancy.occupied}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">متاح</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-emerald-600">{occupancy.available}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">نسبة الإشغال</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{occupancy.occupancy_rate}%</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">محجوز</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{occupancy.reserved}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">صيانة</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{occupancy.maintenance}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">تنظيف</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{occupancy.cleaning}</p>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
