import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import QtQuick.Window 2.15
import "."

Card {
    id: root

    property var appController
    property color textMain: "#1f2d3d"
    property color textSoft: "#607084"
    readonly property int contentPadding: 14

    property int viewMode: 2
    property int selectedNodeIndex: 0
    property var nodeEnabledMap: ({})
    property var nodeSpoilerExpandedMap: ({})
    property var metricsSpoilerExpandedMap: ({})
    property var overlayLegendModel: []
    property var popupLegendModel: []
    property bool showPointLabels: false
    property bool includeLoadedCsv: true
    property int rangeStartIndex: 0
    property int rangeEndIndex: -1

    readonly property var nodePalette: ["#2563eb", "#10b981", "#f97316", "#8b5cf6", "#ef4444", "#14b8a6", "#0ea5e9", "#a855f7"]

    Layout.fillWidth: true
    implicitHeight: contentColumn.implicitHeight + (contentPadding * 2)

    function trendNodes() { return root.appController ? root.appController.collectorTrendNodes : [] }
    function csvSeries() { return root.appController ? root.appController.collectorTrendCsvSeries : [] }
    function nodeLabelList() { return root.appController ? root.appController.collectorTrendNodeLabels : [] }
    function metricsRows() { return root.appController ? root.appController.collectorTrendMetricsRows : [] }
    function networkMetrics() { return root.appController ? root.appController.collectorTrendNetworkMetrics : ({}) }

    function colorForNode(index) {
        if (index < 0) return "#2563eb"
        return root.nodePalette[index % root.nodePalette.length]
    }

    function syncNodeEnabled() {
        var nodes = trendNodes()
        var nextMap = {}
        for (var i = 0; i < nodes.length; i++) {
            var label = String(nodes[i].node)
            nextMap[label] = root.nodeEnabledMap.hasOwnProperty(label) ? root.nodeEnabledMap[label] : true
        }
        root.nodeEnabledMap = nextMap
        if (nodes.length === 0) root.selectedNodeIndex = -1
        else if (root.selectedNodeIndex < 0 || root.selectedNodeIndex >= nodes.length) root.selectedNodeIndex = 0
    }

    function syncSpoilerState() {
        var nodes = trendNodes()
        var nextMap = {}
        for (var i = 0; i < nodes.length; i++) {
            var label = String(nodes[i].node)
            nextMap[label] = root.nodeSpoilerExpandedMap.hasOwnProperty(label) ? root.nodeSpoilerExpandedMap[label] : (i === 0)
        }
        root.nodeSpoilerExpandedMap = nextMap
    }

    function nodeSpoilerExpanded(label, index) {
        if (root.nodeSpoilerExpandedMap.hasOwnProperty(label)) return root.nodeSpoilerExpandedMap[label] === true
        return index === 0
    }

    function setNodeSpoilerExpanded(label, expanded) {
        var nextMap = {}
        for (var key in root.nodeSpoilerExpandedMap)
            if (root.nodeSpoilerExpandedMap.hasOwnProperty(key)) nextMap[key] = root.nodeSpoilerExpandedMap[key]
        nextMap[String(label)] = !!expanded
        root.nodeSpoilerExpandedMap = nextMap
    }

    function syncMetricsSpoilerState() {
        var rows = metricsRows()
        var nextMap = {}
        for (var i = 0; i < rows.length; i++) {
            var label = String(rows[i].node)
            nextMap[label] = root.metricsSpoilerExpandedMap.hasOwnProperty(label) ? root.metricsSpoilerExpandedMap[label] : false
        }
        root.metricsSpoilerExpandedMap = nextMap
    }

    function metricsSpoilerExpanded(label) {
        var key = String(label)
        if (root.metricsSpoilerExpandedMap.hasOwnProperty(key))
            return root.metricsSpoilerExpandedMap[key] === true
        return false
    }

    function setMetricsSpoilerExpanded(label, expanded) {
        var key = String(label)
        var nextMap = {}
        for (var existing in root.metricsSpoilerExpandedMap) {
            if (root.metricsSpoilerExpandedMap.hasOwnProperty(existing))
                nextMap[existing] = root.metricsSpoilerExpandedMap[existing]
        }
        nextMap[key] = !!expanded
        root.metricsSpoilerExpandedMap = nextMap
    }

    function isNodeVisible(label) { return !root.nodeEnabledMap.hasOwnProperty(label) || root.nodeEnabledMap[label] !== false }

    function toggleNodeVisible(label) {
        var nextMap = {}
        for (var key in root.nodeEnabledMap)
            if (root.nodeEnabledMap.hasOwnProperty(key)) nextMap[key] = root.nodeEnabledMap[key]
        var current = nextMap.hasOwnProperty(label) ? (nextMap[label] !== false) : true
        nextMap[label] = !current
        root.nodeEnabledMap = nextMap
    }

    function setAllNodesVisible(flag) {
        var nodes = trendNodes()
        var nextMap = {}
        for (var i = 0; i < nodes.length; i++) nextMap[String(nodes[i].node)] = flag
        root.nodeEnabledMap = nextMap
    }

    function hasNodeVisibilityFilter() {
        var nodes = trendNodes()
        for (var i = 0; i < nodes.length; i++) {
            var label = String(nodes[i].node)
            if (!isNodeVisible(label))
                return true
        }
        return false
    }

    function selectedNodeEntry() {
        var nodes = trendNodes()
        if (nodes.length === 0) return null
        var index = root.selectedNodeIndex
        if (index < 0 || index >= nodes.length) index = 0
        return nodes[index]
    }

    function liveOverlaySeries() {
        var allNodes = trendNodes()
        var result = []
        for (var i = 0; i < allNodes.length; i++) {
            var node = allNodes[i]
            var rawLabel = String(node.node)
            if (!isNodeVisible(rawLabel)) continue
            result.push({"node": rawLabel, "points": node.points, "color": colorForNode(i)})
        }
        return result
    }

    function csvOverlaySeries(colorOffset) {
        var csvItems = csvSeries()
        var result = []
        var startIndex = Math.max(0, Number(colorOffset))
        for (var i = 0; i < csvItems.length; i++) {
            var item = csvItems[i]
            if (!item || !item.points || item.points.length <= 0)
                continue
            var label = String(item.node ? item.node : ("CSV " + (i + 1)))
            result.push({
                "node": label,
                "points": item.points,
                "color": colorForNode(startIndex + i)
            })
        }
        return result
    }

    function overlaySeries() {
        var result = liveOverlaySeries()
        if (root.includeLoadedCsv) {
            var csvItems = csvOverlaySeries(result.length)
            for (var i = 0; i < csvItems.length; i++)
                result.push(csvItems[i])
        }
        return result
    }

    function popupUseOverlayMode() {
        return root.viewMode !== 0 || root.hasNodeVisibilityFilter() || (root.includeLoadedCsv && root.csvSeries().length > 0)
    }

    function popupSeries() {
        var result = []
        if (root.viewMode === 0 && !root.hasNodeVisibilityFilter()) {
            var selected = root.selectedNodeEntry()
            if (selected && selected.points && selected.points.length > 0)
                result.push({"node": String(selected.node), "points": selected.points, "color": colorForNode(root.selectedNodeIndex)})
        } else {
            result = liveOverlaySeries()
        }

        if (root.includeLoadedCsv) {
            var csvItems = csvOverlaySeries(result.length)
            for (var i = 0; i < csvItems.length; i++)
                result.push(csvItems[i])
        }
        return result
    }

    function refreshLegendModels() {
        root.overlayLegendModel = root.overlaySeries()
        root.popupLegendModel = root.overlaySeries()
    }

    function csvSummaryText() {
        var files = csvSeries()
        if (files.length === 0)
            return "CSV не загружены"
        var total = 0
        for (var i = 0; i < files.length; i++) {
            var count = Number(files[i].count)
            if (!isNaN(count))
                total += count
        }
        return "CSV файлов: " + files.length + ", точек: " + total
    }

    function fmtSigned(value, digits) {
        var numberValue = Number(value)
        if (isNaN(numberValue)) return "-"
        return (numberValue >= 0 ? "+" : "") + numberValue.toFixed(digits)
    }

    function fmt(value, digits) {
        var numberValue = Number(value)
        if (isNaN(numberValue)) return "-"
        return numberValue.toFixed(digits)
    }

    function maxPointCountForCurrentMode() {
        if (!root.popupUseOverlayMode()) {
            var selected = root.selectedNodeEntry()
            return selected ? Number(selected.count) : 0
        }

        var maxCount = 0
        var allSeries = root.popupSeries()
        for (var i = 0; i < allSeries.length; i++) {
            var item = allSeries[i]
            if (!item || !item.points)
                continue
            var count = Number(item.points.length)
            if (count > maxCount)
                maxCount = count
        }
        return maxCount
    }

    function applyRange(startText, endText) {
        var total = maxPointCountForCurrentMode()
        if (total <= 0) { root.rangeStartIndex = 0; root.rangeEndIndex = -1; return }
        var start = parseInt(String(startText).trim())
        if (isNaN(start)) start = 0
        start = Math.max(0, Math.min(total - 1, start))
        var end = -1
        var endRaw = String(endText).trim()
        if (endRaw.length > 0) {
            end = parseInt(endRaw)
            if (isNaN(end)) end = -1
        }
        if (end >= total) end = total - 1
        if (end >= 0 && end < start) { var tmp = start; start = end; end = tmp }
        root.rangeStartIndex = start
        root.rangeEndIndex = end
    }

    function resetRange() {
        root.rangeStartIndex = 0
        root.rangeEndIndex = -1
        popupRangeStartField.text = "0"
        popupRangeEndField.text = ""
    }

    function clampRangeToData() {
        var total = maxPointCountForCurrentMode()
        if (total <= 0) { root.rangeStartIndex = 0; root.rangeEndIndex = -1; return }
        root.rangeStartIndex = Math.max(0, Math.min(total - 1, root.rangeStartIndex))
        if (root.rangeEndIndex >= 0) {
            root.rangeEndIndex = Math.max(0, Math.min(total - 1, root.rangeEndIndex))
            if (root.rangeEndIndex < root.rangeStartIndex) {
                var tmp = root.rangeStartIndex
                root.rangeStartIndex = root.rangeEndIndex
                root.rangeEndIndex = tmp
            }
        }
    }

    function rangeInfoText() {
        var total = maxPointCountForCurrentMode()
        if (total <= 0) return "Диапазон индексов: нет данных"
        var endValue = root.rangeEndIndex >= 0 ? root.rangeEndIndex : (total - 1)
        return "Диапазон индексов точек: " + root.rangeStartIndex + " ... " + endValue + " из " + total
    }

    function networkMetricTiles() {
        var m = networkMetrics()
        return [
            {"title": "Узлов в сети", "value": String(m.nodesCount !== undefined ? m.nodesCount : 0)},
            {"title": "Среднее топливо", "value": fmt(m.fuelMean, 2) + " %"},
            {"title": "Средняя температура", "value": fmt(m.temperatureMean, 2) + " °C"},
            {"title": "Разброс топлива", "value": fmt(m.fuelSpread, 2)},
            {"title": "Разброс температуры", "value": fmt(m.temperatureSpread, 2)}
        ]
    }

    Component.onCompleted: {
        syncNodeEnabled()
        syncSpoilerState()
        syncMetricsSpoilerState()
        clampRangeToData()
        refreshLegendModels()
    }
    onViewModeChanged: {
        clampRangeToData()
        refreshLegendModels()
    }
    onSelectedNodeIndexChanged: {
        clampRangeToData()
        refreshLegendModels()
    }
    onNodeEnabledMapChanged: {
        clampRangeToData()
        refreshLegendModels()
    }
    onIncludeLoadedCsvChanged: {
        clampRangeToData()
        refreshLegendModels()
        popupRangeStartField.text = String(root.rangeStartIndex)
        popupRangeEndField.text = root.rangeEndIndex >= 0 ? String(root.rangeEndIndex) : ""
    }

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
            text: "Графики параметров узлов CAN"
            color: root.textMain
            font.pixelSize: 18
            font.bold: true
            font.family: "Bahnschrift"
        }

        Text {
            Layout.fillWidth: true
            text: "Оси: Y слева - топливо (%), Y справа - температура (°C), X - индекс точки."
            color: root.textSoft
            font.pixelSize: 12
            font.family: "Bahnschrift"
            wrapMode: Text.Wrap
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 10
            color: "#f8fbff"
            border.color: "#d6e2ef"
            border.width: 1
            implicitHeight: previewHeaderLayout.implicitHeight + 14

            ColumnLayout {
                id: previewHeaderLayout
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        Layout.fillWidth: true
                        text: root.rangeInfoText()
                        color: root.textSoft
                        font.pixelSize: 11
                        font.family: "Bahnschrift"
                        wrapMode: Text.Wrap
                    }

                    FancyButton {
                        Layout.preferredWidth: 112
                        Layout.preferredHeight: 34
                        text: "CSV..."
                        tone: "#0f766e"
                        toneHover: "#115e59"
                        tonePressed: "#134e4a"
                        onClicked: csvFileDialog.open()
                    }

                    FancyButton {
                        Layout.preferredWidth: 170
                        Layout.preferredHeight: 34
                        text: "Открыть в окне"
                        tone: "#1d4ed8"
                        toneHover: "#1e40af"
                        tonePressed: "#1e3a8a"
                        onClicked: {
                            trendWindow.visible = true
                            trendWindow.raise()
                            trendWindow.requestActivate()
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Параметры отображения и выбор узлов доступны только в расширенном окне графика. " + root.csvSummaryText()
                    color: root.textSoft
                    font.pixelSize: 11
                    font.family: "Bahnschrift"
                    wrapMode: Text.Wrap
                }
            }
        }

        TrendCanvas {
            Layout.fillWidth: true
            overlayMode: true
            series: root.overlaySeries()
            emptyText: "Нет данных по узлам"
            rangeStart: root.rangeStartIndex
            rangeEnd: root.rangeEndIndex
            showPointLabels: false
            maxRenderPoints: 500
            maxPointLabels: 0
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 9
            color: "#f7fbff"
            border.color: "#d6e2ef"
            border.width: 1
            implicitHeight: legendLayout.implicitHeight + 14

            ColumnLayout {
                id: legendLayout
                anchors.fill: parent
                anchors.margins: 7
                spacing: 6

                Text {
                    text: "Легенда: узлы и параметры"
                    color: root.textSoft
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "Bahnschrift"
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle { width: 20; height: 2; radius: 1; color: "#334155"; opacity: 1.0 }
                        Rectangle { width: 8; height: 8; radius: 4; color: "#334155"; opacity: 1.0 }
                        Text {
                            Layout.fillWidth: true
                            text: "Топливо, %: сплошная линия и точки"
                            color: root.textSoft
                            font.pixelSize: 10
                            font.family: "Bahnschrift"
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle { width: 20; height: 2; radius: 1; color: "#334155"; opacity: 0.45 }
                        Rectangle { width: 8; height: 8; radius: 4; color: "#334155"; opacity: 0.55 }
                        Text {
                            Layout.fillWidth: true
                            text: "Температура, °C: полупрозрачная линия и точки"
                            color: root.textSoft
                            font.pixelSize: 10
                            font.family: "Bahnschrift"
                            elide: Text.ElideRight
                        }
                    }
                }

                Rectangle {
                    id: overlayLegendTable
                    Layout.fillWidth: true
                    radius: 7
                    color: "#f7fbff"
                    border.color: "#d6e2ef"
                    border.width: 1
                    clip: true
                    implicitHeight: overlayLegendTableLayout.implicitHeight + 10

                    readonly property int innerPadding: 8
                    readonly property real columnsWidth: Math.max(0, width - (innerPadding * 2))
                    readonly property real nodeColumn: Math.max(108, Math.round(columnsWidth * 0.34))
                    readonly property real fuelColumn: Math.max(100, Math.round(columnsWidth * 0.31))
                    readonly property real tempColumn: Math.max(82, columnsWidth - nodeColumn - fuelColumn)
                    readonly property real fuelColumnX: innerPadding + nodeColumn
                    readonly property real tempColumnX: innerPadding + nodeColumn + fuelColumn

                    ColumnLayout {
                        id: overlayLegendTableLayout
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 4

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 24
                            radius: 6
                            color: "#ecf4fd"
                            border.color: "#d4e3f1"

                            Text {
                                x: overlayLegendTable.innerPadding
                                y: 0
                                width: overlayLegendTable.nodeColumn
                                height: parent.height
                                text: "Узел"
                                color: root.textSoft
                                font.pixelSize: 10
                                font.bold: true
                                font.family: "Bahnschrift"
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                            Text {
                                x: overlayLegendTable.fuelColumnX
                                y: 0
                                width: overlayLegendTable.fuelColumn
                                height: parent.height
                                text: "Топливо: цвет"
                                color: root.textSoft
                                font.pixelSize: 10
                                font.bold: true
                                font.family: "Bahnschrift"
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                            Text {
                                x: overlayLegendTable.tempColumnX
                                y: 0
                                width: overlayLegendTable.tempColumn
                                height: parent.height
                                text: "Температура: цвет"
                                color: root.textSoft
                                font.pixelSize: 10
                                font.bold: true
                                font.family: "Bahnschrift"
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                        }

                        Repeater {
                            model: root.overlayLegendModel
                            delegate: Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 28
                                radius: 6
                                color: "#f1f6fc"
                                border.color: "#d1deea"
                                clip: true

                                Text {
                                    x: overlayLegendTable.innerPadding
                                    y: 0
                                    width: overlayLegendTable.nodeColumn
                                    height: parent.height
                                    text: modelData.node
                                    color: root.textMain
                                    font.pixelSize: 11
                                    font.family: "Bahnschrift"
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                Item {
                                    x: overlayLegendTable.fuelColumnX
                                    y: 0
                                    width: overlayLegendTable.fuelColumn
                                    height: parent.height

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 6
                                        spacing: 6

                                        Rectangle {
                                            Layout.preferredWidth: 12
                                            Layout.preferredHeight: 12
                                            radius: 3
                                            color: modelData.color
                                            border.color: "#1e293b"
                                            border.width: 1
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: "топливо"
                                            color: root.textMain
                                            font.pixelSize: 10
                                            font.family: "Bahnschrift"
                                            verticalAlignment: Text.AlignVCenter
                                            elide: Text.ElideRight
                                        }
                                    }
                                }

                                Item {
                                    x: overlayLegendTable.tempColumnX
                                    y: 0
                                    width: overlayLegendTable.tempColumn
                                    height: parent.height

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 6
                                        spacing: 6

                                        Rectangle {
                                            Layout.preferredWidth: 12
                                            Layout.preferredHeight: 12
                                            radius: 3
                                            color: modelData.color
                                            opacity: 0.55
                                            border.color: "#1e293b"
                                            border.width: 1
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: "температура"
                                            color: root.textMain
                                            font.pixelSize: 10
                                            font.family: "Bahnschrift"
                                            verticalAlignment: Text.AlignVCenter
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }
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
            implicitHeight: summaryLayout.implicitHeight + 16

            ColumnLayout {
                id: summaryLayout
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Text { text: "Сводный математический анализ"; color: root.textSoft; font.pixelSize: 12; font.bold: true; font.family: "Bahnschrift" }

                SpoilerSection {
                    Layout.fillWidth: true
                    title: "Основные параметры сети"
                    hintText: "Показать или скрыть группу"
                    expanded: true
                    cardColor: "#ffffff"
                    cardBorder: "#d6e2ef"
                    textMain: root.textMain
                    textSoft: root.textSoft

                    Rectangle {
                        Layout.fillWidth: true
                        radius: 8
                        color: "#ffffff"
                        border.color: "#d6e2ef"
                        border.width: 1
                        implicitHeight: networkTableLayout.implicitHeight + 12

                        ColumnLayout {
                            id: networkTableLayout
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 6

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 28
                                radius: 6
                                color: "#eef5fd"
                                border.color: "#d4e3f1"
                                border.width: 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    spacing: 8
                                    Text {
                                        Layout.preferredWidth: parent.width * 0.68
                                        text: "Параметр"
                                        color: root.textSoft
                                        font.pixelSize: 10
                                        font.bold: true
                                        font.family: "Bahnschrift"
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "Значение"
                                        horizontalAlignment: Text.AlignRight
                                        color: root.textSoft
                                        font.pixelSize: 10
                                        font.bold: true
                                        font.family: "Bahnschrift"
                                        elide: Text.ElideRight
                                    }
                                }
                            }

                            Repeater {
                                model: root.networkMetricTiles()
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    radius: 6
                                    color: index % 2 === 0 ? "#f8fbff" : "#f2f8ff"
                                    border.color: "#dce8f4"
                                    border.width: 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        spacing: 8
                                        Text {
                                            Layout.preferredWidth: parent.width * 0.68
                                            text: modelData.title
                                            color: root.textMain
                                            font.pixelSize: 11
                                            font.family: "Bahnschrift"
                                            elide: Text.ElideRight
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.value
                                            horizontalAlignment: Text.AlignRight
                                            color: root.textMain
                                            font.pixelSize: 11
                                            font.bold: true
                                            font.family: "Bahnschrift"
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: root.metricsRows()
                        delegate: SpoilerSection {
                            readonly property int nodeIndex: index
                            Layout.fillWidth: true
                            title: "Узел " + modelData.node
                            hintText: "Показать или скрыть параметры"
                            expanded: root.metricsSpoilerExpanded(String(modelData.node))
                            cardColor: "#ffffff"
                            cardBorder: "#d6e2ef"
                            textMain: root.textMain
                            textSoft: root.textSoft
                            accentColor: root.colorForNode(nodeIndex)
                            onExpandedChanged: root.setMetricsSpoilerExpanded(String(modelData.node), expanded)

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 8
                                color: nodeIndex % 2 === 0 ? "#ffffff" : "#f6fafe"
                                border.color: "#d6e2ef"
                                border.width: 1
                                implicitHeight: nodeMetricsLayout.implicitHeight + 12

                                ColumnLayout {
                                    id: nodeMetricsLayout
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    spacing: 6

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 28
                                        radius: 6
                                        color: "#eef5fd"
                                        border.color: "#d4e3f1"
                                        border.width: 1

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 8
                                            anchors.rightMargin: 8
                                            spacing: 8
                                            Text {
                                                Layout.preferredWidth: parent.width * 0.42
                                                text: "Параметр"
                                                color: root.textSoft
                                                font.pixelSize: 10
                                                font.bold: true
                                                font.family: "Bahnschrift"
                                            }
                                            Text {
                                                Layout.preferredWidth: parent.width * 0.26
                                                text: "Топливо"
                                                horizontalAlignment: Text.AlignRight
                                                color: root.textSoft
                                                font.pixelSize: 10
                                                font.bold: true
                                                font.family: "Bahnschrift"
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: "Температура"
                                                horizontalAlignment: Text.AlignRight
                                                color: root.textSoft
                                                font.pixelSize: 10
                                                font.bold: true
                                                font.family: "Bahnschrift"
                                            }
                                        }
                                    }

                                    Repeater {
                                        model: [
                                            { "label": "Изменение (Δ)", "fuel": modelData.deltaFuel, "temp": modelData.deltaTemperature },
                                            { "label": "Отклонение", "fuel": modelData.devFuel, "temp": modelData.devTemperature },
                                            { "label": "Погрешность", "fuel": modelData.errFuel, "temp": modelData.errTemperature },
                                            { "label": "Расхождение", "fuel": modelData.divFuel, "temp": modelData.divTemperature }
                                        ]

                                        delegate: Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 30
                                            radius: 6
                                            color: index % 2 === 0 ? "#f8fbff" : "#f2f8ff"
                                            border.color: "#dce8f4"
                                            border.width: 1

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 8
                                                anchors.rightMargin: 8
                                                spacing: 8
                                                Text {
                                                    Layout.preferredWidth: parent.width * 0.42
                                                    text: modelData.label
                                                    color: root.textMain
                                                    font.pixelSize: 11
                                                    font.family: "Bahnschrift"
                                                    elide: Text.ElideRight
                                                }
                                                Text {
                                                    Layout.preferredWidth: parent.width * 0.26
                                                    text: modelData.fuel
                                                    horizontalAlignment: Text.AlignRight
                                                    color: root.textMain
                                                    font.pixelSize: 11
                                                    font.family: "Bahnschrift"
                                                    elide: Text.ElideRight
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: modelData.temp
                                                    horizontalAlignment: Text.AlignRight
                                                    color: root.textMain
                                                    font.pixelSize: 11
                                                    font.family: "Bahnschrift"
                                                    elide: Text.ElideRight
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Window {
        id: trendWindow
        width: 1180
        height: 760
        minimumWidth: 920
        minimumHeight: 560
        modality: Qt.NonModal
        visible: false
        title: "Графики узлов CAN (расширенный режим)"
        transientParent: root.Window.window

        Rectangle { anchors.fill: parent; color: "#eef5fc" }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                Text { text: "Расширенный просмотр"; color: root.textMain; font.pixelSize: 16; font.bold: true; font.family: "Bahnschrift" }
                Item { Layout.fillWidth: true }
                FancyButton { Layout.preferredWidth: 110; Layout.preferredHeight: 34; text: "Закрыть"; onClicked: trendWindow.visible = false }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: "#ffffff"
                border.color: "#d6e2ef"
                border.width: 1
                implicitHeight: modePanelLayout.implicitHeight + 12

                ColumnLayout {
                    id: modePanelLayout
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            Layout.preferredWidth: 170
                            text: "Режим отображения"
                            color: root.textSoft
                            font.pixelSize: 11
                            font.bold: true
                            font.family: "Bahnschrift"
                            verticalAlignment: Text.AlignVCenter
                        }

                        FancyComboBox {
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 34
                            model: ["Выбранный узел", "Все узлы по отдельности", "Все узлы на одном графике"]
                            currentIndex: root.viewMode
                            onCurrentIndexChanged: root.viewMode = currentIndex
                        }

                        FancyComboBox {
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 34
                            enabled: root.viewMode === 0
                            model: root.nodeLabelList()
                            currentIndex: root.selectedNodeIndex
                            onCurrentIndexChanged: root.selectedNodeIndex = currentIndex
                        }

                        FancyButton {
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 34
                            text: root.showPointLabels ? "Подписи точек: ВКЛ" : "Подписи точек: ВЫКЛ"
                            onClicked: root.showPointLabels = !root.showPointLabels
                        }

                        Item { Layout.fillWidth: true }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            Layout.preferredWidth: 170
                            text: "CSV для анализа"
                            color: root.textSoft
                            font.pixelSize: 11
                            font.bold: true
                            font.family: "Bahnschrift"
                            verticalAlignment: Text.AlignVCenter
                        }

                        FancyButton {
                            Layout.preferredWidth: 150
                            Layout.preferredHeight: 34
                            text: "Загрузить CSV"
                            tone: "#0f766e"
                            toneHover: "#115e59"
                            tonePressed: "#134e4a"
                            onClicked: csvFileDialog.open()
                        }

                        FancyButton {
                            Layout.preferredWidth: 150
                            Layout.preferredHeight: 34
                            text: "Очистить CSV"
                            enabled: root.csvSeries().length > 0
                            tone: "#64748b"
                            toneHover: "#55657a"
                            tonePressed: "#475569"
                            onClicked: if (root.appController) root.appController.clearCollectorTrendCsv()
                        }

                        FancyButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 34
                            text: root.includeLoadedCsv ? "CSV на графике: ВКЛ" : "CSV на графике: ВЫКЛ"
                            onClicked: root.includeLoadedCsv = !root.includeLoadedCsv
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.csvSummaryText()
                            color: root.textSoft
                            font.pixelSize: 11
                            font.family: "Bahnschrift"
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: "#ffffff"
                border.color: "#d6e2ef"
                border.width: 1
                implicitHeight: rangePanelLayout.implicitHeight + 12

                ColumnLayout {
                    id: rangePanelLayout
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            Layout.preferredWidth: 170
                            text: "Диапазон точек"
                            color: root.textSoft
                            font.pixelSize: 11
                            font.bold: true
                            font.family: "Bahnschrift"
                            verticalAlignment: Text.AlignVCenter
                        }

                        FancyTextField {
                            id: popupRangeStartField
                            Layout.preferredWidth: 160
                            Layout.preferredHeight: 34
                            placeholderText: "От, индекс"
                            text: String(root.rangeStartIndex)
                            validator: IntValidator { bottom: 0; top: 9999999 }
                            onAccepted: root.applyRange(text, popupRangeEndField.text)
                        }

                        FancyTextField {
                            id: popupRangeEndField
                            Layout.preferredWidth: 160
                            Layout.preferredHeight: 34
                            placeholderText: "До, индекс"
                            text: root.rangeEndIndex >= 0 ? String(root.rangeEndIndex) : ""
                            validator: IntValidator { bottom: 0; top: 9999999 }
                            onAccepted: root.applyRange(popupRangeStartField.text, text)
                        }

                        FancyButton {
                            Layout.preferredWidth: 160
                            Layout.preferredHeight: 34
                            text: "Применить"
                            onClicked: root.applyRange(popupRangeStartField.text, popupRangeEndField.text)
                        }

                        FancyButton {
                            Layout.preferredWidth: 160
                            Layout.preferredHeight: 34
                            text: "Весь период"
                            onClicked: root.resetRange()
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: "#ffffff"
                border.color: "#d6e2ef"
                border.width: 1
                implicitHeight: 54

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8

                    Text {
                        Layout.preferredWidth: 170
                        text: "Видимость узлов"
                        color: root.textSoft
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Bahnschrift"
                        verticalAlignment: Text.AlignVCenter
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        clip: true
                        interactive: true
                        contentWidth: popupNodesRow.implicitWidth
                        contentHeight: 34

                        Row {
                            id: popupNodesRow
                            y: 0
                            spacing: 6

                            Repeater {
                                model: root.trendNodes()
                                delegate: FancyButton {
                                    readonly property string nodeLabel: String(modelData.node)
                                    width: 100
                                    height: 34
                                    text: nodeLabel
                                    fontPixelSize: 12
                                    tone: root.isNodeVisible(nodeLabel) ? "#1d4ed8" : "#94a3b8"
                                    toneHover: root.isNodeVisible(nodeLabel) ? "#1e40af" : "#7f8fa6"
                                    tonePressed: root.isNodeVisible(nodeLabel) ? "#1e3a8a" : "#6b7d95"
                                    onClicked: root.toggleNodeVisible(nodeLabel)
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 8
                color: "#ffffff"
                border.color: "#d6e2ef"
                border.width: 1
                implicitHeight: popupLegendLayout.implicitHeight + 12

                ColumnLayout {
                    id: popupLegendLayout
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 6

                    Text {
                        text: "Легенда (узлы и параметры)"
                        color: root.textSoft
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Bahnschrift"
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Rectangle { width: 20; height: 2; radius: 1; color: "#334155"; opacity: 1.0 }
                            Rectangle { width: 8; height: 8; radius: 4; color: "#334155"; opacity: 1.0 }
                            Text {
                                Layout.fillWidth: true
                                text: "Топливо, %"
                                color: root.textSoft
                                font.pixelSize: 10
                                font.family: "Bahnschrift"
                                elide: Text.ElideRight
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Rectangle { width: 20; height: 2; radius: 1; color: "#334155"; opacity: 0.45 }
                            Rectangle { width: 8; height: 8; radius: 4; color: "#334155"; opacity: 0.55 }
                            Text {
                                Layout.fillWidth: true
                                text: "Температура, °C"
                                color: root.textSoft
                                font.pixelSize: 10
                                font.family: "Bahnschrift"
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Rectangle {
                        id: popupLegendTable
                        Layout.fillWidth: true
                        radius: 7
                        color: "#f7fbff"
                        border.color: "#d6e2ef"
                        border.width: 1
                        clip: true
                        implicitHeight: popupLegendTableLayout.implicitHeight + 10

                        readonly property int innerPadding: 8
                        readonly property real columnsWidth: Math.max(0, width - (innerPadding * 2))
                        readonly property real nodeColumn: Math.max(108, Math.round(columnsWidth * 0.34))
                        readonly property real fuelColumn: Math.max(100, Math.round(columnsWidth * 0.31))
                        readonly property real tempColumn: Math.max(82, columnsWidth - nodeColumn - fuelColumn)
                        readonly property real fuelColumnX: innerPadding + nodeColumn
                        readonly property real tempColumnX: innerPadding + nodeColumn + fuelColumn

                        ColumnLayout {
                            id: popupLegendTableLayout
                            anchors.fill: parent
                            anchors.margins: 5
                            spacing: 4

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 24
                                radius: 6
                                color: "#ecf4fd"
                                border.color: "#d4e3f1"

                                Text {
                                    x: popupLegendTable.innerPadding
                                    y: 0
                                    width: popupLegendTable.nodeColumn
                                    height: parent.height
                                    text: "Узел"
                                    color: root.textSoft
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.family: "Bahnschrift"
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }
                                Text {
                                    x: popupLegendTable.fuelColumnX
                                    y: 0
                                    width: popupLegendTable.fuelColumn
                                    height: parent.height
                                    text: "Топливо: цвет"
                                    color: root.textSoft
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.family: "Bahnschrift"
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }
                                Text {
                                    x: popupLegendTable.tempColumnX
                                    y: 0
                                    width: popupLegendTable.tempColumn
                                    height: parent.height
                                    text: "Температура: цвет"
                                    color: root.textSoft
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.family: "Bahnschrift"
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }
                            }

                            Repeater {
                                model: root.popupLegendModel
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 28
                                    radius: 6
                                    color: "#f3f8ff"
                                    border.color: "#d4e3f1"
                                    clip: true

                                    Text {
                                        x: popupLegendTable.innerPadding
                                        y: 0
                                        width: popupLegendTable.nodeColumn
                                        height: parent.height
                                        text: modelData.node
                                        color: root.textMain
                                        font.pixelSize: 11
                                        font.family: "Bahnschrift"
                                        verticalAlignment: Text.AlignVCenter
                                        elide: Text.ElideRight
                                    }

                                    Item {
                                        x: popupLegendTable.fuelColumnX
                                        y: 0
                                        width: popupLegendTable.fuelColumn
                                        height: parent.height

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 6
                                            anchors.rightMargin: 6
                                            spacing: 6

                                            Rectangle {
                                                Layout.preferredWidth: 12
                                                Layout.preferredHeight: 12
                                                radius: 3
                                                color: modelData.color
                                                border.color: "#1e293b"
                                                border.width: 1
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: "топливо"
                                                color: root.textMain
                                                font.pixelSize: 10
                                                font.family: "Bahnschrift"
                                                verticalAlignment: Text.AlignVCenter
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }

                                    Item {
                                        x: popupLegendTable.tempColumnX
                                        y: 0
                                        width: popupLegendTable.tempColumn
                                        height: parent.height

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 6
                                            anchors.rightMargin: 6
                                            spacing: 6

                                            Rectangle {
                                                Layout.preferredWidth: 12
                                                Layout.preferredHeight: 12
                                                radius: 3
                                                color: modelData.color
                                                opacity: 0.55
                                                border.color: "#1e293b"
                                                border.width: 1
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: "температура"
                                                color: root.textMain
                                                font.pixelSize: 10
                                                font.family: "Bahnschrift"
                                                verticalAlignment: Text.AlignVCenter
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            TrendCanvas {
                Layout.fillWidth: true
                Layout.fillHeight: true
                points: {
                    var selected = root.selectedNodeEntry()
                    if (!root.popupUseOverlayMode() && selected && selected.points)
                        return selected.points
                    return []
                }
                overlayMode: root.popupUseOverlayMode()
                series: root.popupSeries()
                emptyText: root.viewMode === 0 ? "Нет данных для выбранного узла" : "Нет выбранных узлов для графика"
                rangeStart: root.rangeStartIndex
                rangeEnd: root.rangeEndIndex
                showPointLabels: root.showPointLabels
            }
        }
    }

    FileDialog {
        id: csvFileDialog
        title: "Выберите CSV файлы для анализа"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["CSV файлы (*.csv)", "Все файлы (*)"]
        onAccepted: {
            if (!root.appController)
                return
            var files = selectedFiles
            if (!files || files.length === 0) {
                if (selectedFile)
                    files = [selectedFile]
                else
                    files = []
            }
            root.appController.loadCollectorTrendCsv(files)
        }
    }

    Connections {
        target: root.appController
        function onCollectorTrendChanged() {
            root.syncNodeEnabled()
            root.syncSpoilerState()
            root.syncMetricsSpoilerState()
            root.clampRangeToData()
            root.refreshLegendModels()
            popupRangeStartField.text = String(root.rangeStartIndex)
            popupRangeEndField.text = root.rangeEndIndex >= 0 ? String(root.rangeEndIndex) : ""
        }
    }
}
