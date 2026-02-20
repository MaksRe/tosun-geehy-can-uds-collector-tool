from __future__ import annotations

import csv
from copy import copy
from datetime import datetime
import logging
import math
from pathlib import Path
import time

from PySide6.QtCore import QObject, Property, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor

from app_can.CanDevice import CanDevice
from colors import RowColor
from j1939.j1939_can_identifier import J1939CanIdentifier
from uds.data_identifiers import UdsData
from uds.bootloader import Bootloader
from uds.firmware import Firmware, FirmwareState
from uds.services.ecu_reset import ServiceEcuReset
from uds.services.read_data_by_id import ServiceReadDataById
from uds.uds_identifiers import UdsIdentifiers
from ui.qml.collector_csv_manager import CollectorCsvManager
from ui.qml.app_controller_parts.can_traffic import AppControllerCanTrafficMixin
from ui.qml.app_controller_parts.collector import AppControllerCollectorMixin

LOGGER = logging.getLogger(__name__)


class FirmwareLoadWorker(QObject):
    finished = Signal(str, bool, bytes, str)

    def __init__(self, file_path: str):
        super().__init__()
        self._file_path = file_path

    @Slot()
    def run(self):
        firmware = Firmware(self._file_path)
        if firmware.state == FirmwareState.successfully_uploaded and firmware.binary_content is not None:
            self.finished.emit(self._file_path, True, firmware.binary_content, "")
            return
        self.finished.emit(self._file_path, False, b"", "Не удалось открыть BIN файл.")


