from app.models import Classification
from app.services.demo_data import DEMO_NUTRITION
from app.services.open_food_facts_client import OpenFoodFactsClient, OffMatch
from app.services.schijf_classifier import classify_by_rules


def normalize_item_name(name: str) -> str:
    lowered = name.strip().lower()
    replacements = {
        "bananen": "bananas",
        "volkoren brood": "wholegrain bread",
        "magere yoghurt": "low-fat yogurt",
        "paprika mix": "bell peppers",
        "wortelen": "carrots",
        "keukenpapier": "kitchen paper",
        "chips paprika": "potato chips",
        "melk halfvol": "semi-skimmed milk",
        "chocoladereep": "chocolate bar",
        "appels": "apples",
        "statiegeld": "deposit",
        "whopper menu": "burger meal",
        "soda medium": "cola",
    }
    for source, target in replacements.items():
        if source in lowered:
            return target
    return " ".join(lowered.split())


def demo_lookup(normalized_name: str) -> dict:
    if normalized_name in DEMO_NUTRITION:
        return DEMO_NUTRITION[normalized_name]
    for key, value in DEMO_NUTRITION.items():
        if key in normalized_name or normalized_name in key:
            return value
    classification, confidence, source = classify_by_rules(normalized_name, None)
    return {
        "calories": None,
        "classification": classification.value,
        "confidence": confidence,
        "is_food": classification != Classification.NON_FOOD,
        "source": source,
    }


async def enrich_item(raw_name: str, normalized_name: str | None = None) -> dict:
    normalized = normalized_name or normalize_item_name(raw_name)
    off_match: OffMatch | None = await OpenFoodFactsClient().search_product(normalized)
    if off_match and off_match.calories_per_100g is not None:
        calories_total = round(off_match.calories_per_100g, 1)
        classification, confidence, source = classify_by_rules(normalized, calories_total)
        return {
            "normalized_name": normalized,
            "calories_total": calories_total,
            "classification": classification,
            "confidence": max(confidence, off_match.confidence),
            "source": source if classification != Classification.UNKNOWN else "open_food_facts",
            "is_food": classification != Classification.NON_FOOD,
            "match": off_match,
        }

    demo = demo_lookup(normalized)
    classification = Classification(demo["classification"])
    return {
        "normalized_name": normalized,
        "calories_total": demo.get("calories"),
        "classification": classification,
        "confidence": float(demo.get("confidence", 0.4)),
        "source": demo.get("source", "demo_nutrition"),
        "is_food": bool(demo.get("is_food", classification != Classification.NON_FOOD)),
        "match": None,
    }

