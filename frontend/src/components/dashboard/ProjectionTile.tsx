import { useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip } from "recharts";

import { Card, CardContent } from "../ui/Card";
import { eur } from "../../lib/format";

function compound(monthly: number, years: number, rate = 0.05) {
  const r = rate / 12;
  const n = years * 12;
  return monthly * ((1 + r) ** n - 1) / r;
}

function sparkline(monthly: number, years: number, rate = 0.05) {
  const r = rate / 12;
  return Array.from({ length: years * 12 }, (_, i) => ({
    m: i + 1,
    v: monthly * ((1 + r) ** (i + 1) - 1) / r,
  }));
}

const HORIZONS = [
  { label: "1 yr", years: 1 },
  { label: "3 yr", years: 3 },
  { label: "5 yr", years: 5 },
] as const;

export function ProjectionTile({ outsideSchijfMtd }: { outsideSchijfMtd: number }) {
  const [horizonIdx, setHorizonIdx] = useState(0);
  const { years } = HORIZONS[horizonIdx];
  const projected = compound(outsideSchijfMtd, years);
  const data = sparkline(outsideSchijfMtd, years);

  return (
    <Card className="overflow-hidden border-mint/30 bg-gradient-to-br from-ink to-ink/90 text-white">
      <CardContent className="p-0">
        <div className="grid lg:grid-cols-[1fr_1.6fr]">
          {/* Left — numbers */}
          <div className="flex flex-col justify-between p-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-white/40">
                💶 What your buiten-de-Schijf spend could become
              </p>
              <div className="mt-4 flex gap-2">
                {HORIZONS.map((h, i) => (
                  <button
                    key={h.label}
                    onClick={() => setHorizonIdx(i)}
                    className={[
                      "rounded-full px-3 py-1 text-xs font-semibold transition",
                      i === horizonIdx
                        ? "bg-mint text-white"
                        : "border border-white/15 text-white/50 hover:border-white/30 hover:text-white/80",
                    ].join(" ")}
                  >
                    {h.label}
                  </button>
                ))}
              </div>
              <p className="mt-5 text-4xl font-semibold text-mint">{eur(projected)}</p>
              <p className="mt-1 text-sm text-white/50">
                {eur(outsideSchijfMtd)}/month invested over {years} year{years > 1 ? "s" : ""}
              </p>
            </div>
            <p className="mt-6 text-[11px] text-white/30 italic">5% real return, illustrative only</p>
          </div>

          {/* Right — sparkline */}
          <div className="relative flex items-end">
            <div className="absolute inset-x-0 top-4 px-4">
              <p className="text-right text-xs text-white/25">Growth curve</p>
            </div>
            <div className="h-36 w-full lg:h-full lg:min-h-[160px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 16, right: 0, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="mintGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#54b689" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#54b689" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke="#54b689"
                    strokeWidth={2}
                    fill="url(#mintGrad)"
                    dot={false}
                  />
                  <Tooltip
                    content={({ active, payload }) =>
                      active && payload?.length ? (
                        <div className="rounded-md bg-white px-2 py-1 text-xs font-semibold text-ink shadow">
                          {eur(payload[0].value as number)}
                        </div>
                      ) : null
                    }
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
