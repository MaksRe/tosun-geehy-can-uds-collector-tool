import time
import logging
from ctypes import c_char_p, c_float
from dataclasses import dataclass

from PySide6.QtCore import Signal, Slot, QObject

from libTSCANAPI import tsapp_configure_baudrate_can, tscan_scan_devices, tscan_get_device_info, s32, size_t, \
    tsapp_disconnect_by_handle, tsapp_connect, tsapp_register_event_can_whandle, OnTx_RxFUNC_CAN_WHandle, \
    DLC_DATA_BYTE_CNT, TLIBCAN, tsapp_delete_cyclic_msg_can, tsapp_add_cyclic_msg_can, tsapp_transmit_can_async, \
    tsapp_transmit_can_sync, tsapp_unregister_event_can_whandle

LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    manufacturer: c_char_p = c_char_p()
    product: c_char_p = c_char_p()
    serial: c_char_p = c_char_p()


class CanDevice(QObject):
    _instance = None
    signal_new_message = Signal(str, str, str, str, list)
    signal_tracing_started = Signal()
    signal_tracing_stopped = Signal()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CanDevice, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            super(CanDevice, self).__init__()

            self._initialized = True

            self._devices = s32(0)

            self._device_info: DeviceInfo = DeviceInfo()
            self._hardware_handle = size_t(0)
            self._is_connect: bool = False
            self._is_trace: bool = False

            self._channel: int = -1
            self._baud_rate: int = -1
            self._terminator: bool = False

            self._can_tx_start_time = time.perf_counter()
            self._refresh_time: float = 0.1
            self._message_handler = OnTx_RxFUNC_CAN_WHandle(self._event_handler)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = CanDevice()
        return cls._instance

    @property
    def is_trace(self) -> bool:
        return self._is_trace

    @is_trace.setter
    def is_trace(self, state: bool):
        self._is_trace = state

    @property
    def channel(self) -> int:
        return self._channel

    @channel.setter
    def channel(self, chan: int):
        self._channel = chan

    @property
    def baud_rate(self) -> int:
        return self._baud_rate

    @baud_rate.setter
    def baud_rate(self, br: int):
        self._baud_rate = br

    @property
    def terminator(self):
        return self._terminator

    @terminator.setter
    def terminator(self, ter: bool):
        self._terminator = ter

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @device_info.setter
    def device_info(self, info: DeviceInfo):
        self._device_info = info

    @property
    def is_connect(self) -> bool:
        return self._is_connect

    @is_connect.setter
    def is_connect(self, state: bool):
        self._is_connect = state

    def disconnect_device(self) -> bool:
        if self._is_connect:
            try:
                tsapp_disconnect_by_handle(self._hardware_handle)
                self.is_connect = False
                LOGGER.info("Успешное отключение CAN-устройства")
            except Exception as err:
                LOGGER.error(f"{err}")
            finally:
                return not self._is_connect

    def _register_receive_event(self) -> bool:
        if self._hardware_handle.value == 0 or self._message_handler is None:
            return False
        ret = tsapp_register_event_can_whandle(self._hardware_handle,
                                               self._message_handler)
        if ret == 0 or ret == 5:
            LOGGER.info("Успешная регистрация обработчика событий")
            return True

        LOGGER.info(f"Ошибка регистрации обработчика событий: {ret}")
        return False

    def _unregister_receive_event(self) -> bool:
        if self._hardware_handle.value == 0 or self._message_handler is None:
            return False
        ret = tsapp_unregister_event_can_whandle(self._hardware_handle,
                                                 self._message_handler)
        if ret == 0 or ret == 5:
            LOGGER.info("Успешное аннулирование обработчика событий")
            return True

        LOGGER.error(f"Ошибка аннулирования обработчика событий: {ret}")
        return False

    def connect_to(self, device_index: int) -> size_t:
        """
        Подключение к выбранному устройству по device_index
        :param device_index: индекс выбранного устройства
        :return: size_t(0) если ошибка подключения, иначе self._hardware_handle
        """
        success: bool = True
        ret: int = -1
        err = None

        try:
            if self._is_connect:
                success = False
            if self.device_info.serial.value is None:
                self.update_device_info(device_index)
            ret = tsapp_connect(self.device_info.serial,
                                self._hardware_handle)
            if ret == 0 or ret == 5:
                self.is_connect = True
            else:
                raise Exception(f"error connect to device")
        except Exception as err:
            success = False
            LOGGER.error(f"CanDevice.connect_to(): {err}")
        finally:
            if success:
                LOGGER.info("Успешное подключение к CAN-устройству")
                return self._hardware_handle
            else:
                LOGGER.error(f"Ошибка подключения к CAN-устройству: {ret}")
                return size_t(0)

    def update_device_info(self, device_index: int):
        if device_index != -1:
            tscan_get_device_info(device_index,
                                  self.device_info.manufacturer,
                                  self.device_info.product,
                                  self.device_info.serial)

    def get_devices(self) -> s32:
        # ????? ????????????? ?????? ???????? ???????,
        # ????? ????????? ????????????? ??????????? ????????.
        self._devices = s32(0)
        try:
            tscan_scan_devices(self._devices)
        except Exception as err:
            LOGGER.error(f"CanDevice.get_devices(): {err}")
            self._devices = s32(0)
        return self._devices

    def start_trace(self, channel: int, baud_rate: int, terminator: bool):
        if self._is_trace:
            return
        self.channel = channel
        self.baud_rate = baud_rate
        self.terminator = terminator
        self._register_receive_event()
        ret = tsapp_configure_baudrate_can(self._hardware_handle,
                                           self.channel,
                                           self.baud_rate,
                                           self.terminator)
        if ret == 0 or ret == 5:
            LOGGER.info("Запуск отслеживания сообщений")
            self.is_trace = True

            self.signal_tracing_started.emit()
        else:
            LOGGER.info(f"Ошибка запуска отслеживания сообщений: {ret}")

    def stop_trace(self):
        if self.is_trace:
            self._unregister_receive_event()
            self.is_trace = False

        self.signal_tracing_stopped.emit()

    def _event_handler(self, obj, a_can):
        # 1 - error frame
        if a_can.contents.FProperties & 0x80:
            return

        msg = a_can.contents
        _time = str(float(msg.FTimeUs) / 1000000.0)
        _id = str(hex(msg.FIdentifier))
        _data_len_code = str(msg.FDLC)
        _data_len = DLC_DATA_BYTE_CNT[msg.FDLC]
        _dir = 'Tx' if (msg.FProperties & 1) == 1 else 'Rx'
        _data = [msg.FData[i] for i in range(_data_len)]

        # TX кадры для UI логируются явно в send_async/send_sync.
        # Из callback оставляем только RX, чтобы избежать дублей.
        if _dir == 'Tx':
            return

        self.signal_new_message.emit(_time, _id, _dir, _data_len_code, _data)

    def _create_message(self, iden: int, dlc: int, data: list[int]) -> TLIBCAN | None:
        # [7] 0 - normal frame, 1 - error frame
        # [6] 0-not logged, 1-already logged
        # [5-3] tbd
        # [2] 0-std frame, 1-extended frame
        # [1] 0-data frame, 1-remote frame
        # [0] dir: 0-RX, 1-TX
        properties = 0
        properties |= 0x1  # TX
        properties |= 0x4  # extended frame

        if self._channel == -1:
            return None

        return TLIBCAN(FIdxChn=self._channel,
                       FDLC=dlc,
                       FIdentifier=iden,
                       FData=data,
                       FProperties=properties)

    def send_cyclic(self, iden: int, dlc: int, data: list[int], timeout: int) -> TLIBCAN | None:
        if self._hardware_handle is None or self._hardware_handle.value == 0:
            return None
        if timeout == 0:
            return None

        message: TLIBCAN = self._create_message(iden, dlc, data)
        tsapp_add_cyclic_msg_can(self._hardware_handle, message, c_float(timeout))

        return message

    def stop_cyclic(self, message: TLIBCAN):
        if self._hardware_handle is None or self._hardware_handle.value == 0:
            return
        return tsapp_delete_cyclic_msg_can(self._hardware_handle, message)

    @Slot(int, int, list)
    def send_async(self, iden: int, dlc: int, data: list[int]):
        if self._hardware_handle is None or self._hardware_handle.value == 0:
            return
        message: TLIBCAN = self._create_message(iden, dlc, data)
        if message is None:
            return
        ret = tsapp_transmit_can_async(self._hardware_handle, message)

        # Явно логируем TX кадр для UI независимо от режима trace.
        payload_len = min(max(int(dlc), 0), len(data))
        payload = [int(data[i]) & 0xFF for i in range(payload_len)]
        self.signal_new_message.emit(
            f"{time.perf_counter():.6f}",
            hex(int(iden) & 0x1FFFFFFF),
            "Tx",
            str(int(dlc)),
            payload,
        )

        return ret

    def send_sync(self, iden: int, dlc: int, data: list[int], timeout: int):
        if self._hardware_handle is None or self._hardware_handle.value == 0:
            return
        message: TLIBCAN = self._create_message(iden, dlc, data)
        ret = tsapp_transmit_can_sync(self._hardware_handle, message, timeout)

        payload_len = min(max(int(dlc), 0), len(data))
        payload = [int(data[i]) & 0xFF for i in range(payload_len)]
        self.signal_new_message.emit(
            f"{time.perf_counter():.6f}",
            hex(int(iden) & 0x1FFFFFFF),
            "Tx",
            str(int(dlc)),
            payload,
        )

        return ret
