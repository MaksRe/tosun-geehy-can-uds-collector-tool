from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class ServiceSecurityAccess:
    def __init__(self):
        self._seed: int = 0
        self._key: int = 0
        self._access = False

    @property
    def access(self) -> bool:
        return self._access

    def _calc_key(self) -> int:
        return (self._seed ^ 0xAA55) | self._seed

    def request_seed(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x02,              # Single Frame, длина запроса
             0x27,              # SID: Security Access
             0x01,              # PID: Request Seed
             0xff, 0xff, 0xff, 0xff, 0xff])

    def request_check_key(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x04,                                  # Single Frame, длина запроса
             0x27,                                  # SID: Security Access
             0x02,                                  # PID: Send key
             self._key >> 8, self._key & 0x00ff,    # Key
             0xff, 0xff, 0xff])

    def get_session(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x03,          # Single Frame, 3 байта длина запроса
             0x22,          # Service ReadDataById
             0x00, 0x16,    # Data Id - Current session
             0x00, 0x00, 0x00, 0x00])

    def verify_answer_request_seed(self, response_data) -> bool:
        data_length = response_data[0]
        state = response_data[1]
        sub_function = response_data[2]
        if state == 0x67 and sub_function == 0x01:
            # self._seed = (response_data[3] << 8) | response_data[4]
            self._seed = (response_data[4] << 8) | response_data[3]
            # print(f"seed={self._seed}, {hex(self._seed)}")
            self._key = self._calc_key()
            # print(f"key={self._key}, {hex(self._key)}")
            return True
        return False

    def verify_answer_request_check_key(self, response_data) -> bool:
        data_length = response_data[0]
        state = response_data[1]
        sub_function = response_data[2]
        if state == 0x67 and sub_function == 0x02:
            self._access = True
        else:
            self._access = False
        return self._access
