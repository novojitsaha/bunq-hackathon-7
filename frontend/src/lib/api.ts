import type { Dashboard, Goal, Monthly, Receipt, ReceiptItem, ReceiptSummary, Transaction } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<Dashboard>("/dashboard"),
  monthly: () => request<Monthly>("/monthly"),
  transactions: () => request<Transaction[]>("/transactions"),
  activeGoal: () => request<Goal | null>("/goals"),
  createGoal: (payload: { metric: Goal["metric"]; reduction_percent: number; start_mode?: string }) =>
    request<Goal>("/goals", { method: "POST", body: JSON.stringify(payload) }),
  uploadReceipt: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Receipt>("/receipts/upload", { method: "POST", body: form });
  },
  receipt: (id: string | number) => request<Receipt>(`/receipts/${id}`),
  updateReceiptItem: (receiptId: string | number, itemId: number, payload: Partial<ReceiptItem>) =>
    request<ReceiptItem>(`/receipts/${receiptId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  confirmReceipt: (receiptId: string | number) =>
    request<ReceiptSummary>(`/receipts/${receiptId}/confirm`, { method: "POST" }),
  receiptSummary: (receiptId: string | number) => request<ReceiptSummary>(`/receipts/${receiptId}/summary`),
  syncBunq: () => request<{ mode: string; created_transactions: number; message: string }>("/bunq/sync", { method: "POST" }),
  seedDemo: () => request<{ ok: boolean; message: string }>("/settings/seed-demo", { method: "POST" }),
  resetDemo: () => request<{ ok: boolean; message: string }>("/settings/reset-demo", { method: "POST" }),
};

