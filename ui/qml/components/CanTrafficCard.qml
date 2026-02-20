import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

/*
  Карточка журнала CAN-трафика.
  Фильтр каждой колонки совмещает выбор из списка и произвольный ввод.
*/
Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    readonly property string anyOptionText: "Все"

    // Единые размеры колонок для строгого выравнивания.
    readonly property int colTime: 90
    readonly property int colDir: 54
    readonly property int colId: 110
    readonly property int colPgn: 86
    readonly property int colSrc: 48
    readonly property int colDst: 48
    readonly property int colJ1939: 360
    readonly property int colDlc: 40
    readonly property int colUds: 210

    readonly property int rowLeftPadding: 8
    readonly property int rowSpacing: 6
    readonly property int headerRightPadding: 8 + ((trafficScrollBar && trafficScrollBar.visible) ? trafficScrollBar.width : 0)

    function optionsWithAny(options) {
        var result = [anyOptionText]
        if (options) {
            for (var i = 0; i < options.length; i++) {
                result.push(options[i])
            }
        }
        return result
    }

    function comboValue(combo) {
        var raw = combo.editable ? combo.editText : combo.currentText
        var value = raw ? String(raw).trim() : ""
        if (value === anyOptionText) {
            return ""
        }
        return value
    }

    function applyFilter(field, value) {
        if (root.appController) {
            root.appController.setCanTrafficFilter(field, value)
        }
    }

    function applyFilterFromCombo(field, combo) {
        root.applyFilter(field, root.comboValue(combo))
    }

    function resetCombo(combo, field) {
        combo.currentIndex = 0
        if (combo.editable) {
            combo.editText = ""
        }
        root.applyFilter(field, "")
    }

    function clearFilters() {
        resetCombo(timeFilter, "time")
        resetCombo(dirFilter, "dir")
        resetCombo(idFilter, "frameId")
        resetCombo(pgnFilter, "pgn")
        resetCombo(srcFilter, "src")
        resetCombo(dstFilter, "dst")
        resetCombo(j1939Filter, "j1939")
        resetCombo(dlcFilter, "dlc")
        resetCombo(udsFilter, "uds")
        resetCombo(dataFilter, "data")
        if (root.appController) {
            root.appController.resetCanTrafficFilters()
        }
    }

    Layout.fillWidth: true
    Layout.preferredHeight: 332

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: "Журнал CAN"
                    color: root.textMain
                    font.pixelSize: 20
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                Text {
                    text: "TX/RX сообщения с разбором ID, PGN, адресов и ISO-TP"
                    color: root.textSoft
                    font.pixelSize: 12
                    font.family: "Bahnschrift"
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 32
            radius: 10
            color: "#e9f1fa"
            border.color: "#c9d8e8"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: root.rowLeftPadding
                anchors.rightMargin: root.headerRightPadding
                spacing: root.rowSpacing

                Text { text: "Время"; Layout.preferredWidth: root.colTime; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "Напр"; Layout.preferredWidth: root.colDir; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                Text { text: "ID"; Layout.preferredWidth: root.colId; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "PGN"; Layout.preferredWidth: root.colPgn; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "SRC"; Layout.preferredWidth: root.colSrc; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "DST"; Layout.preferredWidth: root.colDst; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "J1939"; Layout.preferredWidth: root.colJ1939; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "DLC"; Layout.preferredWidth: root.colDlc; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                Text { text: "UDS/ISO-TP"; Layout.preferredWidth: root.colUds; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
                Text { text: "Данные"; Layout.fillWidth: true; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; font.bold: true }
            }
        }

        // Единая строка фильтров: выбор из выпадающего списка + произвольный ввод.
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 32
            radius: 10
            color: "#f7fbff"
            border.color: "#d8e4f0"
            border.width: 1

            RowLayout {
                id: filtersRow
                anchors.fill: parent
                anchors.leftMargin: root.rowLeftPadding
                anchors.rightMargin: 6
                spacing: root.rowSpacing

                FilterComboBox { id: timeFilter; Layout.preferredWidth: root.colTime; popupMinWidth: 130; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterTimeOptions : []); onActivated: root.applyFilterFromCombo("time", timeFilter); onEditTextChanged: root.applyFilter("time", root.comboValue(timeFilter)) }
                FilterComboBox { id: dirFilter; Layout.preferredWidth: root.colDir; popupMinWidth: 95; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterDirOptions : []); onActivated: root.applyFilterFromCombo("dir", dirFilter); onEditTextChanged: root.applyFilter("dir", root.comboValue(dirFilter)) }
                FilterComboBox { id: idFilter; Layout.preferredWidth: root.colId; popupMinWidth: 180; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterIdOptions : []); onActivated: root.applyFilterFromCombo("frameId", idFilter); onEditTextChanged: root.applyFilter("frameId", root.comboValue(idFilter)) }
                FilterComboBox { id: pgnFilter; Layout.preferredWidth: root.colPgn; popupMinWidth: 140; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterPgnOptions : []); onActivated: root.applyFilterFromCombo("pgn", pgnFilter); onEditTextChanged: root.applyFilter("pgn", root.comboValue(pgnFilter)) }
                FilterComboBox { id: srcFilter; Layout.preferredWidth: root.colSrc; popupMinWidth: 120; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterSrcOptions : []); onActivated: root.applyFilterFromCombo("src", srcFilter); onEditTextChanged: root.applyFilter("src", root.comboValue(srcFilter)) }
                FilterComboBox { id: dstFilter; Layout.preferredWidth: root.colDst; popupMinWidth: 120; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterDstOptions : []); onActivated: root.applyFilterFromCombo("dst", dstFilter); onEditTextChanged: root.applyFilter("dst", root.comboValue(dstFilter)) }
                FilterComboBox { id: j1939Filter; Layout.preferredWidth: root.colJ1939; popupMinWidth: 520; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterJ1939Options : []); onActivated: root.applyFilterFromCombo("j1939", j1939Filter); onEditTextChanged: root.applyFilter("j1939", root.comboValue(j1939Filter)) }
                FilterComboBox { id: dlcFilter; Layout.preferredWidth: root.colDlc; popupMinWidth: 90; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterDlcOptions : []); onActivated: root.applyFilterFromCombo("dlc", dlcFilter); onEditTextChanged: root.applyFilter("dlc", root.comboValue(dlcFilter)) }
                FilterComboBox { id: udsFilter; Layout.preferredWidth: root.colUds; popupMinWidth: 340; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterUdsOptions : []); onActivated: root.applyFilterFromCombo("uds", udsFilter); onEditTextChanged: root.applyFilter("uds", root.comboValue(udsFilter)) }
                FilterComboBox { id: dataFilter; Layout.fillWidth: true; Layout.minimumWidth: 80; popupMinWidth: 620; editable: true; model: root.optionsWithAny(root.appController ? root.appController.canFilterDataOptions : []); onActivated: root.applyFilterFromCombo("data", dataFilter); onEditTextChanged: root.applyFilter("data", root.comboValue(dataFilter)) }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 12
            color: "#f4f8fd"
            border.color: "#d6e2ef"
            border.width: 1

            ListView {
                id: trafficList
                anchors.fill: parent
                anchors.leftMargin: 0
                anchors.rightMargin: 0
                anchors.topMargin: 6
                anchors.bottomMargin: 6
                clip: true
                spacing: 3
                model: root.appController ? root.appController.filteredCanTrafficLogs : []

                onCountChanged: if (count > 0) positionViewAtEnd()

                delegate: Rectangle {
                    width: trafficList.width
                    height: 26
                    radius: 8
                    color: index % 2 === 0 ? "#f8fbff" : "#eef4fb"
                    border.width: 1
                    border.color: "#e1ebf6"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: root.rowLeftPadding
                        anchors.rightMargin: root.headerRightPadding
                        spacing: root.rowSpacing

                        Text { text: modelData.time ? modelData.time : ""; Layout.preferredWidth: root.colTime; color: root.textSoft; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }

                        Rectangle {
                            Layout.preferredWidth: root.colDir
                            Layout.preferredHeight: 20
                            radius: 8
                            color: modelData.dirBg ? modelData.dirBg : "#e2e8f0"
                            border.color: modelData.dirBorder ? modelData.dirBorder : "#cbd5e1"
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: modelData.dir ? modelData.dir : "-"
                                color: modelData.dirColor ? modelData.dirColor : "#334155"
                                font.pixelSize: 11
                                font.bold: true
                                font.family: "Consolas"
                            }
                        }

                        Text { text: modelData.frameId ? modelData.frameId : ""; Layout.preferredWidth: root.colId; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.pgn ? modelData.pgn : ""; Layout.preferredWidth: root.colPgn; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.src ? modelData.src : ""; Layout.preferredWidth: root.colSrc; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.dst ? modelData.dst : ""; Layout.preferredWidth: root.colDst; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.j1939 ? modelData.j1939 : ""; Layout.preferredWidth: root.colJ1939; color: "#334155"; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.dlc ? modelData.dlc : ""; Layout.preferredWidth: root.colDlc; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.uds ? modelData.uds : ""; Layout.preferredWidth: root.colUds; color: "#475569"; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                        Text { text: modelData.data ? modelData.data : ""; Layout.fillWidth: true; color: root.textMain; font.pixelSize: 12; font.family: "Consolas"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
                    }
                }

                ScrollBar.vertical: ScrollBar {
                    id: trafficScrollBar
                }
            }

            Text {
                anchors.centerIn: parent
                text: "CAN сообщения пока не поступали"
                color: root.textSoft
                font.pixelSize: 13
                font.family: "Bahnschrift"
                visible: trafficList.count === 0
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Rectangle {
                Layout.preferredWidth: 212
                Layout.preferredHeight: 28
                radius: 8
                color: "#f7fbff"
                border.color: "#d5e2ef"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 6
                    spacing: 6

                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: root.appController && root.appController.canJournalEnabled ? "#16a34a" : "#f59e0b"
                        border.width: 0
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.appController && root.appController.canJournalEnabled ? "Журнал активен" : "Журнал на паузе"
                        color: "#51657a"
                        font.pixelSize: 10
                        font.family: "Bahnschrift"
                        elide: Text.ElideRight
                    }

                    FancySwitch {
                        checked: root.appController ? root.appController.canJournalEnabled : true
                        enabled: root.appController !== null
                        trackWidth: 38
                        trackHeight: 22
                        onToggled: if (root.appController) root.appController.setCanJournalEnabled(checked)
                    }
                }
            }

            Item {
                Layout.fillWidth: true
            }

            Text {
                text: root.appController ? ("Записей: " + trafficList.count + " / " + root.appController.canTrafficLogs.length) : ("Записей: " + trafficList.count)
                color: "#7489a1"
                font.pixelSize: 10
                font.family: "Bahnschrift"
            }

            Item {
                id: resetFiltersButton
                Layout.preferredWidth: 110
                Layout.preferredHeight: 26
                property bool hovered: resetFiltersMouse.containsMouse

                Rectangle {
                    anchors.fill: parent
                    radius: 8
                    color: resetFiltersButton.hovered ? "#eaf2ff" : "#f6f9ff"
                    border.width: 1
                    border.color: resetFiltersButton.hovered ? "#4f79a7" : "#b9cce1"
                }

                Text {
                    anchors.centerIn: parent
                    text: "Сброс фильтров"
                    color: resetFiltersButton.hovered ? "#234869" : "#3f5b78"
                    font.pixelSize: 10
                    font.family: "Bahnschrift"
                    font.bold: true
                }

                MouseArea {
                    id: resetFiltersMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.clearFilters()
                }
            }

            Item {
                id: clearJournalButton
                Layout.preferredWidth: 112
                Layout.preferredHeight: 26
                property bool hovered: clearJournalMouse.containsMouse

                Rectangle {
                    anchors.fill: parent
                    radius: 8
                    color: clearJournalButton.hovered ? "#e7f6f5" : "#f3fbfa"
                    border.width: 1
                    border.color: clearJournalButton.hovered ? "#0f766e" : "#94d6d2"
                }

                Text {
                    anchors.centerIn: parent
                    text: "Очистить CAN"
                    color: clearJournalButton.hovered ? "#0f4f4a" : "#255f5b"
                    font.pixelSize: 10
                    font.family: "Bahnschrift"
                    font.bold: true
                }

                MouseArea {
                    id: clearJournalMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: root.appController !== null
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (root.appController) root.appController.clearCanTrafficLogs()
                }
            }

        }
    }
}
