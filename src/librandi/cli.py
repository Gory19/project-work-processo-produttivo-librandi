from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config_loader import list_scenario_files, load_scenario
from .export_excel import export_result_to_excel
from .models import ScenarioSimulationResult
from .randomizer import generate_quantities, resolve_weather_multiplier
from .report_utils import render_result
from .simulator import simulate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pianificazione del Processo Produttivo in un'Azienda Vinicola: "
            "Caso Librandi."
        )
    )
    return parser


def main() -> int:
    parser = build_parser()
    parser.parse_args()
    _print_start_context()

    root_dir = Path(__file__).resolve().parents[2]
    scenario_dir = root_dir / "data" / "scenarios"
    scenario_files = list_scenario_files(scenario_dir)
    if not scenario_files:
        raise SystemExit("Nessuno scenario trovato nella cartella data/scenarios.")

    preview_scenario = _load_preview_scenario(scenario_files)
    selected_sequences = _ask_sequences(preview_scenario)

    scenario_name = _ask_scenario_name(scenario_files)
    scenario = _load_selected_scenario(scenario_files, scenario_name)

    weather_condition, weather_multiplier = resolve_weather_multiplier(scenario=scenario)

    # [REQ-RANDOMQ] Quantities are generated randomly for each product/output.
    quantities = generate_quantities(scenario.products)
    result = simulate(
        scenario=scenario,
        selected_sequence_ids=selected_sequences,
        quantities=quantities,
        weather_condition=weather_condition,
        weather_multiplier=weather_multiplier,
        scenario_selected=_scenario_display_label(scenario_name),
    )
    print(render_result(result))
    _handle_excel_export(result)
    return 0


def _handle_excel_export(result: ScenarioSimulationResult) -> None:
    default_path = "output/pianificazione_librandi.xlsx"

    if not sys.stdin.isatty():
        return

    print("\nVuoi salvare anche il risultato in un file Excel? (s/n)")
    while True:
        raw = input("> ").strip().lower()
        if raw in {"s", "si", "y", "yes"}:
            print(
                "Inserisci il percorso del file Excel (.xlsx) oppure premi Invio "
                f"per usare '{default_path}':"
            )
            custom_path = input("> ").strip()
            output_path = custom_path or default_path
            exported_path = export_result_to_excel(result, output_path)
            print(f"\nFile Excel esportato in: {exported_path}")
            return
        if raw in {"n", "no"}:
            return
        print("Valore non valido. Inserisci 's' per Si oppure 'n' per No.")


def _print_start_context() -> None:
    print("=" * 68)
    print("PIANIFICAZIONE DEL PROCESSO PRODUTTIVO")
    print("IN UN'AZIENDA VINICOLA: CASO LIBRANDI")
    print("=" * 68)
    print("Questo programma stima tempi e giorni minimi per le lavorazioni")
    print("di raccolta e vinificazione, considerando capacita operative e meteo.")
    print("")


def _load_preview_scenario(scenario_files: dict[str, Path]):
    preview_name = "viticoltura" if "viticoltura" in scenario_files else sorted(scenario_files)[0]
    return load_scenario(scenario_files[preview_name])


def _load_selected_scenario(scenario_files: dict[str, Path], scenario_name: str):
    if scenario_name not in scenario_files:
        available = ", ".join(sorted(scenario_files))
        raise SystemExit(
            f"Scenario meteo '{scenario_name}' non valido. Valori disponibili: {available}"
        )
    return load_scenario(scenario_files[scenario_name])


def _ask_scenario_name(scenario_files: dict[str, Path]) -> str:
    names = list(scenario_files.keys())
    print("Seleziona lo scenario meteo del processo da simulare:")
    for idx, name in enumerate(names, start=1):
        print(f"{idx}) {_scenario_display_label(name)}")
    print("Inserisci il numero.")
    while True:
        raw = input("> ").strip()
        if raw.isdigit():
            numeric = int(raw)
            if 1 <= numeric <= len(names):
                return names[numeric - 1]
        print("Valore non valido. Inserisci il numero della lista.")


def _scenario_display_label(scenario_key: str) -> str:
    labels = {
        "viticoltura": "Meteo buono",
        "viticoltura_bad_weather": "Maltempo",
    }
    return labels.get(scenario_key, scenario_key)


def _ask_sequences(scenario) -> list[str]:
    sequence_map = scenario.sequence_map()
    sequence_ids = list(sequence_map.keys())

    print("Seleziona la Sequenza Produttiva da applicare:")
    for idx, sequence in enumerate(scenario.sequences, start=1):
        print(f"{idx}) {sequence.id.title()} - {sequence.label}")
    print(f"{len(scenario.sequences) + 1}) Tutte le Sequenze")
    print("Inserisci il numero.")

    while True:
        raw = input("> ").strip().lower()
        if raw.isdigit():
            numeric = int(raw)
            if 1 <= numeric <= len(scenario.sequences):
                return [scenario.sequences[numeric - 1].id]
            if numeric == len(scenario.sequences) + 1:
                return sequence_ids
        print("Valore non valido. Inserisci il numero della lista.")


if __name__ == "__main__":
    raise SystemExit(main())
