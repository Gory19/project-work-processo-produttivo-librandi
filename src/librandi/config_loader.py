from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    yaml = None

from .models import (
    GlobalCapacity,
    Product,
    RandomQtyRange,
    Scenario,
    Sequence,
    Step,
    WeatherConfig,
)


def list_scenario_files(scenario_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for ext in ("*.yaml", "*.yml"):
        for path in scenario_dir.glob(ext):
            files[path.stem] = path
    return dict(sorted(files.items()))


def load_scenario(path: Path) -> Scenario:
    raw = _load_raw(path)
    return _parse_scenario(raw)


def apply_overrides(
    scenario: Scenario,
    max_minutes_per_day: float | None = None,
    time_per_unit_overrides: dict[str, float] | None = None,
    daily_capacity_overrides: dict[str, int] | None = None,
) -> Scenario:
    updated = copy.deepcopy(scenario)

    if max_minutes_per_day is not None:
        if max_minutes_per_day <= 0:
            raise ValueError("max_minutes_per_day override must be > 0.")
        updated = Scenario(
            scenario_name=updated.scenario_name,
            quantity_unit=updated.quantity_unit,
            time_unit=updated.time_unit,
            global_capacity=GlobalCapacity(max_minutes_per_day=max_minutes_per_day),
            weather=updated.weather,
            products=updated.products,
            sequences=updated.sequences,
        )

    tpu_overrides = time_per_unit_overrides or {}
    cap_overrides = daily_capacity_overrides or {}
    if not tpu_overrides and not cap_overrides:
        return updated

    known_products = updated.product_map()
    unknown_ids = (set(tpu_overrides) | set(cap_overrides)) - set(known_products)
    if unknown_ids:
        unknown = ", ".join(sorted(unknown_ids))
        raise ValueError(f"Unknown product id(s) in overrides: {unknown}")

    overridden_products: list[Product] = []
    for product in updated.products:
        next_tpu = tpu_overrides.get(product.id, product.time_per_unit)
        next_cap = cap_overrides.get(product.id, product.daily_capacity_qty)
        if next_tpu <= 0:
            raise ValueError(f"time_per_unit for {product.id} must be > 0.")
        if next_cap <= 0:
            raise ValueError(f"daily_capacity_qty for {product.id} must be > 0.")
        overridden_products.append(
            Product(
                id=product.id,
                label=product.label,
                daily_capacity_qty=next_cap,
                time_per_unit=next_tpu,
                random_qty=product.random_qty,
            )
        )

    return Scenario(
        scenario_name=updated.scenario_name,
        quantity_unit=updated.quantity_unit,
        time_unit=updated.time_unit,
        global_capacity=updated.global_capacity,
        weather=updated.weather,
        products=overridden_products,
        sequences=updated.sequences,
    )


def _load_raw(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("PyYAML is not installed. Install requirements.")
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported scenario extension: {path.suffix}")


def _parse_scenario(raw: dict[str, Any]) -> Scenario:
    try:
        scenario_name = str(raw["scenario_name"])
        units = raw["units"]
        quantity_unit = str(units["quantity"])
        time_unit = str(units["time"])

        max_minutes_per_day = float(raw["global_capacity"]["max_minutes_per_day"])
        if max_minutes_per_day <= 0:
            raise ValueError("global_capacity.max_minutes_per_day must be > 0")

        weather = _parse_weather(raw.get("weather"))
        products = [_parse_product(item) for item in raw["products"]]
        sequences = [_parse_sequence(item) for item in raw["sequences"]]
    except KeyError as exc:
        raise ValueError(f"Missing required scenario key: {exc}") from exc

    if len(products) < 3:
        raise ValueError("Scenario must define at least 3 products.")
    if len(sequences) < 2:
        raise ValueError("Scenario must define at least 2 sequences.")

    return Scenario(
        scenario_name=scenario_name,
        quantity_unit=quantity_unit,
        time_unit=time_unit,
        global_capacity=GlobalCapacity(max_minutes_per_day=max_minutes_per_day),
        weather=weather,
        products=products,
        sequences=sequences,
    )


def _parse_product(raw: dict[str, Any]) -> Product:
    random_qty = raw["random_qty"]
    minimum = int(random_qty["min"])
    maximum = int(random_qty["max"])
    if minimum > maximum:
        raise ValueError(f"Invalid random_qty range for product {raw['id']}")

    product = Product(
        id=str(raw["id"]),
        label=str(raw["label"]),
        daily_capacity_qty=int(raw["daily_capacity_qty"]),
        time_per_unit=float(raw["time_per_unit"]),
        random_qty=RandomQtyRange(minimum=minimum, maximum=maximum),
    )
    if product.daily_capacity_qty <= 0:
        raise ValueError(f"daily_capacity_qty for {product.id} must be > 0")
    if product.time_per_unit <= 0:
        raise ValueError(f"time_per_unit for {product.id} must be > 0")
    return product


def _parse_sequence(raw: dict[str, Any]) -> Sequence:
    steps: list[Step] = []
    for step_raw in raw["steps"]:
        multiplier = step_raw.get("multiplier_time")
        fixed_minutes = float(step_raw.get("fixed_time_minutes", 0.0))
        if multiplier is None and fixed_minutes == 0:
            raise ValueError(
                f"Step {step_raw['id']} in sequence {raw['id']} must define time."
            )
        if multiplier is not None and float(multiplier) < 0:
            raise ValueError(
                f"Step {step_raw['id']} in sequence {raw['id']} has invalid multiplier."
            )
        if fixed_minutes < 0:
            raise ValueError(
                f"Step {step_raw['id']} in sequence {raw['id']} has invalid fixed time."
            )
        steps.append(
            Step(
                id=str(step_raw["id"]),
                label=str(step_raw["label"]),
                multiplier_time=None if multiplier is None else float(multiplier),
                fixed_time_minutes=fixed_minutes,
            )
        )

    if not steps:
        raise ValueError(f"Sequence {raw['id']} must include at least one step.")
    return Sequence(id=str(raw["id"]), label=str(raw["label"]), steps=steps)


def _parse_weather(raw: dict[str, Any] | None) -> WeatherConfig:
    weather = raw or {}
    mode = str(weather.get("mode", "fixed_good"))
    good_multiplier = float(weather.get("good_multiplier", 1.0))
    bad_multiplier = float(weather.get("bad_multiplier", 1.35))

    if mode not in {"fixed_good", "fixed_bad"}:
        raise ValueError("weather.mode must be one of: fixed_good, fixed_bad")
    if good_multiplier <= 0:
        raise ValueError("weather.good_multiplier must be > 0")
    if bad_multiplier <= 0:
        raise ValueError("weather.bad_multiplier must be > 0")

    return WeatherConfig(
        mode=mode,
        good_multiplier=good_multiplier,
        bad_multiplier=bad_multiplier,
    )
