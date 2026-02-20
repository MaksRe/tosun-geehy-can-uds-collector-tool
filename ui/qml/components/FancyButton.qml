import QtQuick 2.15

/*
  FancyButton
  - Stable click handling via MouseArea.
  - No system rectangular hover/focus overlay.
  - Compatible with `onClicked:` handlers in parent QML.
*/
Item {
    id: btn

    property alias text: label.text
    property color tone: "#3b82f6"
    property color toneHover: "#2563eb"
    property color tonePressed: "#1d4ed8"
    property color toneDisabled: "#d3deea"
    property bool debugLog: false
    property bool enabled: true
    property bool loading: false
    property int fontPixelSize: 14
    property string fontFamily: "Bahnschrift"
    readonly property bool interactiveEnabled: btn.enabled && !btn.loading

    signal clicked()

    implicitHeight: 38
    implicitWidth: Math.max(120, label.implicitWidth + (btn.loading ? 52 : 24))

    Rectangle {
        anchors.fill: parent
        radius: 10
        antialiasing: true
        border.width: 1
        border.color: btn.interactiveEnabled ? "#3f83d9" : "#b9c9d9"

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: !btn.interactiveEnabled ? btn.toneDisabled : (hitArea.pressed ? btn.tonePressed : btn.tone)
            }
            GradientStop {
                position: 1.0
                color: !btn.interactiveEnabled ? "#c7d4e2" : (hitArea.pressed ? "#1e4fa0" : "#2f69c8")
            }
        }
    }

    Row {
        anchors.centerIn: parent
        spacing: 8

        Item {
            id: spinner
            width: 16
            height: 16
            visible: btn.loading
            rotation: 0

            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: "transparent"
                border.width: 2
                border.color: "#0ea5e9"
                opacity: 0.35
            }

            Rectangle {
                width: 5
                height: 5
                radius: 2.5
                color: "#ffffff"
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
            }

            RotationAnimator on rotation {
                running: spinner.visible
                loops: Animation.Infinite
                from: 0
                to: 360
                duration: 780
            }
        }

        Text {
            id: label
            color: btn.interactiveEnabled ? "#ffffff" : "#7d93aa"
            font.pixelSize: btn.fontPixelSize
            font.family: btn.fontFamily
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: hitArea
        anchors.fill: parent
        enabled: btn.interactiveEnabled
        hoverEnabled: true
        preventStealing: true
        cursorShape: btn.interactiveEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor

        onClicked: function(mouse) {
            if (mouse.button !== Qt.LeftButton) {
                return
            }
            if (btn.debugLog) {
                console.log("[UI][FancyButton] clicked. text:", btn.text, "enabled:", btn.enabled)
            }
            btn.clicked()
        }
    }
}
