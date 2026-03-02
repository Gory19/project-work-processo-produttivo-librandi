from __future__ import annotations

import random

from .models import Product, Scenario


def generate_quantities(
    products: list[Product],
    seed: int | None = None,
    rng: random.Random | None = None,
) -> dict[str, int]:
    # [REQ-FN-RANDOM] Generates random lot quantities for each product.
    random_engine = rng or random.Random(seed)
    quantities: dict[str, int] = {}
    for product in products:
        quantities[product.id] = random_engine.randint(
            product.random_qty.minimum, product.random_qty.maximum
        )
    return quantities


def resolve_weather_multiplier(
    scenario: Scenario,
) -> tuple[str, float]:
    weather = scenario.weather
    if weather.mode == "fixed_good":
        return "good", weather.good_multiplier
    return "bad", weather.bad_multiplier
