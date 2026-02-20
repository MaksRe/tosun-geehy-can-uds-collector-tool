import enum

from PySide6.QtCore import Slot, Signal, QObject, QTimer

from app_can.BaseTranslator import BaseTranslator
from app_can.CanDevice import CanDevice
from colors import RowColor
from uds.data_identifiers import UdsData
from uds.services.ecu_reset import ServiceEcuReset
from uds.services.read_data_by_id import ServiceReadDataById
from uds.services.request_download import ServiceRequestDownload
from uds.services.request_transfer_exit import ServiceRequestTransferExit
from uds.services.routine_control import ServiceRoutineControl
from uds.services.security_access import ServiceSecurityAccess
from uds.services.session import ServiceSession, Session
from uds.services.transfer_data import ServiceTransferData
from uds.services.write_data_by_id import ServiceWriteDataById
from uds.uds_identifiers import UdsIdentifiers


class BootloaderState(enum.IntEnum):
    ERROR = -1,
    READY = 0,

    SET_PROGRAMMING_SESSION = 1,

    REQUEST_SEED = 2,
    SEED_VERIFICATION = 3,

    WRITE_FINGERPRINT = 4,

    ERASE_FIRMWARE = 5,

    REQUEST_DOWNLOAD = 6,
    REQUEST_DOWNLOAD_CONSECUTIVE = 7

    TRANSFER_DATA_FF = 8,
    TRANSFER_DATA_FC = 9,
    TRANSFER_DATA_CF = 10,

    REQUEST_TRANSFER_EXIT = 11,

    ECU_UDS_RESET = 12,
    ECU_SOFTWARE_RESET = 13,

    READ_FINGERPRINT = 14,

    VERIFICATION = 15,
    DONE = 16
    WRITE_CAN_SOURCE_ADDRESS = 17
    READ_CAN_SOURCE_ADDRESS = 18


