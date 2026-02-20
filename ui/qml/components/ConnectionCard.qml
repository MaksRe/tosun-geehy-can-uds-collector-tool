import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Карточка аппаратного подключения CAN-адаптера.
  Назначение:
  - сканирование доступных устройств;
  - подключение/отключение;
  - запуск/останов trace;
  - выбор канала, скорости и терминатора;
  - вывод краткой информации об адаптере.

  Контракт:
  - appController предоставляет методы scanDevices, toggleConnection, toggleTrace
    и свойства devices/selectedDeviceIndex/connected/traceActionText/connectionActionText.
*/
Card {
    id: root

    property var appController
    readonly property bool traceActive: root.appController ? root.appController.tracing : false
    readonly property bool canSettingsEditable: !root.traceActive
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    property color inputBg: "#f7fbff"
    property color inputBorder: "#c8d9ea"
    property color inputFocus: "#0ea5e9"
    readonly property int contentPadding: 14

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
        spacing: 10

        Text {
            text: "Аппаратное подключение"
            color: root.textMain
            font.pixelSize: 20
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Выберите адаптер, подключитесь и запустите trace"
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
        }

        // Строка выбора физического USB/CAN устройства.
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            FancyComboBox {
                id: deviceCombo
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                model: root.appController ? root.appController.devices : []
                currentIndex: root.appController ? root.appController.selectedDeviceIndex : -1
                textColor: root.textMain
                bgColor: root.inputBg
                borderColor: root.inputBorder
                focusBorderColor: root.inputFocus

                onActivated: {
                    if (root.appController && root.appController.debugEnabled) {
                        console.log("[UI][ConnectionCard] device activated index:", currentIndex, "appController exists:", !!root.appController)
                    }
                    if (root.appController) {
                        if (root.appController.debugEnabled && root.appController.debugEvent) {
                            root.appController.debugEvent("UI: device index changed to " + currentIndex)
                        }
                        root.appController.setSelectedDeviceIndex(currentIndex)
                    } else {
                        console.error("[UI][ConnectionCard] appController is null in onActivated")
                    }
                }
            }

            FancyButton {
                Layout.preferredWidth: 148
                Layout.minimumWidth: 136
                text: "Сканировать"
                debugLog: root.appController ? root.appController.debugEnabled : false
                tone: "#0ea5a4"
                toneHover: "#0f766e"
                tonePressed: "#115e59"
                onClicked: {
                    if (root.appController && root.appController.debugEnabled) {
                        console.log("[UI][ConnectionCard] Scan clicked. appController exists:", !!root.appController)
                    }
                    if (root.appController) {
                        if (root.appController.debugEnabled && root.appController.debugEvent) {
                            root.appController.debugEvent("UI: Scan button clicked")
                        }
                        root.appController.scanDevices()
                    } else {
                        console.error("[UI][ConnectionCard] appController is null on Scan click")
                    }
                }
            }
        }

        // Базовые действия связи: открыть/закрыть канал и старт/стоп trace.
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: root.appController ? root.appController.connectionActionText : "Подключиться"
                tone: "#3b82f6"
                toneHover: "#2563eb"
                tonePressed: "#1d4ed8"
                onClicked: if (root.appController) root.appController.toggleConnection()
            }

            FancyButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                text: root.appController ? root.appController.traceActionText : "Запустить трассировку"
                enabled: root.appController ? root.appController.connected : false
                tone: "#16a34a"
                toneHover: "#15803d"
                tonePressed: "#166534"
                onClicked: {
                    if (root.appController) {
                        root.appController.toggleTrace(channelCombo.currentIndex, parseInt(baudCombo.currentText), terminatorSwitch.checked)
                    }
                }
            }
        }

        // Параметры CAN-шины для текущей trace-сессии.
        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 8
            rowSpacing: 4
            opacity: root.canSettingsEditable ? 1.0 : 0.65

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                spacing: 2

                Text {
                    text: "CAN канал"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.family: "Bahnschrift"
                }

                FancyComboBox {
                    id: channelCombo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    model: ["Канал 1", "Канал 2", "Канал 3", "Канал 4"]
                    currentIndex: 0
                    enabled: root.canSettingsEditable
                    textColor: root.textMain
                    bgColor: root.inputBg
                    borderColor: root.inputBorder
                    focusBorderColor: root.inputFocus
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                spacing: 2

                Text {
                    text: "Скорость, кбит/с"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.family: "Bahnschrift"
                }

                FancyComboBox {
                    id: baudCombo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    model: ["125", "250", "500", "1000"]
                    currentIndex: 2
                    enabled: root.canSettingsEditable
                    textColor: root.textMain
                    bgColor: root.inputBg
                    borderColor: root.inputBorder
                    focusBorderColor: root.inputFocus
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                spacing: 2

                Text {
                    text: "Терминатор"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.family: "Bahnschrift"
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 40
                    radius: 10
                    color: root.inputBg
                    border.color: root.inputBorder
                    border.width: 1

                    Item {
                        anchors.fill: parent

                        // Аппаратный терминатор (обычно 120 Ом), если поддерживается адаптером.
                        FancySwitch {
                            id: terminatorSwitch
                            anchors.centerIn: parent
                            trackWidth: 48
                            trackHeight: 26
                            enabled: root.canSettingsEditable
                            onColor: "#0ea5e9"
                            offColor: "#e4ecf7"
                            borderOnColor: "#0284c7"
                            borderOffColor: "#c0d1e4"
                            checked: true
                        }
                    }
                }
            }
        }

        // Техническая информация о выбранном устройстве.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: infoGrid.implicitHeight + 14
            radius: 10
            color: "#f4f8fd"
            border.color: "#d6e2ef"

            GridLayout {
                id: infoGrid
                anchors.fill: parent
                anchors.margins: 8
                columns: 1
                rowSpacing: 4

                LabelValue {
                    labelText: "Производитель"
                    valueText: root.appController ? root.appController.manufacturer : ""
                    labelColor: root.textSoft
                    valueColor: root.textMain
                    labelWidth: 160
                }

                LabelValue {
                    labelText: "Модель"
                    valueText: root.appController ? root.appController.product : ""
                    labelColor: root.textSoft
                    valueColor: root.textMain
                    labelWidth: 160
                }

                LabelValue {
                    labelText: "Серийный номер"
                    valueText: root.appController ? root.appController.serial : ""
                    labelColor: root.textSoft
                    valueColor: root.textMain
                    labelWidth: 160
                }

                LabelValue {
                    labelText: "Идентификатор устройства"
                    valueText: root.appController ? root.appController.deviceHandle : ""
                    labelColor: root.textSoft
                    valueColor: root.textMain
                    labelWidth: 160
                }
            }
        }
    }
}
