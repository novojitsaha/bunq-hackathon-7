from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Classification, GoalMetric, MerchantCategory, ReceiptStatus, TransactionDirection


class SplitMetrics(BaseModel):
    in_schijf: float = 0.0
    dagkeuze: float = 0.0
    weekkeuze: float = 0.0
    outside_schijf: float = 0.0
    unknown: float = 0.0
    total: float = 0.0


class ReceiptItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_id: int
    raw_name: str
    normalized_name: str
    quantity: float
    unit: str | None
    total_price: float
    calories_total: float | None
    classification: Classification
    confidence: float
    source: str
    selected_for_user: bool
    is_food: bool
    user_override: bool


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ReceiptStatus
    merchant_name: str | None
    purchase_date: datetime | None
    upload_filename: str | None
    total_amount: float | None
    currency: str
    linked_transaction_id: int | None
    validation_notes: str | None
    items: list[ReceiptItemRead] = []


class ReceiptItemUpdate(BaseModel):
    selected_for_user: bool | None = None
    is_food: bool | None = None
    normalized_name: str | None = None
    quantity: float | None = Field(default=None, ge=0)
    total_price: float | None = Field(default=None, ge=0)
    calories_total: float | None = Field(default=None, ge=0)
    classification: Classification | None = None


class ReceiptSummary(BaseModel):
    receipt_id: int
    merchant_name: str | None
    purchase_date: datetime | None
    total_amount: float | None
    selected_spend: float
    selected_calories: float
    spend_split: SplitMetrics
    calorie_split: SplitMetrics
    top_outside_items: list[ReceiptItemRead]
    linked_transaction: "TransactionRead | None" = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bunq_payment_id: str | None
    merchant_name: str
    description: str | None
    amount: float
    currency: str
    payment_date: datetime
    direction: TransactionDirection
    is_food_candidate: bool
    food_confidence: float
    merchant_category: MerchantCategory
    matched_receipt_id: int | None


class GoalCreate(BaseModel):
    metric: GoalMetric
    reduction_percent: int = Field(ge=10, le=30)
    start_mode: str = "demo-immediate"


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric: GoalMetric
    reduction_percent: int
    baseline_value: float
    target_value: float
    start_date: date
    active: bool
    current_value: float
    remaining_value: float
    budget_used_pct: float


class PurchaseSummary(BaseModel):
    receipt_id: int
    merchant_name: str | None
    date: datetime | None
    selected_calories: float
    outside_schijf_spend: float
    outside_schijf_calories: float
    classification_label: str


class DashboardResponse(BaseModel):
    month: str
    elapsed_days_in_month: int
    calories: SplitMetrics
    spend: SplitMetrics
    avg_daily_tracked_calories: float
    goal: GoalRead | None
    last_purchases: list[PurchaseSummary]
    unmatched_food_transactions: list[TransactionRead]


class MonthlyResponse(BaseModel):
    month: str
    start_date: date
    end_date: date
    calories: SplitMetrics
    spend: SplitMetrics
    avg_daily_tracked_calories: float
    top_outside_items_by_calories: list[ReceiptItemRead]
    top_outside_items_by_spend: list[ReceiptItemRead]
    top_merchants_by_outside_spend: list[dict[str, Any]]
    goal: GoalRead | None
    insight: dict[str, str]


class BunqSyncResponse(BaseModel):
    mode: str
    created_transactions: int
    message: str


class SettingsActionResponse(BaseModel):
    ok: bool
    message: str


TransactionRead.model_rebuild()
ReceiptSummary.model_rebuild()

