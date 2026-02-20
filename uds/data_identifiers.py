class UdsVar:

    def __init__(self, pid, size, description):
        self._pid: int = pid
        self._size: int = size
        self._description: str = description

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def size(self) -> int:
        return self._size

    @property
    def description(self) -> str:
        return self._description


class UdsData:
    vars = {
        "can_baud_rate"     : UdsVar(0x0010, 1, "Скорость CAN шины"),
        "can_sa"            : UdsVar(0x0011, 1, "Адрес источника данных"),
        "empty_fuel_tank"   : UdsVar(0x0012, 2, "Пустой бак"),
        "full_fuel_tank"    : UdsVar(0x0013, 2, "Полный бак"),
        "curr_fuel_tank"    : UdsVar(0x0014, 2, "Текущий уровень"),
        "fingerprint"       : UdsVar(0x1500, 2, "Отпечаток пальцев"),
        "type_session"      : UdsVar(0x0016, 1, "Тип сессии"),
        "k_fuel_level"      : UdsVar(0x0017, 2, "Коэффициент фильтра"),
        "raw_fuel_level"    : UdsVar(0x0018, 2, "Сырые данные уровня топлива"),
        "raw_temperature"   : UdsVar(0x0019, 2, "Сырые данные текущей температуры"),

        "vmecusndid"        : UdsVar(0xF188, 18, "Номер ПО ЭБУ изготовителя ТС"),
        "vmecusvndid"       : UdsVar(0xF189, 32, "Номер версии ПО ЭБУ изготовителя ТС"),
        "ssiddid"           : UdsVar(0xF18A, 32, "Название поставщика системы и информация об адресе"),
        "ecumddid"          : UdsVar(0xF18B, 16, "Дата изготовления ЭБУ"),
        "ecusndid"          : UdsVar(0xF18C, 253, "Серийный номер ЭБУ"),
        "vindid"            : UdsVar(0xF190, 17, "VIN-номер"),
        "vmecuhndid"        : UdsVar(0xF191, 32, "Номер аппаратного обеспечения, определенного ЭБУ изготовителя ТС"),
        "ssecuhwndid"       : UdsVar(0xF192, 32, "Номер аппаратного обеспечения, определенного ЭБУ поставщика системы"),
        "ssecuhwvndid"      : UdsVar(0xF193, 16, "Номер версии аппаратного обеспечения"),
        "ssecuswndid"       : UdsVar(0xF194, 128, "Номер программного обеспечения"),
        "ssecuswvndid"      : UdsVar(0xF195, 128, "Версия программного обеспечения"),
        "erotandid"         : UdsVar(0xF196, 64, "Норма выхлопных газов или номер официального утверждения типа"),
        "snoetdid"          : UdsVar(0xF197, 64, "Наименование системы или тип двигателя"),
        "rscotsndid"        : UdsVar(0xF198, 32, "Код ремонтной мастерской или серийный номер тестера"),
        "pddid"             : UdsVar(0xF199, 16, "Дата последнего перепрограммирования устройства"),
        "eiddid"            : UdsVar(0xF19D, 16, "Дата установки ЭБУ в транспортное средство"),
        "vmecuscndid"       : UdsVar(0xF1A0, 18, "Номер конфигурации программного обеспечения ЭБУ изготовителя ТС"),
        "vmecuscvndid"      : UdsVar(0xF1A1, 32, "Номер версии конфигурации ПО ЭБУ изготовителя ТС"),
        "idoptvms"          : UdsVar(0xF1A2, 256, "Опции идентификации определенного устройства/ТС производителем ТС"),
        "idoptsss"          : UdsVar(0xF1F0, 256, "Опции идентификации определенного устройства/ТС поставщиком системы")
    }

    can_baud_rate       = vars.get("can_baud_rate")
    can_sa              = vars.get("can_sa")
    empty_fuel_tank     = vars.get("empty_fuel_tank")
    full_fuel_tank      = vars.get("full_fuel_tank")
    curr_fuel_tank      = vars.get("curr_fuel_tank")
    fingerprint         = vars.get("fingerprint")
    type_session        = vars.get("type_session")
    k_fuel_level        = vars.get("k_fuel_level")
    raw_fuel_level      = vars.get("raw_fuel_level")
    raw_temperature     = vars.get("raw_temperature")

    vmecusndid          = vars.get("vmecusndid")
    vmecusvndid         = vars.get("vmecusvndid")
    ssiddid             = vars.get("ssiddid")
    ecumddid            = vars.get("ecumddid")
    ecusndid            = vars.get("ecusndid")
    vindid              = vars.get("vindid")
    vmecuhndid          = vars.get("vmecuhndid")
    ssecuhwndid         = vars.get("ssecuhwndid")
    ssecuhwvndid        = vars.get("ssecuhwvndid")
    ssecuswndid         = vars.get("ssecuswndid")
    ssecuswvndid        = vars.get("ssecuswvndid")
    erotandid           = vars.get("erotandid")
    snoetdid            = vars.get("snoetdid")
    rscotsndid          = vars.get("rscotsndid")
    pddid               = vars.get("pddid")
    eiddid              = vars.get("eiddid")
    vmecuscndid         = vars.get("vmecuscndid")
    vmecuscvndid        = vars.get("vmecuscvndid")
    idoptvms            = vars.get("idoptvms")
    idoptsss            = vars.get("idoptsss")

    @classmethod
    def get_pid(cls, index: int) -> int | None:
        if index > len(cls.vars) or index < 0:
            return None
        return list(cls.vars.values())[index].pid

    @classmethod
    def get_var(cls, index) -> UdsVar | None:
        if index > len(cls.vars) or index < 0:
            return None
        return list(cls.vars.values())[index]

    @classmethod
    def descriptions(cls) -> list:
        return [var.description for var in cls.vars.values()]
