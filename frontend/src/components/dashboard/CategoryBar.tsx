import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import type { ReceiptItem } from "../../lib/types";
import { eur } from "../../lib/format";

const CATEGORY_RULES: { label: string; keywords: string[]; tier: "weekkeuze" | "dagkeuze" }[] = [
  { label: "Drinks (sugary)", keywords: ["cola", "fanta", "pepsi", "red bull", "energy", "limonade", "soda", "juice", "sap", "drink"], tier: "weekkeuze" },
  { label: "Fast food", keywords: ["burger", "pizza", "fries", "kebab", "mc", "kfc", "domino", "wrap"], tier: "weekkeuze" },
  { label: "Snacks", keywords: ["doritos", "chips", "crisps", "popcorn", "snack", "noten", "crackers", "borrelhapje"], tier: "weekkeuze" },
  { label: "Confectionery", keywords: ["chocolate", "chocolade", "candy", "snoep", "ice cream", "ijs", "hagelslag", "stroopwafel", "koek", "cookie", "biscuit"], tier: "weekkeuze" },
  { label: "Processed meals", keywords: ["ready meal", "pasta meal", "noodles", "maaltijd", "soep blik", "magnetron"], tier: "dagkeuze" },
  { label: "Dairy alternatives", keywords: ["almond milk", "oat milk", "soy milk", "haver", "amandel", "soja"], tier: "dagkeuze" },
];

const TIER_COLORS = { weekkeuze: "#ef7667", dagkeuze: "#e9aa3f" };

function categorise(name: string): { label: string; tier: "weekkeuze" | "dagkeuze" } {
  const lower = name.toLowerCase();
  for (const rule of CATEGORY_RULES) {
    if (rule.keywords.some((k) => lower.includes(k))) return { label: rule.label, tier: rule.tier };
  }
  return { label: "Other", tier: "weekkeuze" };
}

function buildCategories(items: ReceiptItem[]) {
  const map = new Map<string, { amount: number; tier: "weekkeuze" | "dagkeuze" }>();
  for (const item of items) {
    if (item.total_price === 0) continue;
    const { label, tier } = categorise(item.normalized_name || item.raw_name);
    const existing = map.get(label) ?? { amount: 0, tier };
    existing.amount += item.total_price;
    map.set(label, existing);
  }
  return [...map.entries()]
    .map(([label, { amount, tier }]) => ({ label, amount, tier }))
    .filter((c) => c.amount > 0)
    .sort((a, b) => b.amount - a.amount);
}

export function CategoryBar({ items }: { items: ReceiptItem[] }) {
  const data = buildCategories(items);

  if (!data.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spend by category</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-ink/20 text-sm text-ink/50">
            No buiten-de-Schijf items yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Where your buiten-de-Schijf spend goes</CardTitle>
        <div className="flex items-center gap-3 text-xs text-ink/50">
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-coral" />Weekkeuze</span>
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-amber" />Dagkeuze</span>
        </div>
      </CardHeader>
      <CardContent>
        <div style={{ height: Math.max(160, data.length * 44) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 0, right: 56, left: 0, bottom: 0 }}>
              <XAxis type="number" tickFormatter={(v) => `€${v}`} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 12 }} width={110} />
              <Tooltip formatter={(v: number) => eur(v)} />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {data.map((entry) => (
                  <Cell key={entry.label} fill={TIER_COLORS[entry.tier]} />
                ))}
                <LabelList dataKey="amount" position="right" formatter={(v: number) => eur(v)} style={{ fontSize: 11, fill: "#16201d" }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
