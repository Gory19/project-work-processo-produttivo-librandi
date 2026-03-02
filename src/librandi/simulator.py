from __future__ import annotations

from .capacity import days_from_minutes, min_days_required
from .models import Product, ProductSimulationResult, Scenario, ScenarioSimulationResult, Sequence


def simulate(
    scenario: Scenario,
    selected_sequence_ids: list[str],
    quantities: dict[str, int],
    weather_condition: str = "good",
    weather_multiplier: float = 1.0,
    scenario_selected: str | None = None,
) -> ScenarioSimulationResult:
    # [REQ-TIMEOUT] Computes total lot time for each output/product.
    sequence_map = scenario.sequence_map()
    selected_sequences = [_require_sequence(sequence_map, seq_id) for seq_id in selected_sequence_ids]

    product_results: list[ProductSimulationResult] = []
    total_minutes = 0.0
    for product in scenario.products:
        quantity = quantities.get(product.id)
        if quantity is None:
            raise ValueError(f"Missing quantity for product '{product.id}'")
        product_result = _simulate_product(
            product=product,
            quantity=quantity,
            selected_sequences=selected_sequences,
            max_minutes_per_day=scenario.global_capacity.max_minutes_per_day,
            weather_multiplier=weather_multiplier,
        )
        product_results.append(product_result)
        total_minutes += product_result.total_minutes

    global_days_required = days_from_minutes(
        minutes=total_minutes, max_minutes_per_day=scenario.global_capacity.max_minutes_per_day
    )
    global_days_required = max(
        global_days_required, max((item.min_days_required for item in product_results), default=0)
    )

    return ScenarioSimulationResult(
        scenario_name=scenario.scenario_name,
        quantity_unit=scenario.quantity_unit,
        time_unit=scenario.time_unit,
        selected_sequences=selected_sequence_ids,
        weather_condition=weather_condition,
        weather_multiplier=weather_multiplier,
        per_product=product_results,
        total_minutes=total_minutes,
        total_hours=total_minutes / 60.0,
        global_days_required=global_days_required,
        max_minutes_per_day=scenario.global_capacity.max_minutes_per_day,
        metadata={"scenario_selected": scenario_selected} if scenario_selected else {},
    )


def _simulate_product(
    product: Product,
    quantity: int,
    selected_sequences: list[Sequence],
    max_minutes_per_day: float,
    weather_multiplier: float,
) -> ProductSimulationResult:
    nominal_base_minutes = quantity * product.time_per_unit
    base_minutes = nominal_base_minutes * weather_multiplier
    sequence_minutes: dict[str, float] = {}
    total_minutes = 0.0

    for sequence in selected_sequences:
        current_sequence_minutes = 0.0
        for step in sequence.steps:
            if step.multiplier_time is not None:
                current_sequence_minutes += base_minutes * step.multiplier_time
            current_sequence_minutes += step.fixed_time_minutes
        sequence_minutes[sequence.id] = current_sequence_minutes
        total_minutes += current_sequence_minutes

    by_qty, by_minutes, min_days = min_days_required(
        quantity=quantity,
        daily_capacity_qty=product.daily_capacity_qty,
        minutes_required=total_minutes,
        max_minutes_per_day=max_minutes_per_day,
    )

    return ProductSimulationResult(
        product_id=product.id,
        product_label=product.label,
        quantity=quantity,
        nominal_base_minutes=nominal_base_minutes,
        base_minutes=base_minutes,
        sequence_minutes=sequence_minutes,
        total_minutes=total_minutes,
        days_by_quantity_capacity=by_qty,
        days_by_time_capacity=by_minutes,
        min_days_required=min_days,
    )


def _require_sequence(sequence_map: dict[str, Sequence], sequence_id: str) -> Sequence:
    sequence = sequence_map.get(sequence_id)
    if sequence is None:
        available = ", ".join(sorted(sequence_map))
        raise ValueError(f"Unknown sequence '{sequence_id}'. Available: {available}")
    return sequence
