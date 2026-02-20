from app_can.CanDevice import CanDevice
from uds.data_identifiers import UdsData, UdsVar
from uds.uds_identifiers import UdsIdentifiers


class ServiceWriteDataById:
    def __init__(self):
        self._sid = 0x2E
        self._saved_pid = 0
        self._byte_order = "big"

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

    def write_data(self, var: UdsVar, value, tx_identifier: int | None = None) -> bool:
        if var.size > 4:
            return False

        self._saved_pid = var.pid
        pid_b0, pid_b1 = self._pid_to_bytes(var.pid)

        frame = [3 + var.size, self._sid, pid_b0, pid_b1]

        for _ in range(var.size):
            frame.append(value & 0xFF)
            value = value >> 8

        if var.size < 4:
            rem = 4 - var.size
            for _ in range(rem):
                frame.append(0xFF)

        identifier = UdsIdentifiers.tx.identifier if tx_identifier is None else int(tx_identifier)
        CanDevice.instance().send_async(identifier, 8, frame)
        return True

    def verify_answer_write_data(self, response_data) -> bool:
        sid = response_data[1]
        positive_sid = self._sid + 0x40
        pid = self._parse_pid_field(response_data)
        return sid == positive_sid and pid == self._saved_pid

    def write_fingerprint(self, value: int):
        pid_b0, pid_b1 = self._pid_to_bytes(UdsData.fingerprint.pid)
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x04, self._sid, pid_b0, pid_b1, value, 0xFF, 0xFF, 0xFF],
        )

    def verify_answer_write_fingerprint(self, response_data) -> bool:
        sid = response_data[1]
        pid = self._parse_pid_field(response_data)
        return sid == (self._sid + 0x40) and pid == UdsData.fingerprint.pid

    def parse_pid_field(self, data):
        return self._parse_pid_field(data)
