import QtQuick 2.15
import QtQuick.Controls 2.15

/*
  Стилизованное поле ввода текста.
  Назначение:
  - единый вид всех текстовых полей;
  - явная подсветка фокуса для лучшей читаемости состояния.

  Публичные свойства:
  - textColor/bgColor/borderColor/focusBorderColor: цветовая схема поля;
  - placeholderColor: цвет текста placeholder;
  - fontFamily: семейство шрифта.
*/
TextField {
    id: field

    property color textColor: "#1f2d3d"
    property color bgColor: "#f7fbff"
    property color borderColor: "#c8d9ea"
    property color focusBorderColor: "#0ea5e9"
    property color placeholderColor: "#8aa0b8"
    property string fontFamily: "Bahnschrift"

    color: textColor
    placeholderTextColor: placeholderColor
    palette.text: textColor
    palette.placeholderText: placeholderColor
    font.pixelSize: 13
    font.family: fontFamily
    selectByMouse: true
    padding: 9

    background: Rectangle {
        radius: 10
        color: bgColor
        border.width: field.activeFocus ? 2 : 1
        border.color: field.activeFocus ? focusBorderColor : borderColor
    }
}
