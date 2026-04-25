import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, RefreshCcw, ScanLine, Target } from "lucide-react";

import { CategoryPie } from "../components/charts/CategoryPie";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Progress } from "../components/ui/Progress";
import { api } from "../lib/api";
import { dateLabel, eur, kcal, pct } from "../lib/format";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const sync = useMutation({
    mutationFn: api.syncBunq,
    onSuccess: () => queryClient.invalidateQueries(),
  });
  const seed = useMutation({
    mutationFn: api.seedDemo,
    onSuccess: () => queryClient.invalidateQueries(),
  });

  if (isLoading) return <PageState text="Loading dashboard" />;
  if (error || !data) return <PageState text="Backend is not responding" action={<Button onClick={() => seed.mutate()}>Seed demo</Button>} />;

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-4 rounded-lg bg-ink p-6 text-white sm:flex-row sm:items-center">
        <div>
          <p className="text-sm text-white/65">{data.month}</p>
          <h1 className="mt-1 text-2xl font-semibold sm:text-3xl">Food spend with receipt-level context</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/scan">
            <Button className="bg-white text-ink hover:bg-white/90">
              <ScanLine size={18} />
              Scan receipt
            </Button>
          </Link>
          <Button variant="secondary" onClick={() => sync.mutate()} disabled={sync.isPending}>
            <RefreshCcw size={17} />
            Sync bunq
          </Button>
        </div>
      </section>

      {data.last_purchases.length === 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold">No confirmed receipts yet</p>
              <p className="text-sm text-ink/60">Use demo data or upload a receipt image to populate the dashboard.</p>
            </div>
            <Button onClick={() => seed.mutate()} disabled={seed.isPending}>
              Seed demo data
            </Button>
          </CardContent>
        </Card>
      )}

      <section className="grid gap-6 lg:grid-cols-3">
        <MetricCard title="Tracked calories MTD" value={kcal(data.calories.total)} detail={`${kcal(data.calories.outside_schijf)} Outside Schijf`} />
        <MetricCard title="Average daily tracked calories" value={kcal(data.avg_daily_tracked_calories)} detail={`${data.elapsed_days_in_month} elapsed days`} />
        <MetricCard title="Food spend MTD" value={eur(data.spend.total)} detail={`${eur(data.spend.outside_schijf)} Outside Schijf`} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Calories Split</CardTitle>
            <Badge>{kcal(data.calories.total)}</Badge>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.calories} valueType="kcal" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Spend Split</CardTitle>
            <Badge>{eur(data.spend.total)}</Badge>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.spend} valueType="eur" />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <Card>
          <CardHeader>
            <CardTitle>Goal Summary</CardTitle>
            <Target size={18} />
          </CardHeader>
          <CardContent>
            {data.goal ? (
              <div className="grid gap-4">
                <div>
                  <p className="text-sm text-ink/60">
                    {data.goal.metric === "OUTSIDE_SCHIJF_SPEND" ? "Outside-Schijf spend" : "Outside-Schijf calories"} budget used
                  </p>
                  <p className="mt-1 text-2xl font-semibold">{pct(data.goal.budget_used_pct)}</p>
                </div>
                <Progress value={data.goal.budget_used_pct * 100} />
                <p className="text-sm text-ink/70">
                  {data.goal.metric === "OUTSIDE_SCHIJF_SPEND"
                    ? `${eur(data.goal.current_value)} of ${eur(data.goal.target_value)}`
                    : `${kcal(data.goal.current_value)} of ${kcal(data.goal.target_value)}`}
                </p>
                <Link to="/goals" className="text-sm font-semibold text-ink underline-offset-4 hover:underline">
                  Adjust goal
                </Link>
              </div>
            ) : (
              <div className="grid gap-4">
                <p className="text-sm text-ink/65">Create a 10%, 20%, or 30% reduction goal for next month’s Outside Schijf budget.</p>
                <Link to="/goals">
                  <Button variant="secondary">Set goal</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Last Purchases</CardTitle>
            <Link to="/monthly" className="inline-flex items-center gap-1 text-sm font-semibold">
              Monthly <ArrowRight size={15} />
            </Link>
          </CardHeader>
          <CardContent className="grid gap-3">
            {data.last_purchases.length ? (
              data.last_purchases.map((purchase) => (
                <Link
                  key={purchase.receipt_id}
                  to={`/receipts/${purchase.receipt_id}/summary`}
                  className="grid gap-2 rounded-md border border-ink/10 p-3 transition hover:bg-cloud sm:grid-cols-[1fr_auto]"
                >
                  <div>
                    <p className="font-semibold">{purchase.merchant_name ?? "Unknown merchant"}</p>
                    <p className="text-sm text-ink/55">{dateLabel(purchase.date)}</p>
                  </div>
                  <div className="text-left sm:text-right">
                    <p className="font-semibold">{kcal(purchase.selected_calories)}</p>
                    <p className="text-sm text-ink/60">{eur(purchase.outside_schijf_spend)} Outside Schijf</p>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-sm text-ink/60">No purchases yet.</p>
            )}
          </CardContent>
        </Card>
      </section>

      {data.unmatched_food_transactions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Food Purchases Detected</CardTitle>
            <Link to="/transactions" className="text-sm font-semibold">
              View all
            </Link>
          </CardHeader>
          <CardContent className="grid gap-3">
            {data.unmatched_food_transactions.map((transaction) => (
              <div key={transaction.id} className="flex flex-col justify-between gap-3 rounded-md border border-ink/10 p-3 sm:flex-row sm:items-center">
                <div>
                  <p className="font-semibold">{transaction.merchant_name}</p>
                  <p className="text-sm text-ink/60">
                    {dateLabel(transaction.payment_date)} · {eur(Math.abs(transaction.amount))}
                  </p>
                </div>
                <Link to="/scan">
                  <Button variant="secondary">Scan receipt</Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MetricCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <Card>
      <CardContent>
        <p className="text-sm font-medium text-ink/60">{title}</p>
        <p className="mt-3 text-3xl font-semibold tracking-normal">{value}</p>
        <p className="mt-2 text-sm text-ink/65">{detail}</p>
      </CardContent>
    </Card>
  );
}

function PageState({ text, action }: { text: string; action?: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="flex min-h-48 flex-col items-center justify-center gap-4 text-center">
        <p className="font-semibold">{text}</p>
        {action}
      </CardContent>
    </Card>
  );
}

