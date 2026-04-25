import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Flame, RefreshCcw, ScanLine, ShoppingCart, TrendingDown, CheckCircle2, AlertCircle } from "lucide-react";

import { CategoryPie } from "../components/charts/CategoryPie";
import { CategoryBar } from "../components/dashboard/CategoryBar";
import { ChallengeBar } from "../components/dashboard/ChallengeBar";
import { ProjectionTile } from "../components/dashboard/ProjectionTile";
import { WeeklyTrend } from "../components/dashboard/WeeklyTrend";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Progress } from "../components/ui/Progress";
import { api } from "../lib/api";
import { auth } from "../lib/auth";
import { dateLabel, eur, kcal } from "../lib/format";

const TIER_DOT: Record<string, string> = {
  in_schijf: "bg-mint",
  dagkeuze: "bg-amber",
  weekkeuze: "bg-coral",
};

function tierDotClass(label: string, outsideSpend: number) {
  const l = label.toLowerCase();
  if (outsideSpend === 0) return TIER_DOT.in_schijf;
  if (l.includes("dag")) return TIER_DOT.dagkeuze;
  return TIER_DOT.weekkeuze;
}

export function DashboardPage() {
  const queryClient = useQueryClient();
  const user = auth.get();

  const { data, isLoading, error } = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const { data: monthly } = useQuery({ queryKey: ["monthly"], queryFn: api.monthly });

  const sync = useMutation({ mutationFn: api.syncBunq, onSuccess: () => queryClient.invalidateQueries() });
  const seed = useMutation({ mutationFn: api.seedDemo, onSuccess: () => queryClient.invalidateQueries() });

  if (isLoading) return <PageState text="Loading dashboard" />;
  if (error || !data) return <PageState text="Backend is not responding" action={<Button onClick={() => seed.mutate()}>Seed demo data</Button>} />;

  const dailyAvgBuiten = data.elapsed_days_in_month > 0 ? data.spend.outside_schijf / data.elapsed_days_in_month : 0;
  const scanCoverage = data.last_purchases.length;
  const totalFoodTx = data.last_purchases.length + data.unmatched_food_transactions.length;
  const coveragePct = totalFoodTx > 0 ? Math.round((scanCoverage / totalFoodTx) * 100) : 0;
  const outsideItems = monthly?.top_outside_items_by_spend ?? [];

  return (
    <div className="grid gap-6">
      {/* Header banner */}
      <section className="relative overflow-hidden flex flex-col justify-between gap-4 rounded-xl bg-ink p-6 text-white sm:flex-row sm:items-center">
        {/* subtle grid pattern overlay */}
        <div className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative">
          <p className="text-xs font-medium uppercase tracking-widest text-white/40">{data.month}</p>
          <h1 className="mt-1.5 text-2xl font-semibold sm:text-3xl">
            {user ? `Hi ${user.name.split(" ")[0]} 👋` : "Food spend with receipt-level context"}
          </h1>
        </div>
        <div className="relative flex flex-wrap gap-2">
          <Link to="/scan">
            <Button className="bg-white text-ink hover:bg-white/90 shadow-sm">
              <ScanLine size={16} />
              Scan receipt
            </Button>
          </Link>
          <Button variant="secondary" className="border-white/20 bg-white/10 text-white hover:bg-white/20" onClick={() => sync.mutate()} disabled={sync.isPending}>
            <RefreshCcw size={15} className={sync.isPending ? "animate-spin" : ""} />
            Sync bunq
          </Button>
        </div>
      </section>

      {data.last_purchases.length === 0 && (
        <Card className="border-amber/30 bg-amber/5">
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="mt-0.5 shrink-0 text-amber" />
              <div>
                <p className="font-semibold text-ink">No confirmed receipts yet</p>
                <p className="text-sm text-ink/60">Use demo data or upload a receipt image to populate the dashboard.</p>
              </div>
            </div>
            <Button onClick={() => seed.mutate()} disabled={seed.isPending} className="shrink-0">Seed demo data</Button>
          </CardContent>
        </Card>
      )}

      {/* 3 KPI stat cards */}
      <section className="grid gap-4 lg:grid-cols-3">
        <MetricCard
          icon={<Flame size={18} className="text-coral" />}
          iconBg="bg-coral/10"
          title="Tracked calories MTD"
          value={kcal(data.calories.total)}
          detail={`${kcal(data.calories.outside_schijf)} avoidable buiten Schijf`}
        />
        <MetricCard
          icon={<TrendingDown size={18} className="text-amber" />}
          iconBg="bg-amber/10"
          title="Daily avg buiten-de-Schijf"
          value={`${eur(dailyAvgBuiten)} / day`}
          detail={`based on ${data.elapsed_days_in_month} days tracked`}
        />
        <MetricCard
          icon={<ShoppingCart size={18} className="text-mint" />}
          iconBg="bg-mint/10"
          title="Food spend MTD"
          value={eur(data.spend.total)}
          detail={`${eur(data.spend.outside_schijf)} buiten de Schijf`}
          highlight
        />
      </section>

      {/* Investment projection */}
      <ProjectionTile outsideSchijfMtd={data.spend.outside_schijf} />

      {/* Challenge progress bar */}
      <ChallengeBar
        goal={data.goal}
        daysElapsed={data.elapsed_days_in_month}
        daysInMonth={new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()}
      />

      {/* Weekly trend + Spend Split side by side */}
      <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <WeeklyTrend purchases={data.last_purchases} goal={data.goal} />

        <Card>
          <CardHeader>
            <CardTitle>Spend Split</CardTitle>
            <Badge className="bg-ink/8 text-ink/70">{eur(data.spend.total)}</Badge>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.spend} valueType="eur" />
          </CardContent>
        </Card>
      </section>

      {/* Category breakdown */}
      {outsideItems.length > 0 && <CategoryBar items={outsideItems} />}

      {/* Receipt coverage */}
      <Card>
        <CardHeader>
          <CardTitle>Receipt coverage</CardTitle>
          <span className="text-sm font-semibold text-ink/60">{coveragePct}% of food transactions</span>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="flex items-end gap-3">
            <p className="text-3xl font-semibold">{scanCoverage}</p>
            <p className="pb-1 text-sm text-ink/55">
              receipt{scanCoverage !== 1 ? "s" : ""} scanned
              {data.unmatched_food_transactions.length > 0 && (
                <> · <span className="text-amber font-medium">{data.unmatched_food_transactions.length} unscanned</span></>
              )}
            </p>
          </div>
          <Progress value={coveragePct} />
          {coveragePct === 0 && totalFoodTx === 0 && (
            <p className="text-xs text-ink/50">Scan your first receipt to start tracking.</p>
          )}
          {coveragePct > 0 && coveragePct < 60 && (
            <p className="flex items-center gap-1.5 text-xs font-medium text-coral">
              <AlertCircle size={13} />
              {data.unmatched_food_transactions.length} transactions unscanned — projections may be underestimated
            </p>
          )}
          {coveragePct >= 60 && (
            <p className="flex items-center gap-1.5 text-xs font-medium text-mint">
              <CheckCircle2 size={13} />
              Good coverage — your projections are reliable
            </p>
          )}
        </CardContent>
      </Card>

      {/* Last Purchases + Food Purchases Detected */}
      <section className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Last Purchases</CardTitle>
            <Link to="/monthly" className="inline-flex items-center gap-1 text-sm font-semibold text-ink/60 hover:text-ink transition-colors">
              Monthly <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardContent className="grid gap-2">
            {data.last_purchases.length ? (
              data.last_purchases.map((purchase) => (
                <Link
                  key={purchase.receipt_id}
                  to={`/receipts/${purchase.receipt_id}/summary`}
                  className="flex items-start gap-3 rounded-lg border border-ink/8 p-3 transition hover:bg-cloud hover:border-ink/15"
                >
                  <span
                    className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${tierDotClass(purchase.classification_label, purchase.outside_schijf_spend)}`}
                  />
                  <div className="flex flex-1 flex-col gap-0.5 sm:flex-row sm:justify-between">
                    <div>
                      <p className="font-semibold text-sm">{purchase.merchant_name ?? "Unknown merchant"}</p>
                      <p className="text-xs text-ink/50">{dateLabel(purchase.date)}</p>
                    </div>
                    <div className="text-left sm:text-right">
                      <p className="font-semibold text-sm">{kcal(purchase.selected_calories)}</p>
                      <p className="text-xs text-ink/55">{eur(purchase.outside_schijf_spend)} buiten</p>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink/15 py-8 text-center">
                <ShoppingCart size={24} className="text-ink/25" />
                <p className="text-sm text-ink/50">No purchases yet</p>
                <Link to="/scan">
                  <Button variant="secondary" className="mt-1 text-xs h-8 px-3">Scan first receipt</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Food Purchases Detected</CardTitle>
            <Link to="/transactions" className="text-sm font-semibold text-ink/60 hover:text-ink transition-colors">View all</Link>
          </CardHeader>
          <CardContent className="grid gap-2">
            {data.unmatched_food_transactions.length > 0 ? (
              data.unmatched_food_transactions.map((tx) => (
                <div key={tx.id} className="flex items-start gap-3 rounded-lg border border-ink/8 p-3">
                  <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-amber" />
                  <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-semibold text-sm">{tx.merchant_name}</p>
                      <p className="text-xs text-ink/55">
                        {dateLabel(tx.payment_date)} · {eur(Math.abs(tx.amount))}
                      </p>
                    </div>
                    <Link to="/scan">
                      <Button variant="secondary" className="h-8 px-3 text-xs">Scan receipt</Button>
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink/15 py-8 text-center">
                <CheckCircle2 size={24} className="text-mint/60" />
                <p className="text-sm text-ink/50">All purchases accounted for</p>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricCard({
  icon, iconBg, title, value, detail, highlight,
}: {
  icon: ReactNode;
  iconBg: string;
  title: string;
  value: string;
  detail: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? "border-mint/30 bg-gradient-to-br from-mint/8 to-mint/3" : ""}>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-wide text-ink/50">{title}</p>
          <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconBg}`}>{icon}</span>
        </div>
        <p className={`text-2xl font-bold tracking-tight ${highlight ? "text-mint" : "text-ink"}`}>{value}</p>
        <p className="text-xs text-ink/55 border-t border-ink/6 pt-2">{detail}</p>
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
