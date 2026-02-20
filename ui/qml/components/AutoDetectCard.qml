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

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 8

        Text {
            text: "Автоопределение адреса"
            visible: root.showCardHeader
            color: root.textMain
            font.pixelSize: 18
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            text: "Анализ входящего RX J1939 потока и выбор кандидата адреса устройства"
            visible: root.showCardHeader
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            text: "Кандидат адреса из потока"
            color: root.textSoft
            font.pixelSize: 11
            font.family: "Bahnschrift"
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 34
            radius: 9
            color: "#f7fbff"
            border.color: "#d7e3ef"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                Text {
                    Layout.fillWidth: true
                    text: root.appController && root.appController.autoDetectEnabled
                          ? "Автообновление кандидатов: вкл"
                          : "Автообновление кандидатов: пауза"
                    color: root.textSoft
                    font.pixelSize: 11
                    font.family: "Bahnschrift"
                    elide: Text.ElideRight
                }

                FancySwitch {
                    checked: root.appController ? root.appController.autoDetectEnabled : true
                    enabled: root.appController !== null
                    trackWidth: 42
                    trackHeight: 24
                    onToggled: if (root.appController) root.appController.setAutoDetectEnabled(checked)
                }
            }
        }

        FancyComboBox {
            id: observedCandidatesCombo
            Layout.fillWidth: true
            model: root.appController ? root.appController.observedUdsCandidates : []
            enabled: root.appController !== null
                     && root.appController.observedUdsCandidates.length > 0
                     && root.controlsEnabled
            currentIndex: root.appController ? root.appController.selectedObservedUdsCandidateIndex : -1
            textColor: root.textMain
            bgColor: root.inputBg
            borderColor: root.inputBorder
            focusBorderColor: root.inputFocus
            onActivated: {
                if (root.appController) {
                    root.appController.setSelectedObservedUdsCandidateIndex(currentIndex)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 9
            color: "#eef5ff"
            border.color: "#c9d8ec"
            implicitHeight: statusText.implicitHeight + 12

            Text {
                id: statusText
                anchors.fill: parent
                anchors.margins: 6
                text: root.appController ? root.appController.observedUdsCandidateText : "Контроллер недоступен"
                color: root.textSoft
                font.pixelSize: 11
                font.family: "Bahnschrift"
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            FancyButton {
                Layout.fillWidth: true
                Layout.minimumWidth: 148
                text: "Применить адрес"
                enabled: root.controlsEnabled
                         && root.appController !== null
                         && root.appController.observedUdsCandidateAvailable
                tone: "#0284c7"
                toneHover: "#0369a1"
                tonePressed: "#075985"
                onClicked: if (root.appController) root.appController.applyObservedUdsIdentifiers()
            }

            FancyButton {
                Layout.fillWidth: true
                Layout.minimumWidth: 120
                text: "Сбросить"
                enabled: root.appController !== null && root.appController.observedUdsCandidateAvailable
                tone: "#64748b"
                toneHover: "#475569"
                tonePressed: "#334155"
                onClicked: if (root.appController) root.appController.resetObservedUdsCandidate()
            }
        }
    }
}