class AppController(QObject, AppControllerCanTrafficMixin, AppControllerCollectorMixin):
    CAN_FILTER_FIELDS = ("time", "dir", "frameId", "pgn", "src", "dst", "j1939", "dlc", "uds", "data")

    devicesChanged = Signal()
    selectedDeviceIndexChanged = Signal()
    deviceInfoChanged = Signal()
    connectionStateChanged = Signal()
    traceStateChanged = Signal()
    firmwarePathChanged = Signal()
    progressChanged = Signal()
    logsChanged = Signal()
    canTrafficLogsChanged = Signal()
    canFilterOptionsChanged = Signal()
    infoMessage = Signal(str, str)
    programmingActiveChanged = Signal()
    autoResetBeforeProgrammingChanged = Signal()
    debugEnabledChanged = Signal()
    firmwareLoadingChanged = Signal()
    transferByteOrderIndexChanged = Signal()
    sourceAddressTextChanged = Signal()
    sourceAddressBusyChanged = Signal()
    sourceAddressOperationChanged = Signal()
    udsIdentifiersChanged = Signal()
    observedUdsCandidateChanged = Signal()
    canJournalEnabledChanged = Signal()
    autoDetectEnabledChanged = Signal()
    collectorNodesChanged = Signal()
    collectorOutputDirectoryChanged = Signal()
    collectorPollIntervalChanged = Signal()
    collectorCyclePauseChanged = Signal()
    collectorStateChanged = Signal()
    collectorTrendChanged = Signal()

    def __init__(self):
        super().__init__()

        self._can = CanDevice.instance()
        self._bootloader = Bootloader()
        self._bootloader.set_transfer_byte_order("big")
        self._ui_ecu_reset_service = ServiceEcuReset()

        # Display labels for ComboBox and actual hardware indexes from TSCAN.
        self._devices: list[str] = []
        self._device_indices: list[int] = []
        self._selected_device_index = -1

        self._manufacturer = ""
        self._product = ""
        self._serial = ""
        self._device_handle = ""

        self._firmware_path = ""
        self._firmware = None
        self._progress_value = 0
        self._progress_max = 1

        self._logs: list[dict[str, str]] = []
        self._can_traffic_logs: list[dict[str, str]] = []
        self._filtered_can_traffic_logs: list[dict[str, str]] = []
        self._can_filter_values: dict[str, str] = {field: "" for field in self.CAN_FILTER_FIELDS}
        self._can_filter_options: dict[str, list[str]] = {field: [] for field in self.CAN_FILTER_FIELDS}
        self._can_filter_option_seen: dict[str, set[str]] = {field: set() for field in self.CAN_FILTER_FIELDS}
        self._can_filter_option_limits: dict[str, int] = {
            "time": 60,
            "dir": 10,
            "frameId": 120,
            "pgn": 120,
            "src": 120,
            "dst": 120,
            "j1939": 120,
            "dlc": 20,
            "uds": 120,
            "data": 80,
        }
        self._programming_active = False
        self._auto_reset_before_programming = True
        self._auto_reset_delay_ms = 650
        self._pending_programming_after_reset = False
        self._debug_enabled = False
        self._firmware_loading = False
        self._transfer_byte_order_index = 0
        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self._source_address_busy = False
        self._source_address_operation = ""
        self._can_journal_enabled = True
        self._auto_detect_enabled = True
        self._collector_read_service = ServiceReadDataById()
        self._collector_read_service.set_byte_order("big")
        self._collector_nodes: dict[int, dict[str, object]] = {}
        self._collector_node_order: list[int] = []
        self._collector_nodes_view: list[dict[str, str]] = []
        self._collector_state = "stopped"
        self._collector_poll_interval_ms = 1000
        self._collector_cycle_pause_ms = 1000
        self._project_root_directory = self._resolve_project_root_directory()
        self._collector_output_directory = ""
        self._collector_output_is_session_dir = False
        default_collector_directory = self._project_root_directory / "logs"
        if not self._apply_collector_output_directory(default_collector_directory, emit_signal=False):
            self._apply_collector_output_directory(Path.cwd() / "logs", emit_signal=False)
        self._collector_session_dir: Path | None = None
        self._collector_csv_managers: dict[int, CollectorCsvManager] = {}
        self._collector_poll_vars = [UdsData.raw_fuel_level, UdsData.raw_temperature]
        self._collector_poll_node_index = 0
        self._collector_poll_phase = 0
        self._collector_trend_points: list[dict[str, object]] = []
        self._collector_trend_max_points = 180
        # Keep bounded per-node trend history to avoid unbounded memory and repaint cost.
        self._collector_trend_history_limit = 600
        self._collector_trend_caption = "Ожидание данных от узлов..."
        self._collector_trend_latest_fuel = 0.0
        self._collector_trend_latest_temperature = 0.0
        self._collector_trend_points_by_node: dict[int, list[dict[str, object]]] = {}
        self._collector_trend_nodes_view: list[dict[str, object]] = []
        self._collector_trend_metrics_rows: list[dict[str, str]] = []
        self._collector_trend_network_metrics: dict[str, float | int] = {
            "nodesCount": 0,
            "fuelMean": 0.0,
            "temperatureMean": 0.0,
            "fuelSpread": 0.0,
            "temperatureSpread": 0.0,
            "fuelStd": 0.0,
            "temperatureStd": 0.0,
        }
        self._collector_trend_csv_series: list[dict[str, object]] = []

        self._tx_priority_text = ""
        self._tx_pgn_text = ""
        self._tx_src_text = ""
        self._tx_dst_text = ""
        self._tx_identifier_text = ""
        self._rx_priority_text = ""
        self._rx_pgn_text = ""
        self._rx_src_text = ""
        self._rx_dst_text = ""
        self._rx_identifier_text = ""
        self._observed_node_stats: dict[int, dict[str, object]] = {}
        self._observed_candidate_order: list[int] = []
        self._observed_candidate_values: list[int] = []
        self._observed_candidate_items: list[str] = []
        self._observed_candidate_index = -1
        self._observed_frame_seq = 0
        self._observed_uds_text = "Ожидание входящих J1939 RX кадров для автоопределения адреса..."
        self._perf_origin = time.perf_counter()
        self._wall_origin = time.time()
        self._rx_time_anchor_raw: float | None = None
        self._rx_time_anchor_wall: float | None = None

        self._refresh_uds_identifier_texts(emit_signal=False)

        self._firmware_loader_thread: QThread | None = None
        self._firmware_loader_worker: FirmwareLoadWorker | None = None

        self._bootloader.signal_new_state.connect(self._on_bootloader_state)
        self._bootloader.signal_data_sent.connect(self._on_data_sent)
        self._bootloader.signal_finished.connect(self._on_programming_finished)
        self._bootloader.signal_source_address_applied.connect(self._on_source_address_applied)
        self._bootloader.signal_source_address_read.connect(self._on_source_address_read)

        self._can.signal_new_message.connect(self._on_can_message)
        self._can.signal_tracing_started.connect(self._on_trace_state_event)
        self._can.signal_tracing_stopped.connect(self._on_trace_state_event)

        self._can_filter_rebuild_timer = QTimer(self)
        self._can_filter_rebuild_timer.setSingleShot(True)
        self._can_filter_rebuild_timer.setInterval(90)
        self._can_filter_rebuild_timer.timeout.connect(self._rebuild_can_traffic_view)

        self._programming_start_timer = QTimer(self)
        self._programming_start_timer.setSingleShot(True)
        self._programming_start_timer.timeout.connect(self._start_programming_after_reset)

        self._collector_poll_timer = QTimer(self)
        self._collector_poll_timer.setInterval(self._collector_poll_interval_ms)
        self._collector_poll_timer.timeout.connect(self._on_collector_poll_tick)
        self._collector_poll_timer.start()

        self._collector_view_update_pending_nodes = False
        self._collector_view_update_pending_trend = False
        self._collector_view_update_timer = QTimer(self)
        self._collector_view_update_timer.setSingleShot(True)
        self._collector_view_update_timer.setInterval(120)
        self._collector_view_update_timer.timeout.connect(self._flush_collector_views_update)

        self._rebuild_can_traffic_view()

    @Property("QStringList", notify=devicesChanged)
    def devices(self):
        return self._devices

    @Property(int, notify=selectedDeviceIndexChanged)
    def selectedDeviceIndex(self):
        return self._selected_device_index

    @Property(str, notify=deviceInfoChanged)
    def manufacturer(self):
        return self._manufacturer

    @Property(str, notify=deviceInfoChanged)
    def product(self):
        return self._product

    @Property(str, notify=deviceInfoChanged)
    def serial(self):
        return self._serial

    @Property(str, notify=deviceInfoChanged)
    def deviceHandle(self):
        return self._device_handle

    @Property(bool, notify=connectionStateChanged)
    def connected(self):
        return self._can.is_connect

    @Property(str, notify=connectionStateChanged)
    def connectionActionText(self):
        return "Отключиться" if self._can.is_connect else "Подключиться"

    @Property(bool, notify=traceStateChanged)
    def tracing(self):
        return self._can.is_trace

    @Property(str, notify=traceStateChanged)
    def traceActionText(self):
        return "Остановить трассировку" if self._can.is_trace else "Запустить трассировку"

    @Property(str, notify=firmwarePathChanged)
    def firmwarePath(self):
        return self._firmware_path

    @Property(int, notify=progressChanged)
    def progressValue(self):
        return self._progress_value

    @Property(int, notify=progressChanged)
    def progressMax(self):
        return self._progress_max

    @Property("QVariantList", notify=logsChanged)
    def logs(self):
        return self._logs

    @Property("QVariantList", notify=canTrafficLogsChanged)
    def canTrafficLogs(self):
        return self._can_traffic_logs

    @Property("QVariantList", notify=canTrafficLogsChanged)
    def filteredCanTrafficLogs(self):
        return self._filtered_can_traffic_logs

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterTimeOptions(self):
        return self._can_filter_options.get("time", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDirOptions(self):
        return self._can_filter_options.get("dir", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterIdOptions(self):
        return self._can_filter_options.get("frameId", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterPgnOptions(self):
        return self._can_filter_options.get("pgn", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterSrcOptions(self):
        return self._can_filter_options.get("src", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDstOptions(self):
        return self._can_filter_options.get("dst", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterJ1939Options(self):
        return self._can_filter_options.get("j1939", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDlcOptions(self):
        return self._can_filter_options.get("dlc", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterUdsOptions(self):
        return self._can_filter_options.get("uds", [])

    @Property("QStringList", notify=canFilterOptionsChanged)
    def canFilterDataOptions(self):
        return self._can_filter_options.get("data", [])

    @Property(bool, notify=programmingActiveChanged)
    def programmingActive(self):
        return self._programming_active

    @Property(bool, notify=autoResetBeforeProgrammingChanged)
    def autoResetBeforeProgramming(self):
        return self._auto_reset_before_programming

    @Property(bool, notify=debugEnabledChanged)
    def debugEnabled(self):
        return self._debug_enabled

    @Property(bool, notify=canJournalEnabledChanged)
    def canJournalEnabled(self):
        return self._can_journal_enabled

    @Property(bool, notify=autoDetectEnabledChanged)
    def autoDetectEnabled(self):
        return self._auto_detect_enabled

    @Property(bool, notify=firmwareLoadingChanged)
    def firmwareLoading(self):
        return self._firmware_loading

    @Property(int, notify=transferByteOrderIndexChanged)
    def transferByteOrderIndex(self):
        return self._transfer_byte_order_index

    @Property(str, notify=sourceAddressTextChanged)
    def sourceAddressText(self):
        return self._source_address_text

    @Property(bool, notify=sourceAddressBusyChanged)
    def sourceAddressBusy(self):
        return self._source_address_busy

    @Property(str, notify=sourceAddressOperationChanged)
    def sourceAddressOperation(self):
        return self._source_address_operation

    @Property(str, notify=udsIdentifiersChanged)
    def txPriorityText(self):
        return self._tx_priority_text

    @Property(str, notify=udsIdentifiersChanged)
    def txPgnText(self):
        return self._tx_pgn_text

    @Property(str, notify=udsIdentifiersChanged)
    def txSrcText(self):
        return self._tx_src_text

    @Property(str, notify=udsIdentifiersChanged)
    def txDstText(self):
        return self._tx_dst_text

    @Property(str, notify=udsIdentifiersChanged)
    def txIdentifierText(self):
        return self._tx_identifier_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxPriorityText(self):
        return self._rx_priority_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxPgnText(self):
        return self._rx_pgn_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxSrcText(self):
        return self._rx_src_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxDstText(self):
        return self._rx_dst_text

    @Property(str, notify=udsIdentifiersChanged)
    def rxIdentifierText(self):
        return self._rx_identifier_text

    @Property(bool, notify=observedUdsCandidateChanged)
    def observedUdsCandidateAvailable(self):
        return 0 <= self._observed_candidate_index < len(self._observed_candidate_values)

    @Property(str, notify=observedUdsCandidateChanged)
    def observedUdsCandidateText(self):
        return self._observed_uds_text

    @Property("QStringList", notify=observedUdsCandidateChanged)
    def observedUdsCandidates(self):
        return self._observed_candidate_items

    @Property(int, notify=observedUdsCandidateChanged)
    def selectedObservedUdsCandidateIndex(self):
        return self._observed_candidate_index

    @Property("QVariantList", notify=collectorNodesChanged)
    def collectorNodes(self):
        return self._collector_nodes_view

    @Property(str, notify=collectorOutputDirectoryChanged)
    def collectorOutputDirectory(self):
        return self._collector_output_directory

    @Property(int, notify=collectorPollIntervalChanged)
    def collectorPollIntervalMs(self):
        return self._collector_poll_interval_ms

    @Property(int, notify=collectorCyclePauseChanged)
    def collectorCyclePauseMs(self):
        return self._collector_cycle_pause_ms

    @Property(str, notify=collectorStateChanged)
    def collectorStateText(self):
        if self._collector_state == "recording":
            return "Статус записи: идет запись"
        if self._collector_state == "paused":
            return "Статус записи: пауза"
        return "Статус записи: остановлено"

    @Property(bool, notify=collectorStateChanged)
    def collectorRecording(self):
        return self._collector_state == "recording"

    @Property(bool, notify=collectorStateChanged)
    def collectorPaused(self):
        return self._collector_state == "paused"

    @Property("QVariantList", notify=collectorTrendChanged)
    def collectorTrendPoints(self):
        return self._collector_trend_points

    @Property(str, notify=collectorTrendChanged)
    def collectorTrendCaption(self):
        return self._collector_trend_caption

    @Property(str, notify=collectorTrendChanged)
    def collectorTrendFuelText(self):
        return f"{float(self._collector_trend_latest_fuel):.1f} %"

    @Property(str, notify=collectorTrendChanged)
    def collectorTrendTemperatureText(self):
        return f"{float(self._collector_trend_latest_temperature):.1f} °C"

    @Property("QVariantList", notify=collectorTrendChanged)
    def collectorTrendNodes(self):
        return self._collector_trend_nodes_view

    @Property("QStringList", notify=collectorTrendChanged)
    def collectorTrendNodeLabels(self):
        return [str(item.get("node", "")) for item in self._collector_trend_nodes_view]

    @Property("QVariantList", notify=collectorTrendChanged)
    def collectorTrendMetricsRows(self):
        return self._collector_trend_metrics_rows

    @Property("QVariantMap", notify=collectorTrendChanged)
    def collectorTrendNetworkMetrics(self):
        return self._collector_trend_network_metrics

    @Property("QVariantList", notify=collectorTrendChanged)
    def collectorTrendCsvSeries(self):
        return self._collector_trend_csv_series

    @Slot(bool)
    def setDebugEnabled(self, enabled):
        value = bool(enabled)
        if self._debug_enabled == value:
            return
        self._debug_enabled = value
        self.debugEnabledChanged.emit()
        self.infoMessage.emit("Debug", "Debug mode enabled." if value else "Debug mode disabled.")

    @Slot(bool)
    def setCanJournalEnabled(self, enabled):
        value = bool(enabled)
        if self._can_journal_enabled == value:
            return
        self._can_journal_enabled = value
        self.canJournalEnabledChanged.emit()
        if value:
            self._append_log("CAN journal capture resumed.", RowColor.green)
        else:
            self._append_log("CAN journal capture paused.", RowColor.yellow)

    @Slot(bool)
    def setAutoDetectEnabled(self, enabled):
        value = bool(enabled)
        if self._auto_detect_enabled == value:
            return
        self._auto_detect_enabled = value
        self.autoDetectEnabledChanged.emit()
        if value:
            self._append_log("Auto-detect from RX stream enabled.", RowColor.green)
        else:
            self._append_log("Auto-detect from RX stream paused.", RowColor.yellow)

    @Slot(bool)
    def setAutoResetBeforeProgramming(self, enabled):
        value = bool(enabled)
        if self._auto_reset_before_programming == value:
            return
        self._auto_reset_before_programming = value
        self.autoResetBeforeProgrammingChanged.emit()
        state_text = "включен" if value else "отключен"
        self._append_log(f"Автосброс перед программированием: {state_text}", QColor("#0ea5e9"))

    @Slot(int)
    def setTransferByteOrderIndex(self, index):
        try:
            parsed_index = int(index)
        except (TypeError, ValueError):
            parsed_index = 0

        new_index = 1 if parsed_index == 1 else 0
        if self._transfer_byte_order_index == new_index:
            return

        self._transfer_byte_order_index = new_index
        self.transferByteOrderIndexChanged.emit()

        byte_order = "little" if new_index == 1 else "big"
        self._bootloader.set_transfer_byte_order(byte_order)
        self._collector_read_service.set_byte_order(byte_order)

        label = "Little Endian" if new_index == 1 else "Big Endian"
        self._append_log(f"Выбран порядок байтов: {label}", QColor("#0ea5e9"))
        self.infoMessage.emit("Протокол", f"Выбран порядок байтов: {label}.")

    @Slot(str)
    def setSourceAddressText(self, text):
        value = str(text).strip()
        if self._source_address_text == value:
            return
        self._source_address_text = value
        self.sourceAddressTextChanged.emit()

    @Slot(str)
    def applySourceAddress(self, text):
        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Изменение Source Address уже выполняется.")
            return

        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять Source Address во время программирования.")
            return

        try:
            source_address = self._parse_source_address(text)
        except ValueError:
            self.infoMessage.emit("Протокол", "Некорректный Source Address. Допустимо 0..255 или 0x00..0xFF.")
            return

        self._set_source_address_operation("write")
        self._set_source_address_busy(True)
        if not self._bootloader.write_can_source_address(source_address):
            self._set_source_address_busy(False)
            self.infoMessage.emit("Протокол", "Не удалось отправить запрос на изменение Source Address.")
            return

        self._source_address_text = f"0x{source_address:02X}"
        self.sourceAddressTextChanged.emit()

    @Slot()
    def readSourceAddress(self):
        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Операция с Source Address уже выполняется.")
            return

        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя читать Source Address во время программирования.")
            return

        self._set_source_address_operation("read")
        self._set_source_address_busy(True)
        if not self._bootloader.read_can_source_address():
            self._set_source_address_busy(False)
            self.infoMessage.emit("Протокол", "Не удалось отправить запрос на чтение Source Address.")

    @Slot()
    def refreshUdsIdentifiers(self):
        self._refresh_uds_identifier_texts()
        if len(self._observed_candidate_values) > 0:
            self._rebuild_observed_candidate_list()

    @Slot()
    def applyObservedUdsIdentifiers(self):
        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять UDS идентификаторы во время программирования.")
            return

        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Подождите завершения операции Source Address.")
            return

        if not (0 <= self._observed_candidate_index < len(self._observed_candidate_values)):
            self.infoMessage.emit("Протокол", "Нет кандидатов из RX J1939 потока для автоопределения адреса.")
            return

        device_sa = int(self._observed_candidate_values[self._observed_candidate_index]) & 0xFF
        node = self._observed_node_stats.get(device_sa, {})
        tester_sa, _ = self._choose_tester_sa_for_node(node, int(UdsIdentifiers.tx.src) & 0xFF)
        tester_sa = int(tester_sa) & 0xFF

        UdsIdentifiers.tx.src = tester_sa
        UdsIdentifiers.tx.dst = device_sa
        UdsIdentifiers.rx.src = device_sa
        UdsIdentifiers.rx.dst = tester_sa

        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self.sourceAddressTextChanged.emit()
        self._refresh_uds_identifier_texts()

        self.infoMessage.emit(
            "Протокол",
            (
                f"Идентификаторы обновлены из RX потока: "
                f"SA устройства=0x{device_sa:02X}, SA тестера=0x{tester_sa:02X}."
            ),
        )

    @Slot()
    def resetObservedUdsCandidate(self):
        self._reset_observed_uds_candidate()

    @Slot(int)
    def setSelectedObservedUdsCandidateIndex(self, index):
        try:
            new_index = int(index)
        except (TypeError, ValueError):
            return

        if new_index < 0 or new_index >= len(self._observed_candidate_values):
            return

        if self._observed_candidate_index == new_index:
            return

        self._observed_candidate_index = new_index
        self._update_observed_candidate_text()
        self.observedUdsCandidateChanged.emit()

    @Slot(str, str, str, str, str, str, str, str)
    def applyUdsIdentifiers(self, tx_priority, tx_pgn, tx_src, tx_dst, rx_priority, rx_pgn, rx_src, rx_dst):
        if self._programming_active:
            self.infoMessage.emit("Протокол", "Нельзя менять UDS идентификаторы во время программирования.")
            return

        if self._source_address_busy:
            self.infoMessage.emit("Протокол", "Подождите завершения операции Source Address.")
            return

        try:
            tx_priority_value = self._parse_uint_field(tx_priority, 0, 0x7, "TX Priority")
            tx_pgn_value = self._parse_uint_field(tx_pgn, 0, 0xFFFF, "TX PGN")
            tx_src_value = self._parse_uint_field(tx_src, 0, 0xFF, "TX Source")
            tx_dst_value = self._parse_uint_field(tx_dst, 0, 0xFF, "TX Destination")

            rx_priority_value = self._parse_uint_field(rx_priority, 0, 0x7, "RX Priority")
            rx_pgn_value = self._parse_uint_field(rx_pgn, 0, 0xFFFF, "RX PGN")
            rx_src_value = self._parse_uint_field(rx_src, 0, 0xFF, "RX Source")
            rx_dst_value = self._parse_uint_field(rx_dst, 0, 0xFF, "RX Destination")
        except ValueError as exc:
            self.infoMessage.emit("Протокол", str(exc))
            return

        UdsIdentifiers.tx.priority = tx_priority_value
        UdsIdentifiers.tx.pgn = tx_pgn_value
        UdsIdentifiers.tx.src = tx_src_value
        UdsIdentifiers.tx.dst = tx_dst_value

        UdsIdentifiers.rx.priority = rx_priority_value
        UdsIdentifiers.rx.pgn = rx_pgn_value
        UdsIdentifiers.rx.src = rx_src_value
        UdsIdentifiers.rx.dst = rx_dst_value

        self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
        self.sourceAddressTextChanged.emit()

        self._refresh_uds_identifier_texts()
        self.infoMessage.emit(
            "Протокол",
            f"UDS идентификаторы обновлены: TX={self._tx_identifier_text}, RX={self._rx_identifier_text}.",
        )

    @Slot(str)
    def debugEvent(self, text):
        if not self._debug_enabled:
            return
        message = str(text)
        LOGGER.info("QML debug: %s", message)
        self._append_log(f"DEBUG: {message}", QColor("#93c5fd"))
        self.infoMessage.emit("Отладка", message)

    @Slot()
    def scanDevices(self):
        if self._debug_enabled:
            LOGGER.info("scanDevices() called")
        devices_count = self._can.get_devices()
        if devices_count is None:
            self.infoMessage.emit("Сканирование", "TSCAN API не вернул список устройств.")
            self._devices = []
            self._device_indices = []
            self.devicesChanged.emit()
            self._selected_device_index = -1
            self.selectedDeviceIndexChanged.emit()
            self._refresh_device_info()
            return

        count = int(getattr(devices_count, "value", 0) or 0)
        count = max(count, 0)

        self._device_indices = list(range(count))
        labels: list[str] = []

        for hw_index in self._device_indices:
            manufacturer = ""
            product = ""
            serial = ""

            try:
                self._can.update_device_info(hw_index)
                info = self._can.device_info
                manufacturer = self._decode_bytes(getattr(info.manufacturer, "value", None))
                product = self._decode_bytes(getattr(info.product, "value", None))
                serial = self._decode_bytes(getattr(info.serial, "value", None))
            except Exception:
                # Keep scan resilient even if one adapter fails info query.
                pass

            base_name = product or manufacturer or "CAN-адаптер"
            label = f"{hw_index}: {base_name}"
            if serial:
                label += f" [{serial}]"

            labels.append(label)

        self._devices = labels
        self.devicesChanged.emit()

        if self._selected_device_index >= len(self._devices):
            self._selected_device_index = -1

        if self._selected_device_index == -1 and self._devices:
            self._selected_device_index = 0

        self.selectedDeviceIndexChanged.emit()
        self._refresh_device_info()

        if count == 0:
            self.infoMessage.emit("Сканирование", "CAN-адаптеры не найдены.")
        else:
            self.infoMessage.emit("Сканирование", f"Найдено CAN-адаптеров: {count}.")

    @Slot(int)
    def setSelectedDeviceIndex(self, index):
        if index < 0 or index >= len(self._devices):
            return

        if self._selected_device_index == index:
            return

        self._selected_device_index = index
        self.selectedDeviceIndexChanged.emit()
        self._refresh_device_info()

    @Slot()
    def toggleConnection(self):
        if self._can.is_connect:
            self._can.disconnect_device()
            self._can.stop_trace()
            self._device_handle = ""
            self._reset_observed_uds_candidate()
            self._collector_state = "stopped"
            self.collectorStateChanged.emit()
            self._collector_session_dir = None
            self._collector_csv_managers = {}
            if self._programming_start_timer.isActive():
                self._programming_start_timer.stop()
            self._pending_programming_after_reset = False
            self._set_programming_active(False)
            self.deviceInfoChanged.emit()
            self.connectionStateChanged.emit()
            self.traceStateChanged.emit()
            return

        hw_index = self._selected_hw_index()
        if hw_index < 0:
            self.infoMessage.emit("Подключение", "Выберите устройство CAN-адаптера.")
            return

        handle = self._can.connect_to(hw_index)
        if handle is None or handle.value == 0:
            self.infoMessage.emit("Подключение", "Не удалось подключиться к CAN-адаптеру.")
        else:
            self._device_handle = str(handle.value)
            self._refresh_device_info()

        self.connectionStateChanged.emit()
        self.traceStateChanged.emit()

    @Slot(int, int, bool)
    def toggleTrace(self, channel_index, baud_rate, terminator):
        if not self._can.is_connect:
            self.infoMessage.emit("Подключение", "Сначала подключите CAN-адаптер.")
            return

        if self._can.is_trace:
            self._can.stop_trace()
        else:
            self._can.start_trace(channel_index, baud_rate, terminator)

        self.traceStateChanged.emit()

    @Slot(str)
    def loadFirmware(self, path_or_url):
        file_path = self._to_local_path(path_or_url)
        if not file_path:
            self.infoMessage.emit("Прошивка", "Путь не выбран.")
            return

        if self._firmware_loading:
            self.infoMessage.emit("Прошивка", "Загрузка BIN файла уже выполняется. Подождите.")
            return

        # Update UI path immediately after selection, even before file validation.
        self._firmware_path = str(Path(file_path))
        self.firmwarePathChanged.emit()

        self._set_firmware_loading(True)
        self._append_log("Чтение BIN файла...", RowColor.blue)
        self.infoMessage.emit("Прошивка", "BIN файл выбран. Идет загрузка...")

        # Defer actual worker start to the next event loop turn so UI updates instantly.
        QTimer.singleShot(0, lambda p=file_path: self._start_firmware_loading(p))

    @Slot()
    def startProgramming(self):
        if self._programming_active:
            return

        if not self._can.is_connect:
            self.infoMessage.emit("Программирование", "Сначала подключите CAN-адаптер.")
            return

        if self._firmware_loading:
            self.infoMessage.emit("Программирование", "Дождитесь завершения загрузки BIN-файла.")
            return

        self._set_programming_active(True)

        if self._auto_reset_before_programming:
            self._pending_programming_after_reset = True
            self._append_log("Автосброс: отправка команды перехода в загрузчик", RowColor.blue)

            try:
                self._ui_ecu_reset_service.ecu_uds_reset()
            except Exception:
                self._pending_programming_after_reset = False
                self._set_programming_active(False)
                self._append_log("Автосброс: ошибка отправки команды", RowColor.red)
                self.infoMessage.emit("Программирование", "Не удалось отправить команду автосброса.")
                return

            self._programming_start_timer.start(self._auto_reset_delay_ms)
            return

        self._start_programming_flow()

    @Slot()
    def checkState(self):
        self._bootloader.check_state()

    @Slot()
    def resetToBootloader(self):
        if not self._can.is_connect:
            self.infoMessage.emit("Сброс", "Сначала подключите CAN-адаптер.")
            return

        self._ui_ecu_reset_service.ecu_uds_reset()
        self._append_log("Отправлена команда сброса в загрузчик", RowColor.blue)

    @Slot()
    def resetToMainProgram(self):
        if not self._can.is_connect:
            self.infoMessage.emit("Сброс", "Сначала подключите CAN-адаптер.")
            return

        self._ui_ecu_reset_service.ecu_software_reset()
        self._append_log("Отправлена команда сброса в основное ПО", RowColor.blue)

    @Slot()
    def clearLogs(self):
        self._logs = []
        self.logsChanged.emit()

    @Slot(str)
    def setCollectorOutputDirectory(self, path_or_url):
        resolved = self._to_local_path(path_or_url)
        if not resolved:
            return

        candidate = Path(resolved)
        if candidate.is_file():
            candidate = candidate.parent

        if not self._apply_collector_output_directory(candidate):
            self.infoMessage.emit("Коллектор", "Не удалось создать каталог выгрузки CSV.")
            return

        self._collector_output_is_session_dir = False
        self.infoMessage.emit("Коллектор", "Каталог выгрузки CSV обновлен.")

    @Slot()
    def createCollectorTimestampedLogsDirectory(self):
        timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        base_logs_dir = self._project_root_directory / "logs"
        try:
            base_logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.infoMessage.emit("Коллектор", "Не удалось создать корневой каталог logs.")
            return

        candidate = base_logs_dir / timestamp
        if not self._apply_collector_output_directory(candidate):
            self.infoMessage.emit("Коллектор", "Не удалось создать каталог с датой и временем внутри logs.")
            return

        self._collector_output_is_session_dir = True
        self.infoMessage.emit("Коллектор", f"Создан каталог для CSV: {self._collector_output_directory}")

    @Slot(str)
    def setCollectorPollIntervalMs(self, interval_value):
        try:
            parsed = int(str(interval_value).strip())
        except (TypeError, ValueError):
            self.infoMessage.emit("Коллектор", "Интервал опроса должен быть целым числом в миллисекундах.")
            return

        bounded = max(30, min(10000, parsed))
        if bounded != parsed:
            self.infoMessage.emit("Коллектор", "Интервал ограничен диапазоном 30..10000 мс.")

        if self._collector_poll_interval_ms == bounded:
            return

        self._collector_poll_interval_ms = bounded
        if self._collector_poll_phase == 1:
            self._collector_poll_timer.setInterval(self._collector_poll_interval_ms)
        self.collectorPollIntervalChanged.emit()
        self._append_log(f"Интервал UDS-опроса: {self._collector_poll_interval_ms} мс", RowColor.blue)

    @Slot(str)
    def setCollectorCyclePauseMs(self, interval_value):
        try:
            parsed = int(str(interval_value).strip())
        except (TypeError, ValueError):
            self.infoMessage.emit("Коллектор", "Пауза между циклами должна быть целым числом в миллисекундах.")
            return

        bounded = max(30, min(10000, parsed))
        if bounded != parsed:
            self.infoMessage.emit("Коллектор", "Пауза между циклами ограничена диапазоном 30..10000 мс.")

        if self._collector_cycle_pause_ms == bounded:
            return

        self._collector_cycle_pause_ms = bounded
        if self._collector_poll_phase == 0:
            self._collector_poll_timer.setInterval(self._collector_cycle_pause_ms)
        self.collectorCyclePauseChanged.emit()
        self._append_log(f"Пауза между циклами UDS: {self._collector_cycle_pause_ms} мс", RowColor.blue)

    @Slot()
    def startCollectorRecording(self):
        if self._collector_state == "recording":
            return

        if not self._can.is_connect:
            self.infoMessage.emit("Коллектор", "Сначала подключите CAN-адаптер.")
            return

        if not self._can.is_trace:
            self.infoMessage.emit("Коллектор", "Сначала включите трассировку CAN.")
            return

        try:
            base_dir = Path(self._collector_output_directory)
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.infoMessage.emit("Коллектор", "Не удалось создать каталог для CSV.")
            return

        if self._collector_state == "stopped" or self._collector_session_dir is None:
            if self._collector_output_is_session_dir:
                self._collector_session_dir = base_dir
            else:
                self._collector_session_dir = base_dir / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._collector_session_dir.mkdir(parents=True, exist_ok=True)
            self._collector_csv_managers = {}
            self._append_log(f"Сессия записи: {self._collector_session_dir}", RowColor.green)
        else:
            self._append_log("Продолжение записи CSV.", RowColor.blue)

        self._collector_state = "recording"
        self.collectorStateChanged.emit()
        self._set_programming_active(True)

    @Slot()
    def pauseCollectorRecording(self):
        if self._collector_state != "recording":
            return
        self._collector_state = "paused"
        self.collectorStateChanged.emit()
        self._set_programming_active(False)
        self._append_log("Запись CSV приостановлена.", RowColor.yellow)

    @Slot()
    def stopCollectorRecording(self):
        if self._collector_state == "stopped":
            return
        self._collector_state = "stopped"
        self.collectorStateChanged.emit()
        self._set_programming_active(False)
        self._collector_session_dir = None
        self._collector_csv_managers = {}
        self._append_log("Запись CSV остановлена.", RowColor.blue)

    @Slot()
    def clearCollectorNodes(self):
        self._collector_nodes = {}
        self._collector_node_order = []
        self._collector_poll_node_index = 0
        self._collector_poll_phase = 0
        self._collector_nodes_view = []
        self.collectorNodesChanged.emit()
        self._reset_collector_trend()

    @Slot("QVariant")
    def loadCollectorTrendCsv(self, path_or_urls):
        raw_items: list[object] = []
        if isinstance(path_or_urls, (list, tuple, set)):
            raw_items.extend(list(path_or_urls))
        else:
            raw_items.append(path_or_urls)

        paths: list[Path] = []
        for item in raw_items:
            resolved = self._to_local_path(item)
            if not resolved:
                continue
            try:
                paths.append(Path(resolved).expanduser().resolve())
            except Exception:
                paths.append(Path(resolved))

        if len(paths) == 0:
            self.infoMessage.emit("Графики", "CSV файл не выбран.")
            return

        loaded_series = list(self._collector_trend_csv_series)
        loaded_by_path = {
            str(item.get("path", "")): item
            for item in loaded_series
            if isinstance(item, dict)
        }

        appended_count = 0
        total_points = 0
        for csv_path in paths:
            parsed = self._parse_collector_trend_csv_file(csv_path)
            if parsed is None:
                continue
            loaded_by_path[str(parsed.get("path", ""))] = parsed
            appended_count += 1
            total_points += int(parsed.get("count", 0))

        if appended_count <= 0:
            self.infoMessage.emit("Графики", "Не удалось загрузить данные из выбранных CSV файлов.")
            return

        self._collector_trend_csv_series = list(loaded_by_path.values())
        self.collectorTrendChanged.emit()
        self.infoMessage.emit(
            "Графики",
            f"Загружено CSV файлов: {appended_count}, точек: {total_points}.",
        )

    @Slot()
    def clearCollectorTrendCsv(self):
        if len(self._collector_trend_csv_series) == 0:
            return
        self._collector_trend_csv_series = []
        self.collectorTrendChanged.emit()
        self.infoMessage.emit("Графики", "Загруженные CSV данные очищены.")

    @Slot()
    def clearCanTrafficLogs(self):
        if self._can_filter_rebuild_timer.isActive():
            self._can_filter_rebuild_timer.stop()
        self._can_traffic_logs = []
        self._rebuild_can_traffic_view()

    @Slot(str, str)
    def setCanTrafficFilter(self, field, value):
        key = str(field or "").strip()
        if key not in self._can_filter_values:
            return

        text = str(value or "").strip()
        if self._can_filter_values.get(key, "") == text:
            return

        self._can_filter_values[key] = text
        self._schedule_can_traffic_rebuild(restart=True)

    @Slot()
    def resetCanTrafficFilters(self):
        updated = False
        for field in self.CAN_FILTER_FIELDS:
            if self._can_filter_values.get(field):
                self._can_filter_values[field] = ""
                updated = True
        if updated:
            self._schedule_can_traffic_rebuild(restart=True)

    def _on_bootloader_state(self, text, color):
        self._append_log(text, color)

    def _on_data_sent(self, value):
        clamped_value = min(max(value, 0), self._progress_max)
        if self._progress_value == clamped_value:
            return
        self._progress_value = clamped_value
        self.progressChanged.emit()

    def _on_programming_finished(self, success):
        if self._programming_start_timer.isActive():
            self._programming_start_timer.stop()
        self._pending_programming_after_reset = False
        self._set_programming_active(False)
        if not success:
            return

        self._progress_value = self._progress_max
        self.progressChanged.emit()
        self._append_log("Программирование успешно завершено", RowColor.green)

        if not self._can.is_connect:
            self.infoMessage.emit(
                "Программирование",
                "Программирование завершено, но CAN отключен: автосброс в основное ПО не отправлен.",
            )
            return

        try:
            self._ui_ecu_reset_service.ecu_software_reset()
            self._append_log("Автосброс: отправлена команда перехода в основное ПО", RowColor.blue)
            self.infoMessage.emit(
                "Программирование",
                "Программирование завершено. Отправлена команда запуска основного ПО.",
            )
        except Exception:
            self._append_log("Автосброс: ошибка отправки команды перехода в основное ПО", RowColor.red)
            self.infoMessage.emit(
                "Программирование",
                "Программирование завершено, но автосброс в основное ПО не отправлен.",
            )

    def _on_trace_state_event(self):
        self._rx_time_anchor_raw = None
        self._rx_time_anchor_wall = None
        self.traceStateChanged.emit()

    @Slot(int, bool)
    def _on_source_address_applied(self, source_address, success):
        self._set_source_address_busy(False)
        if success:
            self._source_address_text = f"0x{int(source_address) & 0xFF:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", f"Source Address изменен: {self._source_address_text}.")
        else:
            self._source_address_text = f"0x{UdsIdentifiers.rx.src:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", "Не удалось применить Source Address.")

    @Slot(int, bool)
    def _on_source_address_read(self, source_address, success):
        self._set_source_address_busy(False)
        if success:
            self._source_address_text = f"0x{int(source_address) & 0xFF:02X}"
            self.sourceAddressTextChanged.emit()
            self._refresh_uds_identifier_texts()
            self.infoMessage.emit("Протокол", f"Source Address считан: {self._source_address_text}.")
        else:
            self.infoMessage.emit("Протокол", "Не удалось прочитать Source Address.")

    @Slot(str, bool, bytes, str)
    def _on_firmware_loaded(self, _file_path, success, binary_content, error_text):
        try:
            if not success:
                self._append_log("Ошибка загрузки BIN файла", RowColor.red)
                self.infoMessage.emit("Прошивка", error_text if error_text else "Не удалось открыть BIN файл.")
                return

            self._bootloader.set_firmware(binary_content)

            file_size = len(binary_content)
            self._progress_max = max(file_size, 1)
            self._progress_value = 0
            self.progressChanged.emit()

            self._append_log(f"BIN файл загружен ({file_size} байт)", RowColor.green)
            self.infoMessage.emit("Прошивка", f"BIN файл успешно загружен. Размер: {file_size} байт.")
        finally:
            self._set_firmware_loading(False)

    def _start_firmware_loading(self, file_path: str):
        self._firmware_loader_thread = QThread(self)
        self._firmware_loader_worker = FirmwareLoadWorker(file_path)
        self._firmware_loader_worker.moveToThread(self._firmware_loader_thread)

        self._firmware_loader_thread.started.connect(self._firmware_loader_worker.run)
        self._firmware_loader_worker.finished.connect(self._on_firmware_loaded)
        self._firmware_loader_worker.finished.connect(self._firmware_loader_thread.quit)
        self._firmware_loader_worker.finished.connect(self._firmware_loader_worker.deleteLater)
        self._firmware_loader_thread.finished.connect(self._firmware_loader_thread.deleteLater)
        self._firmware_loader_thread.finished.connect(self._clear_firmware_loader)
        self._firmware_loader_thread.start()

    def _clear_firmware_loader(self):
        self._firmware_loader_thread = None
        self._firmware_loader_worker = None

    def _refresh_device_info(self):
        hw_index = self._selected_hw_index()
        if hw_index < 0:
            self._manufacturer = ""
            self._product = ""
            self._serial = ""
            self.deviceInfoChanged.emit()
            return

        self._can.update_device_info(hw_index)
        info = self._can.device_info

        self._manufacturer = self._decode_bytes(getattr(info.manufacturer, "value", None))
        self._product = self._decode_bytes(getattr(info.product, "value", None))
        self._serial = self._decode_bytes(getattr(info.serial, "value", None))
        self.deviceInfoChanged.emit()

    def _selected_hw_index(self) -> int:
        if self._selected_device_index < 0 or self._selected_device_index >= len(self._device_indices):
            return -1
        return self._device_indices[self._selected_device_index]

    @staticmethod
    def _decode_bytes(raw_value):
        if raw_value is None:
            return ""
        if isinstance(raw_value, bytes):
            try:
                return raw_value.decode("utf-8")
            except UnicodeDecodeError:
                return raw_value.decode("cp1251", errors="ignore")
        return str(raw_value)

    @staticmethod
    def _parse_uint_field(text, minimum: int, maximum: int, field_name: str) -> int:
        raw = str(text).strip()
        if not raw:
            raise ValueError(f"Поле '{field_name}' не заполнено.")

        base = 16 if raw.lower().startswith("0x") else 10
        try:
            value = int(raw, base)
        except ValueError as exc:
            raise ValueError(f"Поле '{field_name}' содержит некорректное число.") from exc

        if value < minimum or value > maximum:
            raise ValueError(f"Поле '{field_name}' вне диапазона {minimum}..{maximum}.")

        return value

    def _refresh_uds_identifier_texts(self, emit_signal: bool = True):
        tx = UdsIdentifiers.tx
        rx = UdsIdentifiers.rx

        self._tx_priority_text = str(int(tx.priority) & 0x7)
        self._tx_pgn_text = f"0x{int(tx.pgn) & 0xFFFF:04X}"
        self._tx_src_text = f"0x{int(tx.src) & 0xFF:02X}"
        self._tx_dst_text = f"0x{int(tx.dst) & 0xFF:02X}"
        self._tx_identifier_text = f"0x{int(tx.identifier) & 0x1FFFFFFF:08X}"

        self._rx_priority_text = str(int(rx.priority) & 0x7)
        self._rx_pgn_text = f"0x{int(rx.pgn) & 0xFFFF:04X}"
        self._rx_src_text = f"0x{int(rx.src) & 0xFF:02X}"
        self._rx_dst_text = f"0x{int(rx.dst) & 0xFF:02X}"
        self._rx_identifier_text = f"0x{int(rx.identifier) & 0x1FFFFFFF:08X}"

        if emit_signal:
            self.udsIdentifiersChanged.emit()

    @staticmethod
    def _parse_source_address(text):
        raw = str(text).strip()
        if not raw:
            raise ValueError("Empty Source Address")

        base = 16 if raw.lower().startswith("0x") else 10
        value = int(raw, base)
        if value < 0 or value > 0xFF:
            raise ValueError("Source Address out of range")
        return value

    @staticmethod
    def _to_local_path(path_or_url):
        if not path_or_url:
            return ""

        if isinstance(path_or_url, QUrl):
            parsed = path_or_url
        else:
            parsed = QUrl(path_or_url)

        if parsed.isLocalFile():
            return parsed.toLocalFile()

        if parsed.scheme() == "file":
            return parsed.toLocalFile()

        return str(path_or_url)

        if not value:
            if self._programming_start_timer.isActive():
                self._programming_start_timer.stop()
            self._pending_programming_after_reset = False

        if self._programming_active == value:
            return
        self._programming_active = value
        self.programmingActiveChanged.emit()

    def _start_programming_after_reset(self):
        if not self._pending_programming_after_reset:
            return
        self._pending_programming_after_reset = False
        self._append_log("Автосброс завершен, запуск сценария программирования", RowColor.blue)
        self._start_programming_flow()

    def _start_programming_flow(self):
        if not self._bootloader.start():
            self._set_programming_active(False)

    def _set_source_address_busy(self, busy):
        value = bool(busy)
        if self._source_address_busy == value:
            return
        self._source_address_busy = value
        if not value:
            self._set_source_address_operation("")
        self.sourceAddressBusyChanged.emit()

    def _set_source_address_operation(self, operation: str):
        value = str(operation).strip().lower()
        if value not in ("", "read", "write"):
            value = ""
        if self._source_address_operation == value:
            return
        self._source_address_operation = value
        self.sourceAddressOperationChanged.emit()

    def _set_firmware_loading(self, loading):
        value = bool(loading)
        if self._firmware_loading == value:
            return
        self._firmware_loading = value
        self.firmwareLoadingChanged.emit()

    def _append_log(self, text, color):
        if isinstance(color, QColor):
            color_value = color.name()
        else:
            color_value = "#cbd5e1"

        self._logs.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": str(text),
                "color": color_value,
            }
        )

        if len(self._logs) > 2000:
            self._logs = self._logs[-2000:]

        self.logsChanged.emit()

        if self._programming_active and isinstance(color, QColor) and color == RowColor.red:
            self._set_programming_active(False)

