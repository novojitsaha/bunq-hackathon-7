from app.models import Classification


SUGAR_DRINK_TERMS = {"cola", "soda", "energy drink", "red bull", "soft drink"}
WEEK_TERMS = {"chips", "potato chips", "chocolate", "burger", "fries", "pizza", "fast food"}
IN_SCHIJF_TERMS = {
    "apple",
    "apples",
    "banana",
    "bananas",
    "carrot",
    "carrots",
    "pepper",
    "bell peppers",
    "wholegrain",
    "wholegrain bread",
    "low-fat yogurt",
    "semi-skimmed milk",
    "vegetable",
}
NON_FOOD_TERMS = {"deposit", "statiegeld", "kitchen paper", "napkins", "bag"}


def classify_by_rules(
    normalized_name: str,
    calories_total: float | None,
    saturated_fat_g: float | None = None,
    salt_g: float | None = None,
) -> tuple[Classification, float, str]:
    name = normalized_name.lower()
    if any(term in name for term in NON_FOOD_TERMS):
        return Classification.NON_FOOD, 0.96, "rules:non_food"
    if any(term in name for term in SUGAR_DRINK_TERMS):
        return Classification.WEEKKEUZE, 0.9, "rules:sugar_drink"
    if any(term in name for term in WEEK_TERMS):
        return Classification.WEEKKEUZE, 0.88, "rules:outside_week"
    if any(term in name for term in IN_SCHIJF_TERMS):
        return Classification.IN_SCHIJF, 0.85, "rules:schijf_keyword"
    if calories_total is not None and calories_total <= 75:
        saturated_ok = saturated_fat_g is None or saturated_fat_g <= 1.7
        salt_ok = salt_g is None or salt_g <= 0.5
        if saturated_ok and salt_ok:
            return Classification.DAGKEUZE, 0.68, "rules:dagkeuze_threshold"
    return Classification.UNKNOWN, 0.25, "rules:unknown"


def public_label(classification: Classification) -> str:
    match classification:
        case Classification.IN_SCHIJF:
            return "Schijf"
        case Classification.DAGKEUZE:
            return "Dagkeuze"
        case Classification.WEEKKEUZE:
            return "Weekkeuze"
        case Classification.NON_FOOD:
            return "Non-food"
        case _:
            return "Check"

