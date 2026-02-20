import QtQuick 2.15
import QtQuick.Controls 2.15

/*
  Стилизованный ComboBox для выбора устройств/параметров CAN.
  Назначение:
  - единая геометрия поля и pop-up списка;
  - поддержка как простых списков (string/number), так и моделей с textRole.

  Публичные свойства:
  - textColor/bgColor/borderColor/focusBorderColor: цвета поля;
  - popupColor/popupBorderColor: цвета выпадающего списка;
  - highlightedItemColor: фон выбранного пункта;
  - normalItemTextColor/highlightedItemTextColor: цвета текста пунктов;
  - fontFamily: семейство шрифта.
*/
ComboBox {
    id: combo

    property color textColor: "#1f2d3d"
    property color bgColor: "#f7fbff"
    property color borderColor: "#c8d9ea"
    property color focusBorderColor: "#0ea5e9"
    property color popupColor: "#ffffff"
    property color popupBorderColor: "#c8d9ea"
    property color highlightedItemColor: "#e6f0fb"
    property color normalItemTextColor: "#4a6078"
    property color highlightedItemTextColor: "#1c3f66"
    property string fontFamily: "Bahnschrift"

    implicitHeight: 40
    font.pixelSize: 13
    font.family: fontFamily

    contentItem: Text {
        leftPadding: 10
        rightPadding: 30
        text: combo.displayText
        font: combo.font
        color: textColor
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    // Индикатор стрелки рисуется Canvas-ом, чтобы не тянуть отдельный ресурс-иконку.
    indicator: Canvas {
        x: combo.width - width - 10
        y: combo.topPadding + (combo.availableHeight - height) / 2
        width: 11
        height: 7
        contextType: "2d"

        onPaint: {
            context.reset()
            context.moveTo(0, 0)
            context.lineTo(width, 0)
            context.lineTo(width / 2, height)
            context.closePath()
            context.fillStyle = "#6d8098"
            context.fill()
        }
    }

    background: Rectangle {
        radius: 10
        color: bgColor
        border.width: combo.activeFocus ? 2 : 1
        border.color: combo.activeFocus ? focusBorderColor : borderColor
    }

    popup: Popup {
        y: combo.height + 4
        width: combo.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 220)
        padding: 4

        background: Rectangle {
            radius: 10
            color: popupColor
            border.color: popupBorderColor
            border.width: 1
        }

        contentItem: ListView {
            clip: true
            model: combo.delegateModel
            currentIndex: combo.highlightedIndex
            spacing: 2
            implicitHeight: contentHeight

            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }

    delegate: ItemDelegate {
        width: combo.width - 8
        height: 32

        // Универсальное извлечение текста элемента модели:
        // 1) прямое значение string/number;
        // 2) значение по textRole для объектных моделей.
        property string delegateText: {
            if (typeof modelData === "string" || typeof modelData === "number") {
                return modelData
            }
            if (combo.textRole && modelData && modelData[combo.textRole] !== undefined) {
                return modelData[combo.textRole]
            }
            return ""
        }

        text: delegateText
        font.pixelSize: 13
        font.family: fontFamily

        contentItem: Text {
            text: parent.text
            font: parent.font
            color: parent.highlighted ? highlightedItemTextColor : normalItemTextColor
            verticalAlignment: Text.AlignVCenter
            leftPadding: 10
            elide: Text.ElideRight
        }

        background: Rectangle {
            radius: 7
            color: parent.highlighted ? highlightedItemColor : "transparent"
        }
    }
}
