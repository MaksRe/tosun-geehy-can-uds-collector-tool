import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root

    property bool overlayMode: false
    property var points: []
    property var series: []
    property string emptyText: "Нет данных для построения графика"
    property color panelBg: "#f7fbff"
    property color panelBorder: "#d6e2ef"
    property color fuelColor: "#10b981"
    property color temperatureColor: "#f97316"
    property real zoomX: 1.0
    property int rangeStart: 0
    property int rangeEnd: -1
    property bool showPointLabels: false
    property bool wheelZoomEnabled: true
    property int maxRenderPoints: 700
    property int maxPointLabels: 60
    property int panOffset: 0

    radius: 12
    color: root.panelBg
    border.color: root.panelBorder
    border.width: 1
    implicitHeight: 300

    function requestRepaint() {
        canvas.requestPaint()
    }

    function normalizeRange(totalCount) {
        if (totalCount <= 0)
            return { "start": 0, "end": -1 }

        var start = Number(root.rangeStart)
        if (isNaN(start))
            start = 0
        start = Math.floor(start)
        if (start < 0)
            start = 0
        if (start > totalCount - 1)
            start = totalCount - 1

        var end = Number(root.rangeEnd)
        if (root.rangeEnd < 0 || isNaN(end))
            end = totalCount - 1
        end = Math.floor(end)
        if (end < 0)
            end = 0
        if (end > totalCount - 1)
            end = totalCount - 1

        if (end < start) {
            var tmp = start
            start = end
            end = tmp
        }

        return { "start": start, "end": end }
    }

    function totalPointCount() {
        if (root.overlayMode) {
            var maxCount = 0
            if (!root.series)
                return 0
            for (var i = 0; i < root.series.length; i++) {
                var item = root.series[i]
                if (!item || !item.points)
                    continue
                var count = Number(item.points.length)
                if (count > maxCount)
                    maxCount = count
            }
            return maxCount
        }
        return root.points ? Number(root.points.length) : 0
    }

    function viewportMetrics(totalCount) {
        var normalized = normalizeRange(totalCount)
        if (normalized.end < normalized.start)
            return {
                "start": 0,
                "end": -1,
                "visibleCount": 0,
                "minOffset": 0,
                "maxOffset": 0
            }

        var baseCount = normalized.end - normalized.start + 1
        var zoom = Math.max(1.0, Number(root.zoomX))
        var visibleCount = Math.max(2, Math.floor(baseCount / zoom))
        if (visibleCount > baseCount)
            visibleCount = baseCount

        var maxStart = normalized.end - visibleCount + 1
        if (maxStart < normalized.start)
            maxStart = normalized.start

        var shiftRange = Math.max(0, maxStart - normalized.start)
        return {
            "start": normalized.start,
            "end": normalized.end,
            "visibleCount": visibleCount,
            "minOffset": -shiftRange,
            "maxOffset": 0
        }
    }

    function clampPanOffset() {
        var metrics = viewportMetrics(totalPointCount())
        var candidate = Math.round(Number(root.panOffset))
        if (isNaN(candidate))
            candidate = 0
        if (candidate < metrics.minOffset)
            candidate = metrics.minOffset
        if (candidate > metrics.maxOffset)
            candidate = metrics.maxOffset
        if (candidate !== root.panOffset)
            root.panOffset = candidate
    }

    function buildViewport(sourcePoints) {
        if (!sourcePoints || sourcePoints.length === 0)
            return []

        var total = sourcePoints.length
        var metrics = viewportMetrics(total)
        if (metrics.end < metrics.start || metrics.visibleCount <= 0)
            return []

        var maxStart = metrics.end - metrics.visibleCount + 1
        if (maxStart < metrics.start)
            maxStart = metrics.start

        var viewStart = maxStart + Math.round(Number(root.panOffset))
        if (viewStart < metrics.start)
            viewStart = metrics.start
        if (viewStart > maxStart)
            viewStart = maxStart
        var viewEnd = viewStart + metrics.visibleCount - 1
        if (viewEnd > metrics.end)
            viewEnd = metrics.end

        var result = []
        for (var i = viewStart; i <= viewEnd; i++) {
            var p = sourcePoints[i]
            result.push({
                "_idx": i,
                "fuel": Number(p.fuel),
                "temperature": Number(p.temperature),
                "time": p.time
            })
        }
        return decimatePoints(result, root.maxRenderPoints)
    }

    function buildOverlayViewport(sourceSeries) {
        var result = []
        if (!sourceSeries)
            return result
        for (var i = 0; i < sourceSeries.length; i++) {
            var item = sourceSeries[i]
            var vp = buildViewport(item.points)
            if (vp.length <= 0)
                continue
            result.push({
                "node": item.node,
                "color": item.color,
                "points": vp
            })
        }
        return result
    }

    function decimatePoints(sourcePoints, maxCount) {
        if (!sourcePoints || sourcePoints.length <= 0)
            return []

        var total = sourcePoints.length
        var target = Math.max(2, Math.floor(Number(maxCount)))
        if (total <= target)
            return sourcePoints

        var step = (total - 1) / (target - 1)
        var result = []
        var prevIdx = -1
        for (var i = 0; i < target; i++) {
            var idx = Math.round(i * step)
            if (idx < 0)
                idx = 0
            if (idx >= total)
                idx = total - 1
            if (idx === prevIdx)
                continue
            result.push(sourcePoints[idx])
            prevIdx = idx
        }
        return result
    }

    onPointsChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onSeriesChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onOverlayModeChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onZoomXChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onRangeStartChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onRangeEndChanged: {
        clampPanOffset()
        canvas.requestPaint()
    }
    onPanOffsetChanged: canvas.requestPaint()
    onShowPointLabelsChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        anchors.topMargin: 34
        anchors.bottomMargin: 30
        antialiasing: true
        z: 1

        Component.onCompleted: {
            root.clampPanOffset()
            requestPaint()
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        function drawGrid(ctx, l, t, pw, ph) {
            ctx.fillStyle = "#ffffff"
            ctx.fillRect(0, 0, width, height)

            ctx.strokeStyle = "#dbe7f3"
            ctx.lineWidth = 1
            for (var gy = 0; gy <= 4; gy++) {
                var yy = t + (ph / 4) * gy
                ctx.beginPath()
                ctx.moveTo(l, yy)
                ctx.lineTo(l + pw, yy)
                ctx.stroke()
            }

            ctx.strokeStyle = "#b9ccdf"
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(l, t)
            ctx.lineTo(l, t + ph)
            ctx.lineTo(l + pw, t + ph)
            ctx.lineTo(l + pw, t)
            ctx.stroke()
        }

        function drawLabel(ctx, x, y, text, color) {
            ctx.save()
            ctx.font = "10px Bahnschrift"
            var textWidth = ctx.measureText(text).width
            var rectW = Math.ceil(textWidth + 8)
            var rectH = 14
            var px = Math.round(x - rectW / 2)
            var py = Math.round(y - rectH)

            if (px < 2)
                px = 2
            if (px + rectW > width - 2)
                px = width - rectW - 2
            if (py < 2)
                py = 2
            if (py + rectH > height - 2)
                py = height - rectH - 2

            ctx.fillStyle = "rgba(255,255,255,0.92)"
            ctx.strokeStyle = color
            ctx.lineWidth = 1
            ctx.fillRect(px, py, rectW, rectH)
            ctx.strokeRect(px, py, rectW, rectH)
            ctx.fillStyle = "#1f2d3d"
            ctx.fillText(text, px + 4, py + 10)
            ctx.restore()
        }

        function normalizeTempRange(minVal, maxVal) {
            var minV = Number(minVal)
            var maxV = Number(maxVal)
            if (isNaN(minV) || isNaN(maxV)) {
                minV = 0
                maxV = 100
            }
            if (Math.abs(maxV - minV) < 0.5) {
                minV -= 0.5
                maxV += 0.5
            }
            return { "min": minV, "max": maxV }
        }

        function calcTempRangeFromPoints(seriesPoints) {
            if (!seriesPoints || seriesPoints.length <= 0)
                return normalizeTempRange(0, 100)
            var minV = Number(seriesPoints[0].temperature)
            var maxV = Number(seriesPoints[0].temperature)
            for (var i = 1; i < seriesPoints.length; i++) {
                var tv = Number(seriesPoints[i].temperature)
                if (tv < minV)
                    minV = tv
                if (tv > maxV)
                    maxV = tv
            }
            return normalizeTempRange(minV, maxV)
        }

        function calcTempRangeFromOverlay(allSeries) {
            if (!allSeries || allSeries.length <= 0)
                return normalizeTempRange(0, 100)

            var found = false
            var minV = 0
            var maxV = 0
            for (var si = 0; si < allSeries.length; si++) {
                var pts = allSeries[si].points
                if (!pts || pts.length <= 0)
                    continue
                for (var pi = 0; pi < pts.length; pi++) {
                    var tv = Number(pts[pi].temperature)
                    if (!found) {
                        minV = tv
                        maxV = tv
                        found = true
                    } else {
                        if (tv < minV)
                            minV = tv
                        if (tv > maxV)
                            maxV = tv
                    }
                }
            }

            if (!found)
                return normalizeTempRange(0, 100)
            return normalizeTempRange(minV, maxV)
        }

        function drawYAxisScales(ctx, l, t, pw, ph, tempMin, tempMax) {
            ctx.save()
            ctx.font = "10px Bahnschrift"
            ctx.fillStyle = "#51667d"
            ctx.strokeStyle = "#b6cbe0"
            ctx.lineWidth = 1
            ctx.textBaseline = "middle"

            for (var i = 0; i <= 4; i++) {
                var y = t + (ph / 4) * i
                var fuelValue = 100 - (100 / 4) * i
                var tempValue = tempMax - ((tempMax - tempMin) / 4) * i

                ctx.beginPath()
                ctx.moveTo(l - 4, y)
                ctx.lineTo(l, y)
                ctx.stroke()

                ctx.textAlign = "right"
                ctx.fillText(fuelValue.toFixed(0), l - 6, y)

                ctx.beginPath()
                ctx.moveTo(l + pw, y)
                ctx.lineTo(l + pw + 4, y)
                ctx.stroke()

                ctx.textAlign = "left"
                ctx.fillText(tempValue.toFixed(1), l + pw + 6, y)
            }

            ctx.restore()
        }

        function compactTimeLabel(rawValue) {
            var text = String(rawValue === undefined ? "" : rawValue).trim()
            if (text.length === 0)
                return "-"

            var candidate = text
            var spacePos = candidate.lastIndexOf(" ")
            if (spacePos >= 0 && spacePos < candidate.length - 1)
                candidate = candidate.slice(spacePos + 1)

            var tPos = candidate.lastIndexOf("T")
            if (tPos >= 0 && tPos < candidate.length - 1)
                candidate = candidate.slice(tPos + 1)

            if (candidate.indexOf("_") >= 0) {
                var underscoreParts = candidate.split("_")
                candidate = underscoreParts[underscoreParts.length - 1]
            }

            var dotPos = candidate.indexOf(".")
            if (dotPos > 0)
                candidate = candidate.slice(0, dotPos)

            if (candidate.indexOf("-") >= 0 && candidate.indexOf(":") < 0) {
                var dashParts = candidate.split("-")
                if (dashParts.length >= 3)
                    candidate = dashParts[0] + ":" + dashParts[1] + ":" + dashParts[2]
            }

            if (candidate.indexOf(":") >= 0 && candidate.length > 8)
                candidate = candidate.slice(candidate.length - 8)

            candidate = candidate.trim()
            return candidate.length > 0 ? candidate : text
        }

        function drawXAxisTimeTicks(ctx, l, t, pw, ph, seriesPoints) {
            if (!seriesPoints || seriesPoints.length <= 0)
                return

            var count = seriesPoints.length
            var labelWidth = 62
            var labelHeight = 14
            var labelGap = 8
            var maxByWidth = Math.max(2, Math.floor(pw / (labelWidth + labelGap)))
            var tickCount = Math.min(count, Math.min(6, maxByWidth))
            if (count === 1)
                tickCount = 1
            if (tickCount < 1)
                return

            ctx.save()
            ctx.font = "9px Bahnschrift"
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            ctx.fillStyle = "#4f6379"
            ctx.strokeStyle = "#b6cbe0"
            ctx.lineWidth = 1

            var lastRight = -100000
            for (var i = 0; i < tickCount; i++) {
                var idx = 0
                if (tickCount > 1)
                    idx = Math.round((i * (count - 1)) / (tickCount - 1))
                if (idx < 0)
                    idx = 0
                if (idx >= count)
                    idx = count - 1

                var x = count <= 1 ? (l + pw / 2) : (l + (pw * idx) / (count - 1))
                var px = Math.round(x - labelWidth / 2)
                var minPx = Math.round(l)
                var maxPx = Math.round(l + pw - labelWidth)
                if (px < minPx)
                    px = minPx
                if (px > maxPx)
                    px = maxPx

                if (px <= lastRight + 2)
                    continue

                var py = Math.round(t + ph + 6)

                ctx.beginPath()
                ctx.moveTo(x, t + ph)
                ctx.lineTo(x, t + ph + 4)
                ctx.stroke()

                ctx.fillStyle = "rgba(255,255,255,0.92)"
                ctx.strokeStyle = "#d4e3f1"
                ctx.fillRect(px, py, labelWidth, labelHeight)
                ctx.strokeRect(px, py, labelWidth, labelHeight)

                ctx.fillStyle = "#4f6379"
                var labelText = compactTimeLabel(seriesPoints[idx].time)
                ctx.fillText(labelText, px + labelWidth / 2, py + labelHeight / 2 + 0.5)

                lastRight = px + labelWidth
            }

            ctx.restore()
        }

        function drawSingle(ctx, l, t, pw, ph, seriesPoints, tempMin, tempMax) {
            var n = seriesPoints.length
            if (n <= 0)
                return

            function xAt(index) {
                if (n <= 1)
                    return l
                return l + (pw * index) / (n - 1)
            }

            function yFuel(v) {
                var clamped = Math.max(0, Math.min(100, Number(v)))
                return t + (1.0 - clamped / 100.0) * ph
            }

            function yTemp(v) {
                var ratio = (Number(v) - tempMin) / (tempMax - tempMin)
                ratio = Math.max(0, Math.min(1, ratio))
                return t + (1.0 - ratio) * ph
            }

            ctx.globalAlpha = 1.0
            ctx.strokeStyle = root.fuelColor
            ctx.lineWidth = 2
            ctx.beginPath()
            for (var fi = 0; fi < n; fi++) {
                var fx = xAt(fi)
                var fy = yFuel(seriesPoints[fi].fuel)
                if (fi === 0)
                    ctx.moveTo(fx, fy)
                else
                    ctx.lineTo(fx, fy)
            }
            ctx.stroke()

            ctx.strokeStyle = root.temperatureColor
            ctx.lineWidth = 2
            ctx.beginPath()
            for (var ti = 0; ti < n; ti++) {
                var tx = xAt(ti)
                var ty = yTemp(seriesPoints[ti].temperature)
                if (ti === 0)
                    ctx.moveTo(tx, ty)
                else
                    ctx.lineTo(tx, ty)
            }
            ctx.stroke()

            for (var pi = 0; pi < n; pi++) {
                var px = xAt(pi)
                var pyFuel = yFuel(seriesPoints[pi].fuel)
                var pyTemp = yTemp(seriesPoints[pi].temperature)

                ctx.fillStyle = root.fuelColor
                ctx.beginPath()
                ctx.arc(px, pyFuel, 3.0, 0, Math.PI * 2)
                ctx.fill()
                ctx.fillStyle = root.temperatureColor
                ctx.beginPath()
                ctx.arc(px, pyTemp, 3.0, 0, Math.PI * 2)
                ctx.fill()
            }

            if (root.showPointLabels) {
                var maxLabels = Math.max(1, Number(root.maxPointLabels))
                var labelStep = Math.max(1, Math.ceil(n / maxLabels))
                for (var li = 0; li < n; li += labelStep) {
                    var lx = xAt(li)
                    var fy = yFuel(seriesPoints[li].fuel)
                    var ty = yTemp(seriesPoints[li].temperature)
                    var fuelLabel = Number(seriesPoints[li].fuel).toFixed(1)
                    var tempLabel = Number(seriesPoints[li].temperature).toFixed(1)
                    drawLabel(ctx, lx, fy - 6 - (li % 2) * 10, fuelLabel, root.fuelColor)
                    drawLabel(ctx, lx, ty + 16 + (li % 2) * 10, tempLabel, root.temperatureColor)
                }
            }
        }

        function drawOverlay(ctx, l, t, pw, ph, allSeries, tempMin, tempMax) {
            var validSeries = []
            for (var i = 0; i < allSeries.length; i++) {
                var s = allSeries[i]
                if (s && s.points && s.points.length > 0)
                    validSeries.push(s)
            }
            if (validSeries.length === 0)
                return

            function xAt(index, totalCount) {
                if (totalCount <= 1)
                    return l
                return l + (pw * index) / (totalCount - 1)
            }

            function yFuel(v) {
                var clamped = Math.max(0, Math.min(100, Number(v)))
                return t + (1.0 - clamped / 100.0) * ph
            }

            function yTemp(v) {
                var ratio = (Number(v) - tempMin) / (tempMax - tempMin)
                ratio = Math.max(0, Math.min(1, ratio))
                return t + (1.0 - ratio) * ph
            }

            for (var sidx = 0; sidx < validSeries.length; sidx++) {
                var seriesItem = validSeries[sidx]
                var dataPoints = seriesItem.points
                var color = seriesItem.color ? seriesItem.color : "#2563eb"
                var count = dataPoints.length

                ctx.globalAlpha = 1.0
                ctx.strokeStyle = color
                ctx.lineWidth = 2
                ctx.beginPath()
                for (var fi = 0; fi < count; fi++) {
                    var fx = xAt(fi, count)
                    var fy = yFuel(dataPoints[fi].fuel)
                    if (fi === 0)
                        ctx.moveTo(fx, fy)
                    else
                        ctx.lineTo(fx, fy)
                }
                ctx.stroke()

                ctx.globalAlpha = 0.45
                ctx.strokeStyle = color
                ctx.lineWidth = 1.6
                ctx.beginPath()
                for (var ti = 0; ti < count; ti++) {
                    var tx = xAt(ti, count)
                    var ty = yTemp(dataPoints[ti].temperature)
                    if (ti === 0)
                        ctx.moveTo(tx, ty)
                    else
                        ctx.lineTo(tx, ty)
                }
                ctx.stroke()

                for (var pii = 0; pii < count; pii++) {
                    var pxx = xAt(pii, count)
                    var pyyFuel = yFuel(dataPoints[pii].fuel)
                    var pyyTemp = yTemp(dataPoints[pii].temperature)

                    ctx.globalAlpha = 1.0
                    ctx.fillStyle = color
                    ctx.beginPath()
                    ctx.arc(pxx, pyyFuel, 2.6, 0, Math.PI * 2)
                    ctx.fill()
                    ctx.globalAlpha = 0.55
                    ctx.beginPath()
                    ctx.arc(pxx, pyyTemp, 2.6, 0, Math.PI * 2)
                    ctx.fill()
                }

                if (root.showPointLabels) {
                    var maxLabels = Math.max(1, Number(root.maxPointLabels))
                    var labelStep = Math.max(1, Math.ceil(count / maxLabels))
                    for (var li = 0; li < count; li += labelStep) {
                        var lxx = xAt(li, count)
                        var fy = yFuel(dataPoints[li].fuel)
                        var ty = yTemp(dataPoints[li].temperature)
                        var fuelLabel = Number(dataPoints[li].fuel).toFixed(1)
                        var tempLabel = Number(dataPoints[li].temperature).toFixed(1)
                        drawLabel(ctx, lxx, fy - 6 - ((sidx + li) % 2) * 10, fuelLabel, color)
                        drawLabel(ctx, lxx, ty + 16 + ((sidx + li) % 2) * 10, tempLabel, color)
                    }
                }
                ctx.globalAlpha = 1.0
            }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()

            var w = width
            var h = height
            if (w < 24 || h < 24)
                return

            var l = 44
            var r = 52
            var t = 8
            var b = 28
            var pw = w - l - r
            var ph = h - t - b
            if (pw <= 2 || ph <= 2)
                return

            drawGrid(ctx, l, t, pw, ph)

            var hasData = false
            var xAxisPoints = []
            var tempRange = normalizeTempRange(0, 100)
            if (root.overlayMode) {
                var overlayViewport = root.buildOverlayViewport(root.series)
                hasData = overlayViewport.length > 0
                if (hasData) {
                    tempRange = calcTempRangeFromOverlay(overlayViewport)
                    drawOverlay(ctx, l, t, pw, ph, overlayViewport, tempRange.min, tempRange.max)
                    var bestCount = 0
                    for (var osi = 0; osi < overlayViewport.length; osi++) {
                        var op = overlayViewport[osi].points
                        if (op && op.length > bestCount) {
                            bestCount = op.length
                            xAxisPoints = op
                        }
                    }
                }
            } else {
                var singleViewport = root.buildViewport(root.points)
                hasData = singleViewport.length > 0
                if (hasData) {
                    tempRange = calcTempRangeFromPoints(singleViewport)
                    drawSingle(ctx, l, t, pw, ph, singleViewport, tempRange.min, tempRange.max)
                    xAxisPoints = singleViewport
                }
            }

            if (!hasData) {
                ctx.fillStyle = "#8aa0b6"
                ctx.font = "12px Bahnschrift"
                ctx.fillText(root.emptyText, l + 10, t + ph / 2)
            } else {
                drawYAxisScales(ctx, l, t, pw, ph, tempRange.min, tempRange.max)
                drawXAxisTimeTicks(ctx, l, t, pw, ph, xAxisPoints)
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        z: 5
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        property bool dragging: false
        property real dragStartX: 0
        property int dragStartPanOffset: 0
        cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor

        onPressed: function(mouse) {
            if (mouse.button !== Qt.LeftButton)
                return
            dragging = true
            dragStartX = mouse.x
            dragStartPanOffset = root.panOffset
            mouse.accepted = true
        }

        onReleased: function(mouse) {
            if (mouse.button !== Qt.LeftButton)
                return
            dragging = false
            mouse.accepted = true
        }

        onCanceled: {
            dragging = false
        }

        onPositionChanged: function(mouse) {
            if (!dragging)
                return

            var total = root.totalPointCount()
            var metrics = root.viewportMetrics(total)
            if (metrics.visibleCount <= 0 || metrics.minOffset === metrics.maxOffset) {
                root.panOffset = 0
                return
            }

            var plotWidth = Math.max(80, canvas.width - 96)
            var deltaPoints = Math.round(((mouse.x - dragStartX) / plotWidth) * metrics.visibleCount)
            var candidate = dragStartPanOffset - deltaPoints
            if (candidate < metrics.minOffset)
                candidate = metrics.minOffset
            if (candidate > metrics.maxOffset)
                candidate = metrics.maxOffset
            if (candidate !== root.panOffset)
                root.panOffset = candidate
            mouse.accepted = true
        }

        onWheel: function(wheel) {
            if (!root.wheelZoomEnabled)
                return
            var delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
            if (delta === 0)
                return
            var factor = delta > 0 ? 1.12 : (1.0 / 1.12)
            root.zoomX = Math.max(1.0, Math.min(24.0, root.zoomX * factor))
            root.clampPanOffset()
            wheel.accepted = true
        }
    }

    Text {
        text: "Y слева: топливо, %"
        color: "#4f6379"
        font.pixelSize: 11
        font.family: "Bahnschrift"
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.top: parent.top
        anchors.topMargin: 8
        z: 3
    }

    Text {
        text: "Y справа: температура, °C"
        color: "#4f6379"
        font.pixelSize: 11
        font.family: "Bahnschrift"
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.top: parent.top
        anchors.topMargin: 8
        z: 3
    }

    Text {
        text: "Масштаб ×" + Number(root.zoomX).toFixed(2)
        color: "#1f2d3d"
        font.pixelSize: 11
        font.bold: true
        font.family: "Bahnschrift"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 8
        z: 3
    }

    Text {
        text: "X: время измерения | Колесо: масштаб | ЛКМ + перетаскивание: панорамирование"
        color: "#607084"
        font.pixelSize: 10
        font.family: "Bahnschrift"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 6
        z: 3
    }
}
