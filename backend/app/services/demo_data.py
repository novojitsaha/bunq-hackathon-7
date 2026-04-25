from datetime import UTC, datetime


RECEIPT_FIXTURES = {
    "healthy": {
        "merchant_name": "Lidl Amsterdam",
        "purchase_date": "2026-04-25T12:20:00+00:00",
        "total_amount": 16.45,
        "currency": "EUR",
        "items": [
            {"raw_name": "Bananen", "normalized_name": "bananas", "quantity": 1.0, "unit": "bunch", "total_price": 1.79},
            {"raw_name": "Volkoren brood", "normalized_name": "wholegrain bread", "quantity": 1.0, "unit": "loaf", "total_price": 2.29},
            {"raw_name": "Magere yoghurt", "normalized_name": "low-fat yogurt", "quantity": 1.0, "unit": "tub", "total_price": 1.49},
            {"raw_name": "Paprika mix", "normalized_name": "bell peppers", "quantity": 1.0, "unit": "pack", "total_price": 2.99},
            {"raw_name": "Wortelen", "normalized_name": "carrots", "quantity": 1.0, "unit": "bag", "total_price": 1.19},
            {"raw_name": "Keukenpapier", "normalized_name": "kitchen paper", "quantity": 1.0, "unit": "pack", "total_price": 6.70},
        ],
    },
    "junk": {
        "merchant_name": "Albert Heijn",
        "purchase_date": "2026-04-24T18:10:00+00:00",
        "total_amount": 18.42,
        "currency": "EUR",
        "items": [
            {"raw_name": "Red Bull 250ml", "normalized_name": "energy drink", "quantity": 2.0, "unit": "can", "total_price": 3.98},
            {"raw_name": "Chips paprika", "normalized_name": "potato chips", "quantity": 1.0, "unit": "bag", "total_price": 2.49},
            {"raw_name": "Cola 1.5L", "normalized_name": "cola", "quantity": 1.0, "unit": "bottle", "total_price": 2.19},
            {"raw_name": "Melk halfvol", "normalized_name": "semi-skimmed milk", "quantity": 1.0, "unit": "carton", "total_price": 1.25},
            {"raw_name": "Chocoladereep", "normalized_name": "chocolate bar", "quantity": 2.0, "unit": "bar", "total_price": 2.98},
            {"raw_name": "Appels", "normalized_name": "apples", "quantity": 1.0, "unit": "bag", "total_price": 2.29},
            {"raw_name": "Statiegeld", "normalized_name": "deposit", "quantity": 1.0, "unit": None, "total_price": 3.24},
        ],
    },
    "fast_food": {
        "merchant_name": "Burger King",
        "purchase_date": "2026-04-23T20:35:00+00:00",
        "total_amount": 13.95,
        "currency": "EUR",
        "items": [
            {"raw_name": "Whopper menu", "normalized_name": "burger meal", "quantity": 1.0, "unit": "meal", "total_price": 8.95},
            {"raw_name": "Fries medium", "normalized_name": "fries", "quantity": 1.0, "unit": "portion", "total_price": 2.75},
            {"raw_name": "Soda medium", "normalized_name": "cola", "quantity": 1.0, "unit": "cup", "total_price": 2.25},
        ],
    },
}


DEMO_NUTRITION = {
    "bananas": {"calories": 210, "classification": "IN_SCHIJF", "confidence": 0.88, "is_food": True},
    "wholegrain bread": {"calories": 620, "classification": "IN_SCHIJF", "confidence": 0.86, "is_food": True},
    "low-fat yogurt": {"calories": 280, "classification": "IN_SCHIJF", "confidence": 0.84, "is_food": True},
    "bell peppers": {"calories": 95, "classification": "IN_SCHIJF", "confidence": 0.88, "is_food": True},
    "carrots": {"calories": 110, "classification": "IN_SCHIJF", "confidence": 0.88, "is_food": True},
    "kitchen paper": {"calories": 0, "classification": "NON_FOOD", "confidence": 0.96, "is_food": False},
    "energy drink": {"calories": 220, "classification": "WEEKKEUZE", "confidence": 0.9, "is_food": True},
    "potato chips": {"calories": 780, "classification": "WEEKKEUZE", "confidence": 0.92, "is_food": True},
    "cola": {"calories": 315, "classification": "WEEKKEUZE", "confidence": 0.91, "is_food": True},
    "semi-skimmed milk": {"calories": 470, "classification": "IN_SCHIJF", "confidence": 0.82, "is_food": True},
    "chocolate bar": {"calories": 460, "classification": "WEEKKEUZE", "confidence": 0.91, "is_food": True},
    "apples": {"calories": 260, "classification": "IN_SCHIJF", "confidence": 0.88, "is_food": True},
    "deposit": {"calories": 0, "classification": "NON_FOOD", "confidence": 0.96, "is_food": False},
    "burger meal": {"calories": 980, "classification": "WEEKKEUZE", "confidence": 0.86, "is_food": True},
    "fries": {"calories": 365, "classification": "WEEKKEUZE", "confidence": 0.89, "is_food": True},
}


DEMO_TRANSACTIONS = [
    {
        "bunq_payment_id": "demo-payment-lidl-1645",
        "merchant_name": "Lidl Amsterdam",
        "description": "Card payment Lidl",
        "amount": -16.45,
        "payment_date": datetime(2026, 4, 25, 12, 19, tzinfo=UTC),
    },
    {
        "bunq_payment_id": "demo-payment-ah-1842",
        "merchant_name": "Albert Heijn",
        "description": "Card payment AH",
        "amount": -18.42,
        "payment_date": datetime(2026, 4, 24, 18, 8, tzinfo=UTC),
    },
    {
        "bunq_payment_id": "demo-payment-bk-1395",
        "merchant_name": "Burger King",
        "description": "Card payment Burger King",
        "amount": -13.95,
        "payment_date": datetime(2026, 4, 23, 20, 33, tzinfo=UTC),
    },
    {
        "bunq_payment_id": "demo-income-april",
        "merchant_name": "Demo Employer",
        "description": "Salary April",
        "amount": 2600.00,
        "payment_date": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
    },
]

