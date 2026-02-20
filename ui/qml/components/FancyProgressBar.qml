import QtQuick 2.15
import QtQuick.Controls 2.15

/*
  Кастомный ProgressBar для процесса программирования.
  Назначение:
  - визуально читаемый трек и заполнение с градиентом;
  - плавная анимация роста полосы при поступлении данных.

  Публичные свойства:
  - trackColor/trackBorderColor: цвета подложки;
  - fillStartColor/fillEndColor: градиент активной части.
*/
ProgressBar {
    id: control

    property color trackColor: "#edf3fa"
    property color trackBorderColor: "#c8d9ea"
    property color fillStartColor: "#38bdf8"
    property color fillEndColor: "#0ea5e9"

    implicitHeight: 20

    background: Rectangle {
        radius: 10
        color: trackColor
        border.color: trackBorderColor
        border.width: 1
    }

    contentItem: Item {
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            // Ограничиваем минимум ширины видимой части, чтобы прогресс не выглядел "мертвым" на старте.
            width: control.visualPosition <= 0 ? 0 : Math.max(14, parent.width * control.visualPosition)
            radius: 10
            visible: width > 0

            gradient: Gradient {
                GradientStop { position: 0.0; color: fillStartColor }
                GradientStop { position: 1.0; color: fillEndColor }
            }

            Behavior on width {
                NumberAnimation {
                    duration: 220
                    easing.type: Easing.OutCubic
                }
            }
        }
    }
}
