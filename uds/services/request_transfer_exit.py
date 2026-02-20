from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class ServiceRequestTransferExit:
    def __init__(self):
        self._sid = 0x37

    def request_transfer_exit(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x01,
             self._sid,
             0xff, 0xff, 0xff, 0xff, 0xff, 0xff])

    def verify_answer_request_transfer_exit(self, data) -> bool:
        data_length = data[0]
        sid = data[1]
        positive_sid = self._sid + 0x40
        if sid == positive_sid:
            return True
        return False
