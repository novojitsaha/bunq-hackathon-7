import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SplitMetrics } from "../../lib/types";
import { eur, kcal } from "../../lib/format";

const COLORS = {
  Schijf: "#54b689",
  Dagkeuze: "#e9aa3f",
  Weekkeuze: "#ef7667",
  Check: "#8f5c7e",
};

export function CategoryPie({ split, valueType }: { split: SplitMetrics; valueType: "kcal" | "eur" }) {
  const data = [
    { name: "Schijf", value: split.in_schijf },
    { name: "Dagkeuze", value: split.dagkeuze },
    { name: "Weekkeuze", value: split.weekkeuze },
    { name: "Check", value: split.unknown },
  ].filter((item) => item.value > 0);

  if (!data.length) {
    return <div className="flex h-40 items-center justify-center rounded-md border border-dashed border-ink/20 text-sm text-ink/60">No tracked data</div>;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-[minmax(160px,1fr)_auto]">
      <div className="h-44 min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={76} paddingAngle={2}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => (valueType === "kcal" ? kcal(value) : eur(value))} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="grid content-center gap-2 text-sm">
        {data.map((item) => (
          <div key={item.name} className="flex min-w-36 items-center justify-between gap-4">
            <span className="flex items-center gap-2 text-ink/70">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLORS[item.name as keyof typeof COLORS] }} />
              {item.name}
            </span>
            <strong>{valueType === "kcal" ? kcal(item.value) : eur(item.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

