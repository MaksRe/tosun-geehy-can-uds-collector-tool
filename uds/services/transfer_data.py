import math

from PySide6.QtCore import QTimer, QObject, Signal

from app_can.CanDevice import CanDevice
from dataclasses import dataclass

from uds.uds_identifiers import UdsIdentifiers


@dataclass
class FlowControl:
    frame_type: int
    flow_status: int
    block_size: int  # количество consecutive фреймов, которые может получить приёмник
    sep_time: int


class ServiceTransferData(QObject):
    signal_data_sent = Signal(int)  # bytes

    def __init__(self):
        super().__init__()

        self._sid = 0x36  # RequestDownload SID запроса

        self._timer = QTimer()
        self._timer.timeout.connect(self._send_consecutive_frame)

        self._binary_content_size = 0
        self._binary_content = None
        self._bytes_sent = 0
        self._total_bytes_sent = 0
        self._index_binary_content = 0

        self._block_sequence = 0  # счетчик последовательности блоков в сервисе TransferData (0x36)
        self._frame_number = 0  # номер фрейма в Consecutive Frame

        self._flow_control: FlowControl = FlowControl(0, 0, 0, 0)
        # Берем максимальное количество байт для передачи данных в одной последовательности
        # так как на приёмной стороне буфер 2050 байт
        # (1024 байт полезных данных + 2 байта служебные (sid и block_sequence))
        self._ff_max_data_length = 1026
        self._ff_data_length = 0

    def set_firmware(self, binary_content: bytes):
        self._binary_content = binary_content
        self._binary_content_size = len(self._binary_content)
        # Учитываем, что для каждого блока (_ff_max_data_length) еще по 2 байта служебной информации в виде sid и block_sequence
        num_of_blocks = math.ceil(self._binary_content_size / self._ff_max_data_length)
        self._binary_content_size += num_of_blocks * 2

    def _form_first_message(self, data_length) -> list | None:
        if self._binary_content is None:
            return None

        self._block_sequence += 1

        message = [
            0x10 | ((data_length >> 8) & 0xf),
            data_length & 0xff,
            self._sid,
            self._block_sequence]

        data = [0xff, 0xff, 0xff, 0xff]
        if data_length > 4:
            data_length = 4
        for i in range(data_length):
            data[i] = self._binary_content[self._index_binary_content + i]
        message += data

        self._frame_number = 0

        if data_length < 4:
            self._index_binary_content += data_length
            # self._sid + self._block_sequence + data_length
            self._total_bytes_sent += data_length + 2
            self._bytes_sent = data_length + 2
        else:
            self._index_binary_content += 4
            # self._sid + self._block_sequence + data = 6 bytes
            self._total_bytes_sent += 6
            self._bytes_sent = 6

        # print(list(map(hex, data)), self._total_bytes_sent)

        return message

    def block_transferred(self) -> bool:
        return self._bytes_sent == self._ff_data_length

    def data_transferred(self):
        return self._total_bytes_sent == self._binary_content_size

    def send_first_frame(self) -> int:
        if self._total_bytes_sent + self._ff_max_data_length < self._binary_content_size:
            self._ff_data_length = self._ff_max_data_length
        else:
            self._ff_data_length = self._binary_content_size - self._total_bytes_sent

        first_frame = self._form_first_message(self._ff_data_length)
        CanDevice.instance().send_async(UdsIdentifiers.tx.identifier, 8, first_frame)

        self.signal_data_sent.emit(self._total_bytes_sent)

        # 2 байта - служебная информация (sid, block_sequence)
        return self._ff_data_length - 2

    def send_consecutive_frames(self):
        if self._flow_control is None:
            return
        if self._flow_control.block_size == 0:
            return
        if self._flow_control.sep_time > 0:
            self._timer.start(self._flow_control.sep_time)
        else:
            self._timer.start(10)

    def _send_consecutive_frame(self):
        self._frame_number += 1
        if self._frame_number > 0xf:
            self._frame_number = 0
        data_length = 7
        if self._bytes_sent + data_length > self._ff_data_length:
            data_length = self._ff_data_length - self._bytes_sent

        frame = [0x20 | self._frame_number, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        for i in range(data_length):
            frame[i + 1] = self._binary_content[self._index_binary_content + i]

        self._index_binary_content += data_length
        self._total_bytes_sent += data_length
        self._bytes_sent += data_length

        # print(list(map(hex, frame)), self._total_bytes_sent)

        CanDevice.instance().send_async(UdsIdentifiers.tx.identifier, 8, frame)

        self.signal_data_sent.emit(self._total_bytes_sent)

        if self._bytes_sent >= self._ff_data_length:
            self._timer.stop()

    def verify_answer_after_sent_block(self, data) -> bool:
        frame_type = data[0] >> 4 & 0x0f
        status = data[1]
        success_status = self._sid | 0x40
        block_sequence_counter = data[2]

        if status == success_status and block_sequence_counter == self._block_sequence:
            return True
        return False

    def verify_flow_control(self, data) -> bool:
        frame_type = data[0] >> 4 & 0x0f
        flow_status = data[0] & 0x0f
        block_size = data[1]
        sep_time = data[2]

        if frame_type == 3:  # flow control
            self._flow_control.block_size = block_size
            self._flow_control.flow_status = flow_status
            self._flow_control.sep_time = sep_time
            self._flow_control.frame_type = frame_type
            return True
        return False

    def reset_transfer(self):
        self._total_bytes_sent = 0
        self._frame_number = 0
