import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw, ScanLine } from "lucide-react";

import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { api } from "../lib/api";
import { dateLabel, eur } from "../lib/format";

export function TransactionsPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading, error } = useQuery({ queryKey: ["transactions"], queryFn: api.transactions });
  const sync = useMutation({ mutationFn: api.syncBunq, onSuccess: () => queryClient.invalidateQueries() });

  if (isLoading) return <p className="text-sm text-ink/60">Loading transactions</p>;
  if (error) return <p className="text-sm text-red-700">Transactions unavailable.</p>;

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm text-ink/55">bunq sandbox</p>
          <h1 className="text-2xl font-semibold">Transactions</h1>
        </div>
        <Button onClick={() => sync.mutate()} disabled={sync.isPending}>
          <RefreshCcw size={17} />
          Sync
        </Button>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {data.length ? (
            data.map((transaction) => (
              <div key={transaction.id} className="grid gap-3 rounded-md border border-ink/10 p-3 sm:grid-cols-[1fr_auto_auto] sm:items-center">
                <div>
                  <p className="font-semibold">{transaction.merchant_name}</p>
                  <p className="text-sm text-ink/55">{dateLabel(transaction.payment_date)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {transaction.is_food_candidate && <Badge className="bg-mint/15 text-green-800">{transaction.merchant_category}</Badge>}
                  {transaction.matched_receipt_id && <Badge>linked</Badge>}
                </div>
                <div className="flex items-center justify-between gap-3 sm:justify-end">
                  <span className="font-semibold">{eur(Math.abs(transaction.amount))}</span>
                  {transaction.is_food_candidate && !transaction.matched_receipt_id && (
                    <Link to="/scan">
                      <Button variant="secondary">
                        <ScanLine size={16} />
                        Scan
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-ink/60">No transactions yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

