from enum import IntEnum

from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class Session(IntEnum):
    DEFAULT = 1,
    PROGRAMMING = 2,
    EXTENDED = 3


class ServiceSession:
    def __init__(self):
        self._verify_state: bool = False

    @property
    def verify_state(self) -> bool:
        return self._verify_state

    def verify_answer(self, response_data) -> bool:
        data_length = response_data[0]
        state = response_data[1]
        if state == 0x50:
            self._verify_state = True
        else:
            self._verify_state = False

        return self._verify_state

    def set(self, session: Session):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x02,      # Single Frame, data length
             0x10,      # Service CurrentSession
             session,   # Programming session
             0xff, 0xff, 0xff, 0xff, 0xff])