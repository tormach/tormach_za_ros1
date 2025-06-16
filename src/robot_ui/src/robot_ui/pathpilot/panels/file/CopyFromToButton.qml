import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotButton {
  id: root
  property alias icon_: iconItem.icon
  text: "Copy"
  implicitHeight: 90
  implicitWidth: 70

  contentItem: Item {
    Text {
      id: textLabel
      anchors.fill: parent
      anchors.topMargin: root.labelMargin
      anchors.leftMargin: root.labelMargin
      anchors.rightMargin: anchors.leftMargin
      horizontalAlignment: Text.AlignLeft
      font: root.font
      text: root.text
      color: !root.enabled ? root.disabledColor : (root.blink && d.blinkHelper) ? root.blinkColor : root.labelColor
      style: Text.Outline
      styleColor: root.shadowColor
    }
  }

  Icon {
    id: iconItem
    //anchors.bottom: parent.bottom
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.margins: parent.width * 0.25
    anchors.bottomMargin: root.labelMargin * 2
    height: width
    opacity: root.enabled ? 1.0 : 0.3
    image {
      width: iconItem.width
      height: width
    }
    icon: Icons.filepanel.left
  }
}
