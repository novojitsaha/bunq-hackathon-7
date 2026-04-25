from datetime import UTC, date, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Classification(str, Enum):
    IN_SCHIJF = "IN_SCHIJF"
    DAGKEUZE = "DAGKEUZE"
    WEEKKEUZE = "WEEKKEUZE"
    UNKNOWN = "UNKNOWN"
    NON_FOOD = "NON_FOOD"


class ReceiptStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class GoalMetric(str, Enum):
    OUTSIDE_SCHIJF_CALORIES = "OUTSIDE_SCHIJF_CALORIES"
    OUTSIDE_SCHIJF_SPEND = "OUTSIDE_SCHIJF_SPEND"


class TransactionDirection(str, Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class MerchantCategory(str, Enum):
    SUPERMARKET = "supermarket"
    RESTAURANT = "restaurant"
    BAR = "bar"
    DELIVERY = "delivery"
    UNKNOWN = "unknown"


class Receipt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(default="demo-user", index=True)
    status: ReceiptStatus = Field(default=ReceiptStatus.PROCESSING, index=True)
    merchant_name: str | None = Field(default=None, index=True)
    purchase_date: datetime | None = Field(default=None, index=True)
    upload_filename: str | None = None
    file_type: str | None = None
    total_amount: float | None = None
    currency: str = "EUR"
    linked_transaction_id: int | None = Field(default=None, foreign_key="transaction.id")
    raw_extraction_json: str | None = None
    validation_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class ReceiptItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id", index=True)
    raw_name: str
    normalized_name: str
    quantity: float = 1.0
    unit: str | None = None
    total_price: float = 0.0
    calories_total: float | None = None
    classification: Classification = Field(default=Classification.UNKNOWN, index=True)
    confidence: float = 0.0
    source: str = "fixture"
    selected_for_user: bool = True
    is_food: bool = True
    user_override: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProductMatch(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="receiptitem.id", index=True)
    normalized_query: str = Field(index=True)
    source: str
    external_id: str | None = None
    product_name: str | None = None
    brand: str | None = None
    calories_per_100g: float | None = None
    serving_size: str | None = None
    confidence: float = 0.0
    raw_json: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    bunq_payment_id: str | None = Field(default=None, index=True, unique=True)
    user_id: str = Field(default="demo-user", index=True)
    merchant_name: str = Field(index=True)
    description: str | None = None
    amount: float
    currency: str = "EUR"
    payment_date: datetime = Field(default_factory=utc_now, index=True)
    direction: TransactionDirection = TransactionDirection.OUTGOING
    is_food_candidate: bool = Field(default=False, index=True)
    food_confidence: float = 0.0
    merchant_category: MerchantCategory = MerchantCategory.UNKNOWN
    matched_receipt_id: int | None = Field(default=None, foreign_key="receipt.id")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Goal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(default="demo-user", index=True)
    metric: GoalMetric = Field(index=True)
    reduction_percent: int
    baseline_value: float
    target_value: float
    start_date: date
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

