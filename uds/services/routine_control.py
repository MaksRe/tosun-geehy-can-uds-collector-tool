from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class ServiceRoutineControl:
    def __init__(self):
        self._sid = 0x31
        self._pid_start_routine = 0x01
        self._id_erase_memory = 0x00ff

    def request_erase_firmware(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x04,                      # Single Frame, длина запроса
             self._sid,                 # SID: Routine Control (0x31)
             self._pid_start_routine,   # PID: Start Routine (0x01)
             self._id_erase_memory & 0x00ff, self._id_erase_memory >> 8,  # ID Routine: Erase Memory (0xFF00)
             0xff, 0xff, 0xff])

    def verify_answer_erase_firmware(self, data) -> bool:
        data_length = data[0]
        positive_sid = self._sid + 0x40
        sid = data[1]
        pid = data[2]
        id_routine = (data[4] << 8) | data[3]
        if sid == positive_sid:
            if pid == self._pid_start_routine:
                if id_routine == self._id_erase_memory:
                    return True
        return False

