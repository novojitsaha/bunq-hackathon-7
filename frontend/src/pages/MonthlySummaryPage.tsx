import { useQuery } from "@tanstack/react-query";

import { CategoryPie } from "../components/charts/CategoryPie";
import { ClassificationBadge } from "../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Progress } from "../components/ui/Progress";
import { api } from "../lib/api";
import { eur, kcal, pct } from "../lib/format";

export function MonthlySummaryPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["monthly"], queryFn: api.monthly });
  if (isLoading) return <p className="text-sm text-ink/60">Loading monthly summary</p>;
  if (error || !data) return <p className="text-sm text-red-700">Monthly summary unavailable.</p>;

  return (
    <div className="grid gap-6">
      <section>
        <p className="text-sm text-ink/55">
          {data.start_date} to {data.end_date}
        </p>
        <h1 className="text-2xl font-semibold">Monthly Summary</h1>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
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

      <section className="grid gap-6 lg:grid-cols-3">
        <TopItems title="Top Calories" items={data.top_outside_items_by_calories} metric="calories" />
        <TopItems title="Top Spend" items={data.top_outside_items_by_spend} metric="spend" />
        <Card>
          <CardHeader>
            <CardTitle>Merchants</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {data.top_merchants_by_outside_spend.length ? (
              data.top_merchants_by_outside_spend.map((merchant) => (
                <div key={merchant.merchant_name} className="flex justify-between gap-3 rounded-md border border-ink/10 p-3">
                  <span className="font-semibold">{merchant.merchant_name}</span>
                  <span>{eur(merchant.outside_schijf_spend)}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/60">No merchant totals yet.</p>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Goal Performance</CardTitle>
          </CardHeader>
          <CardContent>
            {data.goal ? (
              <div className="grid gap-4">
                <p className="text-2xl font-semibold">{pct(data.goal.budget_used_pct)}</p>
                <Progress value={data.goal.budget_used_pct * 100} />
                <p className="text-sm text-ink/65">
                  Remaining: {data.goal.metric === "OUTSIDE_SCHIJF_SPEND" ? eur(data.goal.remaining_value) : kcal(data.goal.remaining_value)}
                </p>
              </div>
            ) : (
              <p className="text-sm text-ink/60">No active goal.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Insight</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-ink/75">
            <p className="font-semibold text-ink">{data.insight.summary}</p>
            <p>{data.insight.positive_note}</p>
            <p>{data.insight.one_actionable_tip}</p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function TopItems({ title, items, metric }: { title: string; items: MonthlySummaryPageItem[]; metric: "calories" | "spend" }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className="grid gap-2 rounded-md border border-ink/10 p-3">
              <div className="flex items-start justify-between gap-3">
                <p className="font-semibold">{item.raw_name}</p>
                <ClassificationBadge value={item.classification} />
              </div>
              <p className="text-sm text-ink/60">{metric === "calories" ? kcal(item.calories_total) : eur(item.total_price)}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-ink/60">No items yet.</p>
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

