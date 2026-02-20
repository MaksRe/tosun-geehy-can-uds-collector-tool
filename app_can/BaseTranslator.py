

class BaseTranslator:

    @staticmethod
    def to_int(value: str) -> int:
        """

        :param value:
        :return:
        """
        try:
            if isinstance(value, str):
                # Проверяем префикс и определяем основание
                if value.startswith("0b"):
                    return int(value, 2)
                elif value.startswith("0x"):
                    return int(value, 16)
                else:
                    return int(value)  # Десятичное представление по умолчанию
            else:
                return int(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def to_base(base: int, value: str | int) -> str:
        """

        :param base:
        :param value:
        :return:
        """
        if isinstance(value, str):
            int_value: int = BaseTranslator.to_int(value)
        else:
            int_value = value
        # Форматируем число в зависимости от системы счисления
        if base == 2:
            return bin(int_value)
        elif base == 16:
            return hex(int_value)
        else:
            return str(int(int_value))

    @staticmethod
    def hex_to_base(base: int, value: str) -> str:
        """

        :param base:
        :param value:
        :return:
        """
        int_value: int
        try:
            if isinstance(value, str):
                int_value = int(value, 16)
            else:
                int_value = int(value)
        except (ValueError, TypeError):
            return str(value)  # Возвращаем исходное значение, если оно не является числом

        # Форматируем число в зависимости от системы счисления
        if base == 2:
            return bin(int_value)
        elif base == 16:
            return hex(int_value)
        else:
            return str(int(int_value))
