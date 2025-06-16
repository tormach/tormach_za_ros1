import QtQuick
import pathpilot.core

Item {
  id: root
  property bool active: false
  property int size: 20
  property color higlightColor: Colors.cyan1
  property color defaultColor: Colors.white1
  property bool disabledColor: Colors.gray1
  width: size * 1.3
  height: size * 1.3

  Text {
    anchors.centerIn: parent
    anchors.verticalCenterOffset: root.size * -0.1
    anchors.horizontalCenterOffset: root.size * -0.05
    color: enabled ? (root.active ? root.higlightColor : root.defaultColor) : root.disabledColor
    font.family: Fonts.font3
    font.pixelSize: root.size
    style: Text.Outline
    styleColor: Colors.gray3
    text: "◀"
  }
}
