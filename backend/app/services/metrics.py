from collections import defaultdict
from datetime import UTC, date, datetime, time

from sqlmodel import Session, select

from app.models import Classification, Receipt, ReceiptItem, ReceiptStatus, Transaction
from app.schemas import PurchaseSummary, SplitMetrics
from app.services.schijf_classifier import public_label


def month_bounds(today: date | None = None) -> tuple[datetime, datetime]:
    now = today or datetime.now(UTC).date()
    start = datetime.combine(now.replace(day=1), time.min)
    end = datetime.combine(now, time.max)
    return start, end


def elapsed_days_in_month(today: date | None = None) -> int:
    return (today or datetime.now(UTC).date()).day


def receipt_metric_date(receipt: Receipt) -> datetime:
    value = receipt.purchase_date or receipt.created_at
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _empty_split() -> SplitMetrics:
    return SplitMetrics()


def add_to_split(split: SplitMetrics, classification: Classification, value: float) -> None:
    if classification == Classification.NON_FOOD:
        return
    if classification == Classification.IN_SCHIJF:
        split.in_schijf += value
    elif classification == Classification.DAGKEUZE:
        split.dagkeuze += value
        split.outside_schijf += value
    elif classification == Classification.WEEKKEUZE:
        split.weekkeuze += value
        split.outside_schijf += value
    else:
        split.unknown += value
    split.total += value


def get_confirmed_items(session: Session, start: datetime | None = None, end: datetime | None = None) -> list[tuple[Receipt, ReceiptItem]]:
    statement = (
        select(Receipt, ReceiptItem)
        .join(ReceiptItem, ReceiptItem.receipt_id == Receipt.id)
        .where(Receipt.status == ReceiptStatus.CONFIRMED)
        .where(ReceiptItem.selected_for_user == True)  # noqa: E712
        .where(ReceiptItem.is_food == True)  # noqa: E712
    )
    rows = list(session.exec(statement).all())
    if start is None and end is None:
        return rows
    filtered: list[tuple[Receipt, ReceiptItem]] = []
    for receipt, item in rows:
        metric_date = receipt_metric_date(receipt)
        if start and metric_date < start:
            continue
        if end and metric_date > end:
            continue
        filtered.append((receipt, item))
    return filtered


def split_for_items(rows: list[tuple[Receipt, ReceiptItem]], field: str) -> SplitMetrics:
    split = _empty_split()
    for _, item in rows:
        value = getattr(item, field) or 0.0
        add_to_split(split, item.classification, value)
    return SplitMetrics(**{key: round(value, 2) for key, value in split.model_dump().items()})


def mtd_splits(session: Session, today: date | None = None) -> tuple[SplitMetrics, SplitMetrics]:
    start, end = month_bounds(today)
    rows = get_confirmed_items(session, start, end)
    return split_for_items(rows, "calories_total"), split_for_items(rows, "total_price")


def receipt_splits(session: Session, receipt_id: int) -> tuple[SplitMetrics, SplitMetrics]:
    statement = (
        select(Receipt, ReceiptItem)
        .join(ReceiptItem, ReceiptItem.receipt_id == Receipt.id)
        .where(Receipt.id == receipt_id)
        .where(ReceiptItem.selected_for_user == True)  # noqa: E712
        .where(ReceiptItem.is_food == True)  # noqa: E712
    )
    rows = list(session.exec(statement).all())
    return split_for_items(rows, "calories_total"), split_for_items(rows, "total_price")


def last_purchase_summaries(session: Session, limit: int = 5) -> list[PurchaseSummary]:
    receipts = session.exec(
        select(Receipt).where(Receipt.status == ReceiptStatus.CONFIRMED).order_by(Receipt.purchase_date.desc()).limit(limit)
    ).all()
    summaries: list[PurchaseSummary] = []
    for receipt in receipts:
        items = session.exec(
            select(ReceiptItem)
            .where(ReceiptItem.receipt_id == receipt.id)
            .where(ReceiptItem.selected_for_user == True)  # noqa: E712
            .where(ReceiptItem.is_food == True)  # noqa: E712
        ).all()
        outside_items = [item for item in items if item.classification in {Classification.DAGKEUZE, Classification.WEEKKEUZE}]
        dominant = max(outside_items or items, key=lambda item: item.calories_total or 0, default=None)
        summaries.append(
            PurchaseSummary(
                receipt_id=receipt.id or 0,
                merchant_name=receipt.merchant_name,
                date=receipt_metric_date(receipt),
                selected_calories=round(sum(item.calories_total or 0 for item in items), 2),
                outside_schijf_spend=round(sum(item.total_price for item in outside_items), 2),
                outside_schijf_calories=round(sum(item.calories_total or 0 for item in outside_items), 2),
                classification_label=public_label(dominant.classification) if dominant else "Check",
            )
        )
    return summaries


def top_outside_items(session: Session, sort_by: str, limit: int = 5) -> list[ReceiptItem]:
    rows = get_confirmed_items(session)
    outside = [item for _, item in rows if item.classification in {Classification.DAGKEUZE, Classification.WEEKKEUZE}]
    return sorted(outside, key=lambda item: getattr(item, sort_by) or 0.0, reverse=True)[:limit]


def top_merchants_by_outside_spend(session: Session, limit: int = 5) -> list[dict[str, float | str]]:
    totals: dict[str, float] = defaultdict(float)
    for receipt, item in get_confirmed_items(session):
        if item.classification in {Classification.DAGKEUZE, Classification.WEEKKEUZE}:
            totals[receipt.merchant_name or "Unknown merchant"] += item.total_price
    return [
        {"merchant_name": merchant, "outside_schijf_spend": round(value, 2)}
        for merchant, value in sorted(totals.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    ]


def unmatched_food_transactions(session: Session, limit: int = 5) -> list[Transaction]:
    return list(
        session.exec(
            select(Transaction)
            .where(Transaction.direction == "OUTGOING")
            .where(Transaction.is_food_candidate == True)  # noqa: E712
            .where(Transaction.matched_receipt_id.is_(None))
            .order_by(Transaction.payment_date.desc())
            .limit(limit)
        ).all()
    )
