import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Save } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { ClassificationBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { api } from "../lib/api";
import { classificationLabel, eur, kcal } from "../lib/format";
import type { Classification, ReceiptItem } from "../lib/types";

const classifications: Classification[] = ["IN_SCHIJF", "DAGKEUZE", "WEEKKEUZE", "UNKNOWN", "NON_FOOD"];

export function ReceiptReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const queryKey = ["receipt", id];
  const { data, isLoading, error } = useQuery({ queryKey, queryFn: () => api.receipt(id!), enabled: Boolean(id) });
  const update = useMutation({
    mutationFn: ({ itemId, payload }: { itemId: number; payload: Partial<ReceiptItem> }) => api.updateReceiptItem(id!, itemId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });
  const confirm = useMutation({
    mutationFn: () => api.confirmReceipt(id!),
    onSuccess: () => {
      queryClient.invalidateQueries();
      navigate(`/receipts/${id}/summary`);
    },
  });

  if (isLoading) return <p className="text-sm text-ink/60">Loading receipt</p>;
  if (error || !data) return <p className="text-sm text-red-700">Receipt not found.</p>;

  const selectedCalories = data.items.filter((item) => item.selected_for_user && item.is_food).reduce((sum, item) => sum + (item.calories_total ?? 0), 0);
  const selectedSpend = data.items.filter((item) => item.selected_for_user && item.is_food).reduce((sum, item) => sum + item.total_price, 0);

  return (
    <div className="grid gap-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm text-ink/55">Receipt #{data.id}</p>
          <h1 className="text-2xl font-semibold">{data.merchant_name ?? "Unknown merchant"}</h1>
          <p className="mt-1 text-sm text-ink/65">
            Selected: {kcal(selectedCalories)} · {eur(selectedSpend)}
          </p>
        </div>
        <Button onClick={() => confirm.mutate()} disabled={confirm.isPending}>
          <CheckCircle2 size={18} />
          Confirm receipt
        </Button>
      </section>

      {data.validation_notes && <p className="rounded-md bg-amber/15 p-3 text-sm text-amber-900">{data.validation_notes}</p>}

      <Card className="hidden overflow-hidden lg:block">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-cloud text-left text-ink/60">
            <tr>
              <th className="px-4 py-3">Selected</th>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3">Quantity</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Calories</th>
              <th className="px-4 py-3">Classification</th>
              <th className="px-4 py-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id} className="border-t border-ink/10">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={item.selected_for_user}
                    onChange={(event) => update.mutate({ itemId: item.id, payload: { selected_for_user: event.target.checked } })}
                    className="h-4 w-4 accent-ink"
                  />
                </td>
                <td className="px-4 py-3">
                  <p className="font-semibold">{item.raw_name}</p>
                  <p className="text-ink/55">{item.normalized_name}</p>
                </td>
                <td className="px-4 py-3">{item.quantity} {item.unit ?? ""}</td>
                <td className="px-4 py-3">{eur(item.total_price)}</td>
                <td className="px-4 py-3">{kcal(item.calories_total)}</td>
                <td className="px-4 py-3">
                  <select
                    value={item.classification}
                    onChange={(event) => update.mutate({ itemId: item.id, payload: { classification: event.target.value as Classification } })}
                    className="rounded-md border border-ink/15 bg-white px-2 py-1"
                  >
                    {classifications.map((classification) => (
                      <option key={classification} value={classification}>
                        {classificationLabel(classification)}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">{Math.round(item.confidence * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="grid gap-4 lg:hidden">
        {data.items.map((item) => (
          <MobileItemCard key={item.id} item={item} onUpdate={(payload) => update.mutate({ itemId: item.id, payload })} />
        ))}
      </div>

      {update.isPending && (
        <div className="fixed bottom-5 left-1/2 z-40 -translate-x-1/2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-panel">
          <Save className="mr-2 inline" size={15} />
          Saving
        </div>
      )}
    </div>
  );
}

function MobileItemCard({ item, onUpdate }: { item: ReceiptItem; onUpdate: (payload: Partial<ReceiptItem>) => void }) {
  return (
    <Card>
      <CardContent className="grid gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold">{item.raw_name}</p>
            <p className="text-sm text-ink/55">{item.normalized_name}</p>
          </div>
          <ClassificationBadge value={item.classification} />
        </div>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <p className="text-ink/50">Price</p>
            <p className="font-semibold">{eur(item.total_price)}</p>
          </div>
          <div>
            <p className="text-ink/50">Calories</p>
            <p className="font-semibold">{kcal(item.calories_total)}</p>
          </div>
          <div>
            <p className="text-ink/50">Confidence</p>
            <p className="font-semibold">{Math.round(item.confidence * 100)}%</p>
          </div>
        </div>
        <div className="flex items-center justify-between gap-3">
          <label className="inline-flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={item.selected_for_user}
              onChange={(event) => onUpdate({ selected_for_user: event.target.checked })}
              className="h-4 w-4 accent-ink"
            />
            Selected
          </label>
          <select
            value={item.classification}
            onChange={(event) => onUpdate({ classification: event.target.value as Classification })}
            className="rounded-md border border-ink/15 bg-white px-2 py-1 text-sm"
          >
            {classifications.map((classification) => (
              <option key={classification} value={classification}>
                {classificationLabel(classification)}
              </option>
            ))}
          </select>
        </div>
      </CardContent>
    </Card>
  );
}

