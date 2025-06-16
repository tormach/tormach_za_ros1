import QtQuick
import pathpilot.core
import pathpilot.controls

Item {
  id: root
  property bool focused: false
  property Item popupSpace: null

  signal forceFocus
  signal releaseFocus

  Rectangle {
    anchors.fill: parent
    color: Colors.white3

    PathPilotBackgroundImage {
      anchors.fill: parent
      anchors.margins: Sizes.thinBorder
    }
  }
}
