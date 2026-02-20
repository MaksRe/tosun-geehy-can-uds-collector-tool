import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

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

    readonly property bool controlsEnabled: root.appController ? (!root.appController.programmingActive && !root.appController.sourceAddressBusy) : false

    Layout.fillWidth: true
    Layout.preferredHeight: contentColumn.implicitHeight + (root.contentPadding * 2)

    function syncFromController() {
        if (!root.appController) {
            return
        }

        txPriorityField.text = root.appController.txPriorityText
        txPgnField.text = root.appController.txPgnText
        txSrcField.text = root.appController.txSrcText
        txDstField.text = root.appController.txDstText

        rxPriorityField.text = root.appController.rxPriorityText
        rxPgnField.text = root.appController.rxPgnText
        rxSrcField.text = root.appController.rxSrcText
        rxDstField.text = root.appController.rxDstText
    }

    Component.onCompleted: syncFromController()

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 8

        Text {
            text: "UDS CAN идентификаторы"
            visible: root.showCardHeader
            color: root.textMain
            font.pixelSize: 18
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Изменяйте поля J1939 отдельно для TX и RX: Priority, PGN, Source, Destination"
            visible: root.showCardHeader
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Rectangle {
            id: txBox
            Layout.fillWidth: true
            Layout.preferredHeight: txColumn.implicitHeight + 16
            Layout.minimumHeight: txColumn.implicitHeight + 16
            radius: 10
            color: "#f4f8fd"
            border.color: "#d6e2ef"

            ColumnLayout {
                id: txColumn
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                Text {
                    text: "TX (отправка)"
                    color: root.textMain
                    font.pixelSize: 14
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    rowSpacing: 6
                    columnSpacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Приоритет"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: txPriorityField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Priority 0..7"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "PGN (2 байта)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: txPgnField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            maximumLength: 6
                            placeholderText: "PGN (например 0xDA6A)"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Адрес источника (SRC)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: txSrcField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Source 0x00..0xFF"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Адрес назначения (DST)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: txDstField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Destination 0x00..0xFF"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }
                }

                Text {
                    text: "TX ID: " + (root.appController ? root.appController.txIdentifierText : "-")
                    color: root.textSoft
                    font.pixelSize: 11
                    font.family: "Bahnschrift"
                }
            }
        }

        Rectangle {
            id: rxBox
            Layout.fillWidth: true
            Layout.preferredHeight: rxColumn.implicitHeight + 16
            Layout.minimumHeight: rxColumn.implicitHeight + 16
            radius: 10
            color: "#f4f8fd"
            border.color: "#d6e2ef"

            ColumnLayout {
                id: rxColumn
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                Text {
                    text: "RX (прием)"
                    color: root.textMain
                    font.pixelSize: 14
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    rowSpacing: 6
                    columnSpacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Приоритет"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: rxPriorityField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Priority 0..7"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "PGN (2 байта)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: rxPgnField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            maximumLength: 6
                            placeholderText: "PGN (например 0xDAF1)"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Адрес источника (SRC)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: rxSrcField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Source 0x00..0xFF"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        spacing: 2

                        Text {
                            text: "Адрес назначения (DST)"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: rxDstField
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Destination 0x00..0xFF"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            enabled: root.controlsEnabled
                        }
                    }
                }

                Text {
                    text: "RX ID: " + (root.appController ? root.appController.rxIdentifierText : "-")
                    color: root.textSoft
                    font.pixelSize: 11
                    font.family: "Bahnschrift"
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: "Применить ID"
                enabled: root.controlsEnabled
                tone: "#0ea5a4"
                toneHover: "#0f766e"
                tonePressed: "#115e59"
                onClicked: {
                    if (root.appController) {
                        root.appController.applyUdsIdentifiers(
                            txPriorityField.text,
                            txPgnField.text,
                            txSrcField.text,
                            txDstField.text,
                            rxPriorityField.text,
                            rxPgnField.text,
                            rxSrcField.text,
                            rxDstField.text
                        )
                    }
                }
            }

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: "Обновить"
                enabled: root.appController !== null
                tone: "#2563eb"
                toneHover: "#1d4ed8"
                tonePressed: "#1e40af"
                onClicked: if (root.appController) root.appController.refreshUdsIdentifiers()
            }
        }

    }

    Connections {
        target: root.appController

        function onUdsIdentifiersChanged() {
            root.syncFromController()
        }
    }
}
