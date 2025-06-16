import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.panels.jog

UnscaledTestBase {
  id: root
  default property alias data_: container.data

  Item {
    id: container
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: bottomItem.top
    anchors.margins: Sizes.singleMargin
  }

  Item {
    id: bottomItem
    height: parent.height * 0.39
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    anchors.margins: Sizes.singleMargin
  }
}
