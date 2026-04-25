import json
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.config import Settings, get_settings


@dataclass(frozen=True)
class OffMatch:
    source: str
    external_id: str | None
    product_name: str | None
    brand: str | None
    calories_per_100g: float | None
    serving_size: str | None
    confidence: float
    raw_json: str


class OpenFoodFactsClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = "https://world.openfoodfacts.org"

    async def search_product(self, query: str) -> OffMatch | None:
        if not self.settings.open_food_facts_live:
            return None

        fields = "code,product_name,brands,nutriments,serving_size,categories_tags,nutriscore_grade,nova_group"
        url = (
            f"{self.base_url}/api/v2/search?search_terms={quote(query)}"
            f"&countries_tags_en=netherlands&page_size=1&fields={fields}"
        )
        headers = {"User-Agent": self.settings.open_food_facts_user_agent}
        async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()

        products = payload.get("products") or []
        if not products:
            return None
        product = products[0]
        nutriments = product.get("nutriments") or {}
        calories = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal")
        try:
            calories_float = float(calories) if calories is not None else None
        except (TypeError, ValueError):
            calories_float = None

        return OffMatch(
            source="open_food_facts",
            external_id=product.get("code"),
            product_name=product.get("product_name"),
            brand=product.get("brands"),
            calories_per_100g=calories_float,
            serving_size=product.get("serving_size"),
            confidence=0.72,
            raw_json=json.dumps(product),
        )

