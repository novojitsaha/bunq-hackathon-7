import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SplitMetrics } from "../../lib/types";
import { eur, kcal } from "../../lib/format";

const COLORS = {
  Schijf: "#54b689",
  Dagkeuze: "#e9aa3f",
  Weekkeuze: "#ef7667",
  Check: "#8f5c7e",
};

const PLACEHOLDER = [
  { name: "Schijf", value: 60 },
  { name: "Dagkeuze", value: 25 },
  { name: "Weekkeuze", value: 15 },
];

export function CategoryPie({ split, valueType }: { split: SplitMetrics; valueType: "kcal" | "eur" }) {
  const data = [
    { name: "Schijf", value: split.in_schijf },
    { name: "Dagkeuze", value: split.dagkeuze },
    { name: "Weekkeuze", value: split.weekkeuze },
    { name: "Check", value: split.unknown },
  ].filter((item) => item.value > 0);

  const isEmpty = data.length === 0;

  return (
    <div className="grid gap-4 sm:grid-cols-[minmax(160px,1fr)_auto]">
      <div className="relative h-44 min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            {isEmpty ? (
              <Pie
                data={PLACEHOLDER}
                dataKey="value"
                nameKey="name"
                innerRadius={48}
                outerRadius={76}
                paddingAngle={2}
                isAnimationActive={false}
              >
                {PLACEHOLDER.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} fillOpacity={0.18} stroke="none" />
                ))}
              </Pie>
            ) : (
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={48}
                outerRadius={76}
                paddingAngle={2}
                label={({ name, value, percent }) =>
                  percent > 0.08 ? (valueType === "eur" ? eur(value) : kcal(value)) : ""
                }
                labelLine={{ stroke: "rgba(22,32,29,0.2)", strokeWidth: 1 }}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
                ))}
              </Pie>
            )}
            {!isEmpty && (
              <Tooltip formatter={(value: number) => (valueType === "kcal" ? kcal(value) : eur(value))} />
            )}
          </PieChart>
        </ResponsiveContainer>
        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-center text-xs font-medium text-ink/35 leading-snug px-2">No data<br />yet</p>
          </div>
        )}
      </div>

      <div className="grid content-center gap-2 text-sm">
        {isEmpty ? (
          <>
            {(["Schijf", "Dagkeuze", "Weekkeuze"] as const).map((name) => (
              <div key={name} className="flex min-w-36 items-center justify-between gap-4 opacity-35">
                <span className="flex items-center gap-2 text-ink/70">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLORS[name] }} />
                  {name}
                </span>
                <strong className="text-ink/40">—</strong>
              </div>
            ))}
          </>
        ) : (
          data.map((item) => (
            <div key={item.name} className="flex min-w-36 items-center justify-between gap-4">
              <span className="flex items-center gap-2 text-ink/70">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLORS[item.name as keyof typeof COLORS] }} />
                {item.name}
              </span>
              <strong>{valueType === "kcal" ? kcal(item.value) : eur(item.value)}</strong>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
