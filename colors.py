from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass
class RowColor:
    red = QColor(220, 20, 60)       # контрастный красный
    blue = QColor(100, 149, 237)    # контрастный голубой
    green = QColor(60, 179, 113)    # контрастный зеленый
    yellow = QColor(255, 215, 0)    # контрастный желтый
