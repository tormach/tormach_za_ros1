import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotNotebookTab {
  default property alias itemData: container.data
  title: "Untitled"

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
    anchors.leftMargin: Sizes.doubleMargin
    spacing: Sizes.singleSpacing
  }
}