class Bootloader(QObject):
    signal_new_state = Signal(str, RowColor)
    signal_data_sent = Signal(int)
    signal_finished = Signal(bool)
    signal_source_address_applied = Signal(int, bool)
    signal_source_address_read = Signal(int, bool)

    def __init__(self):
        super().__init__()

        self._state: BootloaderState = BootloaderState.READY

        self._binary_content = None
        self._transfer_byte_order = "big"
        self._pending_source_address: int | None = None
        self._pending_rx_identifier: int | None = None

        self._service_session = ServiceSession()
        self._service_security_access = ServiceSecurityAccess()
        self._service_write_data_by_id = ServiceWriteDataById()
        self._service_routine_control = ServiceRoutineControl()
        self._service_request_download = ServiceRequestDownload()
        self._service_transfer_data = ServiceTransferData()
        self._service_request_transfer_exit = ServiceRequestTransferExit()
        self._service_ecu_reset = ServiceEcuReset()
        self._service_read_data_by_id = ServiceReadDataById()
        self._service_request_download.set_byte_order(self._transfer_byte_order)
        self._service_read_data_by_id.set_byte_order(self._transfer_byte_order)
        self._service_write_data_by_id.set_byte_order(self._transfer_byte_order)

        self._source_address_timeout_timer = QTimer(self)
        self._source_address_timeout_timer.setSingleShot(True)
        self._source_address_timeout_timer.setInterval(2500)
        self._source_address_timeout_timer.timeout.connect(self._on_source_address_timeout)

        self._service_transfer_data.signal_data_sent.connect(self._handle_data_sent)

        CanDevice.instance().signal_new_message.connect(self.on_new_message)

    @Slot(int)
    def _handle_data_sent(self, total_bytes):
        self.signal_data_sent.emit(total_bytes)

    def set_firmware(self, binary_content: bytes):
        self._binary_content = binary_content
        if self._service_request_download is not None:
            self._service_request_download.set_memory_length(len(self._binary_content))

    def set_transfer_byte_order(self, byte_order: str):
        order = str(byte_order).strip().lower()
        self._transfer_byte_order = order if order in ("big", "little") else "big"
        if self._service_request_download is not None:
            self._service_request_download.set_byte_order(self._transfer_byte_order)
        if self._service_read_data_by_id is not None:
            self._service_read_data_by_id.set_byte_order(self._transfer_byte_order)
        if self._service_write_data_by_id is not None:
            self._service_write_data_by_id.set_byte_order(self._transfer_byte_order)

    def write_can_source_address(self, source_address: int) -> bool:
        if self._state != BootloaderState.READY:
            self.signal_new_state.emit("Загрузчик занят", RowColor.red)
            return False

        if source_address < 0 or source_address > 0xFF:
            self.signal_new_state.emit("Некорректный Source Address", RowColor.red)
            return False

        current_tx_identifier = UdsIdentifiers.tx.identifier
        current_rx_identifier = UdsIdentifiers.rx.identifier

        if not self._service_write_data_by_id.write_data(
            UdsData.can_sa,
            source_address,
            tx_identifier=current_tx_identifier,
        ):
            self.signal_new_state.emit("Не удалось отправить WriteDataById для Source Address", RowColor.red)
            return False

        self._pending_source_address = source_address
        self._pending_rx_identifier = (current_rx_identifier & ~0xFF) | (source_address & 0xFF)
        self._state = BootloaderState.WRITE_CAN_SOURCE_ADDRESS
        self._source_address_timeout_timer.start()
        self.signal_new_state.emit(f"Отправлен запрос на изменение Source Address: 0x{source_address:02X}", RowColor.blue)

        return True

    def read_can_source_address(self) -> bool:
        if self._state != BootloaderState.READY:
            self.signal_new_state.emit("Загрузчик занят", RowColor.red)
            return False

        current_tx_identifier = UdsIdentifiers.tx.identifier
        self._service_read_data_by_id.read_data_by_identifier(current_tx_identifier, UdsData.can_sa)
        self._state = BootloaderState.READ_CAN_SOURCE_ADDRESS
        self._source_address_timeout_timer.start()
        self.signal_new_state.emit("Отправлен запрос на чтение Source Address", RowColor.blue)
        return True

    def _on_source_address_timeout(self):
        if self._state not in (BootloaderState.WRITE_CAN_SOURCE_ADDRESS, BootloaderState.READ_CAN_SOURCE_ADDRESS):
            return

        if self._state == BootloaderState.WRITE_CAN_SOURCE_ADDRESS:
            source_address = self._pending_source_address if self._pending_source_address is not None else UdsIdentifiers.rx.src
            self.signal_new_state.emit("Таймаут применения Source Address", RowColor.red)
            self.signal_source_address_applied.emit(source_address, False)
        else:
            current_source_address = UdsIdentifiers.rx.src
            self.signal_new_state.emit("Таймаут чтения Source Address", RowColor.red)
            self.signal_source_address_read.emit(current_source_address, False)

        self._pending_source_address = None
        self._pending_rx_identifier = None
        self._state = BootloaderState.READY

    def ecu_uds_reset(self):
        self._service_ecu_reset.ecu_uds_reset()

        self._state = BootloaderState.ECU_UDS_RESET
        self.signal_new_state.emit("Запрос на сброс МК для перехода в загрузчик", RowColor.blue)

    def ecu_software_reset(self):
        self._service_ecu_reset.ecu_software_reset()

        self._state = BootloaderState.ECU_SOFTWARE_RESET
        self.signal_new_state.emit("Запрос на сброс МК для перехода в основную программу", RowColor.blue)

    def check_state(self):
        self._service_read_data_by_id.read_data(UdsData.fingerprint)

        self._state = BootloaderState.READ_FINGERPRINT
        self.signal_new_state.emit("Чтение статуса", RowColor.blue)

    def start(self) -> bool:
        if self._state == BootloaderState.READY:

            if self._binary_content is None:
                self.signal_new_state.emit("Не загружена основная программа", RowColor.red)
                return False

            self._service_transfer_data.set_firmware(self._binary_content)

            self._state = BootloaderState.SET_PROGRAMMING_SESSION
            self._service_session.set(Session.PROGRAMMING)

            self.signal_new_state.emit("Запрос на установку сессии 'programming'", RowColor.blue)

            return True
        else:
            self.signal_new_state.emit("Загрузчик не готов к работе", RowColor.red)

            return False

    @Slot(str, str, str, str, list)
    def on_new_message(self, _time, _id, _dir, _data_len_code, _data):

        identifier = BaseTranslator.to_int(_id)

        if self._state == BootloaderState.WRITE_CAN_SOURCE_ADDRESS:
            expected_identifier = UdsIdentifiers.rx.identifier
            pending_identifier = self._pending_rx_identifier
            if identifier != expected_identifier and identifier != pending_identifier:
                return
        else:
            if identifier != UdsIdentifiers.rx.identifier:
                return

        if self._state == BootloaderState.SET_PROGRAMMING_SESSION:
            if self._service_session.verify_answer(_data):

                self.signal_new_state.emit("Сессия 'programming' установлена", RowColor.green)

                self._state = BootloaderState.REQUEST_SEED
                self._service_security_access.request_seed()

                self.signal_new_state.emit("Запрос seed-фразы", RowColor.blue)

            else:
                self.signal_new_state.emit("Ошибка перехода в сессию 'programming'", RowColor.red)

        elif self._state == BootloaderState.REQUEST_SEED:
            if self._service_security_access.verify_answer_request_seed(_data):

                self.signal_new_state.emit("Успешно получена seed-фраза", RowColor.green)

                self._state = BootloaderState.SEED_VERIFICATION
                self._service_security_access.request_check_key()

                self.signal_new_state.emit("Запрос на проверку ключа доступа", RowColor.blue)

            else:
                self.signal_new_state.emit("Ошибочный ответ", RowColor.red)

        elif self._state == BootloaderState.SEED_VERIFICATION:
            if self._service_security_access.verify_answer_request_check_key(_data):
                self.signal_new_state.emit("Доступ успешно получен", RowColor.green)

                self._state = BootloaderState.WRITE_FINGERPRINT
                self._service_write_data_by_id.write_fingerprint(0xAA)

                self.signal_new_state.emit("Запись fingerprint", RowColor.blue)

            else:
                self.signal_new_state.emit("Ошибка получения доступа", RowColor.red)

        elif self._state == BootloaderState.WRITE_FINGERPRINT:
            if self._service_write_data_by_id.verify_answer_write_fingerprint(_data):
                self.signal_new_state.emit("Успешная запись fingerprint", RowColor.green)

                self._state = BootloaderState.ERASE_FIRMWARE
                self._service_routine_control.request_erase_firmware()

                self.signal_new_state.emit("Запрос на очистку области памяти основной программы", RowColor.blue)

            else:
                self.signal_new_state.emit("Ошибка записи fingerprint", RowColor.red)

        elif self._state == BootloaderState.ERASE_FIRMWARE:
            if self._service_routine_control.verify_answer_erase_firmware(_data):
                self.signal_new_state.emit("Память успешно очищена", RowColor.green)

                self._state = BootloaderState.REQUEST_DOWNLOAD
                self._service_request_download.request_download_first()

                self.signal_new_state.emit("Запрос на программирование области памяти", RowColor.blue)

            else:
                self.signal_new_state.emit("Ошибка в процессе очистки памяти", RowColor.red)

        elif self._state == BootloaderState.REQUEST_DOWNLOAD:
            # приходит FlowControl
            if self._service_request_download.verify_flow_control(_data):

                self._state = BootloaderState.REQUEST_DOWNLOAD_CONSECUTIVE
                self._service_request_download.request_download_consecutive()

        elif self._state == BootloaderState.REQUEST_DOWNLOAD_CONSECUTIVE:
            if self._service_request_download.verify_request_download(_data):
                self.signal_new_state.emit("Успешный запрос на передачу данных", RowColor.green)

                self._state = BootloaderState.TRANSFER_DATA_FF
                block_size = self._service_transfer_data.send_first_frame()
                self.signal_new_state.emit(f"Передача блока ({block_size} байт)", RowColor.blue)

        elif self._state == BootloaderState.TRANSFER_DATA_FF:
            if self._service_transfer_data.verify_flow_control(_data):
                self._state = BootloaderState.TRANSFER_DATA_CF
                self._service_transfer_data.send_consecutive_frames()
            else:
                self.signal_new_state.emit("Ошибка обработки flow control", RowColor.red)
                self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.TRANSFER_DATA_CF:
            if self._service_transfer_data.data_transferred():
                self.signal_new_state.emit("Все данные переданы", RowColor.green)

                self._state = BootloaderState.REQUEST_TRANSFER_EXIT
                self._service_request_transfer_exit.request_transfer_exit()
                self.signal_new_state.emit("Завершение передачи", RowColor.blue)

            else:
                # После передачи полного блока (2048 байт)
                # формируем другой блок, начиная с first frame
                if self._service_transfer_data.block_transferred():
                    if self._service_transfer_data.verify_answer_after_sent_block(_data):
                        self._state = BootloaderState.TRANSFER_DATA_FF
                        block_size = self._service_transfer_data.send_first_frame()
                        self.signal_new_state.emit(f"Передача блока ({block_size} байт)", RowColor.blue)
                else:
                    # После передачи максимального количества фреймов в одном блоке,
                    # принимаем очередной flow_control и из него берем очередное количество
                    # фреймов (block_size) для последущей передачи
                    if self._service_transfer_data.verify_flow_control(_data):
                        self._service_transfer_data.send_consecutive_frames()
                    else:
                        self.signal_new_state.emit("Ошибка обработки flow control", RowColor.red)
                        self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.REQUEST_TRANSFER_EXIT:
            if self._service_request_transfer_exit.verify_answer_request_transfer_exit(_data):
                self.signal_new_state.emit("Успешное завершение передачи данных", RowColor.green)

                self.signal_finished.emit(True)
                self._state = BootloaderState.READY

            else:
                self.signal_new_state.emit("Ошибка завершения передачи данных", RowColor.red)
                self._state = BootloaderState.ERROR

        elif self._state == BootloaderState.WRITE_CAN_SOURCE_ADDRESS:
            if self._source_address_timeout_timer.isActive():
                self._source_address_timeout_timer.stop()

            source_address = self._pending_source_address if self._pending_source_address is not None else UdsIdentifiers.rx.src

            if self._service_write_data_by_id.verify_answer_write_data(_data):
                UdsIdentifiers.set_src(source_address)
                self.signal_new_state.emit(f"Source Address изменен: 0x{source_address:02X}", RowColor.green)
                self.signal_source_address_applied.emit(source_address, True)
            else:
                self.signal_new_state.emit("Изменение Source Address отклонено", RowColor.red)
                self.signal_source_address_applied.emit(source_address, False)

            self._pending_source_address = None
            self._pending_rx_identifier = None
            self._state = BootloaderState.READY

        elif self._state == BootloaderState.READ_CAN_SOURCE_ADDRESS:
            if self._source_address_timeout_timer.isActive():
                self._source_address_timeout_timer.stop()

            current_source_address = UdsIdentifiers.rx.src

            if self._service_read_data_by_id.verify_answer_read_data(_data):
                source_address = self._service_read_data_by_id.parse_data_field(_data) & 0xFF
                self.signal_new_state.emit(f"Source Address считан: 0x{source_address:02X}", RowColor.green)
                self.signal_source_address_read.emit(source_address, True)
            else:
                self.signal_new_state.emit("Чтение Source Address отклонено", RowColor.red)
                self.signal_source_address_read.emit(current_source_address, False)

            self._pending_source_address = None
            self._pending_rx_identifier = None
            self._state = BootloaderState.READY

        elif self._state == BootloaderState.ECU_UDS_RESET:
            if self._service_ecu_reset.verify_ecu_uds_reset(_data):

                self.signal_new_state.emit("Успешный сброс", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("Ошибка сброса", RowColor.red)
                self._state = BootloaderState.READY

        elif self._state == BootloaderState.ECU_SOFTWARE_RESET:
            if self._service_ecu_reset.verify_ecu_software_reset(_data):

                self.signal_new_state.emit("Успешный сброс", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("Ошибка сброса", RowColor.red)
                self._state = BootloaderState.READY

        elif self._state == BootloaderState.READ_FINGERPRINT:
            if self._service_read_data_by_id.verify_answer_read_data(_data):

                self.signal_new_state.emit("Загрузчик активен", RowColor.green)
                self._state = BootloaderState.READY
            else:
                self.signal_new_state.emit("Загрузчик не активен", RowColor.red)
                self._state = BootloaderState.READY

        if self._state == BootloaderState.ERROR:
            pass
            # CanDevice.instance().signal_new_message.disconnect(self.on_new_message)


