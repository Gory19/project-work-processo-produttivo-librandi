from __future__ import annotations

import math


def days_from_quantity_capacity(quantity: int, daily_capacity_qty: int) -> int:
    # [REQ-FN-CONFIG] Per-product daily capacity constraint.
    if daily_capacity_qty <= 0:
        raise ValueError("daily_capacity_qty must be > 0")
    if quantity <= 0:
        return 0
    return math.ceil(quantity / daily_capacity_qty)


def days_from_minutes(minutes: float, max_minutes_per_day: float) -> int:
    # [REQ-FN-CONFIG] Global time capacity constraint.
    if max_minutes_per_day <= 0:
        raise ValueError("max_minutes_per_day must be > 0")
    if minutes <= 0:
        return 0
    return math.ceil(minutes / max_minutes_per_day)


def min_days_required(
    quantity: int,
    daily_capacity_qty: int,
    minutes_required: float,
    max_minutes_per_day: float,
) -> tuple[int, int, int]:
    by_qty = days_from_quantity_capacity(quantity=quantity, daily_capacity_qty=daily_capacity_qty)
    by_minutes = days_from_minutes(minutes=minutes_required, max_minutes_per_day=max_minutes_per_day)
    return by_qty, by_minutes, max(by_qty, by_minutes)
