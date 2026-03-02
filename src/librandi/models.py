from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RandomQtyRange:
    minimum: int
    maximum: int


@dataclass(frozen=True)
class Product:
    id: str
    label: str
    daily_capacity_qty: int
    time_per_unit: float
    random_qty: RandomQtyRange


@dataclass(frozen=True)
class Step:
    id: str
    label: str
    multiplier_time: float | None = None
    fixed_time_minutes: float = 0.0


@dataclass(frozen=True)
class Sequence:
    id: str
    label: str
    steps: list[Step]


@dataclass(frozen=True)
class GlobalCapacity:
    max_minutes_per_day: float


@dataclass(frozen=True)
class WeatherConfig:
    mode: str
    good_multiplier: float
    bad_multiplier: float


@dataclass(frozen=True)
class Scenario:
    scenario_name: str
    quantity_unit: str
    time_unit: str
    global_capacity: GlobalCapacity
    weather: WeatherConfig
    products: list[Product]
    sequences: list[Sequence]

    def product_map(self) -> dict[str, Product]:
        return {product.id: product for product in self.products}

    def sequence_map(self) -> dict[str, Sequence]:
        return {sequence.id: sequence for sequence in self.sequences}


@dataclass(frozen=True)
class ProductSimulationResult:
    product_id: str
    product_label: str
    quantity: int
    nominal_base_minutes: float
    base_minutes: float
    sequence_minutes: dict[str, float]
    total_minutes: float
    days_by_quantity_capacity: int
    days_by_time_capacity: int
    min_days_required: int


@dataclass(frozen=True)
class ScenarioSimulationResult:
    scenario_name: str
    quantity_unit: str
    time_unit: str
    selected_sequences: list[str]
    weather_condition: str
    weather_multiplier: float
    per_product: list[ProductSimulationResult]
    total_minutes: float
    total_hours: float
    global_days_required: int
    max_minutes_per_day: float
    metadata: dict[str, str | int | float] = field(default_factory=dict)
