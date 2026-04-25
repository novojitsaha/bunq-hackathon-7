import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ScanLine } from "lucide-react";

import { CategoryPie } from "../components/charts/CategoryPie";
import { ClassificationBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { api } from "../lib/api";
import { dateLabel, eur, kcal } from "../lib/format";

export function InstantSummaryPage() {
  const { id } = useParams();
  const { data, isLoading, error } = useQuery({ queryKey: ["receipt-summary", id], queryFn: () => api.receiptSummary(id!), enabled: Boolean(id) });

  if (isLoading) return <p className="text-sm text-ink/60">Loading summary</p>;
  if (error || !data) return <p className="text-sm text-red-700">Summary not found.</p>;

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm text-ink/55">{dateLabel(data.purchase_date)}</p>
          <h1 className="text-2xl font-semibold">{data.merchant_name ?? "Receipt summary"}</h1>
          <p className="mt-1 text-sm text-ink/65">
            {kcal(data.selected_calories)} · {eur(data.selected_spend)}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/">
            <Button variant="secondary">
              <ArrowLeft size={17} />
              Dashboard
            </Button>
          </Link>
          <Link to="/scan">
            <Button>
              <ScanLine size={17} />
              Scan another
            </Button>
          </Link>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Calories</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.calorie_split} valueType="kcal" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryPie split={data.spend_split} valueType="eur" />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Outside-Schijf Contributors</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {data.top_outside_items.length ? (
              data.top_outside_items.map((item) => (
                <div key={item.id} className="flex items-center justify-between gap-4 rounded-md border border-ink/10 p-3">
                  <div>
                    <p className="font-semibold">{item.raw_name}</p>
                    <p className="text-sm text-ink/55">{eur(item.total_price)} · {kcal(item.calories_total)}</p>
                  </div>
                  <ClassificationBadge value={item.classification} />
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/60">No outside-Schijf items selected.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>bunq Link</CardTitle>
          </CardHeader>
          <CardContent>
            {data.linked_transaction ? (
              <div>
                <p className="text-2xl font-semibold">{eur(Math.abs(data.linked_transaction.amount))}</p>
                <p className="mt-1 text-sm text-ink/60">{data.linked_transaction.merchant_name}</p>
              </div>
            ) : (
              <p className="text-sm text-ink/60">No matching transaction linked.</p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

