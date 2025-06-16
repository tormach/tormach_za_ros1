import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.frame
import pathpilot.robot.preview
import pathpilot.handlers

FramesPanelBase {
  id: root
  title: qsTr("Frames")
  enabled: Handlers.app.modifyFramesAllowed

  readonly property QtObject _d: QtObject {
    id: d
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleMargin

    PathPilotNotebook {
      Layout.fillWidth: true
      Layout.fillHeight: true

      alignment: Qt.AlignTop
      visible: !d.wizardMode

      UserFramesTab {
        id: userFramesTab
      }

      ToolFramesTab {
        id: toolFramesTab
      }

      MachineFramesTab {
        id: machineFramesTab
      }
    }

    RvizPreviewController {
      id: previewController
      Layout.fillHeight: true
      Layout.preferredWidth: 500
      mode: PreviewMode.View
    }
  }
}
