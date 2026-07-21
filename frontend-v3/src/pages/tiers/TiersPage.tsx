import { useQuery } from "@tanstack/react-query";
import { tiersApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Crown, CheckCircle2, Star } from "lucide-react";

const tierColors: Record<string, string> = {
  free: "bg-gray-100 border-gray-300 dark:bg-gray-800",
  basic: "bg-blue-50 border-blue-300 dark:bg-blue-900/20",
  professional: "bg-purple-50 border-purple-300 dark:bg-purple-900/20",
  enterprise: "bg-amber-50 border-amber-300 dark:bg-amber-900/20",
};

const tierIcons: Record<string, typeof Crown> = {
  free: Star,
  basic: Star,
  professional: Crown,
  enterprise: Crown,
};

export function TiersPage() {
  const { data: tiersData, isLoading: tiersLoading } = useQuery({
    queryKey: ["tiers"],
    queryFn: () => tiersApi.list(),
  });

  const { data: myTier, isLoading: myLoading } = useQuery({
    queryKey: ["my-tier"],
    queryFn: () => tiersApi.my(),
  });

  if (tiersLoading || myLoading) return <LoadingSpinner />;

  const tiers = (tiersData as any)?.tiers || [];
  const currentTier = (myTier as any)?.tier || "free";

  return (
    <div className="space-y-6">
      <PageHeader title="الباقات" description="اختر الباقة المناسبة لمختبرك" />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {tiers.map((tier: any) => {
          const Icon = tierIcons[tier.name] || Star;
          const isCurrent = tier.name === currentTier;
          return (
            <Card key={tier.name} className={`relative border-2 ${tierColors[tier.name] || ""} ${isCurrent ? "ring-2 ring-primary" : ""}`}>
              {isCurrent && (
                <Badge className="absolute -top-2 end-2">
                  <CheckCircle2 className="h-3 w-3 ms-1" /> الحالية
                </Badge>
              )}
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="h-6 w-6 text-primary" />
                  <CardTitle>{tier.name}</CardTitle>
                </div>
                <p className="text-2xl font-bold">{tier.price || 0}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-2 text-sm">
                  {(tier.features || []).map((f: string, i: number) => (
                    <li key={i} className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Button className="w-full" variant={isCurrent ? "outline" : "default"} disabled={isCurrent}>
                  {isCurrent ? "الباقة الحالية" : "ترقية"}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
