import logging
from enum import Enum

LOGGER = logging.getLogger(__name__)


class FirmwareState(Enum):
    no_errors = -1,
    successfully_uploaded = 0,
    loading_error = 1


class Firmware:

    def __init__(self, file_path: str):
        self._errcode: FirmwareState = FirmwareState.no_errors
        self._binary_content = self._open_file(file_path)

    def _open_file(self, file_path: str) -> bytes | None:
        file = None
        if file_path:
            try:
                # Открываем файл в бинарном режиме и читаем его содержимое
                with open(file_path, "rb") as file:
                    file = file.read()
                    self._errcode = FirmwareState.successfully_uploaded
            except Exception as e:
                self._errcode = FirmwareState.loading_error
                LOGGER.error(f"Ошибка при открытии файла: {e}")
            finally:
                if self._errcode == FirmwareState.successfully_uploaded:
                    LOGGER.info("Файл успешно открыт")
                    return file
                return None

    @property
    def state(self) -> FirmwareState:
        return self._errcode

    @property
    def binary_content(self) -> bytes:
        return self._binary_content

    def binary_content_size(self) -> int:
        if self._binary_content is None:
            return 0
        return len(self._binary_content)
