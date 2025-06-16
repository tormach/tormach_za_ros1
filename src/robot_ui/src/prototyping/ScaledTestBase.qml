import QtQuick
import pathpilot.base
import pathpilot.core
import pathpilot.controls

ScaleContainer {
  default property alias data_: container.data

  width: 900
  height: 700
  scale: 0.6

  TestBackground {
    id: container
    anchors.fill: parent
  }
}
