from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class ServiceRequestDownload:
    def __init__(self):
        self._sid = 0x34
        self._data_length = 0x0B
        self._data_format_id = 0x00
        self._addr_and_len_id = 0x44

        self._memory_addr = 0x08000000 + 1024 * 30
        self._memory_length = 0
        self._max_memory_length = 1024 * 80
        self._counter = 0

        # Transfer format for multibyte address/length fields.
        self._byte_order = "big"

    def set_memory_length(self, memory_length):
        if memory_length > self._max_memory_length:
            self._memory_length = self._max_memory_length
        else:
            self._memory_length = memory_length

    def set_byte_order(self, byte_order: str):
        order = str(byte_order).strip().lower()
        self._byte_order = order if order in ("big", "little") else "big"

    def _u32_to_bytes(self, value: int) -> list[int]:
        value = int(value) & 0xFFFFFFFF
        if self._byte_order == "little":
            return [
                value & 0xFF,
                (value >> 8) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 24) & 0xFF,
            ]
        return [
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ]

    def verify_flow_control(self, data) -> bool:
        frame_type = data[0] >> 4 & 0x0F
        if frame_type == 3:
            return True
        return False

    def request_download_first(self):
        addr = self._u32_to_bytes(self._memory_addr)
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [
                0x10,  # first frame
                self._data_length,  # data length
                self._sid,
                self._data_format_id,
                self._addr_and_len_id,
                addr[0],
                addr[1],
                addr[2],
            ],
        )

    def request_download_consecutive(self):
        addr = self._u32_to_bytes(self._memory_addr)
        length = self._u32_to_bytes(self._memory_length)
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [
                0x21,
                addr[3],
                length[0],
                length[1],
                length[2],
                length[3],
                0xFF,
                0xFF,
            ],
        )

    def verify_request_download(self, data) -> bool:
        sid = data[1]
        positive_sid = self._sid + 0x40
        if sid == positive_sid:
            return True
        return False
