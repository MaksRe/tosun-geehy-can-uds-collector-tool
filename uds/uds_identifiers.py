from j1939.j1939_can_identifier import J1939CanIdentifier


class UdsIdentifiers:
    rx = J1939CanIdentifier(0x18daf16a)
    tx = J1939CanIdentifier(0x18da6af1)

    @classmethod
    def set_tx(cls, iden: int):
        cls.tx.identifier = iden
        cls.rx.src = cls.tx.dst

    @classmethod
    def set_rx(cls, iden: int):
        cls.rx.identifier = iden
        cls.tx.dst = cls.rx.src

    @classmethod
    def set_src(cls, src: int):
        cls.tx.dst = src
        cls.rx.src = src
