class J1939CanIdentifier:
    """
    Идентификатор состовляет 29 бит
    """

    __slots__ = ['_prio', '_pgn', '_dst', '_src']

    def __init__(self, identifier: int):
        self._prio = 0
        self._pgn = 0
        self._src = 0
        self._parse(identifier)

    def _parse(self, identifier: int):
        self._prio = identifier >> 26  # 3 bits
        self._pgn = (identifier >> 8) & 0x3FFFF  # 18 bits
        self._src = identifier & 0xff  # 8 bits

    @property
    def priority(self) -> int:
        return self._prio

    @priority.setter
    def priority(self, prio: int):
        self._prio = prio

    @property
    def pgn(self) -> int:
        return self._pgn

    @pgn.setter
    def pgn(self, pgn: int):
        self._pgn = pgn

    @property
    def src(self) -> int:
        return self._src

    @src.setter
    def src(self, src: int):
        self._src = src

    @property
    def dst(self) -> int:
        return self.pgn & 0xff

    @dst.setter
    def dst(self, dst: int):
        self.pgn = self.pgn & 0x3FF00
        self.pgn = self.pgn | (dst & 0xff)

    @property
    def identifier(self) -> int:
        return ((self._prio << 26) |
                (self._pgn << 8) |
                (self._src & 0xff))

    @identifier.setter
    def identifier(self, val: int):
        self._parse(val)
