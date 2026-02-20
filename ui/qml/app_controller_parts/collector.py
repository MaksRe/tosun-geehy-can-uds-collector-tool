from __future__ import annotations

import csv
from copy import copy
import logging
import math
from pathlib import Path
import time

from j1939.j1939_can_identifier import J1939CanIdentifier
from uds.data_identifiers import UdsData
from uds.services.read_data_by_id import ServiceReadDataById
from uds.uds_identifiers import UdsIdentifiers
from ui.qml.collector_csv_manager import CollectorCsvManager


LOGGER = logging.getLogger(__name__)


class AppControllerCollectorMixin:
    @staticmethod
    def _parse_collector_csv_number(raw_value: str) -> float | None:
        text = str(raw_value).strip().replace(" ", "")
        if not text:
            return None
        normalized = text.replace(",", ".")
        try:
            return float(normalized)
        except (TypeError, ValueError):
            return None
    @staticmethod
    def _resolve_collector_csv_indexes(header: list[str]) -> dict[str, int]:
        idx_time = -1
        idx_temp = -1
        idx_fuel = -1

        for index, raw_name in enumerate(header):
            name = str(raw_name).strip().casefold()
            if not name:
                continue
            if idx_time < 0 and ("время" in name or "time" in name):
                idx_time = index
                continue
            if idx_temp < 0 and ("температ" in name or "temp" in name):
                idx_temp = index
                continue
            if idx_fuel < 0 and ("топлив" in name or "fuel" in name):
                idx_fuel = index
                continue

        if idx_temp < 0 or idx_fuel < 0:
            if len(header) >= 4:
                if idx_time < 0:
                    idx_time = 0
                idx_temp = 2 if idx_temp < 0 else idx_temp
                idx_fuel = 3 if idx_fuel < 0 else idx_fuel
            elif len(header) >= 3:
                idx_temp = 1 if idx_temp < 0 else idx_temp
                idx_fuel = 2 if idx_fuel < 0 else idx_fuel

        return {
            "time": idx_time,
            "temperature": idx_temp,
            "fuel": idx_fuel,
        }

    def _parse_collector_trend_csv_file(self, csv_path: Path) -> dict[str, object] | None:
        try:
            resolved_path = Path(csv_path).expanduser().resolve()
        except Exception:
            resolved_path = Path(csv_path)

        if not resolved_path.exists() or not resolved_path.is_file():
            return None

        points: list[dict[str, object]] = []
        try:
            with resolved_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file, delimiter=";")
                header: list[str] | None = None
                indexes: dict[str, int] = {"time": -1, "temperature": -1, "fuel": -1}

                for row in reader:
                    normalized_row = [str(value).strip() for value in row]
                    if len(normalized_row) == 0:
                        continue
                    if not any(normalized_row):
                        continue

                    if header is None:
                        header = normalized_row
                        indexes = self._resolve_collector_csv_indexes(header)
                        continue

                    idx_temp = int(indexes.get("temperature", -1))
                    idx_fuel = int(indexes.get("fuel", -1))
                    if idx_temp < 0 or idx_fuel < 0:
                        continue
                    if idx_temp >= len(normalized_row) or idx_fuel >= len(normalized_row):
                        continue

                    temperature_value = self._parse_collector_csv_number(normalized_row[idx_temp])
                    fuel_value = self._parse_collector_csv_number(normalized_row[idx_fuel])
                    if temperature_value is None or fuel_value is None:
                        continue

                    idx_time = int(indexes.get("time", -1))
                    if 0 <= idx_time < len(normalized_row):
                        time_text = normalized_row[idx_time]
                    else:
                        time_text = str(len(points) + 1)

                    points.append(
                        {
                            "fuel": float(fuel_value),
                            "temperature": float(temperature_value),
                            "time": str(time_text),
                        }
                    )
        except Exception as exc:
            LOGGER.exception("Ошибка чтения CSV %s: %s", resolved_path, exc)
            return None

        if len(points) == 0:
            return None

        node_text = f"CSV {resolved_path.stem}"
        return {
            "node": node_text,
            "nodeSa": -1,
            "count": len(points),
            "points": points,
            "path": str(resolved_path),
            "source": "csv",
        }
    @staticmethod
    def _resolve_project_root_directory() -> Path:
        try:
            return Path(__file__).resolve().parents[2]
        except Exception:
            return Path.cwd()

    def _apply_collector_output_directory(self, directory: Path, emit_signal: bool = True) -> bool:
        try:
            resolved = Path(directory).resolve()
            resolved.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False

        new_value = str(resolved)
        changed = self._collector_output_directory != new_value
        self._collector_output_directory = new_value
        if emit_signal and changed:
            self.collectorOutputDirectoryChanged.emit()
        return True

    @staticmethod
    def _extract_collector_node_sa(parsed_id: J1939CanIdentifier) -> int:
        node_sa = int(parsed_id.src) & 0xFF
        tester_sa = int(UdsIdentifiers.rx.dst) & 0xFF
        if node_sa == tester_sa:
            node_sa = int(parsed_id.dst) & 0xFF
        return node_sa

    def _ensure_collector_node(self, node_sa: int) -> dict[str, object]:
        normalized = int(node_sa) & 0xFF
        node = self._collector_nodes.get(normalized)
        if node is None:
            node = {
                "nodeSa": normalized,
                "period": 0,
                "fuelLevel": 0,
                "temperature": 0.0,
                "fuelCount": 0,
                "temperatureCount": 0,
                "lastSeen": "-",
                "lastSeenMonotonic": time.monotonic(),
            }
            self._collector_nodes[normalized] = node
            if normalized not in self._collector_node_order:
                self._collector_node_order.append(normalized)
        return node

    def _collector_node_stale_timeout_sec(self) -> float:
        nodes_count = max(1, len(self._collector_node_order))
        cycle_estimate_sec = (float(self._collector_poll_interval_ms) + float(self._collector_cycle_pause_ms)) * nodes_count / 1000.0
        return max(6.0, cycle_estimate_sec * 2.5)

    def _prune_collector_inactive_nodes(self):
        if len(self._collector_node_order) == 0:
            return

        now_monotonic = time.monotonic()
        timeout_sec = self._collector_node_stale_timeout_sec()
        kept_nodes: list[int] = []
        removed_nodes: list[int] = []

        for node_sa in self._collector_node_order:
            node = self._collector_nodes.get(node_sa)
            if node is None:
                continue
            try:
                last_seen_monotonic = float(node.get("lastSeenMonotonic", 0.0))
            except (TypeError, ValueError):
                last_seen_monotonic = 0.0

            if last_seen_monotonic <= 0.0 or (now_monotonic - last_seen_monotonic) > timeout_sec:
                removed_nodes.append(int(node_sa) & 0xFF)
            else:
                kept_nodes.append(int(node_sa) & 0xFF)

        if len(removed_nodes) == 0:
            return

        removed_set = {int(node_sa) & 0xFF for node_sa in removed_nodes}
        for node_sa in removed_set:
            self._collector_nodes.pop(node_sa, None)
            self._collector_trend_points_by_node.pop(node_sa, None)

        self._collector_node_order = [node_sa for node_sa in kept_nodes if node_sa not in removed_set]
        if len(self._collector_node_order) == 0:
            self._collector_poll_node_index = 0
            self._collector_poll_phase = 0
        else:
            self._collector_poll_node_index %= len(self._collector_node_order)

        self._schedule_collector_views_update(nodes=True, trend=True)
    @staticmethod
    def _calc_series_stats(values: list[float]) -> dict[str, float]:
        if len(values) == 0:
            return {
                "last": 0.0,
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "std": 0.0,
                "span": 0.0,
                "delta": 0.0,
            }

        normalized = [float(v) for v in values]
        count = len(normalized)
        minimum = min(normalized)
        maximum = max(normalized)
        mean = sum(normalized) / float(count)
        variance = 0.0
        for value in normalized:
            variance += (value - mean) ** 2
        variance /= float(count)
        std = math.sqrt(variance)
        delta = normalized[-1] - normalized[-2] if count > 1 else 0.0
        return {
            "last": normalized[-1],
            "min": minimum,
            "max": maximum,
            "mean": mean,
            "std": std,
            "span": maximum - minimum,
            "delta": delta,
        }

    def _schedule_collector_views_update(self, *, nodes: bool = False, trend: bool = False):
        if nodes:
            self._collector_view_update_pending_nodes = True
        if trend:
            self._collector_view_update_pending_trend = True

        if self._collector_view_update_pending_nodes or self._collector_view_update_pending_trend:
            if not self._collector_view_update_timer.isActive():
                self._collector_view_update_timer.start()

    def _flush_collector_views_update(self):
        emit_nodes = self._collector_view_update_pending_nodes
        emit_trend = self._collector_view_update_pending_trend

        self._collector_view_update_pending_nodes = False
        self._collector_view_update_pending_trend = False

        if emit_nodes:
            self._refresh_collector_nodes_view()

        if emit_trend:
            self._rebuild_collector_trend_views()
            self.collectorTrendChanged.emit()

    def _rebuild_collector_trend_views(self):
        entries: list[dict[str, object]] = []
        for node_sa in self._collector_node_order:
            normalized_sa = int(node_sa) & 0xFF
            points = list(self._collector_trend_points_by_node.get(normalized_sa, []))
            node = self._collector_nodes.get(normalized_sa, {})

            if len(points) == 0:
                fallback_fuel = float(node.get("fuelLevel", 0.0))
                fallback_temp = float(node.get("temperature", 0.0))
                fallback_time = str(node.get("lastSeen", "-"))
                points = [{"fuel": fallback_fuel, "temperature": fallback_temp, "time": fallback_time}]

            fuel_values = [float(point.get("fuel", 0.0)) for point in points]
            temp_values = [float(point.get("temperature", 0.0)) for point in points]
            fuel_stats = self._calc_series_stats(fuel_values)
            temp_stats = self._calc_series_stats(temp_values)

            latest_time = str(points[-1].get("time", "-"))
            fuel_error_pct = abs(fuel_stats["std"] / fuel_stats["mean"] * 100.0) if abs(fuel_stats["mean"]) > 1e-9 else 0.0
            temp_error_pct = abs(temp_stats["std"] / temp_stats["mean"] * 100.0) if abs(temp_stats["mean"]) > 1e-9 else 0.0

            entries.append(
                {
                    "nodeSa": normalized_sa,
                    "node": f"0x{normalized_sa:02X}",
                    "points": points,
                    "count": len(points),
                    "latestTime": latest_time,
                    "latestFuel": float(fuel_stats["last"]),
                    "latestTemperature": float(temp_stats["last"]),
                    "fuelMin": float(fuel_stats["min"]),
                    "fuelMax": float(fuel_stats["max"]),
                    "fuelMean": float(fuel_stats["mean"]),
                    "fuelStd": float(fuel_stats["std"]),
                    "fuelSpan": float(fuel_stats["span"]),
                    "fuelDelta": float(fuel_stats["delta"]),
                    "fuelErrorPct": float(fuel_error_pct),
                    "temperatureMin": float(temp_stats["min"]),
                    "temperatureMax": float(temp_stats["max"]),
                    "temperatureMean": float(temp_stats["mean"]),
                    "temperatureStd": float(temp_stats["std"]),
                    "temperatureSpan": float(temp_stats["span"]),
                    "temperatureDelta": float(temp_stats["delta"]),
                    "temperatureErrorPct": float(temp_error_pct),
                    "fuelDeviationFromNetwork": 0.0,
                    "temperatureDeviationFromNetwork": 0.0,
                    "fuelDivergencePct": 0.0,
                    "temperatureDivergencePct": 0.0,
                }
            )

        latest_fuel_values = [float(item.get("latestFuel", 0.0)) for item in entries]
        latest_temp_values = [float(item.get("latestTemperature", 0.0)) for item in entries]
        fuel_network = self._calc_series_stats(latest_fuel_values)
        temp_network = self._calc_series_stats(latest_temp_values)
        fuel_mean = float(fuel_network["mean"])
        temp_mean = float(temp_network["mean"])
        fuel_spread = float(fuel_network["span"])
        temp_spread = float(temp_network["span"])

        for item in entries:
            fuel_dev = float(item.get("latestFuel", 0.0)) - fuel_mean
            temp_dev = float(item.get("latestTemperature", 0.0)) - temp_mean
            item["fuelDeviationFromNetwork"] = fuel_dev
            item["temperatureDeviationFromNetwork"] = temp_dev
            item["fuelDivergencePct"] = abs(fuel_dev / fuel_mean * 100.0) if abs(fuel_mean) > 1e-9 else 0.0
            item["temperatureDivergencePct"] = abs(temp_dev / temp_mean * 100.0) if abs(temp_mean) > 1e-9 else 0.0

        metrics_rows: list[dict[str, str]] = []
        for item in entries:
            metrics_rows.append(
                {
                    "node": str(item.get("node", "")),
                    "deltaFuel": f"{float(item.get('fuelDelta', 0.0)):+.2f}",
                    "deltaTemperature": f"{float(item.get('temperatureDelta', 0.0)):+.2f}",
                    "devFuel": f"{float(item.get('fuelDeviationFromNetwork', 0.0)):+.2f}",
                    "devTemperature": f"{float(item.get('temperatureDeviationFromNetwork', 0.0)):+.2f}",
                    "errFuel": f"{float(item.get('fuelErrorPct', 0.0)):.2f}%",
                    "errTemperature": f"{float(item.get('temperatureErrorPct', 0.0)):.2f}%",
                    "divFuel": f"{float(item.get('fuelDivergencePct', 0.0)):.2f}%",
                    "divTemperature": f"{float(item.get('temperatureDivergencePct', 0.0)):.2f}%",
                }
            )

        self._collector_trend_nodes_view = entries
        self._collector_trend_metrics_rows = metrics_rows
        self._collector_trend_network_metrics = {
            "nodesCount": len(entries),
            "fuelMean": fuel_mean,
            "temperatureMean": temp_mean,
            "fuelSpread": fuel_spread,
            "temperatureSpread": temp_spread,
            "fuelStd": float(fuel_network["std"]),
            "temperatureStd": float(temp_network["std"]),
        }

    def _append_collector_trend_sample(self, node_sa: int, node: dict[str, object], timestamp: str):
        normalized_sa = int(node_sa) & 0xFF
        fuel = float(node.get("fuelLevel", 0))
        temperature = float(node.get("temperature", 0.0))
        sample = {
            "fuel": fuel,
            "temperature": temperature,
            "node": f"0x{normalized_sa:02X}",
            "time": str(timestamp),
        }
        points = list(self._collector_trend_points)
        points.append(sample)
        if len(points) > self._collector_trend_max_points:
            points = points[-self._collector_trend_max_points:]
        self._collector_trend_points = points

        node_points = list(self._collector_trend_points_by_node.get(normalized_sa, []))
        node_points.append(sample)
        if self._collector_trend_history_limit > 0 and len(node_points) > self._collector_trend_history_limit:
            node_points = node_points[-self._collector_trend_history_limit:]
        self._collector_trend_points_by_node[normalized_sa] = node_points

        self._collector_trend_caption = f"Узел {sample['node']} | Последнее обновление: {sample['time']}"
        self._collector_trend_latest_fuel = fuel
        self._collector_trend_latest_temperature = temperature
        self._schedule_collector_views_update(trend=True)

    def _reset_collector_trend(self):
        if self._collector_view_update_timer.isActive():
            self._collector_view_update_timer.stop()
        self._collector_view_update_pending_nodes = False
        self._collector_view_update_pending_trend = False
        self._collector_trend_points = []
        self._collector_trend_points_by_node = {}
        self._collector_trend_nodes_view = []
        self._collector_trend_metrics_rows = []
        self._collector_trend_network_metrics = {
            "nodesCount": 0,
            "fuelMean": 0.0,
            "temperatureMean": 0.0,
            "fuelSpread": 0.0,
            "temperatureSpread": 0.0,
            "fuelStd": 0.0,
            "temperatureStd": 0.0,
        }
        self._collector_trend_caption = "Ожидание данных от узлов..."
        self._collector_trend_latest_fuel = 0.0
        self._collector_trend_latest_temperature = 0.0
        self.collectorTrendChanged.emit()

    def _refresh_collector_nodes_view(self):
        rows: list[dict[str, str]] = []
        for node_sa in self._collector_node_order:
            node = self._collector_nodes.get(node_sa)
            if not node:
                continue
            rows.append(
                {
                    "node": f"0x{int(node_sa) & 0xFF:02X}",
                    "period": str(int(node.get("period", 0))),
                    "fuelLevel": str(int(node.get("fuelLevel", 0))),
                    "temperature": f"{float(node.get('temperature', 0.0)):.1f}",
                    "fuelCount": str(int(node.get("fuelCount", 0))),
                    "temperatureCount": str(int(node.get("temperatureCount", 0))),
                    "lastSeen": str(node.get("lastSeen", "-")),
                }
            )
        self._collector_nodes_view = rows
        self.collectorNodesChanged.emit()

    def _append_collector_csv(self, node_sa: int, node: dict[str, object], timestamp: str):
        if self._collector_state != "recording" or self._collector_session_dir is None:
            return
        manager = self._collector_csv_managers.get(node_sa)
        if manager is None:
            manager = CollectorCsvManager(f"0x{int(node_sa) & 0xFF:02X}", self._collector_session_dir)
            self._collector_csv_managers[node_sa] = manager
        manager.append_metric(
            measurement_time=str(timestamp),
            period_ticks=int(node.get("period", 0)),
            temperature_c=float(node.get("temperature", 0.0)),
            fuel_percent=int(node.get("fuelLevel", 0)),
        )

    def _handle_collector_frame(self, timestamp: str, parsed_id: J1939CanIdentifier, payload: list[int]):
        node_sa = self._extract_collector_node_sa(parsed_id)
        tester_sa = int(UdsIdentifiers.rx.dst) & 0xFF
        if node_sa == tester_sa:
            return

        was_new_node = int(node_sa) not in self._collector_nodes
        node = self._ensure_collector_node(node_sa)
        nodes_changed = was_new_node
        node["lastSeenMonotonic"] = time.monotonic()
        new_last_seen = timestamp[:8] if len(timestamp) >= 8 else timestamp
        if str(node.get("lastSeen", "")) != new_last_seen:
            node["lastSeen"] = new_last_seen
            nodes_changed = True

        pgn = int(parsed_id.pgn) & 0x3FFFF
        if pgn != (int(UdsIdentifiers.rx.pgn) & 0x3FFFF):
            if nodes_changed:
                self._schedule_collector_views_update(nodes=True, trend=was_new_node)
            return

        if len(payload) < 4:
            if nodes_changed:
                self._schedule_collector_views_update(nodes=True, trend=was_new_node)
            return

        sid = int(payload[1]) & 0xFF
        if sid != self._collector_read_service.success_sid:
            if nodes_changed:
                self._schedule_collector_views_update(nodes=True, trend=was_new_node)
            return

        did = self._collector_read_service.parse_did_field(payload)
        value = int(ServiceReadDataById.parse_data_field(payload))
        has_trend_update = False

        if did == int(UdsData.curr_fuel_tank.pid):
            node["period"] = value
            self._append_collector_csv(node_sa, node, timestamp)
            nodes_changed = True
        elif did == int(UdsData.raw_fuel_level.pid):
            node["period"] = int(self._collector_poll_interval_ms)
            node["fuelLevel"] = value
            node["fuelCount"] = int(node.get("fuelCount", 0)) + 1
            self._append_collector_csv(node_sa, node, timestamp)
            has_trend_update = True
            nodes_changed = True
        elif did == int(UdsData.raw_temperature.pid):
            node["period"] = int(self._collector_poll_interval_ms)
            temperature = value / 10.0
            node["temperature"] = temperature
            node["temperatureCount"] = int(node.get("temperatureCount", 0)) + 1
            self._append_collector_csv(node_sa, node, timestamp)
            has_trend_update = True
            nodes_changed = True

        if has_trend_update:
            self._append_collector_trend_sample(node_sa, node, str(node.get("lastSeen", "-")))

        if nodes_changed:
            self._schedule_collector_views_update(nodes=True, trend=was_new_node)

    def _on_collector_poll_tick(self):
        if not self._can.is_connect:
            return
        if self._source_address_busy:
            return

        self._prune_collector_inactive_nodes()

        if len(self._collector_poll_vars) == 0:
            return

        nodes = list(self._collector_node_order)
        if len(nodes) == 0:
            return

        self._collector_poll_node_index %= len(nodes)

        node_sa = int(nodes[self._collector_poll_node_index]) & 0xFF
        self._collector_poll_phase = 0 if self._collector_poll_phase <= 0 else 1
        poll_var = self._collector_poll_vars[self._collector_poll_phase]

        tx_identifier = copy(UdsIdentifiers.tx)
        tx_identifier.dst = node_sa
        self._collector_read_service.read_data_by_identifier(tx_identifier.identifier, poll_var)

        if self._collector_poll_phase == 0:
            self._collector_poll_phase = 1
            self._collector_poll_timer.setInterval(self._collector_poll_interval_ms)
        else:
            self._collector_poll_phase = 0
            self._collector_poll_node_index = (self._collector_poll_node_index + 1) % len(nodes)
            self._collector_poll_timer.setInterval(self._collector_cycle_pause_ms)

