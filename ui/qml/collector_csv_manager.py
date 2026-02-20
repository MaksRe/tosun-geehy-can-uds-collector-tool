from __future__ import annotations

import csv
from pathlib import Path


class CollectorCsvManager:
    """Writes collector values to a single per-node CSV file."""

    def __init__(self, node_hex: str, session_dir: Path):
        self._node_hex = str(node_hex).lower()
        session_dir.mkdir(parents=True, exist_ok=True)
        self._csv_path = session_dir / f"{self._node_hex}.csv"

        self._init_csv(
            self._csv_path,
            (
                "Время",
                "Период",
                "Температура (°C)",
                "Топливо (%)",
            ),
        )

    @staticmethod
    def _init_csv(csv_path: Path, header: tuple[str, ...]):
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file, delimiter=";").writerow(header)

    @staticmethod
    def _format_value(value: int | float | str) -> str:
        if isinstance(value, float):
            return f"{value:.1f}".replace(".", ",")
        if isinstance(value, int):
            return str(value)
        return str(value)

    @staticmethod
    def _append(csv_path: Path, row: tuple[str, ...]):
        with csv_path.open("a", newline="", encoding="utf-8") as file:
            csv.writer(file, delimiter=";").writerow(row)

    def append_metric(
        self,
        measurement_time: str,
        period_ticks: int,
        temperature_c: float,
        fuel_percent: int,
    ):
        row = (
            self._format_value(str(measurement_time)),
            self._format_value(int(period_ticks)),
            self._format_value(float(temperature_c)),
            self._format_value(int(fuel_percent)),
        )
        self._append(self._csv_path, row)
