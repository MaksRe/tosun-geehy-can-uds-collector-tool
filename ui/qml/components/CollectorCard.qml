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
    readonly property int contentPadding: 14

    signal selectOutputDirectoryRequested()

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
            text: "Коллектор"
            color: root.textMain
            font.pixelSize: 20
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Опрос узлов по UDS и запись параметров в CSV"
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 10
            color: "#f8fbff"
            border.color: "#d6e2ef"
            border.width: 1
            implicitHeight: csvSectionLayout.implicitHeight + 18

            ColumnLayout {
                id: csvSectionLayout
                anchors.fill: parent
                anchors.margins: 9
                spacing: 7

                Text {
                    text: "CSV и каталог выгрузки"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                Text {
                    text: "Каталог"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.family: "Bahnschrift"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    FancyTextField {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        text: root.appController ? root.appController.collectorOutputDirectory : ""
                        readOnly: true
                        placeholderText: "Папка для CSV не выбрана"
                        textColor: root.textMain
                        bgColor: root.inputBg
                        borderColor: root.inputBorder
                        focusBorderColor: root.inputFocus
                    }

                    FancyButton {
                        Layout.preferredWidth: 168
                        Layout.preferredHeight: 34
                        fontPixelSize: 12
                        text: "Выбрать каталог"
                        tone: "#0ea5a4"
                        toneHover: "#0f766e"
                        tonePressed: "#115e59"
                        onClicked: root.selectOutputDirectoryRequested()
                    }

                    FancyButton {
                        Layout.preferredWidth: 182
                        Layout.preferredHeight: 34
                        fontPixelSize: 12
                        text: "Создать папку с датой"
                        tone: "#64748b"
                        toneHover: "#55657a"
                        tonePressed: "#465669"
                        onClicked: if (root.appController) root.appController.createCollectorTimestampedLogsDirectory()
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 10
            color: "#f8fbff"
            border.color: "#d6e2ef"
            border.width: 1
            implicitHeight: pollSectionLayout.implicitHeight + 18

            ColumnLayout {
                id: pollSectionLayout
                anchors.fill: parent
                anchors.margins: 9
                spacing: 8

                Text {
                    text: "Параметры опроса"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        spacing: 4
                        Layout.preferredWidth: 176

                        Text {
                            text: "Шаг UDS, мс"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: pollIntervalField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            text: root.appController ? String(root.appController.collectorPollIntervalMs) : "1000"
                            placeholderText: "мс"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            validator: IntValidator { bottom: 30; top: 10000 }
                            onAccepted: if (root.appController) root.appController.setCollectorPollIntervalMs(text)
                        }
                    }

                    ColumnLayout {
                        spacing: 4
                        Layout.preferredWidth: 216

                        Text {
                            text: "Пауза между циклами, мс"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.family: "Bahnschrift"
                        }

                        FancyTextField {
                            id: cyclePauseField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            text: root.appController ? String(root.appController.collectorCyclePauseMs) : "1000"
                            placeholderText: "мс"
                            textColor: root.textMain
                            bgColor: root.inputBg
                            borderColor: root.inputBorder
                            focusBorderColor: root.inputFocus
                            validator: IntValidator { bottom: 30; top: 10000 }
                            onAccepted: if (root.appController) root.appController.setCollectorCyclePauseMs(text)
                        }
                    }

                    Item { Layout.fillWidth: true }

                    FancyButton {
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 34
                        Layout.alignment: Qt.AlignBottom
                        fontPixelSize: 12
                        text: "Применить"
                        tone: "#0284c7"
                        toneHover: "#0369a1"
                        tonePressed: "#075985"
                        onClicked: if (root.appController) {
                            root.appController.setCollectorPollIntervalMs(pollIntervalField.text)
                            root.appController.setCollectorCyclePauseMs(cyclePauseField.text)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 304
            radius: 12
            color: "#f4f8fd"
            border.color: "#d6e2ef"

            Item {
                anchors.fill: parent
                anchors.margins: 8
                clip: true

                Rectangle {
                    id: controlPanel
                    width: 132
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    z: 2
                    radius: 10
                    color: "#ffffff"
                    border.color: "#d7e4f0"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        Text {
                            text: "Управление"
                            color: root.textSoft
                            font.pixelSize: 12
                            font.bold: true
                            font.family: "Bahnschrift"
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                        }

                        FancyButton {
                            text: "Старт"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            fontPixelSize: 12
                            tone: "#10b981"
                            toneHover: "#059669"
                            tonePressed: "#047857"
                            enabled: root.appController ? !root.appController.collectorRecording : false
                            onClicked: if (root.appController) root.appController.startCollectorRecording()
                        }

                        FancyButton {
                            text: "Пауза"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            fontPixelSize: 12
                            tone: "#f59e0b"
                            toneHover: "#d97706"
                            tonePressed: "#b45309"
                            enabled: root.appController ? root.appController.collectorRecording : false
                            onClicked: if (root.appController) root.appController.pauseCollectorRecording()
                        }

                        FancyButton {
                            text: "Стоп"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            fontPixelSize: 12
                            tone: "#ef4444"
                            toneHover: "#dc2626"
                            tonePressed: "#b91c1c"
                            enabled: root.appController ? (root.appController.collectorRecording || root.appController.collectorPaused) : false
                            onClicked: if (root.appController) root.appController.stopCollectorRecording()
                        }

                        FancyButton {
                            text: "Очистить узлы"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            fontPixelSize: 11
                            tone: "#64748b"
                            toneHover: "#55657a"
                            tonePressed: "#465669"
                            onClicked: if (root.appController) root.appController.clearCollectorNodes()
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                ColumnLayout {
                    id: tableArea
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: controlPanel.left
                    anchors.rightMargin: 10
                    z: 1
                    clip: true
                    spacing: 6
                    readonly property real columnWidth: Math.max(54, Math.floor((width - 52) / 7))

                    Text {
                        Layout.fillWidth: true
                        text: root.appController ? root.appController.collectorStateText : "Статус записи: -"
                        color: root.textSoft
                        font.pixelSize: 12
                        font.family: "Bahnschrift"
                        elide: Text.ElideRight
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Repeater {
                            model: [
                                "Узел",
                                "Период",
                                "Топливо",
                                "Температура",
                                "Cnt(топл.)",
                                "Cnt(темп.)",
                                "Время"
                            ]
                            delegate: Text {
                                Layout.preferredWidth: tableArea.columnWidth
                                text: modelData
                                color: root.textSoft
                                font.pixelSize: 11
                                font.family: "Bahnschrift"
                                font.bold: true
                                elide: Text.ElideRight
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }

                    ListView {
                        id: nodesList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 4
                        model: root.appController ? root.appController.collectorNodes : []

                        delegate: Rectangle {
                            width: nodesList.width
                            height: 28
                            radius: 8
                            color: index % 2 === 0 ? "#f8fbff" : "#edf3fa"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.node; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.period; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.fuelLevel; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.temperature; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.fuelCount; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.temperatureCount; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Text { Layout.preferredWidth: tableArea.columnWidth; text: modelData.lastSeen; color: root.textMain; font.pixelSize: 12; font.family: "Bahnschrift"; elide: Text.ElideRight }
                                Item { Layout.fillWidth: true }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: root.appController ? ("Узлов: " + root.appController.collectorNodes.length) : "Узлов: 0"
                            color: root.textSoft
                            font.pixelSize: 11
                            font.family: "Bahnschrift"
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }
    }

    Connections {
        target: root.appController
        function onCollectorPollIntervalChanged() {
            if (!pollIntervalField.activeFocus && root.appController) {
                pollIntervalField.text = String(root.appController.collectorPollIntervalMs)
            }
        }
        function onCollectorCyclePauseChanged() {
            if (!cyclePauseField.activeFocus && root.appController) {
                cyclePauseField.text = String(root.appController.collectorCyclePauseMs)
            }
        }
    }
}
