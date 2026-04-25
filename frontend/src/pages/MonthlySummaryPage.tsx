import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Flame, ShoppingCart, Target, TrendingUp } from "lucide-react";

import { CategoryPie } from "../components/charts/CategoryPie";
import { ClassificationBadge } from "../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Progress } from "../components/ui/Progress";
import { api } from "../lib/api";
import { eur, kcal, pct } from "../lib/format";

export function MonthlySummaryPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["monthly"], queryFn: api.monthly });
  if (isLoading) return <p className="text-sm text-ink/60">Loading monthly summary…</p>;
  if (error || !data) return <p className="text-sm text-red-700">Monthly summary unavailable.</p>;

  const goalUsedPct = data.goal ? data.goal.budget_used_pct * 100 : 0;

  return (
    <div className="grid gap-6">
      {/* Page header */}
      <section className="flex items-end justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-ink/8 px-3 py-1 text-xs font-medium text-ink/60">
            {data.start_date} — {data.end_date}
          </span>
          <h1 className="mt-2 text-2xl font-semibold">Monthly Summary</h1>
        </div>
      </section>

      {/* Quick KPI strip */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiStrip
          icon={<Flame size={16} className="text-coral" />}
          bg="bg-coral/10"
          label="Total calories"
          value={kcal(data.calories.total)}
        />
        <KpiStrip
          icon={<ShoppingCart size={16} className="text-mint" />}
          bg="bg-mint/10"
          label="Food spend"
          value={eur(data.spend.total)}
        />
        <KpiStrip
          icon={<TrendingUp size={16} className="text-amber" />}
          bg="bg-amber/10"
          label="Outside Schijf"
          value={eur(data.spend.outside_schijf)}
        />
        <KpiStrip
          icon={<Target size={16} className="text-berry" />}
          bg="bg-berry/10"
          label="Goal used"
          value={data.goal ? pct(data.goal.budget_used_pct) : "—"}
        />
      </section>

      {/* Pie charts */}
      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Calories</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.calories} valueType="kcal" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.spend} valueType="eur" />
          </CardContent>
        </Card>
      </section>

      {/* Top items row */}
      <section className="grid gap-4 lg:grid-cols-3">
        <TopItems title="Top Calories" items={data.top_outside_items_by_calories} metric="calories" />
        <TopItems title="Top Spend" items={data.top_outside_items_by_spend} metric="spend" />
        <Card>
          <CardHeader>
            <CardTitle>Merchants</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2">
            {data.top_merchants_by_outside_spend.length ? (
              data.top_merchants_by_outside_spend.map((merchant) => (
                <div key={merchant.merchant_name} className="flex items-center justify-between gap-3 rounded-lg border border-ink/8 px-3 py-2.5">
                  <span className="font-medium text-sm">{merchant.merchant_name}</span>
                  <span className="font-semibold text-sm text-ink/80">{eur(merchant.outside_schijf_spend)}</span>
                </div>
              ))
            ) : (
              <EmptyItems label="No merchant totals yet." />
            )}
          </CardContent>
        </Card>
      </section>

      {/* Goal + Insight */}
      <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Goal Performance</CardTitle>
            {data.goal && (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${goalUsedPct < 75 ? "bg-mint/15 text-green-800" : goalUsedPct < 95 ? "bg-amber/20 text-amber-900" : "bg-coral/15 text-red-800"}`}>
                {goalUsedPct < 75 ? "On track" : goalUsedPct < 95 ? "Getting close" : "Over target"}
              </span>
            )}
          </CardHeader>
          <CardContent>
            {data.goal ? (
              <div className="grid gap-4">
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold">{pct(data.goal.budget_used_pct)}</p>
                  <p className="text-sm text-ink/55">used</p>
                </div>
                <Progress value={goalUsedPct} />
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg bg-cloud p-3">
                    <p className="text-xs text-ink/50 mb-1">Spent</p>
                    <p className="font-semibold">
                      {data.goal.metric === "OUTSIDE_SCHIJF_SPEND"
                        ? eur(data.goal.current_value)
                        : kcal(data.goal.current_value)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-cloud p-3">
                    <p className="text-xs text-ink/50 mb-1">Remaining</p>
                    <p className="font-semibold text-mint">
                      {data.goal.metric === "OUTSIDE_SCHIJF_SPEND"
                        ? eur(data.goal.remaining_value)
                        : kcal(data.goal.remaining_value)}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink/15 py-8 text-center">
                <Target size={24} className="text-ink/25" />
                <p className="text-sm text-ink/50">No active goal set</p>
                <p className="text-xs text-ink/40">Visit the Goals page to create one</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Insight</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="rounded-lg bg-cloud p-4">
              <p className="font-semibold text-sm text-ink">{data.insight.summary}</p>
            </div>
            <div className="grid gap-2 text-sm text-ink/70">
              {data.insight.positive_note && (
                <p className="flex gap-2">
                  <span className="shrink-0 text-mint">✓</span>
                  {data.insight.positive_note}
                </p>
              )}
              {data.insight.one_actionable_tip && (
                <p className="flex gap-2">
                  <span className="shrink-0 text-amber">→</span>
                  {data.insight.one_actionable_tip}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function KpiStrip({ icon, bg, label, value }: { icon: ReactNode; bg: string; label: string; value: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${bg}`}>{icon}</span>
        <div className="min-w-0">
          <p className="text-xs text-ink/50 truncate">{label}</p>
          <p className="font-bold text-sm leading-tight">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyItems({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center rounded-lg border border-dashed border-ink/15 py-8">
      <p className="text-sm text-ink/45">{label}</p>
    </div>
  );
}

function TopItems({ title, items, metric }: { title: string; items: MonthlySummaryPageItem[]; metric: "calories" | "spend" }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className="grid gap-1.5 rounded-lg border border-ink/8 px-3 py-2.5">
              <div className="flex items-start justify-between gap-3">
                <p className="font-medium text-sm leading-tight">{item.raw_name}</p>
                <ClassificationBadge value={item.classification} />
              </div>
              <p className="text-xs text-ink/55">
                {metric === "calories" ? kcal(item.calories_total) : eur(item.total_price)}
              </p>
            </div>
          ))
        ) : (
          <EmptyItems label="No items yet." />
        )}
      </CardContent>
    </Card>
  );
}

type MonthlySummaryPageItem = {
  id: number;
  raw_name: string;
  calories_total: number | null;
  total_price: number;
  classification: "IN_SCHIJF" | "DAGKEUZE" | "WEEKKEUZE" | "UNKNOWN" | "NON_FOOD";
};
