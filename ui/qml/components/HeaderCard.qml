import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Top header card with global runtime status chips and debug toggle.
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color accentWarm: "#f59e0b"
    readonly property bool compactLayout: width < 1120
    readonly property int contentPadding: 14

    readonly property bool canConnected: appController ? appController.connected : false
    readonly property bool traceActive: appController ? appController.tracing : false
    readonly property bool programmingActive: appController ? appController.programmingActive : false
    signal openCanJournalRequested()

    implicitHeight: headerColumn.implicitHeight + (root.contentPadding * 2)

    ColumnLayout {
        id: headerColumn
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: "Панель коллектора CAN / UDS"
                color: root.textMain
                font.pixelSize: 26
                font.bold: true
                font.family: "Bahnschrift"
                elide: Text.ElideRight
            }

            FancyButton {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: root.compactLayout ? 150 : 164
                Layout.minimumWidth: 142
                Layout.preferredHeight: 34
                text: "Журнал CAN"
                fontPixelSize: 12
                tone: "#0ea5a4"
                toneHover: "#0f766e"
                tonePressed: "#115e59"
                onClicked: root.openCanJournalRequested()
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.compactLayout ? 2 : 4
            columnSpacing: 8
            rowSpacing: 6

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.canConnected ? "CAN: подключен" : "CAN: отключен"
                chipColor: root.canConnected ? "#e6f8ef" : "#fdecec"
                chipBorder: root.canConnected ? "#7acda5" : "#f5a5a5"
                textColor: root.textMain
            }

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.traceActive ? "Трассировка: активна" : "Трассировка: выкл"
                chipColor: root.traceActive ? "#e9f2ff" : "#f1f5fa"
                chipBorder: root.traceActive ? "#93c5fd" : "#c6d7ea"
                textColor: root.textMain
            }

            StatusChip {
                Layout.fillWidth: root.compactLayout
                label: root.programmingActive ? "Запись CSV: активна" : "Запись CSV: ожидание"
                chipColor: root.programmingActive ? "#fff4e6" : "#f1f5fa"
                chipBorder: root.programmingActive ? root.accentWarm : "#c6d7ea"
                textColor: root.textMain
            }

            Rectangle {
                Layout.fillWidth: root.compactLayout
                Layout.alignment: root.compactLayout ? Qt.AlignLeft : Qt.AlignRight
                radius: 10
                color: root.appController && root.appController.debugEnabled ? "#e7f8ef" : "#f1f5fa"
                border.color: root.appController && root.appController.debugEnabled ? "#88d4af" : "#c6d7ea"
                border.width: 1
                implicitHeight: 34
                implicitWidth: 168

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 7
                    spacing: 6

                    Text {
                        text: "Отладка"
                        color: root.textMain
                        font.pixelSize: 12
                        font.family: "Bahnschrift"
                    }

                    Item { Layout.fillWidth: true }

                    FancySwitch {
                        id: debugSwitch
                        trackWidth: 46
                        trackHeight: 26
                        onColor: "#10b981"
                        offColor: "#dfe9f5"
                        borderOnColor: "#059669"
                        borderOffColor: "#b4c8df"
                        checked: root.appController ? root.appController.debugEnabled : false
                        onToggled: {
                            if (root.appController) {
                                root.appController.setDebugEnabled(checked)
                            }
                        }
                    }
                }
            }
        }

    }
}

