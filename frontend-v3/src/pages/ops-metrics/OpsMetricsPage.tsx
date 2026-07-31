import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { Card, CardContent, Badge } from "@/components/ui";
import { Activity, Gauge, Database, Boxes, List } from "lucide-react";

interface MetricsJson {
  uptime_s: number;
  uptime_h: number;
  memory_mb: number;
  db: { status: string; ok: boolean; ping_ms: number };
  redis: { ok: boolean; ping_ms: number };
  stats: {
    orders_total: number;
    orders_today: number;
    validated_total: number;
    validated_today: number;
    pending: number;
  };
  scope: string;
  timestamp: string;
}

interface PromSample {
  name: string;
  labels: string;
  value: string;
}

const tabs = [
  { id: "summary", label: "الملخص", icon: Gauge },
  { id: "prometheus", label: "Prometheus", icon: Activity },
] as const;

type TabId = (typeof tabs)[number]["id"];

function parsePrometheus(text: string): PromSample[] {
  const samples: PromSample[] = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("gula_")) continue;
    const spaceIdx = trimmed.indexOf(" ");
    if (spaceIdx <= 0) continue;
    const raw = trimmed.slice(0, spaceIdx);
    const value = trimmed.slice(spaceIdx + 1);
    const braceIdx = raw.indexOf("{");
    if (braceIdx === -1) {
      samples.push({ name: raw, labels: "", value });
    } else {
      samples.push({
        name: raw.slice(0, braceIdx),
        labels: raw.slice(braceIdx + 1, -1),
        value,
      });
    }
    if (samples.length >= 50) break;
  }
  return samples;
}

const statusBadge = (ok: boolean): "success" | "destructive" => (ok ? "success" : "destructive");

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-sm text-gray-500">{label}</div>
        <div className="mt-1 text-2xl font-bold">{value}</div>
        {sub ? <div className="text-xs text-gray-400">{sub}</div> : null}
      </CardContent>
    </Card>
  );
}

export default function OpsMetricsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("summary");

  const metrics = useQuery({
    queryKey: ["opsMetrics", "json"],
    queryFn: () => api.get<MetricsJson>("/metrics").then((r) => r.data),
    refetchInterval: 30_000,
  });

  const prom = useQuery({
    queryKey: ["opsMetrics", "prom"],
    queryFn: () => api.get<string>("/metrics/prom").then((r) => r.data),
    refetchInterval: 60_000,
  });

  const data = metrics.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="مؤشرات التشغيل"
        description="لوحة مؤشرات أداء المنصة — يتم التحديث كل 30 ثانية"
      />
      <div className="flex border-b flex-wrap">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-b-2 border-indigo-600 text-indigo-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === "summary" && (
        <div className="space-y-6">
          {metrics.error ? (
            <Card>
              <CardContent className="p-4 text-red-600">
                تعذر جلب المؤشرات: {String(metrics.error)}
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  label="مدة التشغيل"
                  value={data ? `${data.uptime_h} ساعة` : "—"}
                  sub={data ? `${data.uptime_s} ثانية` : undefined}
                />
                <StatCard label="الذاكرة" value={data ? `${data.memory_mb} MB` : "—"} sub="RSS" />
                <StatCard
                  label="النطاق"
                  value={data ? (data.scope === "platform" ? "المنصة كاملة" : "مختبر") : "—"}
                />
                <StatCard
                  label="آخر تحديث"
                  value={data ? new Date(data.timestamp).toLocaleTimeString("ar-IQ") : "—"}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Database className="h-4 w-4" /> قاعدة البيانات
                      </div>
                      {data ? (
                        <Badge variant={statusBadge(data.db.ok)}>
                          {data.db.ok ? "متصل" : "معطل"}
                        </Badge>
                      ) : (
                        <Badge variant="default">—</Badge>
                      )}
                    </div>
                    {data ? (
                      <div className="text-xs text-gray-500">
                        الحالة: {data.db.status} · زمن الاستجابة: {data.db.ping_ms.toFixed(1)} ms
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Boxes className="h-4 w-4" /> Redis
                      </div>
                      {data ? (
                        <Badge variant={statusBadge(data.redis.ok)}>
                          {data.redis.ok ? "متصل" : "معطل"}
                        </Badge>
                      ) : (
                        <Badge variant="default">—</Badge>
                      )}
                    </div>
                    {data ? (
                      <div className="text-xs text-gray-500">
                        زمن الاستجابة: {data.redis.ping_ms.toFixed(1)} ms
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-sm font-medium mb-4">
                    <List className="h-4 w-4" /> الطلبات
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <StatCard label="إجمالي" value={data ? String(data.stats.orders_total) : "—"} />
                    <StatCard label="اليوم" value={data ? String(data.stats.orders_today) : "—"} />
                    <StatCard
                      label="مؤكدة (إجمالي)"
                      value={data ? String(data.stats.validated_total) : "—"}
                    />
                    <StatCard
                      label="مؤكدة اليوم"
                      value={data ? String(data.stats.validated_today) : "—"}
                    />
                    <StatCard label="قيد الانتظار" value={data ? String(data.stats.pending) : "—"} />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {activeTab === "prometheus" && (
        <Card>
          <CardContent className="p-0">
            {prom.error ? (
              <div className="p-4 text-red-600">
                تعذر جلب المقاييس: {String(prom.error)}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-right text-gray-500">
                    <th className="px-4 py-3">المقياس</th>
                    <th className="px-4 py-3">التسميات</th>
                    <th className="px-4 py-3 text-left">القيمة</th>
                  </tr>
                </thead>
                <tbody>
                  {parsePrometheus(prom.data ?? "").map((s, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="px-4 py-2 font-mono text-xs">{s.name}</td>
                      <td className="px-4 py-2 font-mono text-xs text-gray-500">{s.labels}</td>
                      <td className="px-4 py-2 font-mono text-xs text-left">{s.value}</td>
                    </tr>
                  ))}
                  {prom.data ? null : <tr><td className="px-4 py-3">جاري التحميل…</td></tr>}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
