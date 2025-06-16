import QtQuick
import pathpilot.controls

Item {
  id: root

  ScaleContainer {
    anchors.fill: parent
    referenceWidth: 1024
    referenceHeight: 800
    scale: 0.9

    Rectangle {
      anchors.fill: parent
      gradient: Gradient {
        GradientStop {
          position: 0.0
          color: "lightsteelblue"
        }
        GradientStop {
          position: 1.0
          color: "blue"
        }
      }
      border.color: "black"
      border.width: 2
    }
  }
}
