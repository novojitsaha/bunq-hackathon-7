import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Target } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Progress } from "../components/ui/Progress";
import { api } from "../lib/api";
import { eur, kcal, pct } from "../lib/format";
import type { Goal } from "../lib/types";

export function GoalSettingsPage() {
  const queryClient = useQueryClient();
  const [metric, setMetric] = useState<Goal["metric"]>("OUTSIDE_SCHIJF_SPEND");
  const [reduction, setReduction] = useState(20);
  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: api.activeGoal });
  const create = useMutation({
    mutationFn: () => api.createGoal({ metric, reduction_percent: reduction, start_mode: "demo-immediate" }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    create.mutate();
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Set Goal</CardTitle>
          <Target size={20} />
        </CardHeader>
        <CardContent>
          <form className="grid gap-5" onSubmit={submit}>
            <label className="grid gap-2">
              <span className="text-sm font-semibold">Metric</span>
              <select value={metric} onChange={(event) => setMetric(event.target.value as Goal["metric"])} className="rounded-md border border-ink/15 bg-white px-3 py-2">
                <option value="OUTSIDE_SCHIJF_SPEND">Outside-Schijf spend</option>
                <option value="OUTSIDE_SCHIJF_CALORIES">Outside-Schijf calories</option>
              </select>
            </label>
            <div className="grid gap-2">
              <span className="text-sm font-semibold">Reduction</span>
              <div className="grid grid-cols-3 gap-2">
                {[10, 20, 30].map((value) => (
                  <button
                    type="button"
                    key={value}
                    onClick={() => setReduction(value)}
                    className={`rounded-md border px-4 py-3 text-sm font-semibold ${reduction === value ? "border-ink bg-ink text-white" : "border-ink/15 bg-white"}`}
                  >
                    {value}%
                  </button>
                ))}
              </div>
            </div>
            <Button type="submit" disabled={create.isPending}>
              Save goal
            </Button>
            {create.error && <p className="text-sm text-red-700">{create.error.message}</p>}
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Active Goal</CardTitle>
        </CardHeader>
        <CardContent>
          {goal ? (
            <div className="grid gap-4">
              <p className="text-sm text-ink/60">
                {goal.reduction_percent}% reduction · {goal.metric === "OUTSIDE_SCHIJF_SPEND" ? "Spend" : "Calories"}
              </p>
              <p className="text-3xl font-semibold">
                {goal.metric === "OUTSIDE_SCHIJF_SPEND" ? eur(goal.current_value) : kcal(goal.current_value)}
              </p>
              <Progress value={goal.budget_used_pct * 100} />
              <p className="text-sm text-ink/65">
                {pct(goal.budget_used_pct)} used · target {goal.metric === "OUTSIDE_SCHIJF_SPEND" ? eur(goal.target_value) : kcal(goal.target_value)}
              </p>
            </div>
          ) : (
            <p className="text-sm text-ink/60">No active goal.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

