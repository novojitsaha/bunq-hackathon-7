from datetime import UTC, datetime

from app.services.schijf_classifier import classify_by_rules
from app.services.transaction_matcher import classify_merchant, receipt_transaction_score


def test_merchant_classifier_detects_supermarket():
    is_food, confidence, category = classify_merchant("Albert Heijn", "Card payment")
    assert is_food is True
    assert confidence > 0.8
    assert category == "supermarket"


def test_sugar_drink_is_weekkeuze():
    classification, confidence, source = classify_by_rules("cola", 315)
    assert classification == "WEEKKEUZE"
    assert confidence >= 0.9
    assert source == "rules:sugar_drink"


def test_receipt_transaction_score_auto_link_threshold():
    score = receipt_transaction_score(
        receipt_total=18.42,
        receipt_date=datetime(2026, 4, 24, 18, 10, tzinfo=UTC),
        receipt_merchant="Albert Heijn",
        transaction_amount=-18.42,
        transaction_date=datetime(2026, 4, 24, 18, 8, tzinfo=UTC),
        transaction_merchant="AH Albert Heijn",
    )
    assert score >= 0.8

