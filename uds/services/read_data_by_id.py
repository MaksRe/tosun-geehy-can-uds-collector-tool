from typing import Optional

from app_can.CanDevice import CanDevice
from uds.data_identifiers import UdsVar
from uds.uds_identifiers import UdsIdentifiers


class ServiceReadDataById:
    def __init__(self):
        self._sid = 0x22
        self._pid_request: int = 0
        self._byte_order = "big"

    @property
    def sid(self) -> int:
        return self._sid

    @property
    def success_sid(self) -> int:
        return self._sid + 0x40

    def set_byte_order(self, byte_order: str):
        order = str(byte_order).strip().lower()
        self._byte_order = order if order in ("big", "little") else "big"

    def _pid_to_bytes(self, pid: int) -> tuple[int, int]:
        pid_l = int(pid) & 0x00FF
        pid_h = (int(pid) >> 8) & 0x00FF
        if self._byte_order == "little":
            return pid_l, pid_h
        return pid_h, pid_l

    def _parse_pid_field(self, data) -> int:
        if self._byte_order == "little":
            return (data[3] << 8) | data[2]
        return (data[2] << 8) | data[3]

    def verify_answer_read_data(self, data) -> bool:
        sid = data[1]
        pid = self._parse_pid_field(data)
        return sid == self.success_sid and pid == self._pid_request

    def read_data(self, var: UdsVar):
        self._pid_request = var.pid
        pid_b0, pid_b1 = self._pid_to_bytes(var.pid)
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x03, self._sid, pid_b0, pid_b1, 0xFF, 0xFF, 0xFF, 0xFF],
        )

    def read_data_by_identifier(self, tx_identifier: Optional[int], var: UdsVar):
        self._pid_request = var.pid
        pid_b0, pid_b1 = self._pid_to_bytes(var.pid)
        CanDevice.instance().send_async(
            tx_identifier,
            8,
            [0x03, self._sid, pid_b0, pid_b1, 0xFF, 0xFF, 0xFF, 0xFF],
        )

    def parse_pid_field(self, data):
        return self._parse_pid_field(data)

    def parse_did_field(self, data):
        return self._parse_pid_field(data)

    @staticmethod
    def parse_data_field(data) -> int:
        data_length = data[0]
        if data_length <= 3:
            return 0
        data_length -= 3
        result = 0
        shift = 0
        for i in range(data_length):
            index = 4 + i
            result = result | (data[index] << shift)
            shift += 8
        return result
