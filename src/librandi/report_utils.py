from __future__ import annotations

from .models import ScenarioSimulationResult


def format_minutes(minutes: float) -> str:
    return f"{minutes:.2f} min ({minutes / 60.0:.2f} h)"


def render_result(result: ScenarioSimulationResult) -> str:
    width = 76
    lines: list[str] = []
    company_name, scenario_from_name = _split_company_and_scenario(result.scenario_name)
    scenario_selected = str(result.metadata.get("scenario_selected", scenario_from_name))
    weather_label = _weather_label(result.weather_condition)
    lines.append("=" * width)
    lines.append("RISULTATO SIMULAZIONE")
    lines.append("=" * width)
    lines.append(_kv("Azienda", company_name))
    lines.append(_kv("Scenario Meteo Selezionato", scenario_selected))
    lines.append(_kv("Sequenze Produttive Selezionate", ", ".join(result.selected_sequences)))
    lines.append(
        _kv(
            "Meteo Applicato",
            f"{weather_label} (x{result.weather_multiplier:.2f} sui tempi variabili)",
        )
    )
    lines.append(
        _kv(
            "Tempo Massimo Lavorabile/Giorno",
            f"{result.max_minutes_per_day:.0f} min ({result.max_minutes_per_day / 60.0:.2f} h)",
        )
    )
    lines.append("")

    for index, item in enumerate(result.per_product, start=1):
        lines.append("-" * width)
        lines.append(f"Prodotto {index} - {item.product_label}")
        lines.append("-" * width)
        lines.append(_kv("Quantita Lotto", f"{item.quantity} {result.quantity_unit}"))
        if abs(item.nominal_base_minutes - item.base_minutes) <= 1e-9:
            lines.append(_kv("Tempo Base di Produzione", format_minutes(item.base_minutes)))
        else:
            lines.append(
                _kv(
                    "Tempo Base di Produzione (Meteo Buono)",
                    format_minutes(item.nominal_base_minutes),
                )
            )
            lines.append(
                _kv("Tempo Base di Produzione (Con Maltempo)", format_minutes(item.base_minutes))
            )
        lines.append("")
        lines.append("Tempi di Produzione per Sequenza:")
        for sequence_id, sequence_minutes in item.sequence_minutes.items():
            lines.append(f"  - {sequence_id.title():<24}: {format_minutes(sequence_minutes)}")
        lines.append("")
        lines.append(_kv("Tempo Totale di Produzione", format_minutes(item.total_minutes)))
        lines.append(
            _kv(
                "Giorni di Produzione Necessari in Base alla Quantita del Prodotto",
                str(item.days_by_quantity_capacity),
            )
        )
        lines.append(
            _kv(
                "Giorni di Produzione Necessari in Base al Tempo Massimo Lavorabile al Giorno",
                str(item.days_by_time_capacity),
            )
        )
        lines.append(
            _kv(
                "Giorni Minimi di Produzione per il Prodotto",
                str(item.min_days_required),
            )
        )
        lines.append("")

    lines.append("=" * width)
    lines.append("RIEPILOGO FINALE")
    lines.append("=" * width)
    lines.append(_kv("Tempo Totale di Produzione del Processo", format_minutes(result.total_minutes)))
    lines.append(
        _kv(
            "Giorni Minimi Complessivi di Produzione",
            str(result.global_days_required),
        )
    )
    lines.append("=" * width)
    return "\n".join(lines)


def _split_company_and_scenario(full_name: str) -> tuple[str, str]:
    if " - " not in full_name:
        return full_name, "Non specificato"
    company, _, scenario = full_name.partition(" - ")
    return company.strip(), scenario.strip() or "Non specificato"


def _weather_label(condition: str) -> str:
    labels = {
        "good": "Meteo Buono",
        "bad": "Maltempo",
    }
    return labels.get(condition, condition)


def _kv(label: str, value: str) -> str:
    return f"{label:<38}: {value}"
