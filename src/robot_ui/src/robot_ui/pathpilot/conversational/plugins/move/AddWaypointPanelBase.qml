import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

Item {
  id: root
  default property alias data_: container.data

  Rectangle {
    anchors.fill: parent
    color: Colors.white3

    PathPilotBackgroundImage {
      anchors.fill: parent
      anchors.margins: Sizes.thinBorder
    }
  }

  ColumnLayout {
    id: container
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
  }
}
