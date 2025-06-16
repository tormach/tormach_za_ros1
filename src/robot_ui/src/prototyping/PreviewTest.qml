import QtQuick
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.preview
import pathpilot.robot.jog

ScaleContainer {
  id: root

  PathPilotNotebook {
    anchors.fill: parent
    anchors.margins: 10
    anchors.bottomMargin: 60

    PathPilotNotebookTab {
      title: "View"

      RvizPreviewController {
        id: controller2
        anchors.fill: parent
        mode: PreviewMode.View
      }
    }

    PathPilotNotebookTab {
      title: "Interactive"

      RvizPreviewController {
        id: controller
        anchors.fill: parent
        mode: PreviewMode.Interactive
      }
    }
  }

  InteractiveMarker {
    id: interactiveMarker
    fixedFrame: Config.data.preview.fixedFrame
  }

  PathPilotButton {
    id: toggleButton
    anchors.bottom: parent.bottom
    anchors.right: parent.right
    anchors.margins: 10
    text: "Move Tool"
    checkable: true
  }

  Timer {
    property bool up: true
    property double z: 0.0

    running: toggleButton.checked
    repeat: true
    interval: 300

    onTriggered: {
      z += (up ? 0.05 : -0.05);
      if (z >= 0.7) {
        up = false;
      } else if (z <= 0.0) {
        up = true;
      }
      interactiveMarker.pose.position = Qt.vector3d(0.5, 0.5, z + 0.8);
    }
  }
}
