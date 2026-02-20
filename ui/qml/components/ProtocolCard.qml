import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Карточка параметров протокола UDS.
  Назначение:
  - изменение Source Address (CAN SA) через WriteDataById;
  - выбор порядка байтов для передачи блоков bootloader-сессии.
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    property color inputBg: "#f7fbff"
    property color inputBorder: "#c8d9ea"
    property color inputFocus: "#0ea5e9"
    property bool showCardHeader: false
    readonly property int contentPadding: 12
    readonly property bool sourceAddressWriteBusy: root.appController ? (root.appController.sourceAddressBusy && root.appController.sourceAddressOperation === "write") : false
    readonly property bool sourceAddressReadBusy: root.appController ? (root.appController.sourceAddressBusy && root.appController.sourceAddressOperation === "read") : false

    Layout.fillWidth: true
    implicitHeight: contentColumn.implicitHeight + (root.contentPadding * 2)

    ColumnLayout {
        id: contentColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: root.contentPadding
        anchors.rightMargin: root.contentPadding
        anchors.topMargin: root.contentPadding
        spacing: 8

        Text {
            text: "Параметры протокола"
            visible: root.showCardHeader
            color: root.textMain
            font.pixelSize: 18
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Изменение Source Address и порядка байтов UDS"
            visible: root.showCardHeader
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
        }

        Text {
            text: "Адрес источника (Source Address, SA)"
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            FancyTextField {
                id: sourceAddressField
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: root.appController ? root.appController.sourceAddressText : "0x6A"
                placeholderText: "0x6A"
                enabled: root.appController ? (!root.appController.sourceAddressBusy && !root.appController.programmingActive) : false
                textColor: root.textMain
                bgColor: root.inputBg
                borderColor: root.inputBorder
                focusBorderColor: root.inputFocus
                onTextEdited: if (root.appController) root.appController.setSourceAddressText(text)
            }

            FancyButton {
                Layout.preferredWidth: 146
                Layout.minimumWidth: 136
                text: root.sourceAddressWriteBusy ? "Применение..." : "Применить SA"
                loading: root.sourceAddressWriteBusy
                enabled: root.appController ? (!root.appController.sourceAddressBusy && !root.appController.programmingActive) : false
                tone: "#0ea5a4"
                toneHover: "#0f766e"
                tonePressed: "#115e59"
                onClicked: if (root.appController) root.appController.applySourceAddress(sourceAddressField.text)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item {
                Layout.fillWidth: true
            }

            FancyButton {
                Layout.fillWidth: false
                text: root.sourceAddressReadBusy ? "Чтение..." : "Прочитать SA"
                enabled: root.appController ? (!root.appController.sourceAddressBusy && !root.appController.programmingActive) : false
                loading: root.sourceAddressReadBusy
                Layout.preferredWidth: 146
                Layout.minimumWidth: 136
                tone: "#2563eb"
                toneHover: "#1d4ed8"
                tonePressed: "#1e40af"
                onClicked: if (root.appController) root.appController.readSourceAddress()
            }
        }

        Text {
            text: "Порядок байтов при передаче"
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            Layout.fillWidth: true
        }

        FancyComboBox {
            id: endianCombo
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            model: ["Big Endian (старший байт первым)", "Little Endian (младший байт первым)"]
            currentIndex: root.appController ? root.appController.transferByteOrderIndex : 0
            enabled: root.appController ? (!root.appController.programmingActive && !root.appController.sourceAddressBusy) : false
            textColor: root.textMain
            bgColor: root.inputBg
            borderColor: root.inputBorder
            focusBorderColor: root.inputFocus

            onActivated: if (root.appController) root.appController.setTransferByteOrderIndex(currentIndex)
        }

    }

    Connections {
        target: root.appController

        function onSourceAddressTextChanged() {
            if (!root.appController) {
                return
            }
            if (sourceAddressField.text !== root.appController.sourceAddressText) {
                sourceAddressField.text = root.appController.sourceAddressText
            }
        }
    }
}
