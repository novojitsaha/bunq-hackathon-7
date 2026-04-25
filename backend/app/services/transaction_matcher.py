from datetime import datetime

from rapidfuzz import fuzz

from app.models import MerchantCategory


SUPERMARKETS = ["albert heijn", " ah ", "jumbo", "lidl", "aldi", "dirk", "plus", "coop", "spar", "ekoplaza"]
RESTAURANTS = ["mcdonald", "burger king", "kfc", "febo", "subway", "pizza", "restaurant", "bistro"]
DELIVERY = ["thuisbezorgd", "uber eats", "deliveroo", "delivery"]
BARS = ["cafe", "bar", "pub", "coffee", "starbucks"]


def classify_merchant(merchant_name: str | None, description: str | None = None) -> tuple[bool, float, MerchantCategory]:
    text = f" {merchant_name or ''} {description or ''} ".lower()
    if any(term in text for term in SUPERMARKETS):
        return True, 0.92, MerchantCategory.SUPERMARKET
    if any(term in text for term in DELIVERY):
        return True, 0.88, MerchantCategory.DELIVERY
    if any(term in text for term in RESTAURANTS):
        return True, 0.86, MerchantCategory.RESTAURANT
    if any(term in text for term in BARS):
        return True, 0.74, MerchantCategory.BAR
    return False, 0.2, MerchantCategory.UNKNOWN


def receipt_transaction_score(
    *,
    receipt_total: float | None,
    receipt_date: datetime | None,
    receipt_merchant: str | None,
    transaction_amount: float,
    transaction_date: datetime,
    transaction_merchant: str | None,
) -> float:
    score = 0.0
    if receipt_total is not None:
        diff = abs(abs(transaction_amount) - receipt_total)
        if diff <= 0.05:
            score += 0.55
        elif diff <= 0.50:
            score += 0.35
    if receipt_date is not None:
        days = abs((receipt_date.date() - transaction_date.date()).days)
        if days == 0:
            score += 0.25
        elif days <= 3:
            score += 0.10
    if receipt_merchant and transaction_merchant:
        score += 0.20 * (fuzz.token_set_ratio(receipt_merchant, transaction_merchant) / 100)
    return round(min(score, 1.0), 3)

