import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotButton {
  id: root
  property alias icon_: iconItem.icon
  implicitWidth: text ? 120 : height

  Icon {
    id: iconItem
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.margins: parent.height * (root.text ? 0.16 : 0.12)
    anchors.rightMargin: root.text ? root.labelMargin * 2 : anchors.margins
    width: height
    opacity: root.enabled ? 1.0 : 0.3
    image {
      width: iconItem.width
      height: width
    }
  }
}
