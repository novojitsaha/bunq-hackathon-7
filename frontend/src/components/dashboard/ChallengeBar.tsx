import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { Progress } from "../ui/Progress";
import { api } from "../../lib/api";
import type { Goal } from "../../lib/types";
import { eur, pct } from "../../lib/format";

function statusInfo(usedPct: number) {
  if (usedPct < 0.75) return { label: "✅ On track", color: "text-mint" };
  if (usedPct < 0.95) return { label: "⚠️ Getting close", color: "text-amber" };
  return { label: "🔴 Over target", color: "text-coral" };
}

export function ChallengeBar({ goal, daysElapsed, daysInMonth }: { goal: Goal | null; daysElapsed: number; daysInMonth: number }) {
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: (reduction_percent: number) =>
      api.createGoal({ metric: "OUTSIDE_SCHIJF_SPEND", reduction_percent }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  if (!goal) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>🎯 Start a savings challenge</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <p className="text-sm text-ink/60">
            Commit to reducing your buiten-de-Schijf spend next month. Lock €20 as your stake.
          </p>
          <div className="flex flex-wrap gap-2">
            {[10, 20, 30].map((pctVal) => (
              <Button
                key={pctVal}
                variant="secondary"
                disabled={create.isPending}
                onClick={() => create.mutate(pctVal)}
              >
                Reduce {pctVal}%
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const { label, color } = statusInfo(goal.budget_used_pct);
  const daysLeft = daysInMonth - daysElapsed;
  const pace = daysElapsed > 0 ? (goal.current_value / daysElapsed) * daysInMonth : 0;
  const isSpend = goal.metric === "OUTSIDE_SCHIJF_SPEND";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Savings challenge</CardTitle>
        <span className={`text-sm font-semibold ${color}`}>{label}</span>
      </CardHeader>
      <CardContent className="grid gap-3">
        <p className="text-sm text-ink/70">
          {isSpend ? eur(goal.current_value) : `${Math.round(goal.current_value).toLocaleString()} kcal`} spent of{" "}
          <strong>{isSpend ? eur(goal.target_value) : `${Math.round(goal.target_value).toLocaleString()} kcal`}</strong> target
        </p>
        <Progress value={Math.min(goal.budget_used_pct * 100, 100)} />
        <p className="text-xs text-ink/50">
          {daysLeft} days left · At this pace:{" "}
          <strong className="text-ink">{isSpend ? eur(pace) : `${Math.round(pace).toLocaleString()} kcal`}</strong> by end of month ·
          {" "}Reduce {goal.reduction_percent}% goal · <span className="text-amber font-semibold">€20 stake locked 🔒</span>
        </p>
      </CardContent>
    </Card>
  );
}
