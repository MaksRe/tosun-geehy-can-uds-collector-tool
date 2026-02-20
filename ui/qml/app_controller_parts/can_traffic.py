from __future__ import annotations

from datetime import datetime
import time

from PySide6.QtCore import Slot

from j1939.j1939_can_identifier import J1939CanIdentifier
from uds.uds_identifiers import UdsIdentifiers


class AppControllerCanTrafficMixin:
    @Slot(str, str, str, str, list)
    def _on_can_message(self, msg_time, msg_id, msg_dir, msg_dlc, msg_data):
        try:
            identifier = int(str(msg_id), 0)
        except (TypeError, ValueError):
            identifier = 0

        direction = self._normalize_can_direction(msg_dir)
        payload = []
        if isinstance(msg_data, list):
            for value in msg_data:
                try:
                    payload.append(int(value) & 0xFF)
                except (TypeError, ValueError):
                    continue

        data_hex = " ".join(f"{byte:02X}" for byte in payload)
        formatted_time = self._format_can_time(msg_time, direction)

        pgn_text = "-"
        src_text = "-"
        dst_text = "-"
        j1939_text = "-"
        parsed_id = None
        try:
            parsed_id = J1939CanIdentifier(int(identifier))
            parsed_pgn = int(parsed_id.pgn) & 0x3FFFF
            parsed_src = int(parsed_id.src) & 0xFF
            parsed_dst = int(parsed_id.dst) & 0xFF

            pgn_text = f"0x{parsed_pgn & 0xFFFF:04X}"
            src_text = f"0x{parsed_src:02X}"
            dst_text = f"0x{parsed_dst:02X}"
            app_summary = self._parse_j1939_application_summary(parsed_pgn, payload)
            if app_summary:
                j1939_text = app_summary
        except Exception:
            pass

        uds_text = "-"
        is_uds_frame = self._is_uds_identifier(identifier)
        if (not is_uds_frame) and parsed_id is not None:
            is_uds_frame = self._is_uds_diagnostic_pgn(int(parsed_id.pgn))
        if is_uds_frame:
            uds_text = self._parse_isotp_summary(payload)

        if direction == "RX" and parsed_id is not None:
            if self._auto_detect_enabled:
                self._update_observed_uds_candidate(parsed_id)
            self._handle_collector_frame(formatted_time, parsed_id, payload)

        if direction == "TX":
            dir_color = "#1d4ed8"
            dir_bg = "#dbeafe"
            dir_border = "#93c5fd"
        elif direction == "RX":
            dir_color = "#15803d"
            dir_bg = "#dcfce7"
            dir_border = "#86efac"
        else:
            dir_color = "#334155"
            dir_bg = "#e2e8f0"
            dir_border = "#cbd5e1"

        row = {
            "time": formatted_time,
            "dir": direction,
            "frameId": f"0x{int(identifier) & 0x1FFFFFFF:08X}",
            "pgn": pgn_text,
            "src": src_text,
            "dst": dst_text,
            "j1939": j1939_text,
            "dlc": str(msg_dlc),
            "uds": uds_text,
            "data": data_hex,
            "dirColor": dir_color,
            "dirBg": dir_bg,
            "dirBorder": dir_border,
        }
        if self._can_journal_enabled:
            self._append_can_traffic_entry(row)
    @staticmethod
    def _normalize_can_direction(direction) -> str:
        raw = str(direction).strip().upper()
        if raw.startswith("T"):
            return "TX"
        if raw.startswith("R"):
            return "RX"
        return raw or "-"

    def _format_can_time(self, raw_time, direction: str) -> str:
        raw_text = str(raw_time).strip()
        try:
            value = float(raw_text)
        except (TypeError, ValueError):
            return raw_text

        # Unix epoch in seconds.
        if value >= 946684800.0:
            try:
                return datetime.fromtimestamp(value).strftime("%H:%M:%S.%f")[:-3]
            except Exception:
                return raw_text

        if direction == "RX":
            if (self._rx_time_anchor_raw is None) or (value < (self._rx_time_anchor_raw - 0.001)):
                self._rx_time_anchor_raw = value
                self._rx_time_anchor_wall = time.time()

            anchor_raw = self._rx_time_anchor_raw if self._rx_time_anchor_raw is not None else value
            anchor_wall = self._rx_time_anchor_wall if self._rx_time_anchor_wall is not None else time.time()
            wall_ts = anchor_wall + (value - anchor_raw)
        else:
            # TX timestamp comes from perf_counter().
            wall_ts = self._wall_origin + (value - self._perf_origin)

        try:
            return datetime.fromtimestamp(wall_ts).strftime("%H:%M:%S.%f")[:-3]
        except Exception:
            return raw_text
    @staticmethod
    def _parse_isotp_summary(payload: list[int]) -> str:
        if not payload:
            return "-"

        pci_type = (payload[0] >> 4) & 0x0F
        if pci_type == 0x0:
            data_len = payload[0] & 0x0F
            if len(payload) > 1:
                sid = payload[1] & 0xFF
                if sid == 0x7F and len(payload) > 3:
                    return f"SF NRC=0x{payload[3] & 0xFF:02X} SID=0x{payload[2] & 0xFF:02X}"
                return f"SF LEN={data_len} SID=0x{sid:02X}"
            return f"SF LEN={data_len}"

        if pci_type == 0x1:
            total_len = ((payload[0] & 0x0F) << 8) | (payload[1] & 0xFF if len(payload) > 1 else 0)
            if len(payload) > 2:
                return f"FF LEN={total_len} SID=0x{payload[2] & 0xFF:02X}"
            return f"FF LEN={total_len}"

        if pci_type == 0x2:
            return f"CF SN={payload[0] & 0x0F}"

        if pci_type == 0x3:
            flow_status = payload[0] & 0x0F
            flow_labels = {0: "CTS", 1: "WAIT", 2: "OVFLW"}
            block_size = payload[1] & 0xFF if len(payload) > 1 else 0
            st_min = payload[2] & 0xFF if len(payload) > 2 else 0
            return f"FC {flow_labels.get(flow_status, 'UNK')} BS={block_size} ST=0x{st_min:02X}"

        return f"ISO-TP PCI=0x{pci_type:X}"
    @staticmethod
    def _parse_j1939_application_summary(pgn: int, payload: list[int]) -> str:
        if not payload:
            return ""

        # PGN 0xFEFC: fuel level, byte[1], scale 0.4%/bit.
        if int(pgn) == 0xFEFC and len(payload) > 1:
            raw = int(payload[1]) & 0xFF
            if raw >= 0xFE:
                return f"FuelLevel=N/A raw=0x{raw:02X}"
            return f"FuelLevel={raw * 0.4:.1f}% raw=0x{raw:02X}"

        # PGN 0xFDA2: temperature, byte[4], offset -40 C.
        if int(pgn) == 0xFDA2 and len(payload) > 4:
            raw = int(payload[4]) & 0xFF
            if raw >= 0xFE:
                return f"Temperature=N/A raw=0x{raw:02X}"
            return f"Temperature={raw - 40}C raw=0x{raw:02X}"

        return ""

    def _append_can_traffic_entry(self, row: dict[str, str]):
        self._can_traffic_logs.append(row)
        self._update_can_filter_options_with_row(row)
        hard_limit = 5000
        keep_tail = 1500
        if len(self._can_traffic_logs) > hard_limit:
            self._can_traffic_logs = self._can_traffic_logs[-keep_tail:]
            self._can_traffic_logs.insert(
                0,
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "dir": "SYS",
                    "frameId": "-",
                    "pgn": "-",
                    "src": "-",
                    "dst": "-",
                    "j1939": "-",
                    "dlc": "-",
                    "uds": "Автоочистка журнала",
                    "data": f"Оставлены последние {keep_tail} записей",
                    "dirColor": "#334155",
                    "dirBg": "#e2e8f0",
                    "dirBorder": "#cbd5e1",
                },
            )
        self._schedule_can_traffic_rebuild()

    def _schedule_can_traffic_rebuild(self, restart: bool = False):
        if self._can_filter_rebuild_timer.isActive():
            if restart:
                self._can_filter_rebuild_timer.stop()
                self._can_filter_rebuild_timer.start()
            return
        self._can_filter_rebuild_timer.start()

    def _rebuild_can_traffic_view(self):
        normalized_filters: dict[str, str] = {}
        for field in self.CAN_FILTER_FIELDS:
            normalized_filters[field] = str(self._can_filter_values.get(field, "")).strip().lower()

        has_filters = any(bool(value) for value in normalized_filters.values())
        if not has_filters:
            self._filtered_can_traffic_logs = list(self._can_traffic_logs)
        else:
            filtered: list[dict[str, str]] = []
            for row in self._can_traffic_logs:
                match = True
                for field, filter_value in normalized_filters.items():
                    if not filter_value:
                        continue
                    value = str(row.get(field, "")).lower()
                    if filter_value not in value:
                        match = False
                        break
                if match:
                    filtered.append(row)
            self._filtered_can_traffic_logs = filtered

        self.canTrafficLogsChanged.emit()

    def _normalize_filter_option_value(self, field: str, value: str) -> str:
        text = str(value or "").strip()
        if (not text) or text == "-":
            return ""

        if field == "time":
            # For options keep second precision to avoid flooding by unique milliseconds.
            if len(text) >= 8 and text[2] == ":" and text[5] == ":":
                return text[:8]
            return text

        if field == "data":
            # Keep first bytes as stable prefix for easier selection.
            parts = text.split()
            if len(parts) > 8:
                return " ".join(parts[:8])
            return text

        return text

    def _update_can_filter_options_with_row(self, row: dict[str, str]):
        changed = False
        for field in self.CAN_FILTER_FIELDS:
            value = self._normalize_filter_option_value(field, row.get(field, ""))
            if not value:
                continue

            seen = self._can_filter_option_seen[field]
            if value in seen:
                continue

            limit = int(self._can_filter_option_limits.get(field, 120))
            values = self._can_filter_options[field]
            if len(values) >= limit:
                continue

            seen.add(value)
            values.append(value)
            changed = True

        if changed:
            self.canFilterOptionsChanged.emit()
    @staticmethod
    def _is_uds_identifier(identifier: int) -> bool:
        try:
            parsed = J1939CanIdentifier(int(identifier))
            pgn = int(parsed.pgn) & 0x3FFFF
            return pgn in (int(UdsIdentifiers.tx.pgn) & 0x3FFFF, int(UdsIdentifiers.rx.pgn) & 0x3FFFF)
        except Exception:
            return False
    @staticmethod
    def _is_uds_diagnostic_pgn(pgn: int) -> bool:
        return ((int(pgn) >> 8) & 0xFF) == 0xDA

    @Slot(int, bool)

    @staticmethod
    def _choose_tester_sa_for_node(node: dict[str, object], default_tester_sa: int) -> tuple[int, int]:
        votes = node.get("tester_votes", {}) if isinstance(node, dict) else {}
        if not isinstance(votes, dict) or len(votes) == 0:
            return int(default_tester_sa) & 0xFF, 0
        best_sa, best_count = max(votes.items(), key=lambda item: int(item[1]))
        return int(best_sa) & 0xFF, int(best_count)

    def _rebuild_observed_candidate_list(self):
        previous_items = list(self._observed_candidate_items)
        previous_values = list(self._observed_candidate_values)
        previous_index = self._observed_candidate_index
        previous_text = self._observed_uds_text

        current_selected_sa = None
        if 0 <= previous_index < len(previous_values):
            current_selected_sa = int(previous_values[previous_index]) & 0xFF

        # Stable append-only ordering for UI list: existing order is kept,
        # new addresses are appended and never reshuffled by live counters.
        known_stats = self._observed_node_stats
        stable_order: list[int] = []
        seen_sa: set[int] = set()

        for sa in self._observed_candidate_order:
            device_sa = int(sa) & 0xFF
            if device_sa in seen_sa:
                continue
            if device_sa in known_stats:
                stable_order.append(device_sa)
                seen_sa.add(device_sa)

        for sa in sorted(int(key) & 0xFF for key in known_stats.keys()):
            if sa in seen_sa:
                continue
            stable_order.append(sa)
            seen_sa.add(sa)

        self._observed_candidate_order = stable_order

        default_tester_sa = int(UdsIdentifiers.tx.src) & 0xFF
        new_values: list[int] = []
        new_items: list[str] = []
        for device_sa in stable_order:
            node = known_stats.get(device_sa, {})
            total_count = int(node.get("total", 0))
            uds_count = int(node.get("uds", 0))
            guessed_tester_sa, _ = self._choose_tester_sa_for_node(node, default_tester_sa)
            label = (
                f"Устройство 0x{device_sa:02X}  |  RX: {total_count}  |  UDS: {uds_count}  |  Тестер: 0x{guessed_tester_sa:02X}"
            )
            new_values.append(device_sa)
            new_items.append(label)

        self._observed_candidate_values = new_values
        self._observed_candidate_items = new_items

        if len(new_values) == 0:
            self._observed_candidate_index = -1
        elif current_selected_sa is not None and current_selected_sa in new_values:
            self._observed_candidate_index = new_values.index(current_selected_sa)
        elif 0 <= previous_index < len(new_values):
            self._observed_candidate_index = previous_index
        else:
            self._observed_candidate_index = 0

        self._update_observed_candidate_text()

        if (
            previous_items != self._observed_candidate_items
            or previous_index != self._observed_candidate_index
            or previous_text != self._observed_uds_text
        ):
            self.observedUdsCandidateChanged.emit()

    def _update_observed_candidate_text(self):
        if not (0 <= self._observed_candidate_index < len(self._observed_candidate_values)):
            self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
            return

        device_sa = int(self._observed_candidate_values[self._observed_candidate_index]) & 0xFF
        node = self._observed_node_stats.get(device_sa, {})
        total_count = int(node.get("total", 0)) if isinstance(node, dict) else 0
        uds_count = int(node.get("uds", 0)) if isinstance(node, dict) else 0
        tester_sa, tester_votes = self._choose_tester_sa_for_node(node, int(UdsIdentifiers.tx.src) & 0xFF)

        self._observed_uds_text = (
            f"Кандидат SA устройства: 0x{device_sa:02X}. "
            f"Всего RX кадров: {total_count}, диагностических: {uds_count}. "
            f"Предполагаемый SA тестера: 0x{tester_sa:02X}"
            + (f" (по {tester_votes} UDS кадр.)" if tester_votes > 0 else " (по умолчанию).")
            + f" Найдено устройств: {len(self._observed_candidate_values)}."
        )

    def _update_observed_uds_candidate(self, parsed_id: J1939CanIdentifier):
        device_sa = int(parsed_id.src) & 0xFF
        tester_sa = int(parsed_id.dst) & 0xFF
        current_tester_sa = int(UdsIdentifiers.tx.src) & 0xFF

        # Исключаем собственный SA тестера, чтобы не подхватывать эхо своих сообщений.
        if device_sa == current_tester_sa:
            return

        pgn = int(parsed_id.pgn) & 0x3FFFF
        is_diag = self._is_uds_diagnostic_pgn(pgn)

        stats = self._observed_node_stats.get(device_sa)
        if stats is None:
            stats = {"total": 0, "uds": 0, "last": 0, "tester_votes": {}}
            self._observed_node_stats[device_sa] = stats
            if device_sa not in self._observed_candidate_order:
                self._observed_candidate_order.append(device_sa)

        stats["total"] = int(stats.get("total", 0)) + 1
        if is_diag:
            stats["uds"] = int(stats.get("uds", 0)) + 1
            votes = stats.get("tester_votes", {})
            if not isinstance(votes, dict):
                votes = {}
            votes[tester_sa] = int(votes.get(tester_sa, 0)) + 1
            stats["tester_votes"] = votes

        self._observed_frame_seq += 1
        stats["last"] = self._observed_frame_seq

        if len(self._observed_node_stats) > 256:
            trimmed = sorted(
                self._observed_node_stats.items(),
                key=lambda item: (
                    int(item[1].get("uds", 0)),
                    int(item[1].get("total", 0)),
                    int(item[1].get("last", 0)),
                ),
                reverse=True,
            )[:128]
            self._observed_node_stats = dict(trimmed)

        self._rebuild_observed_candidate_list()

    def _reset_observed_uds_candidate(self, emit_signal: bool = True):
        self._observed_node_stats = {}
        self._observed_candidate_order = []
        self._observed_candidate_values = []
        self._observed_candidate_items = []
        self._observed_candidate_index = -1
        self._observed_frame_seq = 0
        self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
        if emit_signal:
            self.observedUdsCandidateChanged.emit()

