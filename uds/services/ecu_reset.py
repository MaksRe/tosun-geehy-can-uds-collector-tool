import enum

from app_can.CanDevice import CanDevice
from uds.uds_identifiers import UdsIdentifiers


class EcuResetType(enum.IntEnum):
    NO_RESET = 0x00
    HARDWARE_RESET = 0x01
    KEY_OFF_ON_RESET = 0x02
    SOFTWARE_RESET = 0x03
    UDS_SOFTWARE_RESET = 0x60  # systemSupplierSpecific [0x60-0x7e]


class ServiceEcuReset:

    def __init__(self):
        self._sid = 0x11

    def ecu_uds_reset(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x02,
             self._sid,
             EcuResetType.UDS_SOFTWARE_RESET,
             0xff, 0xff, 0xff, 0xff, 0xff])

    def ecu_software_reset(self):
        CanDevice.instance().send_async(
            UdsIdentifiers.tx.identifier,
            8,
            [0x02,
             self._sid,
             EcuResetType.SOFTWARE_RESET,
             0xff, 0xff, 0xff, 0xff, 0xff])

    def verify_ecu_uds_reset(self, data) -> bool:
        data_length = data[0]
        sid = data[1]
        positive_sid = self._sid + 0x40
        pid = data[2]
        if sid == positive_sid and pid == EcuResetType.UDS_SOFTWARE_RESET:
            return True
        return False

    def verify_ecu_software_reset(self, data) -> bool:
        data_length = data[0]
        sid = data[1]
        positive_sid = self._sid + 0x40
        pid = data[2]
        if sid == positive_sid and pid == EcuResetType.SOFTWARE_RESET:
            return True
        return False
