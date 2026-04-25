import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import type { Goal, PurchaseSummary } from "../../lib/types";
import { eur } from "../../lib/format";

function getWeekLabel(dateStr: string) {
  const d = new Date(dateStr);
  const day = d.getDate();
  const month = d.toLocaleString("en-NL", { month: "short" });
  const week = Math.ceil(day / 7);
  return `W${week} ${month}`;
}

function buildWeeklyData(purchases: PurchaseSummary[]) {
  const buckets = new Map<string, { outside: number; order: number }>();
  for (const p of purchases) {
    if (!p.date) continue;
    const label = getWeekLabel(p.date);
    const d = new Date(p.date);
    const order = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + Math.ceil(d.getDate() / 7);
    const existing = buckets.get(label) ?? { outside: 0, order };
    existing.outside += p.outside_schijf_spend;
    buckets.set(label, existing);
  }
  return [...buckets.entries()]
    .sort((a, b) => a[1].order - b[1].order)
    .map(([label, { outside }], i, arr) => ({
      week: label,
      outside,
      rolling: arr.slice(Math.max(0, i - 3), i + 1).reduce((s, [, v]) => s + v.outside, 0) / Math.min(i + 1, 4),
    }));
}

export function WeeklyTrend({ purchases, goal }: { purchases: PurchaseSummary[]; goal: Goal | null }) {
  const data = buildWeeklyData(purchases);

  if (data.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Buiten-de-Schijf trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-ink/20 text-sm text-ink/50">
            📈 Trend line unlocks after 2 weeks of scanning. Keep going!
          </div>
        </CardContent>
      </Card>
    );
  }

  const targetWeekly =
    goal && goal.metric === "OUTSIDE_SCHIJF_SPEND"
      ? (goal.target_value / 4)
      : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Buiten-de-Schijf trend</CardTitle>
        <div className="flex items-center gap-4 text-xs text-ink/50">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 border-t-2 border-dashed border-coral" />
            Weekly actual
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 bg-coral" />
            4-wk avg
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(22,32,29,0.06)" />
              <XAxis dataKey="week" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `€${v}`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => eur(v)} />
              {targetWeekly !== null && (
                <ReferenceLine
                  y={targetWeekly}
                  stroke="#e9aa3f"
                  strokeDasharray="5 3"
                  label={{ value: `Target €${targetWeekly.toFixed(0)}/wk`, position: "insideBottomRight", fontSize: 10, fill: "#e9aa3f" }}
                />
              )}
              <Line type="monotone" dataKey="outside" stroke="#ef7667" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 4, fill: "#ef7667" }} name="Weekly actual" />
              <Line type="monotone" dataKey="rolling" stroke="#ef7667" strokeWidth={3} dot={false} name="4-wk avg" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
