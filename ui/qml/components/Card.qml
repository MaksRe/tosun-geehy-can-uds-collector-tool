import QtQuick 2.15

/*
  Базовая карточка интерфейса.
  Назначение:
  - задает единый фон, радиус скругления и обводку для крупных блоков экрана;
  - используется как фундамент для HeaderCard, ConnectionCard и остальных карточек.

  Публичные свойства:
  - cardColor: цвет заливки карточки;
  - cardBorder: цвет рамки карточки.
*/
Rectangle {
    property color cardColor: "#ffffff"
    property color cardBorder: "#d6e2ef"

    radius: 14
    color: cardColor
    border.color: cardBorder
    border.width: 1

    // Оставляем слой включенным, чтобы эффекты отрисовки были стабильнее на разных GPU.
    layer.enabled: true
}
