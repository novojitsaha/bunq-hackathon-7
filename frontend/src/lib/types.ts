export type Classification = "IN_SCHIJF" | "DAGKEUZE" | "WEEKKEUZE" | "UNKNOWN" | "NON_FOOD";

export type SplitMetrics = {
  in_schijf: number;
  dagkeuze: number;
  weekkeuze: number;
  outside_schijf: number;
  unknown: number;
  total: number;
};

export type ReceiptItem = {
  id: number;
  receipt_id: number;
  raw_name: string;
  normalized_name: string;
  quantity: number;
  unit: string | null;
  total_price: number;
  calories_total: number | null;
  classification: Classification;
  confidence: number;
  source: string;
  selected_for_user: boolean;
  is_food: boolean;
  user_override: boolean;
};

export type Receipt = {
  id: number;
  status: "PROCESSING" | "READY" | "CONFIRMED" | "FAILED";
  merchant_name: string | null;
  purchase_date: string | null;
  upload_filename: string | null;
  total_amount: number | null;
  currency: string;
  linked_transaction_id: number | null;
  validation_notes: string | null;
  items: ReceiptItem[];
};

export type Transaction = {
  id: number;
  bunq_payment_id: string | null;
  merchant_name: string;
  description: string | null;
  amount: number;
  currency: string;
  payment_date: string;
  direction: "INCOMING" | "OUTGOING";
  is_food_candidate: boolean;
  food_confidence: number;
  merchant_category: "supermarket" | "restaurant" | "bar" | "delivery" | "unknown";
  matched_receipt_id: number | null;
};

export type Goal = {
  id: number;
  metric: "OUTSIDE_SCHIJF_CALORIES" | "OUTSIDE_SCHIJF_SPEND";
  reduction_percent: number;
  baseline_value: number;
  target_value: number;
  start_date: string;
  active: boolean;
  current_value: number;
  remaining_value: number;
  budget_used_pct: number;
};

export type PurchaseSummary = {
  receipt_id: number;
  merchant_name: string | null;
  date: string | null;
  selected_calories: number;
  outside_schijf_spend: number;
  outside_schijf_calories: number;
  classification_label: string;
};

export type Dashboard = {
  month: string;
  elapsed_days_in_month: number;
  calories: SplitMetrics;
  spend: SplitMetrics;
  avg_daily_tracked_calories: number;
  goal: Goal | null;
  last_purchases: PurchaseSummary[];
  unmatched_food_transactions: Transaction[];
};

export type ReceiptSummary = {
  receipt_id: number;
  merchant_name: string | null;
  purchase_date: string | null;
  total_amount: number | null;
  selected_spend: number;
  selected_calories: number;
  spend_split: SplitMetrics;
  calorie_split: SplitMetrics;
  top_outside_items: ReceiptItem[];
  linked_transaction: Transaction | null;
};

export type Monthly = {
  month: string;
  start_date: string;
  end_date: string;
  calories: SplitMetrics;
  spend: SplitMetrics;
  avg_daily_tracked_calories: number;
  top_outside_items_by_calories: ReceiptItem[];
  top_outside_items_by_spend: ReceiptItem[];
  top_merchants_by_outside_spend: { merchant_name: string; outside_schijf_spend: number }[];
  goal: Goal | null;
  insight: {
    summary: string;
    positive_note: string;
    one_actionable_tip: string;
    risk_level: "on_track" | "watch" | "over_target";
  };
};

