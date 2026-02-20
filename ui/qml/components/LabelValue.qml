import QtQuick 2.15
import QtQuick.Layouts 1.15

/*
  Пара "подпись + значение" для отображения диагностических данных.
  Назначение:
  - компактно показывать read-only информацию (производитель, модель, серийный номер и т.д.);
  - визуально разделять заголовок поля и его значение.

  Публичные свойства:
  - labelText: текст подписи;
  - valueText: текст значения;
  - labelColor/valueColor: цвета подписи и значения;
  - fontFamily: семейство шрифта.
*/
Item {
    id: root

    property string labelText: ""
    property string valueText: ""
    property color labelColor: "#607084"
    property color valueColor: "#1f2d3d"
    property string fontFamily: "Bahnschrift"
    property int labelWidth: Math.max(126, Math.min(170, Math.round(root.width * 0.34)))

    implicitHeight: 26
    implicitWidth: 320

    RowLayout {
        anchors.fill: parent
        spacing: 8

        Text {
            Layout.preferredWidth: root.labelWidth
            Layout.minimumWidth: root.labelWidth
            text: labelText + ":"
            color: labelColor
            font.pixelSize: 11
            font.family: fontFamily
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        Text {
            Layout.fillWidth: true
            text: valueText.length > 0 ? valueText : "-"
            color: valueColor
            font.pixelSize: 13
            font.family: fontFamily
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 10
            elide: Text.ElideNone
            verticalAlignment: Text.AlignVCenter
        }
    }
}
