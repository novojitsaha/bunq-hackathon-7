import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, RotateCcw, Trash2 } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { api } from "../lib/api";

export function SettingsPage() {
  const queryClient = useQueryClient();
  const seed = useMutation({ mutationFn: api.seedDemo, onSuccess: () => queryClient.invalidateQueries() });
  const reset = useMutation({ mutationFn: api.resetDemo, onSuccess: () => queryClient.invalidateQueries() });

  return (
    <div className="mx-auto grid max-w-3xl gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Demo Data</CardTitle>
          <Database size={20} />
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button onClick={() => seed.mutate()} disabled={seed.isPending}>
              <RotateCcw size={17} />
              Seed demo
            </Button>
            <Button variant="danger" onClick={() => reset.mutate()} disabled={reset.isPending}>
              <Trash2 size={17} />
              Delete all demo data
            </Button>
          </div>
          {(seed.data || reset.data) && <p className="rounded-md bg-mint/15 p-3 text-sm text-green-900">{seed.data?.message ?? reset.data?.message}</p>}
          {(seed.error || reset.error) && <p className="rounded-md bg-coral/10 p-3 text-sm text-red-800">{seed.error?.message ?? reset.error?.message}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data Use</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-ink/70">
          This app estimates tracked calories and Schijf classifications from receipts and public/product data. It is not medical advice and may be incomplete.
        </CardContent>
      </Card>
    </div>
  );
}

