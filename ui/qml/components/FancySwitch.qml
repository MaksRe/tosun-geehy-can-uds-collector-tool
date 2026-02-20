import QtQuick 2.15
import QtQuick.Controls 2.15

/*
  Кастомный переключатель с плавной анимацией и мягкой подсветкой.
*/
Switch {
    id: control

    property color onColor: "#34d399"
    property color offColor: "#e7eef7"
    property color borderOnColor: "#10b981"
    property color borderOffColor: "#b8cbe0"
    property color knobColor: "#ffffff"
    property color disabledColor: "#d7e3ef"
    property int trackWidth: 52
    property int trackHeight: 30

    implicitWidth: trackWidth
    implicitHeight: trackHeight
    spacing: 0
    padding: 0
    hoverEnabled: true

    indicator: Item {
        implicitWidth: control.trackWidth
        implicitHeight: control.trackHeight

        Rectangle {
            id: track
            anchors.fill: parent
            radius: height / 2
            color: !control.enabled ? control.disabledColor : (control.checked ? control.onColor : control.offColor)
            border.width: 1
            border.color: control.checked ? control.borderOnColor : control.borderOffColor

            Behavior on color {
                ColorAnimation { duration: 140 }
            }

            Behavior on border.color {
                ColorAnimation { duration: 140 }
            }
        }

        Rectangle {
            anchors.fill: track
            radius: track.radius
            color: "#86efac"
            opacity: control.checked && control.enabled ? 0.18 : 0.0
            visible: opacity > 0
        }

        Rectangle {
            id: knob
            width: parent.height - 6
            height: width
            radius: width / 2
            y: 3
            x: control.checked ? parent.width - width - 3 : 3
            color: control.enabled ? control.knobColor : "#c2d2e1"
            border.width: 1
            border.color: control.checked ? "#9be7c6" : "#9fb2c8"

            Behavior on x {
                NumberAnimation {
                    duration: 170
                    easing.type: Easing.OutCubic
                }
            }
        }
    }

    contentItem: Item {}
}
