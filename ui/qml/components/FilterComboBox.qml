import QtQuick 2.15
import QtQuick.Controls 2.15

ComboBox {
    id: control

    property color fieldColor: "#ffffff"
    property color fieldBorderColor: "#c8d8ea"
    property color fieldHoverBorderColor: "#7fb0e0"
    property color fieldFocusBorderColor: "#2b79d2"
    property color fieldTextColor: "#1f2d3d"

    property color popupColor: "#ffffff"
    property color popupBorderColor: "#b7cade"

    property color itemTextColor: "#324b65"
    property color itemHoverTextColor: "#0f3158"
    property color itemSelectedTextColor: "#0b2948"
    property color itemHoverColor: "#d8eafc"
    property color itemSelectedColor: "#bedbfa"
    property color itemSelectedBorderColor: "#7eaee0"
    property int popupMinWidth: 180
    property int popupMaxWidth: 760
    property int _popupWidth: popupMinWidth

    implicitHeight: 24
    font.pixelSize: 10
    font.family: "Consolas"
    hoverEnabled: true

    contentItem: TextInput {
        width: Math.max(0, control.width - 22)
        height: control.availableHeight
        leftPadding: 5
        rightPadding: 2
        text: control.editable ? control.editText : control.displayText
        font: control.font
        color: control.fieldTextColor
        selectionColor: "#9ac3f0"
        selectedTextColor: "#0f2742"
        verticalAlignment: Text.AlignVCenter
        readOnly: !control.editable
        selectByMouse: true
        clip: true

        onTextEdited: {
            if (control.editable) {
                control.editText = text
            }
        }
    }

    function updatePopupWidth() {
        var maxChars = 0
        var n = control.count
        for (var i = 0; i < n; i++) {
            var txt = control.textAt(i)
            if (txt && txt.length > maxChars) {
                maxChars = txt.length
            }
        }

        var estimated = 26 + maxChars * 7
        var base = Math.max(control.width, control.popupMinWidth)
        control._popupWidth = Math.min(control.popupMaxWidth, Math.max(base, estimated))
    }

    Component.onCompleted: updatePopupWidth()
    onCountChanged: updatePopupWidth()
    onModelChanged: updatePopupWidth()

    indicator: Item {
        x: control.width - width - 1
        y: 0
        width: 20
        height: control.availableHeight
        z: 3

        Canvas {
            id: arrowCanvas
            anchors.centerIn: parent
            width: 9
            height: 6
            contextType: "2d"

            onPaint: {
                context.reset()
                context.moveTo(0, 0)
                context.lineTo(width, 0)
                context.lineTo(width / 2, height)
                context.closePath()
                context.fillStyle = "#5f7d9f"
                context.fill()
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            preventStealing: true
            onPressed: mouse.accepted = true
            onClicked: {
                if (control.popup.visible) {
                    control.popup.close()
                } else {
                    control.popup.open()
                }
            }
        }
    }

    background: Rectangle {
        radius: 7
        color: control.fieldColor
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus
            ? control.fieldFocusBorderColor
            : (control.hovered ? control.fieldHoverBorderColor : control.fieldBorderColor)
    }

    popup: Popup {
        y: control.height + 4
        width: control._popupWidth
        padding: 4
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 260)

        background: Rectangle {
            radius: 8
            color: control.popupColor
            border.color: control.popupBorderColor
            border.width: 1
        }

        contentItem: ListView {
            anchors.fill: parent
            clip: true
            model: control.delegateModel
            currentIndex: control.highlightedIndex
            spacing: 2
            implicitHeight: contentHeight

            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }

    delegate: ItemDelegate {
        width: Math.max(0, control.popup.width - 8)
        implicitHeight: 28
        hoverEnabled: true
        highlighted: control.highlightedIndex === index

        property string delegateText: {
            var txt = control.textAt(index)
            if (txt !== undefined && txt !== null && String(txt).length > 0) {
                return String(txt)
            }
            if (modelData !== undefined && modelData !== null) {
                if (typeof modelData === "string" || typeof modelData === "number") {
                    return String(modelData)
                }
                if (typeof modelData === "object") {
                    if (control.textRole && modelData[control.textRole] !== undefined) {
                        return String(modelData[control.textRole])
                    }
                    if (modelData.display !== undefined) {
                        return String(modelData.display)
                    }
                }
            }
            return ""
        }

        text: delegateText

        contentItem: Text {
            text: parent.text
            font.pixelSize: 11
            font.family: "Consolas"
            color: parent.highlighted
                ? control.itemSelectedTextColor
                : (parent.hovered ? control.itemHoverTextColor : control.itemTextColor)
            verticalAlignment: Text.AlignVCenter
            leftPadding: 8
            rightPadding: 8
            elide: Text.ElideRight
        }

        background: Rectangle {
            radius: 6
            color: parent.highlighted
                ? control.itemSelectedColor
                : (parent.hovered ? control.itemHoverColor : "transparent")
            border.width: (parent.highlighted || parent.hovered) ? 1 : 0
            border.color: parent.highlighted ? control.itemSelectedBorderColor : "#b4d0ef"
        }
    }
}
